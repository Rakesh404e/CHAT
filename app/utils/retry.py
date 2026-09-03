import functools
import time
from typing import Callable, Any, Optional, Tuple, Type
from observability.logger import logger
from observability.metrics import metrics_collector


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 0.2,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    fallback_factory: Optional[Callable[..., Any]] = None,
    trace_id: Optional[str] = None
):
    """
    Decorator and utility for executing functions with exponential backoff retries.
    """
    def decorator(func: Callable[..., Any]):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    metrics_collector.record_retry()
                    active_trace = trace_id or kwargs.get("trace_id", "N/A")

                    logger.warning(
                        f"Attempt {attempt}/{max_retries} failed for function '{func.__name__}': {e}. Retrying in {delay:.2f}s...",
                        trace_id=active_trace,
                        attempt=attempt,
                        error=str(e)
                    )

                    if attempt < max_retries:
                        time.sleep(delay)
                        delay *= backoff_factor

            logger.error(
                f"All {max_retries} attempts failed for function '{func.__name__}'.",
                trace_id=trace_id or "N/A",
                error=str(last_exception)
            )

            if fallback_factory:
                logger.info(f"Executing fallback mechanism for '{func.__name__}'.", trace_id=trace_id or "N/A")
                return fallback_factory(*args, **kwargs)

            raise last_exception

        return wrapper
    return decorator
