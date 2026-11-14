"""Upload API — index single or multiple images."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
import time
from datetime import datetime

from app.models.schemas import UploadResponse, BulkUploadResponse
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.utils.image_utils import (
    validate_image, process_image, save_image,
    get_image_hash, generate_image_id, build_image_url
)

router = APIRouter()
logger = logging.getLogger(__name__)

vector_store = VectorStoreService()


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload & index an image",
    description="Upload an image, generate its CLIP embedding, and store it in the vector database.",
)
async def upload_image(
    request: Request,
    file: UploadFile = File(..., description="Image file to index"),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    description: Optional[str] = Form(None, description="Image description"),
):
    start = time.time()
    
    # Read file
    file_bytes = await file.read()
    
    # Validate
    valid, msg = validate_image(file_bytes, file.filename)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)
    
    # Process image metadata
    _, img_info = process_image(file_bytes)
    
    image_id = generate_image_id()
    
    # Save to disk
    saved_filename = save_image(file_bytes, file.filename, image_id)
    
    # Build URL
    base_url = str(request.base_url).rstrip("/")
    url = build_image_url(saved_filename, base_url)
    
    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    
    # Generate embedding
    embedding_service: EmbeddingService = request.app.state.embedding_service
    embedding = await embedding_service.embed_image(file_bytes)
    
    # Store in vector DB
    metadata = {
        "filename": saved_filename,
        "original_filename": file.filename,
        "url": url,
        "width": img_info["width"],
        "height": img_info["height"],
        "format": img_info["format"] or "unknown",
        "file_size": len(file_bytes),
        "tags": ",".join(tag_list),
        "description": description or "",
        "indexed_at": datetime.utcnow().isoformat(),
        "image_hash": get_image_hash(file_bytes),
    }
    
    vector_store.index_image(image_id, embedding, metadata)
    
    elapsed = (time.time() - start) * 1000
    logger.info(f"✅ Indexed {file.filename} in {elapsed:.0f}ms")
    
    return UploadResponse(
        id=image_id,
        filename=saved_filename,
        url=url,
        width=img_info["width"],
        height=img_info["height"],
        format=img_info["format"] or "unknown",
        file_size=len(file_bytes),
        embedding_dim=embedding.shape[0],
        indexed=True,
        message=f"Image indexed successfully in {elapsed:.0f}ms",
    )


@router.post(
    "/upload/bulk",
    response_model=BulkUploadResponse,
    summary="Bulk upload images",
    description="Upload and index multiple images at once (max 20).",
)
async def bulk_upload(
    request: Request,
    files: List[UploadFile] = File(..., description="Image files to index"),
):
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Max 20 files per bulk upload")
    
    embedding_service: EmbeddingService = request.app.state.embedding_service
    results = []
    successful = 0
    
    for file in files:
        try:
            file_bytes = await file.read()
            
            valid, msg = validate_image(file_bytes, file.filename)
            if not valid:
                results.append({"filename": file.filename, "status": "failed", "error": msg})
                continue
            
            _, img_info = process_image(file_bytes)
            image_id = generate_image_id()
            saved_filename = save_image(file_bytes, file.filename, image_id)
            
            base_url = str(request.base_url).rstrip("/")
            url = build_image_url(saved_filename, base_url)
            
            embedding = await embedding_service.embed_image(file_bytes)
            
            metadata = {
                "filename": saved_filename,
                "original_filename": file.filename,
                "url": url,
                "width": img_info["width"],
                "height": img_info["height"],
                "format": img_info["format"] or "unknown",
                "file_size": len(file_bytes),
                "tags": "",
                "description": "",
                "indexed_at": datetime.utcnow().isoformat(),
                "image_hash": get_image_hash(file_bytes),
            }
            
            vector_store.index_image(image_id, embedding, metadata)
            successful += 1
            results.append({
                "filename": file.filename,
                "id": image_id,
                "url": url,
                "status": "success",
            })
        except Exception as e:
            logger.error(f"Error indexing {file.filename}: {e}")
            results.append({"filename": file.filename, "status": "failed", "error": str(e)})
    
    return BulkUploadResponse(
        total=len(files),
        successful=successful,
        failed=len(files) - successful,
        results=results,
    )


@router.delete(
    "/images/{image_id}",
    summary="Delete an indexed image",
)
async def delete_image(image_id: str):
    """Remove an image from the search index."""
    record = vector_store.get_image(image_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Image '{image_id}' not found")
    
    import os
    from app.core.config import settings
    
    # Remove file from disk
    metadata = record.get("metadata") or {}
    filename = metadata.get("filename", "")
    if filename:
        filepath = os.path.join(settings.UPLOAD_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    
    vector_store.delete_image(image_id)
    
    return {"message": f"Image '{image_id}' deleted successfully"}
