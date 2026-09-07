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
    async_processing: Optional[bool] = True


class ChatResponse(BaseModel):
    user_id: int
    conversation_id: int
    user_message: str
    assistant_response: str
    trace_id: str
    duration_ms: float
    background_task_id: Optional[str] = None
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


class TaskResponse(BaseModel):
    task_id: str
    task_type: str
    status: str
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    result: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskReindexRequest(BaseModel):
    user_id: int


class ObservabilityReport(BaseModel):
    conversation_id: int
    context_stats: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
