"""Safe remote sensing image loading, windowing, and downsampling."""

from pathlib import Path

import cv2
import numpy as np
import tifffile
from PIL import Image

from app.image.metadata import extract_raster_metadata
from app.image.normalization import normalize_to_rgb
from app.schemas.responses import RasterMetadata


def load_raster_image(
    file_path: Path | str, max_dimension: int = 1536
) -> tuple[np.ndarray, np.ndarray, RasterMetadata]:
    """Load a remote sensing raster from disk.

    Returns:
        tuple[np.ndarray, np.ndarray, RasterMetadata]:
            - raw_array: Original raster data (possibly multispectral/float)
            - rgb_array: Normalized 8-bit RGB visualization array (H, W, 3)
            - metadata: Extracted raster metadata
    """
    path = Path(file_path)
    metadata = extract_raster_metadata(path)
    suffix = path.suffix.lower()

    raw_arr: np.ndarray | None = None

    if suffix in [".tif", ".tiff"]:
        try:
            raw_arr = tifffile.imread(path)
        except (tifffile.TiffFileError, OSError, ValueError):
            with Image.open(path) as img:
                raw_arr = np.array(img)
    else:
        with Image.open(path) as img:
            raw_arr = np.array(img)

    if raw_arr is None:
        raise ValueError(f"Could not decode image at {path}")

    # Ensure shape consistency
    if raw_arr.ndim == 3 and raw_arr.shape[0] < raw_arr.shape[2] and raw_arr.shape[0] in [1, 2, 3, 4, 8, 12, 13]:
        raw_arr = np.transpose(raw_arr, (1, 2, 0))

    # Downsample if too large to conserve memory and maintain interactive latency
    h, w = raw_arr.shape[:2]
    if max(h, w) > max_dimension:
        scale = max_dimension / float(max(h, w))
        new_w = int(w * scale)
        new_h = int(h * scale)
        if raw_arr.ndim == 2:
            raw_arr = cv2.resize(raw_arr, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            raw_arr = cv2.resize(raw_arr, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Normalize to 8-bit RGB for vision algorithms and visualization
    rgb_arr = normalize_to_rgb(raw_arr, modality=metadata.modality)

    return raw_arr, rgb_arr, metadata
