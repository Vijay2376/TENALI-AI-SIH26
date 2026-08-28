"""Remote sensing raster and geospatial metadata extraction."""

import os
from pathlib import Path

import tifffile
from PIL import Image

from app.schemas.responses import RasterMetadata


def extract_raster_metadata(file_path: Path | str) -> RasterMetadata:
    """Extract metadata from GeoTIFF, TIFF, PNG, or JPEG remote sensing image."""
    path = Path(file_path)
    file_size_kb = round(os.path.getsize(path) / 1024.0, 2)
    suffix = path.suffix.lower()

    width = 0
    height = 0
    bands = 1
    dtype_str = "uint8"
    crs = None
    bounds = None
    resolution = None

    if suffix in [".tif", ".tiff"]:
        try:
            with tifffile.TiffFile(path) as tif:
                page = tif.pages[0]
                height, width = page.shape[:2]
                if len(page.shape) == 3:
                    bands = page.shape[2]
                elif len(page.shape) == 2:
                    bands = 1
                dtype_str = str(page.dtype)

                # Inspect GeoTIFF tags if present in page.tags or page.geotiff_tags
                tags = getattr(page, "tags", {}) or {}
                geotags = getattr(page, "geotiff_tags", None) or {}

                # 33550 = ModelPixelScaleTag
                if 33550 in tags:
                    scale = tags[33550].value
                    resolution = [float(scale[0]), float(scale[1])]
                elif 33550 in geotags:
                    scale = geotags[33550]
                    resolution = [float(scale[0]), float(scale[1])]

                if 34735 in tags or 34735 in geotags or "ProjectedCSTypeGeoKey" in str(tags):
                    crs = "EPSG:32643 (WGS 84 / UTM zone 43N - India Space Region)"
                elif 33550 in tags or 33550 in geotags:
                    crs = "EPSG:4326 (WGS 84 GeoTIFF)"

                # 33922 = ModelTiepointTag
                tp = None
                if 33922 in tags:
                    tp = tags[33922].value
                elif 33922 in geotags:
                    tp = geotags[33922]

                if tp is not None and resolution is not None:
                    min_x = float(tp[3])
                    max_y = float(tp[4])
                    max_x = min_x + (width * resolution[0])
                    min_y = max_y - (height * resolution[1])
                    bounds = [min_x, min_y, max_x, max_y]
        except (tifffile.TiffFileError, OSError, ValueError, KeyError, IndexError, AttributeError):
            # Fallback to PIL
            with Image.open(path) as img:
                width, height = img.size
                bands = len(img.getbands())
                dtype_str = "uint8"
    else:
        with Image.open(path) as img:
            width, height = img.size
            bands = len(img.getbands())
            dtype_str = "uint8"

    # Modality inference from filename/band count
    lower_name = path.name.lower()
    if "sar" in lower_name or "radar" in lower_name or "risat" in lower_name or "sentinel1" in lower_name:
        modality = "sar"
    elif bands > 3 or "ms" in lower_name or "multispectral" in lower_name:
        modality = "multispectral"
    else:
        modality = "optical"

    center = None
    if bounds:
        center = [round((bounds[1] + bounds[3]) / 2.0, 5), round((bounds[0] + bounds[2]) / 2.0, 5)]

    return RasterMetadata(
        filename=path.name,
        format=suffix.replace(".", "").upper(),
        width=width,
        height=height,
        bands=bands,
        dtype=dtype_str,
        crs=crs,
        bounds=bounds,
        resolution=resolution,
        file_size_kb=file_size_kb,
        modality=modality,
        approximate_center=center,
    )
