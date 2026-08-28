"""Synthetic remote sensing GeoTIFF generator for SIH demonstrations and tests."""

from pathlib import Path

import numpy as np
import tifffile


def create_demo_datasets(base_dir: Path | None = None):
    """Generate sample GeoTIFF files for single, bi-temporal, and optical-SAR workflows."""
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent

    single_dir = base_dir / "single"
    bi_dir = base_dir / "bi_temporal"
    opt_sar_dir = base_dir / "optical_sar"

    single_dir.mkdir(parents=True, exist_ok=True)
    bi_dir.mkdir(parents=True, exist_ok=True)
    opt_sar_dir.mkdir(parents=True, exist_ok=True)

    h, w = 512, 512
    y_coords, x_coords = np.mgrid[:h, :w]
    rng = np.random.default_rng(42)

    # -------------------------------------------------------------------------
    # 1. Single Image Samples
    # -------------------------------------------------------------------------
    # 1a. Reservoir Lake (Central deep water body with surrounding vegetation)
    lake_mask = ((x_coords - 256) ** 2 / 160**2 + (y_coords - 256) ** 2 / 100**2) < 1.0
    lake_rgb = np.zeros((h, w, 3), dtype=np.uint8)
    # Vegetation base
    lake_rgb[:, :, 0] = 55 + rng.integers(-8, 8, (h, w), dtype=np.int16).clip(0, 255).astype(np.uint8)
    lake_rgb[:, :, 1] = 145 + rng.integers(-10, 10, (h, w), dtype=np.int16).clip(0, 255).astype(np.uint8)
    lake_rgb[:, :, 2] = 50 + rng.integers(-8, 8, (h, w), dtype=np.int16).clip(0, 255).astype(np.uint8)
    # Water lake
    lake_rgb[lake_mask, 0] = 20
    lake_rgb[lake_mask, 1] = 60
    lake_rgb[lake_mask, 2] = 180

    tifffile.imwrite(
        single_dir / "reservoir_water.tif",
        lake_rgb,
        photometric="rgb",
        extratags=[
            (33550, "d", 3, (10.0, 10.0, 0.0), False),  # 10m pixel resolution
            (33922, "d", 6, (0.0, 0.0, 0.0, 77.58, 12.97, 0.0), False),  # ISRO Bangalore region
        ],
    )

    # 1b. Urban Port / Industrial Scene
    urban_rgb = np.zeros((h, w, 3), dtype=np.uint8)
    urban_rgb[:, :] = 145 + rng.integers(-15, 15, (h, w, 3), dtype=np.int16).clip(0, 255).astype(np.uint8)
    urban_rgb[::32, :, :] = 60
    urban_rgb[:, ::32, :] = 60
    tifffile.imwrite(
        single_dir / "urban_port.tif",
        urban_rgb,
        photometric="rgb",
        extratags=[
            (33550, "d", 3, (5.0, 5.0, 0.0), False),
            (33922, "d", 6, (0.0, 0.0, 0.0, 72.87, 19.07, 0.0), False),
        ],
    )

    # -------------------------------------------------------------------------
    # 2. Bi-Temporal Change Samples
    # -------------------------------------------------------------------------
    # T1: Green agricultural landscape with consistent texture
    t1 = np.zeros((h, w, 3), dtype=np.uint8)
    base_noise = rng.integers(-10, 10, (h, w), dtype=np.int16)
    t1[:, :, 0] = np.clip(60 + base_noise, 0, 255).astype(np.uint8)
    t1[:, :, 1] = np.clip(150 + base_noise, 0, 255).astype(np.uint8)
    t1[:, :, 2] = np.clip(55 + base_noise, 0, 255).astype(np.uint8)

    # T2 is an EXACT clone of T1 plus a major urban expansion in the eastern quadrant
    t2 = t1.copy()
    urban_exp_mask = (x_coords > 300) & (x_coords < 480) & (y_coords > 120) & (y_coords < 380)
    t2[urban_exp_mask, 0] = 215
    t2[urban_exp_mask, 1] = 190
    t2[urban_exp_mask, 2] = 175
    # Add road grid to expansion zone
    t2[urban_exp_mask & ((x_coords % 24 == 0) | (y_coords % 24 == 0)), :] = 50

    tifffile.imwrite(
        bi_dir / "expansion_t1.tif",
        t1,
        photometric="rgb",
        extratags=[
            (33550, "d", 3, (10.0, 10.0, 0.0), False),
            (33922, "d", 6, (0.0, 0.0, 0.0, 78.48, 17.38, 0.0), False),  # Hyderabad corridor
        ],
    )
    tifffile.imwrite(
        bi_dir / "expansion_t2.tif",
        t2,
        photometric="rgb",
        extratags=[
            (33550, "d", 3, (10.0, 10.0, 0.0), False),
            (33922, "d", 6, (0.0, 0.0, 0.0, 78.48, 17.38, 0.0), False),
        ],
    )

    # -------------------------------------------------------------------------
    # 3. Optical + SAR Co-Registered Pair
    # -------------------------------------------------------------------------
    sea_mask = x_coords < 200
    city_mask = (x_coords >= 200) & (x_coords < 360)
    forest_mask = x_coords >= 360

    # Optical image
    opt = np.zeros((h, w, 3), dtype=np.uint8)
    opt[sea_mask, 0] = 20
    opt[sea_mask, 1] = 55
    opt[sea_mask, 2] = 170

    opt[city_mask, 0] = 185
    opt[city_mask, 1] = 180
    opt[city_mask, 2] = 175

    opt[forest_mask, 0] = 45
    opt[forest_mask, 1] = 155
    opt[forest_mask, 2] = 40

    # SAR Radar image
    sar = np.zeros((h, w), dtype=np.uint8)
    sar[sea_mask] = 15      # Specular reflection (dark)
    sar[city_mask] = 235    # Double-bounce structures (bright)
    sar[forest_mask] = 95   # Volume scattering (moderate)

    tifffile.imwrite(
        opt_sar_dir / "harbor_optical.tif",
        opt,
        photometric="rgb",
        extratags=[
            (33550, "d", 3, (10.0, 10.0, 0.0), False),
            (33922, "d", 6, (0.0, 0.0, 0.0, 80.27, 13.08, 0.0), False),  # Chennai coast
        ],
    )
    tifffile.imwrite(
        opt_sar_dir / "harbor_sar.tif",
        sar,
        photometric="minisblack",
        extratags=[
            (33550, "d", 3, (10.0, 10.0, 0.0), False),
            (33922, "d", 6, (0.0, 0.0, 0.0, 80.27, 13.08, 0.0), False),
        ],
    )

    print("Regenerated clean synthetic remote-sensing datasets successfully.")


if __name__ == "__main__":
    create_demo_datasets()
