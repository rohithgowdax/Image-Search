"""Health check endpoint."""

from fastapi import APIRouter, Request
from app.models.schemas import HealthResponse
from app.services.vector_store_service import VectorStoreService

router = APIRouter()
vector_store = VectorStoreService()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
)
async def health(request: Request):
    embedding_service = getattr(request.app.state, "embedding_service", None)
    model_loaded = embedding_service.is_ready if embedding_service else False
    
    stats = vector_store.collection_stats()
    
    return HealthResponse(
        status="healthy",
        model_loaded=model_loaded,
        collection_count=stats["total_images"],
        version="1.0.0",
    )
