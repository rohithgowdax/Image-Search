"""
Search API — similarity search endpoints.

Supports:
- Image similarity search (upload query image)
- Text-based search (search by text description)
- Multi-modal search (image + text)
- Reverse image search (find near-duplicates)
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Form, Query
from typing import Optional, List
import logging
import time
import numpy as np

from app.models.schemas import SearchResponse, SearchResult
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.utils.image_utils import validate_image, build_image_url
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

vector_store = VectorStoreService()


def _build_result(item: dict, base_url: str) -> SearchResult:
    """Convert a vector store result to a SearchResult schema."""
    meta = item["metadata"]
    url = meta.get("url", build_image_url(meta.get("filename", ""), base_url))
    tags_raw = meta.get("tags", "")
    tags = [t for t in tags_raw.split(",") if t] if tags_raw else []
    
    return SearchResult(
        id=item["id"],
        filename=meta.get("filename", ""),
        url=url,
        similarity_score=item["similarity_score"],
        distance=item["distance"],
        metadata=meta,
        width=int(meta.get("width", 0)) or None,
        height=int(meta.get("height", 0)) or None,
        format=meta.get("format"),
        description=meta.get("description") or None,
        tags=tags,
    )


@router.post(
    "/search/image",
    response_model=SearchResponse,
    summary="Search by image",
    description="Upload an image to find visually similar images from the indexed collection.",
)
async def search_by_image(
    request: Request,
    file: UploadFile = File(..., description="Query image"),
    top_k: int = Form(default=5, ge=1, le=50, description="Number of results"),
    min_similarity: float = Form(default=0.0, ge=0.0, le=1.0),
):
    start = time.time()
    file_bytes = await file.read()
    
    valid, msg = validate_image(file_bytes, file.filename)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)
    
    embedding_service: EmbeddingService = request.app.state.embedding_service
    query_embedding = await embedding_service.embed_image(file_bytes)
    
    raw_results = vector_store.search_similar(
        query_embedding=query_embedding,
        top_k=top_k,
        min_similarity=min_similarity,
    )
    
    base_url = str(request.base_url).rstrip("/")
    results = [_build_result(r, base_url) for r in raw_results]
    
    elapsed = (time.time() - start) * 1000
    
    return SearchResponse(
        query_image_id=None,
        total_results=len(results),
        search_time_ms=round(elapsed, 2),
        results=results,
    )


@router.get(
    "/search/text",
    response_model=SearchResponse,
    summary="Search by text description",
    description="Search the image collection using a natural language text query (CLIP zero-shot).",
)
async def search_by_text(
    request: Request,
    q: str = Query(..., description="Text query, e.g. 'a red sports car on a mountain road'"),
    top_k: int = Query(default=5, ge=1, le=50),
    min_similarity: float = Query(default=0.0, ge=0.0, le=1.0),
):
    start = time.time()
    
    embedding_service: EmbeddingService = request.app.state.embedding_service
    query_embedding = await embedding_service.embed_text(q)
    
    raw_results = vector_store.search_similar(
        query_embedding=query_embedding,
        top_k=top_k,
        min_similarity=min_similarity,
    )
    
    base_url = str(request.base_url).rstrip("/")
    results = [_build_result(r, base_url) for r in raw_results]
    
    elapsed = (time.time() - start) * 1000
    
    return SearchResponse(
        query_text=q,
        total_results=len(results),
        search_time_ms=round(elapsed, 2),
        results=results,
    )


@router.post(
    "/search/multimodal",
    response_model=SearchResponse,
    summary="Multi-modal search (image + text)",
    description="Combine an image and a text description to refine search. alpha=1.0 is pure image, 0.0 is pure text.",
)
async def search_multimodal(
    request: Request,
    file: UploadFile = File(..., description="Query image"),
    text: str = Form(..., description="Text description to refine results"),
    alpha: float = Form(default=0.7, ge=0.0, le=1.0, description="Image weight (0=text only, 1=image only)"),
    top_k: int = Form(default=5, ge=1, le=50),
    min_similarity: float = Form(default=0.0, ge=0.0, le=1.0),
):
    start = time.time()
    file_bytes = await file.read()
    
    valid, msg = validate_image(file_bytes, file.filename)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)
    
    embedding_service: EmbeddingService = request.app.state.embedding_service
    query_embedding = await embedding_service.embed_image_text(file_bytes, text, alpha=alpha)
    
    raw_results = vector_store.search_similar(
        query_embedding=query_embedding,
        top_k=top_k,
        min_similarity=min_similarity,
    )
    
    base_url = str(request.base_url).rstrip("/")
    results = [_build_result(r, base_url) for r in raw_results]
    
    elapsed = (time.time() - start) * 1000
    
    return SearchResponse(
        query_text=f"[image] + {text}",
        total_results=len(results),
        search_time_ms=round(elapsed, 2),
        results=results,
    )


@router.get(
    "/search/reverse/{image_id}",
    response_model=SearchResponse,
    summary="Reverse image search",
    description="Find images similar to an already-indexed image by its ID.",
)
async def reverse_search(
    request: Request,
    image_id: str,
    top_k: int = Query(default=5, ge=1, le=50),
    include_self: bool = Query(default=False, description="Include the query image itself"),
    min_similarity: float = Query(default=0.0, ge=0.0, le=1.0),
):
    start = time.time()
    
    # Fetch the stored embedding
    embedding = vector_store.get_image_embedding(image_id)
    if embedding is None:
        raise HTTPException(status_code=404, detail=f"Image '{image_id}' not found in index")
    
    exclude = None if include_self else [image_id]
    
    raw_results = vector_store.search_similar(
        query_embedding=embedding,
        top_k=top_k,
        exclude_ids=exclude,
        min_similarity=min_similarity,
    )
    
    base_url = str(request.base_url).rstrip("/")
    results = [_build_result(r, base_url) for r in raw_results]
    
    elapsed = (time.time() - start) * 1000
    
    return SearchResponse(
        query_image_id=image_id,
        total_results=len(results),
        search_time_ms=round(elapsed, 2),
        results=results,
    )
