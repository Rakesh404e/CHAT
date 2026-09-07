import time
from fastapi import APIRouter, HTTPException, Depends
from api.schemas import ChatRequest, ChatResponse
from api.dependencies import get_services, AppServices

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def send_chat_message(
    body: ChatRequest,
    services: AppServices = Depends(get_services)
):
    user = services.chat_store.get_user(body.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User {body.user_id} not found")

    start_time = time.time()
    
    agent = services.get_agent(
        user_id=body.user_id,
        conversation_id=body.conversation_id,
        async_processing=True if body.async_processing is None else body.async_processing
    )
    
    try:
        response_text = agent.chat(body.message, async_processing=body.async_processing)
        duration_ms = (time.time() - start_time) * 1000
        
        observability_data = agent.get_observability_report()
        
        # If conversation title is default or null, update title to user's first query
        messages = services.chat_store.get_recent_messages(body.conversation_id, limit=2)
        if len(messages) <= 2:
            title_snippet = body.message[:30] + ("..." if len(body.message) > 30 else "")
            conn = services.database.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE conversations SET title = ? WHERE id = ?", (title_snippet, body.conversation_id))
            conn.commit()
            conn.close()

        return ChatResponse(
            user_id=body.user_id,
            conversation_id=body.conversation_id,
            user_message=body.message,
            assistant_response=response_text,
            trace_id=observability_data.get("metrics", {}).get("last_trace_id", "trace-ok"),
            duration_ms=duration_ms,
            background_task_id=agent.get_last_task_id(),
            observability=observability_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")
