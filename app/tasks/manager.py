import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from enum import Enum
from typing import Callable, Any, Dict, List, Optional
from dataclasses import dataclass, field

from observability.logger import logger
from observability.metrics import metrics_collector


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    MEMORY_EXTRACTION = "memory_extraction"
    SUMMARIZATION = "summarization"
    BATCH_REINDEX = "batch_reindex"
    CACHE_WARMUP = "cache_warmup"
    GENERAL = "general"


@dataclass
class TaskRecord:
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    result: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    _done_event: threading.Event = field(default_factory=threading.Event, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": round(self.duration_ms, 2) if self.duration_ms is not None else None,
            "error": self.error,
            "result": self.result if isinstance(self.result, (str, int, float, bool, dict, list)) or self.result is None else str(self.result),
            "metadata": self.metadata
        }


class AsyncTaskManager:
    """
    In-process asynchronous background task manager powered by ThreadPoolExecutor.
    Handles background execution, state tracking, observability logging, and metrics.
    """

    def __init__(self, max_workers: int = 4, max_history: int = 500):
        self.max_workers = max_workers
        self.max_history = max_history
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="async_task_worker")
        self._tasks: Dict[str, TaskRecord] = {}
        self._futures: Dict[str, Future] = {}
        self._lock = threading.RLock()
        self._is_shutdown = False

    def submit(
        self,
        task_type: str,
        fn: Callable,
        *args,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        with self._lock:
            if self._is_shutdown:
                raise RuntimeError("AsyncTaskManager is shut down and cannot accept new tasks.")

            task_id = f"task_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
            meta = metadata or {}
            trace_id = meta.get("trace_id", "N/A")

            record = TaskRecord(
                task_id=task_id,
                task_type=task_type,
                status=TaskStatus.PENDING,
                created_at=time.time(),
                metadata=meta
            )
            self._tasks[task_id] = record
            self._evict_old_tasks()

            metrics_collector.record_task_started()
            logger.info(
                f"Submitted background task {task_id} (type: {task_type})",
                trace_id=trace_id,
                task_id=task_id,
                task_type=task_type
            )

            future = self._executor.submit(self._run_task, task_id, fn, *args, **kwargs)
            self._futures[task_id] = future
            return task_id

    def _run_task(self, task_id: str, fn: Callable, *args, **kwargs):
        with self._lock:
            record = self._tasks.get(task_id)
            if not record:
                return
            record.status = TaskStatus.RUNNING
            record.started_at = time.time()

        trace_id = record.metadata.get("trace_id", "N/A")
        start_time = time.time()
        logger.info(
            f"Executing background task {task_id} [{record.task_type}]",
            trace_id=trace_id,
            task_id=task_id
        )

        try:
            result = fn(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            with self._lock:
                record.status = TaskStatus.COMPLETED
                record.completed_at = time.time()
                record.duration_ms = duration_ms
                record.result = result
                record._done_event.set()

            metrics_collector.record_task_event(record.task_type, duration_ms, success=True)
            logger.info(
                f"Completed background task {task_id} [{record.task_type}] in {duration_ms:.2f}ms",
                trace_id=trace_id,
                task_id=task_id,
                duration_ms=duration_ms
            )
            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            with self._lock:
                record.status = TaskStatus.FAILED
                record.completed_at = time.time()
                record.duration_ms = duration_ms
                record.error = str(e)
                record._done_event.set()

            metrics_collector.record_task_event(record.task_type, duration_ms, success=False)
            logger.error(
                f"Failed background task {task_id} [{record.task_type}]: {e}",
                trace_id=trace_id,
                task_id=task_id,
                error=str(e),
                duration_ms=duration_ms
            )
            return None

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        with self._lock:
            return self._tasks.get(task_id)

    def list_tasks(
        self,
        user_id: Optional[int] = None,
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[TaskRecord]:
        with self._lock:
            tasks = list(self._tasks.values())

        if user_id is not None:
            tasks = [t for t in tasks if t.metadata.get("user_id") == user_id]

        if status:
            tasks = [t for t in tasks if t.status.value == status]

        # Order by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Optional[TaskRecord]:
        with self._lock:
            record = self._tasks.get(task_id)
        if not record:
            return None

        record._done_event.wait(timeout=timeout)
        return record

    def wait_all(self, timeout: Optional[float] = None) -> bool:
        """
        Waits for all currently pending or running tasks to finish.
        Returns True if all completed within timeout, False otherwise.
        """
        with self._lock:
            active_events = [
                t._done_event for t in self._tasks.values()
                if t.status in (TaskStatus.PENDING, TaskStatus.RUNNING)
            ]

        start = time.time()
        for ev in active_events:
            remaining = None if timeout is None else max(0.0, timeout - (time.time() - start))
            if not ev.wait(timeout=remaining):
                return False
        return True

    def _evict_old_tasks(self):
        """Keep task registry bounded to prevent memory leaks."""
        if len(self._tasks) > self.max_history:
            # Find finished tasks sorted by creation time
            finished = [
                (t_id, t) for t_id, t in self._tasks.items()
                if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
            ]
            finished.sort(key=lambda item: item[1].created_at)
            to_remove = len(self._tasks) - self.max_history
            for t_id, _ in finished[:to_remove]:
                self._tasks.pop(t_id, None)
                self._futures.pop(t_id, None)

    def shutdown(self, wait: bool = True):
        with self._lock:
            self._is_shutdown = True
        self._executor.shutdown(wait=wait)


# Global singleton task manager instance
task_manager = AsyncTaskManager()
