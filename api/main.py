import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure app directory is added to Python path
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from api.routes import users, conversations, chat, memory, observability, tasks
from api.dependencies import get_services

app = FastAPI(
    title="AI Agent Chatbot API",
    description="FastAPI Backend for AI Chatbot with Short/Long Term Memory, Async Background Processing & Observability",
    version="1.1.0"
)

# CORS setup for local React/Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(users.router)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(memory.router)
app.include_router(observability.router)
app.include_router(tasks.router)


@app.on_event("startup")
def startup_event():
    # Warm up database and services
    get_services()


@app.on_event("shutdown")
def shutdown_event():
    # Graceful shutdown of background workers
    services = get_services()
    if hasattr(services, "task_manager"):
        services.task_manager.shutdown(wait=False)


@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": "AI Agent API",
        "features": ["dual_store_ltm", "async_background_workers", "observability_telemetry"],
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
