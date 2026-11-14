"""Pydantic schemas for request/response models."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ImageMetadata(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    width: int
    height: int
    format: str
    url: str
    tags: List[str] = []
    description: Optional[str] = None
    indexed_at: str


class SearchResult(BaseModel):
    id: str
    filename: str
    url: str
    similarity_score: float = Field(..., description="Cosine similarity score (0-1)")
    distance: float = Field(..., description="Raw distance from ChromaDB")
    metadata: Dict[str, Any] = {}
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []


class SearchResponse(BaseModel):
    query_image_id: Optional[str] = None
    query_text: Optional[str] = None
    total_results: int
    search_time_ms: float
    results: List[SearchResult]


class UploadResponse(BaseModel):
    id: str
    filename: str
    url: str
    width: int
    height: int
    format: str
    file_size: int
    embedding_dim: int
    indexed: bool
    message: str


class CollectionStats(BaseModel):
    total_images: int
    collection_name: str
    embedding_dim: int
    model: str


class BulkUploadResponse(BaseModel):
    total: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    collection_count: int
    version: str
