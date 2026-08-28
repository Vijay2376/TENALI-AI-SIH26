"""Bi-temporal change detection adapter using image processing and differential morphology."""

from typing import Any

import cv2
import numpy as np

from app.adapters.base import BaseAdapter
from app.image.preprocessing import align_image_pair
from app.schemas.responses import ChangeStatistics, RegionBox
from app.schemas.trace import ExecutionMode


class DemoChangeDetectionAdapter(BaseAdapter):
    """Real image-processing pipeline for bi-temporal remote-sensing change analysis."""

    def __init__(self):
        super().__init__(
            name="DemoChangeDetectionAdapter",
            execution_mode=ExecutionMode.IMAGE_PROCESSING.value,
        )

    def run(
        self,
        t1_rgb: np.ndarray,
        t2_rgb: np.ndarray,
        query: str = "",
        metadata_t1: dict[str, Any] | None = None,
        metadata_t2: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute multi-temporal differential analysis, mask extraction, and change quantification."""
        # 1. Align dimensions
        t1_aligned, t2_aligned = align_image_pair(t1_rgb, t2_rgb)
        h, w = t1_aligned.shape[:2]
        total_pixels = h * w

        # 2. Multi-channel radiometric difference normalized to [0, 255]
        diff_rgb = np.abs(t2_aligned.astype(np.float32) - t1_aligned.astype(np.float32))
        diff_magnitude = np.sqrt(np.sum(diff_rgb**2, axis=-1)) / np.sqrt(3.0)

        # 3. Grayscale intensity and gradient difference
        gray1 = cv2.cvtColor(t1_aligned, cv2.COLOR_RGB2GRAY).astype(np.float32)
        gray2 = cv2.cvtColor(t2_aligned, cv2.COLOR_RGB2GRAY).astype(np.float32)
        gray_diff = np.abs(gray2 - gray1)

        # Combined differential map in [0, 255] uint8
        combined_diff = np.clip(diff_magnitude * 0.65 + gray_diff * 0.35, 0, 255).astype(np.uint8)

        # 4. Adaptive thresholding using Otsu with robust bounding
        otsu_thresh, _ = cv2.threshold(
            combined_diff, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        effective_thresh = max(min(float(otsu_thresh), 65.0), 25.0)

        raw_mask = (combined_diff >= effective_thresh).astype(np.uint8) * 255

        # 5. Morphological noise filtering
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        cleaned_mask = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN, kernel_open)
        cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel_close)

        # 6. Connected components for discrete change clusters
        num_labels, _labels, stats, _centroids = cv2.connectedComponentsWithStats(
            cleaned_mask, connectivity=8
        )

        min_cluster_area = max(int(total_pixels * 0.0008), 20)
        regions: list[RegionBox] = []
        box_id = 1

        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area >= min_cluster_area:
                x = int(stats[i, cv2.CC_STAT_LEFT])
                y = int(stats[i, cv2.CC_STAT_TOP])
                bw = int(stats[i, cv2.CC_STAT_WIDTH])
                bh = int(stats[i, cv2.CC_STAT_HEIGHT])

                regions.append(
                    RegionBox(
                        box_id=box_id,
                        xmin=x,
                        ymin=y,
                        xmax=x + bw,
                        ymax=y + bh,
                        label=f"Change Cluster #{box_id}",
                        confidence_estimate=round(
                            min(0.95, max(0.60, 0.70 + (area / total_pixels) * 5.0)), 2
                        ),
                        area_pixels=int(area),
                    )
                )
                box_id += 1

        # 7. Calculate change statistics
        changed_pixels = int(np.count_nonzero(cleaned_mask))
        changed_percent = round((changed_pixels / float(total_pixels)) * 100.0, 2)

        # Approximate geospatial area if resolution exists in metadata
        approx_ha = None
        approx_sqkm = None
        if metadata_t1 and metadata_t1.get("resolution"):
            res = metadata_t1["resolution"]
            if isinstance(res, (list, tuple)) and len(res) >= 2:
                pixel_area_m2 = abs(float(res[0]) * float(res[1]))
                total_area_m2 = changed_pixels * pixel_area_m2
                approx_ha = round(total_area_m2 / 10000.0, 2)
                approx_sqkm = round(total_area_m2 / 1000000.0, 4)

        # 8. Built-up inference heuristic
        # Compare high-frequency texture change in changed pixels
        lap1 = cv2.Laplacian(gray1, cv2.CV_32F)
        lap2 = cv2.Laplacian(gray2, cv2.CV_32F)
        change_idx = cleaned_mask > 0

        trend = "unchanged"
        if changed_percent < 0.5:
            trend = "unchanged"
        elif np.any(change_idx):
            tex1 = np.mean(np.abs(lap1)[change_idx])
            tex2 = np.mean(np.abs(lap2)[change_idx])
            lum1 = np.mean(gray1[change_idx])
            lum2 = np.mean(gray2[change_idx])

            if tex2 > tex1 * 1.15 and lum2 > lum1:
                trend = "increased"
            elif tex1 > tex2 * 1.15 and lum1 > lum2:
                trend = "decreased"
            else:
                trend = "mixed_change"

        stats_obj = ChangeStatistics(
            total_pixels=total_pixels,
            changed_pixels=changed_pixels,
            changed_percent=changed_percent,
            trend=trend,
            approx_changed_area_ha=approx_ha,
            approx_changed_area_sqkm=approx_sqkm,
            region_count=len(regions),
            is_approximate=True,
        )

        return {
            "t1_aligned": t1_aligned,
            "t2_aligned": t2_aligned,
            "change_mask": cleaned_mask,
            "diff_magnitude": combined_diff,
            "regions": regions,
            "statistics": stats_obj,
            "adapter": self.name,
            "execution_mode": self.execution_mode,
        }
