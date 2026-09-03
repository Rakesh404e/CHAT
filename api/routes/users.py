from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from api.schemas import UserResponse, UserCreate
from api.dependencies import get_services, AppServices

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=UserResponse)
def create_user(services: AppServices = Depends(get_services)):
    user_id = services.chat_store.create_user()
    return UserResponse(id=user_id)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, services: AppServices = Depends(get_services)):
    user = services.chat_store.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return UserResponse(id=user_id)


@router.get("", response_model=List[UserResponse])
def list_users(services: AppServices = Depends(get_services)):
    conn = services.database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, created_at FROM users ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [UserResponse(id=r[0], created_at=str(r[1]) if r[1] else None) for r in rows]
