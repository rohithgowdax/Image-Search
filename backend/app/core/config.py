"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Image Similarity Search Engine"
    DEBUG: bool = False
    
    # Paths
    UPLOAD_DIR: str = "uploads"
    SAMPLE_IMAGES_DIR: str = "uploads/samples"
    CHROMA_DIR: str = "chroma_db"
    
    # Model
    CLIP_MODEL: str = "openai/clip-vit-base-patch32"
    EMBEDDING_DIM: int = 512
    
    # Search
    DEFAULT_TOP_K: int = 5
    MAX_TOP_K: int = 50
    MIN_SIMILARITY: float = 0.0
    
    # Upload
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: list = ["jpg", "jpeg", "png", "gif", "bmp", "webp"]
    
    # Collection
    COLLECTION_NAME: str = "images"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
