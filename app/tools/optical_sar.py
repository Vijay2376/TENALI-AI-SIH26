"""Optical + SAR Cross-Modal Fusion Specialist Tool."""

from typing import Any

import numpy as np

from app.adapters.base import BaseAdapter
from app.adapters.demo_optical_sar import DemoOpticalSARAdapter
from app.schemas.requests import InputMode
from app.tools.base import BaseTool


class OpticalSARFusionTool(BaseTool):
    """Specialist tool for synergistic cross-modal reasoning over Optical and SAR imagery."""

    def __init__(self, adapter: BaseAdapter | None = None):
        super().__init__(
            name="optical_sar_tool",
            description="Fuses optical multi-spectral features with SAR radar backscatter for robust scene reasoning",
            supported_inputs=[InputMode.OPTICAL_SAR],
            adapter=adapter or DemoOpticalSARAdapter(),
        )

    def execute(
        self,
        optical_rgb: np.ndarray,
        sar_rgb: np.ndarray,
        query: str = "",
        metadata_opt: dict[str, Any] | None = None,
        metadata_sar: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute optical + SAR fusion."""
        return self.adapter.run(
            optical_rgb=optical_rgb,
            sar_rgb=sar_rgb,
            query=query,
            metadata_opt=metadata_opt,
            metadata_sar=metadata_sar,
        )
