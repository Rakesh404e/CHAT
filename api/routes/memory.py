from fastapi import APIRouter, HTTPException, Depends
from typing import List
from api.schemas import MemoryItem, MemorySearchRequest, MemorySearchItem
from api.dependencies import get_services, AppServices

router = APIRouter(tags=["memory"])


@router.get("/api/users/{user_id}/memories", response_model=List[MemoryItem])
def get_user_memories(
    user_id: int,
    services: AppServices = Depends(get_services)
):
    ltm = services.get_long_term_memory(user_id)
    memories = ltm.get_memories()
    return [
        MemoryItem(
            id=m["id"],
            user_id=user_id,
            memory_type=m["memory_type"],
            key=m["key"],
            value=m["value"],
            scope=m.get("scope")
        )
        for m in memories
    ]


@router.post("/api/users/{user_id}/memories/search")
def search_user_memories(
    user_id: int,
    body: MemorySearchRequest,
    services: AppServices = Depends(get_services)
):
    ltm = services.get_long_term_memory(user_id)
    results = ltm.search_memories(query=body.query, top_k=body.top_k or 5)
    return {"query": body.query, "results": results}


@router.delete("/api/memories/{memory_id}")
def delete_memory(
    memory_id: int,
    user_id: int,
    services: AppServices = Depends(get_services)
):
    ltm = services.get_long_term_memory(user_id)
    ltm.delete_memory(memory_id)
    return {"status": "success", "deleted_id": memory_id}


@router.delete("/api/users/{user_id}/memories")
def delete_all_user_memories(
    user_id: int,
    services: AppServices = Depends(get_services)
):
    ltm = services.get_long_term_memory(user_id)
    count = ltm.delete_all_memories()
    return {"status": "success", "deleted_count": count}
