"""Tests for raster ingestion, geospatial metadata extraction, and normalization."""

import numpy as np

from app.image.loader import load_raster_image
from app.image.metadata import extract_raster_metadata
from app.image.normalization import (
    normalize_to_rgb,
    percentile_stretch,
    sar_log_stretch,
)
from app.image.preprocessing import align_image_pair, extract_scene_descriptors


def test_metadata_extraction(test_rasters):
    """Test extracting geospatial metadata from GeoTIFF."""
    meta = extract_raster_metadata(test_rasters["single"])
    assert meta.filename == "single_test.tif"
    assert meta.format == "TIF"
    assert meta.width == 128
    assert meta.height == 128
    assert meta.bands == 3
    assert meta.resolution == [10.0, 10.0]
    assert meta.crs is not None


def test_raster_loading(test_rasters):
    """Test loading and normalizing raster to RGB array."""
    raw, rgb, meta = load_raster_image(test_rasters["single"])
    assert raw.shape[:2] == (128, 128)
    assert rgb.shape == (128, 128, 3)
    assert rgb.dtype == np.uint8
    assert meta.width == 128


def test_normalization_modes():
    """Test standard percentile and SAR log transformations."""
    arr = np.linspace(0, 1000, 100, dtype=np.float32).reshape(10, 10)
    stretched = percentile_stretch(arr)
    assert stretched.dtype == np.uint8
    assert stretched.min() == 0
    assert stretched.max() == 255

    sar_stretched = sar_log_stretch(arr)
    assert sar_stretched.dtype == np.uint8

    rgb_norm = normalize_to_rgb(arr, modality="optical")
    assert rgb_norm.shape == (10, 10, 3)
    assert rgb_norm.dtype == np.uint8


def test_alignment_and_descriptors():
    """Test image pair spatial alignment and scene descriptors."""
    img1 = np.zeros((100, 100, 3), dtype=np.uint8)
    img2 = np.zeros((120, 150, 3), dtype=np.uint8)
    a1, a2 = align_image_pair(img1, img2)
    assert a1.shape == (100, 100, 3)
    assert a2.shape == (100, 100, 3)

    desc = extract_scene_descriptors(img1)
    assert "vegetation_ratio" in desc
    assert "water_ratio" in desc
    assert "builtup_ratio" in desc
