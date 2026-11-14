"""
Embedding Service — CLIP-based image and text embeddings.

Uses openai/clip-vit-base-patch32 to generate 512-dimensional embeddings
for both images and text queries, enabling multi-modal similarity search.
"""

import numpy as np
from PIL import Image
import io
import logging
import asyncio
from typing import Optional, List, Union
from transformers import CLIPProcessor, CLIPModel
import torch
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generates CLIP embeddings for images and text."""

    _instance: Optional["EmbeddingService"] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self):
        """Load CLIP model (called once at startup)."""
        if self._initialized:
            return

        logger.info(f"📦 Loading CLIP model: {settings.CLIP_MODEL}")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_model)
        self._initialized = True
        logger.info("✅ CLIP model loaded")

    def _load_model(self):
        """Synchronous model loading (runs in thread pool)."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🖥️  Using device: {self.device}")

        try:
            self.model = CLIPModel.from_pretrained(settings.CLIP_MODEL, local_files_only=True)
            self.processor = CLIPProcessor.from_pretrained(settings.CLIP_MODEL, local_files_only=True)
        except Exception:
            self.model = CLIPModel.from_pretrained(settings.CLIP_MODEL)
            self.processor = CLIPProcessor.from_pretrained(settings.CLIP_MODEL)
        self.model.to(self.device)
        self.model.eval()

    async def embed_image(self, image_data: bytes) -> np.ndarray:
        """Generate embedding for image bytes."""
        if not self._initialized:
            await self.initialize()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._embed_image_sync, image_data)

    def _embed_image_sync(self, image_data: bytes) -> np.ndarray:
        """Synchronous image embedding generation."""
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            # In transformers 5.x, get_image_features() returns BaseModelOutputWithPooling.
            # .pooler_output is the already-projected 512-dim embedding tensor.
            raw = self.model.get_image_features(**inputs)
            image_features = raw.pooler_output if hasattr(raw, "pooler_output") else raw
        
        # Normalize to unit vector (cosine similarity)
        embedding = image_features.detach().cpu().numpy()[0]
        embedding = embedding / np.linalg.norm(embedding)
        return embedding

    async def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a text query."""
        if not self._initialized:
            await self.initialize()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._embed_text_sync, text)

    def _embed_text_sync(self, text: str) -> np.ndarray:
        """Synchronous text embedding generation."""
        inputs = self.processor(text=[text], return_tensors="pt", padding=True).to(self.device)
        
        with torch.no_grad():
            # In transformers 5.x, get_text_features() returns BaseModelOutputWithPooling.
            # .pooler_output is the already-projected 512-dim embedding tensor.
            raw = self.model.get_text_features(**inputs)
            text_features = raw.pooler_output if hasattr(raw, "pooler_output") else raw
        
        embedding = text_features.detach().cpu().numpy()[0]
        embedding = embedding / np.linalg.norm(embedding)
        return embedding

    async def embed_image_text(self, image_data: bytes, text: str, alpha: float = 0.7) -> np.ndarray:
        """
        Generate fused embedding from image + text (multi-modal search).
        alpha controls the image vs text weight (0=text only, 1=image only).
        """
        image_emb = await self.embed_image(image_data)
        text_emb = await self.embed_text(text)
        
        fused = alpha * image_emb + (1 - alpha) * text_emb
        fused = fused / np.linalg.norm(fused)
        return fused

    @property
    def embedding_dim(self) -> int:
        return settings.EMBEDDING_DIM

    @property
    def is_ready(self) -> bool:
        return self._initialized
