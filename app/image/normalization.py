"""Radiometric normalization, spectral stretching, and multi-band conversions."""

import numpy as np


def percentile_stretch(
    band: np.ndarray, lower_percentile: float = 2.0, upper_percentile: float = 98.0
) -> np.ndarray:
    """Apply 2-98% cumulative percentile linear contrast stretch to a single band."""
    valid_mask = np.isfinite(band)
    if not np.any(valid_mask):
        return np.zeros_like(band, dtype=np.uint8)

    valid_vals = band[valid_mask]
    p_low = np.percentile(valid_vals, lower_percentile)
    p_high = np.percentile(valid_vals, upper_percentile)

    if p_high <= p_low:
        p_high = p_low + 1e-5

    stretched = np.clip((band - p_low) / (p_high - p_low), 0.0, 1.0)
    return (stretched * 255.0).astype(np.uint8)


def sar_log_stretch(sar_band: np.ndarray) -> np.ndarray:
    """Transform SAR backscatter intensity using decibel / log-scale stretching."""
    sar_float = sar_band.astype(np.float32)
    # Clamp negative or zero values
    sar_float = np.maximum(sar_float, 1e-6)
    # Convert to dB-like log amplitude
    db = 10.0 * np.log10(sar_float)
    return percentile_stretch(db, lower_percentile=1.0, upper_percentile=99.0)


def normalize_to_rgb(arr: np.ndarray, modality: str = "optical") -> np.ndarray:
    """Normalize arbitrary multi-band/SAR raster arrays to an 8-bit (H, W, 3) RGB representation."""
    if arr.ndim == 2:
        # Single band (e.g. Grayscale or SAR)
        if modality.lower() == "sar":
            stretched = sar_log_stretch(arr)
        else:
            stretched = percentile_stretch(arr)
        # Stack to 3-channel
        return np.stack([stretched, stretched, stretched], axis=-1)

    elif arr.ndim == 3:
        # Check channel dimension: (H, W, C) vs (C, H, W)
        if arr.shape[0] < arr.shape[2] and arr.shape[0] in [1, 2, 3, 4, 8, 12, 13]:
            # Convert (C, H, W) to (H, W, C)
            arr = np.transpose(arr, (1, 2, 0))

        c = arr.shape[2]
        if c == 1:
            stretched = percentile_stretch(arr[:, :, 0])
            return np.stack([stretched, stretched, stretched], axis=-1)
        elif c == 2:
            # Dual-polarization SAR (e.g. VV, VH) -> (VV, VH, VV/VH ratio)
            b1 = sar_log_stretch(arr[:, :, 0])
            b2 = sar_log_stretch(arr[:, :, 1])
            ratio = percentile_stretch(
                (arr[:, :, 0].astype(np.float32) + 1e-5)
                / (arr[:, :, 1].astype(np.float32) + 1e-5)
            )
            return np.stack([b1, b2, ratio], axis=-1)
        elif c == 3:
            # If already 8-bit standard RGB, preserve true radiometric values
            if arr.dtype == np.uint8 and modality.lower() != "sar":
                return arr.copy()
            # Standard RGB stretching for float / 16-bit
            r = percentile_stretch(arr[:, :, 0])
            g = percentile_stretch(arr[:, :, 1])
            b = percentile_stretch(arr[:, :, 2])
            return np.stack([r, g, b], axis=-1)
        else:
            # Multispectral (4+ bands): Extract true-color (B1, B2, B3) or first 3 bands
            r = percentile_stretch(arr[:, :, 0])
            g = percentile_stretch(arr[:, :, 1])
            b = percentile_stretch(arr[:, :, 2])
            return np.stack([r, g, b], axis=-1)

    raise ValueError(f"Unsupported array shape: {arr.shape}")
