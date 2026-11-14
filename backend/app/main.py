"""
Image-Based Similarity Search Engine
FastAPI Backend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import logging

from app.api import search, upload, collection, health
from app.core.config import settings
from app.core.database import init_db
from app.services.embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 Starting Image Search Engine...")
    
    # Initialize database
    await init_db()
    
    # Pre-load embedding model
    embedding_service = EmbeddingService()
    await embedding_service.initialize()
    app.state.embedding_service = embedding_service
    
    # Create uploads directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.SAMPLE_IMAGES_DIR, exist_ok=True)
    
    logger.info("✅ Engine ready!")
    yield
    
    logger.info("🛑 Shutting down...")


app = FastAPI(
    title="Image Similarity Search Engine",
    description="""
    ## 🔍 Image-Based Similarity Search API
    
    Upload an image and find visually similar images from the indexed collection.
    
    ### Features
    - **Image Upload**: Upload and index images with automatic embedding generation
    - **Similarity Search**: Find top-N visually similar images
    - **Multi-modal Search**: Search by image + text combined
    - **Reverse Image Search**: Find exact or near-duplicate images
    - **Collection Management**: Browse and manage the image collection
    
    ### How it works
    1. Images are processed through a CLIP vision model to generate 512-dim embeddings
    2. Embeddings are stored in ChromaDB vector database
    3. Similarity search uses cosine similarity for fast retrieval
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploaded images
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(collection.router, prefix="/api", tags=["Collection"])


@app.get("/")
async def root():
    return {
        "message": "Image Similarity Search Engine",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/health",
    }
