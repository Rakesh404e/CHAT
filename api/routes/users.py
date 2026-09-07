from fastapi import APIRouter, HTTPException, Depends
from typing import List
from api.schemas import UserResponse, UserCreate
from api.dependencies import get_services, AppServices

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=UserResponse)
def create_user(services: AppServices = Depends(get_services)):
    user_id = services.chat_store.create_user()
    user = services.chat_store.get_user(user_id)
    created_at = str(user[1]) if user and len(user) > 1 and user[1] else None
    return UserResponse(id=user_id, created_at=created_at)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, services: AppServices = Depends(get_services)):
    user = services.chat_store.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    created_at = str(user[1]) if len(user) > 1 and user[1] else None
    return UserResponse(id=user_id, created_at=created_at)


@router.get("", response_model=List[UserResponse])
def list_users(services: AppServices = Depends(get_services)):
    conn = services.database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, created_at FROM users ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [UserResponse(id=r[0], created_at=str(r[1]) if r[1] else None) for r in rows]


@router.delete("/{user_id}")
def delete_user(user_id: int, services: AppServices = Depends(get_services)):
    user = services.chat_store.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    # 1. Clean up vector storage memories & query cache
    ltm = services.get_long_term_memory(user_id)
    ltm.delete_all_memories()

    # 2. Delete user and associated conversations/messages from SQLite
    services.chat_store.delete_user(user_id)
    return {"status": "success", "deleted_user_id": user_id}
