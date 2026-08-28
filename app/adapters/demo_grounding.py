"""Grounding adapter using spectral indices, color clustering, and morphological contours."""

from typing import Any

import cv2
import numpy as np

from app.adapters.base import BaseAdapter
from app.schemas.responses import RegionBox
from app.schemas.trace import ExecutionMode


class DemoGroundingAdapter(BaseAdapter):
    """Text-guided region grounding via remote-sensing spectral heuristics and morphological grouping."""

    def __init__(self):
        super().__init__(
            name="DemoGroundingAdapter",
            execution_mode=ExecutionMode.IMAGE_PROCESSING.value,
        )

    def run(
        self,
        rgb_arr: np.ndarray,
        target_query: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate binary mask and bounding boxes for text-guided target region."""
        h, w = rgb_arr.shape[:2]
        query_lower = target_query.lower()

        r = rgb_arr[:, :, 0].astype(np.float32)
        g = rgb_arr[:, :, 1].astype(np.float32)
        b = rgb_arr[:, :, 2].astype(np.float32)
        gray = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2GRAY)

        # 1. Determine spectral heuristic based on target query
        target_label = "Target Region"
        target_color_rgb = (6, 182, 212)  # Cyan default

        if "water" in query_lower or "lake" in query_lower or "river" in query_lower or "ocean" in query_lower or "sea" in query_lower:
            target_label = "Water Body"
            target_color_rgb = (14, 165, 233)  # Sky blue
            # Low overall reflectance or high blue absorption ratio
            raw_mask = (b > r * 1.05) & (b > g * 0.85) & (r < 110)
        elif "vegetation" in query_lower or "forest" in query_lower or "crop" in query_lower or "tree" in query_lower or "green" in query_lower:
            target_label = "Vegetation Area"
            target_color_rgb = (34, 197, 94)  # Green
            # Green superiority / VARI proxy
            raw_mask = (g > r * 1.05) & (g > b * 1.02) & (g > 40)
        elif "built-up" in query_lower or "building" in query_lower or "urban" in query_lower or "settlement" in query_lower or "structure" in query_lower:
            target_label = "Built-up Structure"
            target_color_rgb = (245, 158, 11)  # Amber
            # High texture variation + medium to high luminance
            lap = cv2.Laplacian(gray, cv2.CV_32F)
            raw_mask = (np.abs(lap) > 18.0) & (gray > 90) & (gray < 235)
        elif "road" in query_lower or "highway" in query_lower:
            target_label = "Road Network"
            target_color_rgb = (236, 72, 153)  # Pink
            edges = cv2.Canny(gray, 50, 150)
            raw_mask = edges > 0
        else:
            # Fallback to high-contrast saliency
            target_label = f"Region ({target_query[:20]})"
            target_color_rgb = (168, 85, 247)  # Purple
            mean_lum = np.mean(gray)
            raw_mask = np.abs(gray.astype(np.float32) - mean_lum) > 35

        # 2. Morphological filtering to clean noise and group clusters
        mask_uint8 = (raw_mask.astype(np.uint8)) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned_mask = cv2.morphologyEx(mask_uint8, cv2.MORPH_OPEN, kernel)
        cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel)

        # 3. Find connected contours and extract bounding boxes
        contours, _ = cv2.findContours(
            cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        min_area = max(int(h * w * 0.001), 25)
        boxes: list[RegionBox] = []
        box_id = 1

        # Sort contours by area descending
        sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        for cnt in sorted_contours:
            area = cv2.contourArea(cnt)
            if area >= min_area:
                x, y, bw, bh = cv2.boundingRect(cnt)
                # Compute confidence estimate based on shape compactness & density
                solidity = area / float(bw * bh + 1e-5)
                conf_estimate = min(0.95, max(0.55, 0.65 + solidity * 0.25))

                boxes.append(
                    RegionBox(
                        box_id=box_id,
                        xmin=int(x),
                        ymin=int(y),
                        xmax=int(x + bw),
                        ymax=int(y + bh),
                        label=target_label,
                        confidence_estimate=round(conf_estimate, 2),
                        area_pixels=int(area),
                    )
                )
                box_id += 1

        coverage_percent = round((np.count_nonzero(cleaned_mask) / float(h * w)) * 100.0, 2)

        return {
            "mask": cleaned_mask,
            "boxes": boxes,
            "target_label": target_label,
            "target_color_rgb": target_color_rgb,
            "coverage_percent": coverage_percent,
            "cluster_count": len(boxes),
            "adapter": self.name,
            "execution_mode": self.execution_mode,
        }
