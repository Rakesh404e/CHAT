from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from api.schemas import ConversationCreate, ConversationResponse, MessageItem
from api.dependencies import get_services, AppServices

router = APIRouter(tags=["conversations"])


@router.post("/api/users/{user_id}/conversations", response_model=ConversationResponse)
def create_conversation(
    user_id: int,
    body: ConversationCreate,
    services: AppServices = Depends(get_services)
):
    user = services.chat_store.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
    title = body.title or "New Conversation"
    conv_id = services.chat_store.create_conversation(user_id=user_id, title=title)
    
    return ConversationResponse(
        id=conv_id,
        user_id=user_id,
        title=title,
        summary=None
    )


@router.get("/api/users/{user_id}/conversations", response_model=List[ConversationResponse])
def get_user_conversations(
    user_id: int,
    services: AppServices = Depends(get_services)
):
    user = services.chat_store.get_user(user_id)
    if user is None:
        # Create user automatically if requested or return empty list
        return []
        
    conversations = services.chat_store.get_user_conversations(user_id)
    result = []
    for c in conversations:
        summary = services.chat_store.get_summary(c["id"])
        result.append(ConversationResponse(
            id=c["id"],
            user_id=user_id,
            title=c["title"],
            summary=summary
        ))
    return result


@router.get("/api/conversations/{conversation_id}/messages", response_model=List[MessageItem])
def get_conversation_messages(
    conversation_id: int,
    limit: int = Query(50, ge=1, le=200),
    services: AppServices = Depends(get_services)
):
    messages = services.chat_store.get_recent_messages(conversation_id, limit=limit)
    return [MessageItem(role=m["role"], content=m["content"]) for m in messages]
