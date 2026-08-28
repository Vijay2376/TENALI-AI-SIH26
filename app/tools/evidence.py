"""Evidence Generation Specialist Tool."""

from typing import Any

import numpy as np

from app.adapters.base import BaseAdapter
from app.schemas.requests import InputMode
from app.schemas.responses import RegionBox, VisualEvidence
from app.services.evidence import evidence_renderer
from app.tools.base import BaseTool


class DummyEvidenceAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("EvidenceRenderAdapter", "IMAGE PROCESSING")

    def run(self, **kwargs) -> dict[str, Any]:
        return {}


class EvidenceGenerationTool(BaseTool):
    """Specialist tool for composing and saving multi-layer visual evidence artifacts."""

    def __init__(self):
        super().__init__(
            name="evidence_generation_tool",
            description="Composes high-resolution overlay masks, change heatmaps, and evidence collages",
            supported_inputs=[InputMode.SINGLE, InputMode.BI_TEMPORAL, InputMode.OPTICAL_SAR],
            adapter=DummyEvidenceAdapter(),
        )

    def execute(
        self,
        mode: InputMode,
        rgb_primary: np.ndarray,
        rgb_secondary: np.ndarray | None = None,
        mask: np.ndarray | None = None,
        diff_magnitude: np.ndarray | None = None,
        boxes: list[RegionBox] | None = None,
        target_name: str = "Target Region",
        color_rgb: tuple[int, int, int] = (6, 182, 212),
        fused_map: np.ndarray | None = None,
        statistics: Any = None,
        **kwargs,
    ) -> VisualEvidence:
        """Render and assemble structured VisualEvidence."""
        evidence = VisualEvidence(
            regions=boxes or [],
            statistics=statistics,
        )

        if mode == InputMode.SINGLE:
            from app.image.preview import save_preview_image

            _, orig_url = save_preview_image(rgb_primary, "single_orig")
            evidence.primary_image_url = orig_url
            evidence.layers["original"] = orig_url

            if mask is not None:
                annotated_url, mask_url = evidence_renderer.render_grounding_overlay(
                    rgb_primary,
                    mask=mask,
                    boxes=boxes or [],
                    target_name=target_name,
                    color_rgb=color_rgb,
                )
                evidence.annotated_image_url = annotated_url
                evidence.mask_image_url = mask_url
                evidence.layers["mask"] = mask_url
                evidence.layers["annotated"] = annotated_url

        elif mode == InputMode.BI_TEMPORAL:
            if rgb_secondary is not None and mask is not None and diff_magnitude is not None:
                t1_url, t2_url, change_map_url, comp_url = (
                    evidence_renderer.render_bitemporal_change_evidence(
                        rgb_primary,
                        rgb_secondary,
                        change_mask=mask,
                        diff_magnitude=diff_magnitude,
                        regions=boxes or [],
                    )
                )
                evidence.primary_image_url = t1_url
                evidence.secondary_image_url = t2_url
                evidence.change_map_url = change_map_url
                evidence.composite_url = comp_url
                evidence.layers["t1"] = t1_url
                evidence.layers["t2"] = t2_url
                evidence.layers["change_map"] = change_map_url
                evidence.layers["composite"] = comp_url

        elif mode == InputMode.OPTICAL_SAR and rgb_secondary is not None and fused_map is not None:
            opt_url, sar_url, fused_url, collage_url = (
                evidence_renderer.render_optical_sar_fusion_evidence(
                    rgb_primary,
                    rgb_secondary,
                    fused_thematic_map=fused_map,
                )
            )
            evidence.optical_url = opt_url
            evidence.sar_url = sar_url
            evidence.fused_url = fused_url
            evidence.collage_url = collage_url
            evidence.primary_image_url = opt_url
            evidence.secondary_image_url = sar_url
            evidence.layers["optical"] = opt_url
            evidence.layers["sar"] = sar_url
            evidence.layers["fused"] = fused_url
            evidence.layers["collage"] = collage_url

        return evidence
