"""Browser preview image generator and disk serialization."""

import uuid
from pathlib import Path

import numpy as np
from PIL import Image

from app.config import settings


def save_preview_image(
    rgb_arr: np.ndarray,
    prefix: str = "preview",
    target_dir: Path | None = None,
) -> tuple[Path, str]:
    """Save an RGB numpy array to disk as an optimized web PNG.

    Returns:
        tuple[Path, str]: (absolute_file_path, relative_web_url)
    """
    if target_dir is None:
        target_dir = settings.EVIDENCE_DIR

    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
    out_path = target_dir / filename

    # Ensure shape is (H, W, 3) and uint8
    if rgb_arr.ndim == 2:
        rgb_arr = np.stack([rgb_arr, rgb_arr, rgb_arr], axis=-1)
    elif rgb_arr.ndim == 3 and rgb_arr.shape[2] == 1:
        rgb_arr = np.repeat(rgb_arr, 3, axis=2)

    img = Image.fromarray(rgb_arr.astype(np.uint8), mode="RGB")
    img.save(out_path, format="PNG", optimize=True)

    rel_url = f"/evidence/{filename}"
    return out_path, rel_url
