"""Image processing utilities."""

from PIL import Image
import io
import hashlib
import uuid
import os
import logging
from typing import Tuple, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


def validate_image(file_bytes: bytes, filename: str) -> Tuple[bool, str]:
    """Validate image format and size."""
    # Check file size
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        return False, f"File too large ({size_mb:.1f} MB). Max: {settings.MAX_FILE_SIZE_MB} MB"

    # Check extension
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        return False, f"Invalid file type '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"

    # Verify it's actually an image
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()
    except Exception as e:
        return False, f"Invalid or corrupted image: {str(e)}"

    return True, "OK"


def process_image(file_bytes: bytes) -> Tuple[Image.Image, Dict[str, Any]]:
    """Open image and return PIL Image + metadata."""
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    info = {
        "width": image.width,
        "height": image.height,
        "format": image.format or "JPEG",
    }
    return image, info


def save_image(file_bytes: bytes, filename: str, image_id: str) -> str:
    """
    Save image to uploads directory.
    Returns the saved filename.
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    saved_name = f"{image_id}.{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, saved_name)
    
    with open(save_path, "wb") as f:
        f.write(file_bytes)
    
    return saved_name


def get_image_hash(file_bytes: bytes) -> str:
    """Get MD5 hash of image for deduplication."""
    return hashlib.md5(file_bytes).hexdigest()


def generate_image_id() -> str:
    """Generate a unique image ID."""
    return str(uuid.uuid4())


def build_image_url(filename: str, base_url: str = "") -> str:
    """Build the full URL for accessing an image."""
    return f"{base_url}/uploads/{filename}"


def resize_for_thumbnail(image: Image.Image, max_size: int = 256) -> bytes:
    """Create a thumbnail and return as JPEG bytes."""
    thumbnail = image.copy()
    thumbnail.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    thumbnail.save(buf, format="JPEG", quality=80)
    return buf.getvalue()
