"""Pytest configuration, fixtures, and synthetic test raster builders."""

from pathlib import Path

import numpy as np
import pytest
import tifffile
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def test_rasters(tmp_path: Path):
    """Generate synthetic test images for unit testing."""
    single_path = tmp_path / "single_test.tif"
    t1_path = tmp_path / "t1_test.tif"
    t2_path = tmp_path / "t2_test.tif"
    opt_path = tmp_path / "opt_test.tif"
    sar_path = tmp_path / "sar_test.tif"

    h, w = 128, 128

    # Single optical raster
    img_rgb = np.zeros((h, w, 3), dtype=np.uint8)
    img_rgb[:, :, 1] = 160  # vegetation
    tifffile.imwrite(
        single_path,
        img_rgb,
        photometric="rgb",
        extratags=[
            (33550, "d", 3, (10.0, 10.0, 0.0), False),
            (33922, "d", 6, (0.0, 0.0, 0.0, 77.0, 13.0, 0.0), False),
        ],
    )

    # Bi-temporal T1 and T2
    t1 = img_rgb.copy()
    t2 = img_rgb.copy()
    t2[40:90, 40:90, :] = 220  # change zone
    tifffile.imwrite(t1_path, t1, photometric="rgb")
    tifffile.imwrite(t2_path, t2, photometric="rgb")

    # Optical and SAR
    opt = img_rgb.copy()
    sar = np.random.randint(50, 180, (h, w), dtype=np.uint8)
    tifffile.imwrite(opt_path, opt, photometric="rgb")
    tifffile.imwrite(sar_path, sar, photometric="minisblack")

    return {
        "single": single_path,
        "t1": t1_path,
        "t2": t2_path,
        "optical": opt_path,
        "sar": sar_path,
    }
