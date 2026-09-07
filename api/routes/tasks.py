from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from api.schemas import TaskResponse, TaskReindexRequest
from api.dependencies import get_services, AppServices
from tasks.manager import TaskType

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by task status"),
    limit: int = Query(50, ge=1, le=200, description="Max tasks to return"),
    services: AppServices = Depends(get_services)
):
    tasks = services.task_manager.list_tasks(user_id=user_id, limit=limit, status=status)
    return [TaskResponse(**t.to_dict()) for t in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    services: AppServices = Depends(get_services)
):
    task = services.task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return TaskResponse(**task.to_dict())


def _execute_reindex(services: AppServices, user_id: int):
    """Background worker job to re-index all user memories into vector store."""
    ltm = services.get_long_term_memory(user_id)
    memories = ltm.chat_store.get_memories(user_id)

    reindexed_count = 0
    for mem in memories:
        content = f"{mem['memory_type']}: {mem['key']} = {mem['value']}"
        vector = ltm.embedding_model.embed(content)
        metadata = {
            "user_id": user_id,
            "memory_type": mem["memory_type"],
            "key": mem["key"],
            "scope": mem.get("scope") or "general"
        }
        ltm.vector_store.update(id=str(mem["id"]), vector=vector, metadata=metadata, document=content)
        reindexed_count += 1

    return {"reindexed_count": reindexed_count, "user_id": user_id}


@router.post("/reindex", response_model=TaskResponse)
def trigger_reindex(
    body: TaskReindexRequest,
    services: AppServices = Depends(get_services)
):
    user = services.chat_store.get_user(body.user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {body.user_id} not found")

    task_id = services.task_manager.submit(
        TaskType.BATCH_REINDEX,
        _execute_reindex,
        services,
        body.user_id,
        metadata={"user_id": body.user_id}
    )

    task = services.task_manager.get_task(task_id)
    return TaskResponse(**task.to_dict())
