#!/usr/bin/env python3
"""
Seed sample images into the search index for demo purposes.
Downloads a small set of royalty-free images and indexes them.
"""

import asyncio
import sys
import os
import httpx
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import init_db
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.utils.image_utils import (
    validate_image, process_image, save_image,
    get_image_hash, generate_image_id, build_image_url
)
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample images: (url, tags, description)
SAMPLE_IMAGES = [
    (
        "https://images.unsplash.com/photo-1544636331-e26879cd4d9b?w=400",
        "car,red,sports,ferrari",
        "Red Ferrari sports car"
    ),
    (
        "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=400",
        "car,blue,sports,automobile",
        "Blue sports car on road"
    ),
    (
        "https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?w=400",
        "car,yellow,lamborghini,luxury",
        "Yellow Lamborghini luxury car"
    ),
    (
        "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400",
        "car,white,porsche,sports",
        "White Porsche sports car"
    ),
    (
        "https://images.unsplash.com/photo-1555215695-3004980ad54e?w=400",
        "car,black,bmw,sedan",
        "Black BMW sedan"
    ),
    (
        "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?w=400",
        "car,orange,sports,track",
        "Orange sports car on racing track"
    ),
    (
        "https://images.unsplash.com/photo-1583121274602-3e2820c69888?w=400",
        "car,silver,mercedes,luxury",
        "Silver Mercedes luxury car"
    ),
    (
        "https://images.unsplash.com/photo-1449130841078-6247400c7cc5?w=400",
        "car,red,classic,vintage",
        "Classic vintage red car"
    ),
    (
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
        "person,portrait,man,face",
        "Portrait of a man"
    ),
    (
        "https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=400",
        "person,portrait,woman,face",
        "Portrait of a woman"
    ),
    (
        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
        "mountain,nature,landscape,snow",
        "Mountain landscape with snow"
    ),
    (
        "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=400",
        "city,skyline,urban,buildings",
        "City skyline at night"
    ),
    (
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",
        "dog,puppy,cute,pet",
        "Cute puppy dog"
    ),
    (
        "https://images.unsplash.com/photo-1526336024174-e58f5cdd8e13?w=400",
        "cat,kitten,pet,cute",
        "Cute kitten cat"
    ),
    (
        "https://images.unsplash.com/photo-1497436072909-60f360e1d4b1?w=400",
        "forest,nature,trees,green",
        "Green forest with trees"
    ),
    (
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400",
        "beach,ocean,sea,summer",
        "Tropical beach with ocean"
    ),
    (
        "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400",
        "sofa,furniture,interior,home",
        "Modern sofa furniture"
    ),
    (
        "https://images.unsplash.com/photo-1490730141103-6cac27aaab94?w=400",
        "sunset,sky,clouds,colorful",
        "Beautiful sunset sky"
    ),
    (
        "https://images.unsplash.com/photo-1498579150354-977475b7ea0b?w=400",
        "laptop,computer,technology,desk",
        "Laptop on desk"
    ),
    (
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400",
        "food,healthy,salad,vegetables",
        "Healthy food salad"
    ),
]


async def seed():
    await init_db()
    
    embedding_service = EmbeddingService()
    await embedding_service.initialize()
    
    vector_store = VectorStoreService()
    
    logger.info(f"🌱 Seeding {len(SAMPLE_IMAGES)} sample images...")
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.SAMPLE_IMAGES_DIR, exist_ok=True)
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for i, (url, tags, description) in enumerate(SAMPLE_IMAGES, 1):
            try:
                logger.info(f"  [{i}/{len(SAMPLE_IMAGES)}] Downloading: {description}")
                
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"  ⚠️  HTTP {resp.status_code} for {url}")
                    continue
                
                file_bytes = resp.content
                filename = f"sample_{i:02d}.jpg"
                
                valid, msg = validate_image(file_bytes, filename)
                if not valid:
                    logger.warning(f"  ⚠️  Invalid: {msg}")
                    continue
                
                _, img_info = process_image(file_bytes)
                image_id = generate_image_id()
                saved_filename = save_image(file_bytes, filename, image_id)
                url_path = f"/uploads/{saved_filename}"
                
                embedding = await embedding_service.embed_image(file_bytes)
                
                metadata = {
                    "filename": saved_filename,
                    "original_filename": filename,
                    "url": url_path,
                    "width": img_info["width"],
                    "height": img_info["height"],
                    "format": img_info["format"] or "JPEG",
                    "file_size": len(file_bytes),
                    "tags": tags,
                    "description": description,
                    "indexed_at": datetime.utcnow().isoformat(),
                    "image_hash": get_image_hash(file_bytes),
                }
                
                vector_store.index_image(image_id, embedding, metadata)
                logger.info(f"  ✅ Indexed: {description}")
                
            except Exception as e:
                logger.error(f"  ❌ Failed: {url} — {e}")
    
    stats = vector_store.collection_stats()
    logger.info(f"\n🎉 Done! Total indexed: {stats['total_images']} images")


if __name__ == "__main__":
    asyncio.run(seed())
