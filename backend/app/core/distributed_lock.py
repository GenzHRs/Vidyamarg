"""
Distributed Lock — Redis-backed distributed lock with graceful fallback to file/memory locking.

Guarantees:
- Redis primary distributed lock (nx=True, ex=ttl_seconds) using token-checked release.
- Graceful degradation to file-based or in-memory lock if Redis is unavailable or disconnected.
- Async context manager and decorator patterns for easy use across jobs and background tasks.
"""
from __future__ import annotations

import asyncio
import functools
import hashlib
import logging
import os
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger("app.core.distributed_lock")

# Shared in-memory lock state for memory fallback
_mem_lock = asyncio.Lock()
_memory_locks: dict[str, tuple[str, float]] = {}

# Lua script for atomic token-validated release in Redis
_RELEASE_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


def _get_lock_dir() -> Path:
    """Returns local lock directory, creating it if necessary."""
    try:
        from app.core.config import settings
        storage_base = getattr(settings, "STORAGE_DIR", "storage")
        lock_dir = Path(storage_base) / "locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        return lock_dir
    except Exception:
        fallback = Path(tempfile.gettempdir()) / "vidyamarg_locks"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


class DistributedLock:
    """
    Distributed lock with Redis primary and file/in-memory fallback.
    """

    def __init__(self, key: str, ttl_seconds: int = 60, lock_id: Optional[str] = None):
        self.raw_key = key
        self.key = f"vidyamarg:lock:{key}"
        self.ttl_seconds = ttl_seconds
        self.token = lock_id or str(uuid.uuid4())
        self._backend: Optional[str] = None
        self._is_acquired: bool = False

    @property
    def is_acquired(self) -> bool:
        return self._is_acquired

    async def acquire(self) -> bool:
        """Attempts to acquire the lock across Redis, file, or in-memory fallbacks."""
        # 1. Attempt Redis
        try:
            from app.core.redis_client import get_redis
            client = await get_redis()
            if client is not None:
                # nx=True sets only if not exists, ex=ttl_seconds sets expiry in seconds
                acquired = await client.set(self.key, self.token, nx=True, ex=self.ttl_seconds)
                if acquired:
                    self._backend = "redis"
                    self._is_acquired = True
                    logger.debug("Acquired Redis distributed lock for %s", self.key)
                    return True
                else:
                    logger.debug("Redis distributed lock busy for %s", self.key)
                    return False
        except Exception as exc:
            logger.debug("Redis lock acquisition failed, falling back to local: %s", exc)

        # 2. Attempt File-based lock (cross-process on same node)
        try:
            lock_dir = _get_lock_dir()
            filename = hashlib.sha256(self.key.encode()).hexdigest() + ".lock"
            file_path = lock_dir / filename
            now = time.time()

            # Clean expired lock file if present
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8").strip()
                    if ":" in content:
                        _, exp_str = content.split(":", 1)
                        if now < float(exp_str):
                            # Lock still actively held by another process
                            return False
                    # Expired lock file — attempt removal
                    file_path.unlink(missing_ok=True)
                except Exception:
                    pass

            # Try atomic file creation
            fd = os.open(str(file_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with open(fd, "w", encoding="utf-8") as f:
                f.write(f"{self.token}:{now + self.ttl_seconds}")
            self._backend = "file"
            self._is_acquired = True
            logger.debug("Acquired file-based lock for %s", self.key)
            return True
        except FileExistsError:
            return False
        except Exception as exc:
            logger.debug("File-based lock failed, falling back to in-memory: %s", exc)

        # 3. Fallback to in-memory lock
        async with _mem_lock:
            now_mono = time.monotonic()
            if self.key in _memory_locks:
                cur_token, cur_exp = _memory_locks[self.key]
                if now_mono < cur_exp:
                    return False
            _memory_locks[self.key] = (self.token, now_mono + self.ttl_seconds)
            self._backend = "memory"
            self._is_acquired = True
            logger.debug("Acquired in-memory lock for %s", self.key)
            return True

    async def release(self) -> bool:
        """Releases the lock if held by this instance."""
        if not self._is_acquired:
            return False

        released = False
        try:
            if self._backend == "redis":
                from app.core.redis_client import get_redis
                client = await get_redis()
                if client is not None:
                    res = await client.eval(_RELEASE_LUA, 1, self.key, self.token)
                    released = bool(res)
            elif self._backend == "file":
                lock_dir = _get_lock_dir()
                filename = hashlib.sha256(self.key.encode()).hexdigest() + ".lock"
                file_path = lock_dir / filename
                if file_path.exists():
                    content = file_path.read_text(encoding="utf-8").strip()
                    if ":" in content:
                        tok, _ = content.split(":", 1)
                        if tok == self.token:
                            file_path.unlink(missing_ok=True)
                            released = True
            elif self._backend == "memory":
                async with _mem_lock:
                    if self.key in _memory_locks:
                        tok, _ = _memory_locks[self.key]
                        if tok == self.token:
                            del _memory_locks[self.key]
                            released = True
        except Exception as exc:
            logger.warning("Error releasing lock for %s (%s): %s", self.key, self._backend, exc)
        finally:
            self._is_acquired = False
            self._backend = None

        return released


@asynccontextmanager
async def distributed_lock(key: str, ttl_seconds: int = 60, lock_id: Optional[str] = None):
    """
    Async context manager for acquiring a distributed lock.

    Usage:
        async with distributed_lock("job_sync", ttl_seconds=300) as acquired:
            if not acquired:
                return
            # critical section
    """
    lock = DistributedLock(key, ttl_seconds=ttl_seconds, lock_id=lock_id)
    acquired = await lock.acquire()
    try:
        yield acquired
    finally:
        if acquired:
            await lock.release()


def locked_job(key: str, ttl_seconds: int = 60):
    """
    Decorator for async job functions to prevent concurrent execution.
    If the lock cannot be acquired, logs a message and skips execution cleanly.
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            async with distributed_lock(key, ttl_seconds=ttl_seconds) as acquired:
                if not acquired:
                    logger.info("Job '%s' is already running on another instance/worker. Skipping.", key)
                    return None
                return await func(*args, **kwargs)
        return wrapper
    return decorator
