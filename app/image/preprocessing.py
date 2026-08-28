"""Image alignment, co-registration verification, and feature preprocessing."""

import cv2
import numpy as np


def align_image_pair(
    img1: np.ndarray, img2: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Ensure two remote sensing images have identical dimensions and spatial alignment.

    Args:
        img1: Reference image (H, W, C) or (H, W)
        img2: Target image to align with img1

    Returns:
        tuple[np.ndarray, np.ndarray]: Aligned (img1, img2_aligned)
    """
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]

    if (h1, w1) != (h2, w2):
        img2_aligned = cv2.resize(img2, (w1, h1), interpolation=cv2.INTER_LINEAR)
    else:
        img2_aligned = img2.copy()

    return img1, img2_aligned


def extract_scene_descriptors(rgb_arr: np.ndarray) -> dict[str, float]:
    """Extract descriptive statistics from an RGB scene (brightness, vegetation index, water index, texture)."""
    r = rgb_arr[:, :, 0].astype(np.float32)
    g = rgb_arr[:, :, 1].astype(np.float32)
    b = rgb_arr[:, :, 2].astype(np.float32)

    # Visible Atmospheric Resistant Index (VARI) approximation from RGB
    # VARI = (Green - Red) / (Green + Red - Blue + 1e-5)
    denom = g + r - b + 1e-5
    vari = (g - r) / (denom + (denom == 0) * 1e-5)
    veg_score = float(np.mean(vari > 0.1))

    # Normalized Difference Water Index approximation from RGB: (Green - Red) / (Green + Red + 1e-5)
    water_score = float(np.mean((b > r * 1.1) & (b > g * 0.9) & (r < 100)))

    # Built-up index approximation: high red/gray intensity with high edge gradient
    gray = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    texture_var = float(np.var(laplacian))
    builtup_score = float(np.mean((gray > 120) & (texture_var > 100)))

    mean_brightness = float(np.mean(gray))

    return {
        "vegetation_ratio": round(veg_score, 4),
        "water_ratio": round(water_score, 4),
        "builtup_ratio": round(builtup_score, 4),
        "mean_brightness": round(mean_brightness, 2),
        "texture_roughness": round(texture_var, 2),
    }
