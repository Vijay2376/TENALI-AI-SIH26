"""Visual evidence rendering, mask composition, and multi-layer artifact generation."""

import uuid
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from app.config import settings
from app.schemas.responses import RegionBox


class EvidenceRenderer:
    """Service to create annotated overlays, difference heatmaps, and evidence collages."""

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or settings.EVIDENCE_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _save_image(self, img_arr: np.ndarray, prefix: str) -> tuple[Path, str]:
        """Save uint8 numpy image and return (Path, URL)."""
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
        file_path = self.output_dir / filename
        Image.fromarray(img_arr.astype(np.uint8)).save(file_path, format="PNG", optimize=True)
        return file_path, f"/evidence/{filename}"

    def render_grounding_overlay(
        self,
        rgb_arr: np.ndarray,
        mask: np.ndarray,
        boxes: list[RegionBox],
        target_name: str = "Target Region",
        color_rgb: tuple[int, int, int] = (6, 182, 212),  # Cyan
    ) -> tuple[str, str]:
        """Render colored semi-transparent mask and bounding boxes on top of original imagery.

        Returns:
            tuple[str, str]: (annotated_image_url, mask_image_url)
        """
        h, w = rgb_arr.shape[:2]

        # 1. Generate standalone binary/colored mask image
        mask_viz = np.zeros((h, w, 3), dtype=np.uint8)
        mask_bool = mask > 0
        mask_viz[mask_bool] = color_rgb
        _, mask_url = self._save_image(mask_viz, "mask")

        # 2. Blend mask onto original image with 40% alpha
        overlay = rgb_arr.copy()
        overlay[mask_bool] = (
            overlay[mask_bool].astype(np.float32) * 0.55
            + np.array(color_rgb, dtype=np.float32) * 0.45
        ).astype(np.uint8)

        # 3. Draw bounding boxes and text labels
        annotated = overlay.copy()
        for b in boxes:
            cv2.rectangle(
                annotated,
                (b.xmin, b.ymin),
                (b.xmax, b.ymax),
                color=color_rgb,
                thickness=2,
            )
            # Label tag
            tag = f"{b.label} [{b.confidence_estimate:.2f}]"
            cv2.putText(
                annotated,
                tag,
                (b.xmin, max(b.ymin - 6, 15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        _, annotated_url = self._save_image(annotated, "annotated")
        return annotated_url, mask_url

    def render_bitemporal_change_evidence(
        self,
        t1_rgb: np.ndarray,
        t2_rgb: np.ndarray,
        change_mask: np.ndarray,
        diff_magnitude: np.ndarray,
        regions: list[RegionBox],
    ) -> tuple[str, str, str, str]:
        """Render T1, T2, Change Map heatmap, and a side-by-side composite visualization.

        Returns:
            tuple[str, str, str, str]: (t1_url, t2_url, change_map_url, composite_url)
        """
        # Save normalized T1 and T2
        _, t1_url = self._save_image(t1_rgb, "t1_orig")
        _, t2_url = self._save_image(t2_rgb, "t2_orig")

        # Create colored change map heatmap
        # Normalize diff_magnitude to 0-255
        diff_min = float(np.min(diff_magnitude))
        diff_max = float(np.max(diff_magnitude))
        if diff_max > diff_min:
            norm_diff = np.clip((diff_magnitude - diff_min) / (diff_max - diff_min) * 255.0, 0, 255).astype(np.uint8)
        else:
            norm_diff = np.zeros_like(diff_magnitude, dtype=np.uint8)
        # Apply Jet / Inferno colormap
        heatmap = cv2.applyColorMap(norm_diff, cv2.COLORMAP_MAGMA)
        heatmap_rgb = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

        # Highlight binary change mask with vivid crimson overlay
        change_bool = change_mask > 0
        heatmap_rgb[change_bool] = (
            heatmap_rgb[change_bool].astype(np.float32) * 0.4
            + np.array([239, 68, 68], dtype=np.float32) * 0.6  # Red accent
        ).astype(np.uint8)

        # Draw bounding boxes around top change clusters
        for r in regions:
            cv2.rectangle(
                heatmap_rgb,
                (r.xmin, r.ymin),
                (r.xmax, r.ymax),
                color=(245, 158, 11),  # Amber
                thickness=2,
            )

        _, change_map_url = self._save_image(heatmap_rgb, "change_map")

        # Side-by-side tri-panel composite: [ T1 | T2 | Change Heatmap ]
        composite = np.hstack([t1_rgb, t2_rgb, heatmap_rgb])
        _, composite_url = self._save_image(composite, "bitemporal_composite")

        return t1_url, t2_url, change_map_url, composite_url

    def render_optical_sar_fusion_evidence(
        self,
        optical_rgb: np.ndarray,
        sar_rgb: np.ndarray,
        fused_thematic_map: np.ndarray,
    ) -> tuple[str, str, str, str]:
        """Render Optical, SAR, Fused Map, and a tri-view comparative collage.

        Returns:
            tuple[str, str, str, str]: (optical_url, sar_url, fused_url, collage_url)
        """
        _, optical_url = self._save_image(optical_rgb, "optical_orig")
        _, sar_url = self._save_image(sar_rgb, "sar_orig")
        _, fused_url = self._save_image(fused_thematic_map, "fused_thematic")

        collage = np.hstack([optical_rgb, sar_rgb, fused_thematic_map])
        _, collage_url = self._save_image(collage, "optical_sar_fused_collage")

        return optical_url, sar_url, fused_url, collage_url


evidence_renderer = EvidenceRenderer()
