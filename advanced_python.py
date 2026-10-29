"""Small, runnable demonstrations for CO3: threads, processes and asyncio."""
import asyncio
from concurrent.futures import ProcessPoolExecutor
from threading import Thread


def _count_statuses(statuses):
    """Top-level function so multiprocessing can pickle it."""
    present = sum(1 for status in statuses if status == "Present")
    absent = sum(1 for status in statuses if status == "Absent")
    return {"present": present, "absent": absent, "total": len(statuses)}


def run_thread_demo(callback):
    """Run a calculation in a background thread."""
    def worker():
        result = sum(range(1, 100001))
        callback(
            "Threading demo completed in background. "
            f"Sum of 1 to 100000 = {result:,}"
        )

    Thread(target=worker, daemon=True).start()


def run_process_demo(statuses):
    """Calculate status counts in a separate process."""
    with ProcessPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_count_statuses, statuses)
        return future.result(timeout=10)


async def _async_task():
    await asyncio.sleep(0.25)
    return "Asyncio demo completed: asynchronous task finished."


def run_async_demo(callback):
    """Run an asyncio task without blocking the Tkinter event loop."""
    def worker():
        callback(asyncio.run(_async_task()))

    Thread(target=worker, daemon=True).start()
