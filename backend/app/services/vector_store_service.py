"""
Vector Store Service — ChromaDB operations for image embeddings.
Handles insert, search, delete, and collection management.
"""

import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.core.database import get_collection
from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Manages image embeddings in ChromaDB."""

    def get_collection(self):
        return get_collection()

    def index_image(
        self,
        image_id: str,
        embedding: np.ndarray,
        metadata: Dict[str, Any],
    ) -> bool:
        """Add an image embedding to the vector store."""
        try:
            collection = self.get_collection()
            
            # ChromaDB requires list, not numpy array
            collection.upsert(
                ids=[image_id],
                embeddings=[embedding.tolist()],
                metadatas=[metadata],
            )
            logger.info(f"✅ Indexed image: {image_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to index {image_id}: {e}")
            raise

    def search_similar(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        exclude_ids: Optional[List[str]] = None,
        min_similarity: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Find top-K similar images using cosine similarity.
        Returns list of {id, metadata, distance, similarity_score}.
        """
        collection = self.get_collection()
        
        if collection.count() == 0:
            return []

        where_filter = None
        if exclude_ids:
            if len(exclude_ids) == 1:
                where_filter = {"id": {"$ne": exclude_ids[0]}}
            elif len(exclude_ids) > 1:
                where_filter = {"$and": [{"id": {"$ne": eid}} for eid in exclude_ids]}

        query_kwargs = dict(
            query_embeddings=[query_embedding.tolist()],
            n_results=min(top_k, collection.count()),
            include=["metadatas", "distances", "embeddings"],
        )
        if where_filter:
            query_kwargs["where"] = where_filter

        try:
            results = collection.query(**query_kwargs)
        except Exception as e:
            if "hnsw segment reader" in str(e).lower() or "nothing found on disk" in str(e).lower():
                logger.warning(f"ChromaDB index out of sync ({e}), reloading collection...")
                from app.core.database import reload_db
                collection = reload_db()
                results = collection.query(**query_kwargs)
            else:
                raise

        output = []
        ids = results["ids"][0]
        distances = results["distances"][0]
        metadatas = results["metadatas"][0]

        for img_id, distance, metadata in zip(ids, distances, metadatas):
            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            # Convert to similarity score [0, 1]
            similarity = 1 - (distance / 2)
            
            if similarity >= min_similarity:
                output.append({
                    "id": img_id,
                    "distance": distance,
                    "similarity_score": round(similarity, 4),
                    "metadata": metadata,
                })

        return output

    def get_image(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single image record by ID."""
        try:
            collection = self.get_collection()
            result = collection.get(
                ids=[image_id],
                include=["metadatas", "embeddings"],
            )
            if not result["ids"]:
                return None
            embeddings = result["embeddings"]
            # ChromaDB 1.x returns embeddings as numpy arrays
            emb_value = embeddings[0].tolist() if embeddings is not None and len(embeddings) > 0 else None
            return {
                "id": result["ids"][0],
                "metadata": result["metadatas"][0],
                "embedding": emb_value,
            }
        except Exception as e:
            logger.error(f"Error fetching image {image_id}: {e}")
            return None

    def get_image_embedding(self, image_id: str) -> Optional[np.ndarray]:
        """Retrieve just the embedding for an image."""
        try:
            collection = self.get_collection()
            result = collection.get(
                ids=[image_id],
                include=["embeddings"],
            )
            if not result["ids"]:
                return None
            embeddings = result["embeddings"]
            # ChromaDB 1.x returns embeddings as a numpy array of shape (n, dim)
            if embeddings is None or len(embeddings) == 0:
                return None
            return np.array(embeddings[0])
        except Exception:
            return None

    def delete_image(self, image_id: str) -> bool:
        """Remove an image from the vector store."""
        try:
            collection = self.get_collection()
            collection.delete(ids=[image_id])
            logger.info(f"🗑️  Deleted image: {image_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting {image_id}: {e}")
            return False

    def list_images(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List all indexed images with pagination."""
        collection = self.get_collection()
        total = collection.count()
        
        if total == 0:
            return [], 0

        result = collection.get(
            limit=limit,
            offset=offset,
            include=["metadatas"],
        )
        
        items = []
        for img_id, metadata in zip(result["ids"], result["metadatas"]):
            items.append({"id": img_id, "metadata": metadata})
        
        return items, total

    def collection_stats(self) -> Dict[str, Any]:
        """Return stats about the collection."""
        collection = self.get_collection()
        count = collection.count()
        return {
            "total_images": count,
            "collection_name": settings.COLLECTION_NAME,
            "embedding_dim": settings.EMBEDDING_DIM,
            "model": settings.CLIP_MODEL,
        }

    def clear_collection(self) -> int:
        """Delete all images from the collection."""
        collection = self.get_collection()
        count = collection.count()
        if count > 0:
            all_ids = collection.get(include=[])["ids"]
            collection.delete(ids=all_ids)
        logger.info(f"🗑️  Cleared {count} images from collection")
        return count
