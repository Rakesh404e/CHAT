from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict


class UserCreate(BaseModel):
    pass


class UserResponse(BaseModel):
    id: int
    created_at: Optional[str] = None


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str] = None
    summary: Optional[str] = None
    created_at: Optional[str] = None


class MessageItem(BaseModel):
    id: Optional[int] = None
    role: str
    content: str
    created_at: Optional[str] = None


class ChatRequest(BaseModel):
    user_id: int
    conversation_id: int
    message: str


class ChatResponse(BaseModel):
    user_id: int
    conversation_id: int
    user_message: str
    assistant_response: str
    trace_id: str
    duration_ms: float
    observability: Optional[Dict[str, Any]] = None


class MemoryItem(BaseModel):
    id: int
    user_id: Optional[int] = None
    memory_type: str
    key: str
    value: str
    scope: Optional[str] = None


class MemorySearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class MemorySearchItem(BaseModel):
    memory_type: str
    key: str
    value: str
    scope: Optional[str] = None


class ObservabilityReport(BaseModel):
    conversation_id: int
    context_stats: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
