import time
from contextlib import contextmanager

class Timer:
    """
    Simple utility to measure elapsed time.
    """
    def __init__(self):
        self.start_time = time.perf_counter()

    def stop(self) -> float:
        """
        Returns the duration in seconds since initialization.
        """
        return time.perf_counter() - self.start_time

@contextmanager
def profile_operation(name: str):
    """
    Context manager for easy profiling of code blocks.
    Logs duration automatically upon exit.
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        from ..services.metrics_service import record_metric
        record_metric(f"profile_{name}", value=duration)
