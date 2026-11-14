"""Collection management API."""

from fastapi import APIRouter, HTTPException, Query, Request
from typing import List
import logging

from app.models.schemas import CollectionStats, ImageMetadata
from app.services.vector_store_service import VectorStoreService
from app.utils.image_utils import build_image_url

router = APIRouter()
logger = logging.getLogger(__name__)
vector_store = VectorStoreService()


@router.get(
    "/collection/stats",
    response_model=CollectionStats,
    summary="Collection statistics",
)
async def get_stats():
    """Return stats about the indexed image collection."""
    return CollectionStats(**vector_store.collection_stats())


@router.get(
    "/collection/images",
    summary="List all indexed images",
    description="Paginated list of all images in the collection.",
)
async def list_images(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items, total = vector_store.list_images(limit=limit, offset=offset)
    base_url = str(request.base_url).rstrip("/")
    
    images = []
    for item in items:
        meta = item.get("metadata") or {}
        tags_raw = meta.get("tags", "")
        tags = [t for t in tags_raw.split(",") if t] if tags_raw else []
        url = meta.get("url", build_image_url(meta.get("filename", ""), base_url))
        images.append({
            "id": item["id"],
            "filename": meta.get("filename", ""),
            "original_filename": meta.get("original_filename", ""),
            "url": url,
            "width": int(meta.get("width", 0)),
            "height": int(meta.get("height", 0)),
            "format": meta.get("format", ""),
            "file_size": int(meta.get("file_size", 0)),
            "tags": tags,
            "description": meta.get("description", ""),
            "indexed_at": meta.get("indexed_at", ""),
        })
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "images": images,
    }


@router.get(
    "/collection/images/{image_id}",
    summary="Get image details",
)
async def get_image(request: Request, image_id: str):
    """Get details of a specific indexed image."""
    record = vector_store.get_image(image_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Image '{image_id}' not found")
    
    meta = record.get("metadata") or {}
    base_url = str(request.base_url).rstrip("/")
    url = meta.get("url", build_image_url(meta.get("filename", ""), base_url))
    tags_raw = meta.get("tags", "")
    tags = [t for t in tags_raw.split(",") if t] if tags_raw else []
    
    return {
        "id": record["id"],
        "filename": meta.get("filename", ""),
        "original_filename": meta.get("original_filename", ""),
        "url": url,
        "width": int(meta.get("width", 0)),
        "height": int(meta.get("height", 0)),
        "format": meta.get("format", ""),
        "file_size": int(meta.get("file_size", 0)),
        "tags": tags,
        "description": meta.get("description", ""),
        "indexed_at": meta.get("indexed_at", ""),
    }


@router.delete(
    "/collection/clear",
    summary="Clear all indexed images",
    description="⚠️ Permanently deletes all images from the index.",
)
async def clear_collection():
    deleted = vector_store.clear_collection()
    return {"message": f"Cleared {deleted} images from the collection"}
