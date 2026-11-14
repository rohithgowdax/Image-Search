"""ChromaDB vector database setup."""

import chromadb
from chromadb.config import Settings as ChromaSettings
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

_client: chromadb.Client = None
_collection = None


def reload_db():
    """Reload ChromaDB client and collection (e.g. if files changed externally)."""
    global _client, _collection
    _client = chromadb.PersistentClient(
        path=settings.CHROMA_DIR,
        settings=ChromaSettings(anonymized_telemetry=False)
    )
    _collection = _client.get_or_create_collection(
        name=settings.COLLECTION_NAME,
        metadata={
            "hnsw:space": "cosine",
            "description": "Image embeddings for similarity search"
        }
    )
    return _collection


async def init_db():
    """Initialize ChromaDB client and collection."""
    logger.info("🗄️  Initializing ChromaDB...")
    collection = reload_db()
    count = collection.count()
    logger.info(f"✅ ChromaDB ready — {count} images indexed")


def get_collection():
    """Return the active ChromaDB collection."""
    if _collection is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _collection


def get_client():
    """Return the ChromaDB client."""
    if _client is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _client
