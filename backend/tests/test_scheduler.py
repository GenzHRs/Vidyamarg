"""
Tests for DistributedLock and Scheduler Execution Guards.
Verifies distributed locking (memory, file, Redis) and duplicate job prevention.
"""
import asyncio
from unittest.mock import AsyncMock, patch
import pytest

from app.core.distributed_lock import DistributedLock, distributed_lock, locked_job
from app.core.scheduler import scheduler, start_scheduler, shutdown_scheduler


@pytest.mark.asyncio
async def test_distributed_lock_basic_acquire_and_release():
    """Verify lock can be acquired and released, blocking concurrent access."""
    lock_key = "test:basic_lock"
    
    async with distributed_lock(lock_key, ttl_seconds=10) as acquired1:
        assert acquired1 is True
        
        # Concurrent lock attempt on the same key must fail
        async with distributed_lock(lock_key, ttl_seconds=10) as acquired2:
            assert acquired2 is False

    # After exiting the context, lock is released and can be acquired again
    async with distributed_lock(lock_key, ttl_seconds=10) as acquired3:
        assert acquired3 is True


@pytest.mark.asyncio
async def test_distributed_lock_ttl_expiry():
    """Verify that after TTL expires, the lock can be acquired by another caller."""
    lock_key = "test:ttl_lock"
    
    lock1 = DistributedLock(lock_key, ttl_seconds=1)
    acquired1 = await lock1.acquire()
    assert acquired1 is True
    
    # Try immediately — should fail
    lock2 = DistributedLock(lock_key, ttl_seconds=1)
    acquired2 = await lock2.acquire()
    assert acquired2 is False
    
    # Wait for TTL to elapse
    await asyncio.sleep(1.1)
    
    # Now lock2 should be able to acquire
    acquired3 = await lock2.acquire()
    assert acquired3 is True
    await lock2.release()


@pytest.mark.asyncio
async def test_locked_job_decorator_skips_concurrent():
    """Verify @locked_job decorator prevents duplicate concurrent execution."""
    execution_count = 0
    gate = asyncio.Event()

    @locked_job("test:concurrent_job", ttl_seconds=5)
    async def sample_job():
        nonlocal execution_count
        execution_count += 1
        await gate.wait()
        return "completed"

    # Start first job execution in background
    task1 = asyncio.create_task(sample_job())
    # Yield to let task1 acquire the lock
    await asyncio.sleep(0.05)

    # Trigger second job execution while task1 holds the lock
    task2_result = await sample_job()
    assert task2_result is None  # Skipped!

    # Release gate so task1 can finish
    gate.set()
    task1_result = await task1
    assert task1_result == "completed"
    assert execution_count == 1  # Only executed once


@pytest.mark.asyncio
async def test_redis_distributed_lock_mock():
    """Verify distributed lock interacts properly with Redis commands and Lua script."""
    mock_redis = AsyncMock()
    mock_redis.set.return_value = True
    mock_redis.eval.return_value = 1

    with patch("app.core.redis_client.get_redis", return_value=mock_redis):
        lock = DistributedLock("mock_job", ttl_seconds=30)
        acquired = await lock.acquire()
        assert acquired is True
        assert lock._backend == "redis"
        mock_redis.set.assert_awaited_once_with(
            "vidyamarg:lock:mock_job", lock.token, nx=True, ex=30
        )

        released = await lock.release()
        assert released is True
        mock_redis.eval.assert_awaited_once()


def test_scheduler_job_registrations():
    """Verify all four background jobs are properly registered in APScheduler."""
    try:
        start_scheduler()
        job_ids = [job.id for job in scheduler.get_jobs()]
        expected_jobs = [
            "run_periodic_job_sync",
            "run_hourly_recommendation_updates",
            "run_periodic_alerts",
            "run_expire_old_telegram_jobs",
        ]
        for expected in expected_jobs:
            assert expected in job_ids, f"Expected {expected} to be registered in scheduler"
    finally:
        shutdown_scheduler()
