from fastapi import APIRouter, Depends
from observability.metrics import metrics_collector
from api.dependencies import get_services, AppServices

router = APIRouter(prefix="/api/observability", tags=["observability"])


@router.get("/metrics")
def get_system_metrics(services: AppServices = Depends(get_services)):
    return {
        "status": "active",
        "provider": services.config.provider,
        "model_name": services.config.model_name,
        "embedding_model": services.config.embedding_model,
        "metrics": metrics_collector.get_metrics_summary()
    }
