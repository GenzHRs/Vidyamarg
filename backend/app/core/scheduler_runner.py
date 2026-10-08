"""
Run exactly one scheduler process per deployment.
Provides cross-platform graceful shutdown on both Windows and POSIX systems.
"""
import asyncio
import logging
import signal
import sys
from app.core.scheduler import start_scheduler, shutdown_scheduler

logger = logging.getLogger("app.scheduler_runner")


async def main():
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _on_signal():
        logger.info("Scheduler runner received shutdown signal.")
        stopped.set()

    if sys.platform == "win32":
        # Windows ProactorEventLoop does not support loop.add_signal_handler
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, lambda s, f: loop.call_soon_threadsafe(_on_signal))
            except Exception as e:
                logger.debug("Could not attach signal handler %s: %e", sig, e)
    else:
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, _on_signal)
            except (NotImplementedError, RuntimeError):
                signal.signal(sig, lambda s, f: loop.call_soon_threadsafe(_on_signal))

    logger.info("Starting background scheduler runner...")
    start_scheduler()
    try:
        await stopped.wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Interrupted, shutting down scheduler runner...")
    finally:
        logger.info("Shutting down scheduler...")
        shutdown_scheduler()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
