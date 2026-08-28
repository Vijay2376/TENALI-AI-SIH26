"""Bi-Temporal Change Detection Specialist Tool."""

from typing import Any

import numpy as np

from app.adapters.base import BaseAdapter
from app.adapters.demo_change import DemoChangeDetectionAdapter
from app.schemas.requests import InputMode
from app.tools.base import BaseTool


class ChangeDetectionTool(BaseTool):
    """Specialist tool for bi-temporal remote-sensing differential analysis."""

    def __init__(self, adapter: BaseAdapter | None = None):
        super().__init__(
            name="change_detection_tool",
            description="Analyzes bi-temporal pairs (T1 and T2) to detect and locate landscape/structural changes",
            supported_inputs=[InputMode.BI_TEMPORAL],
            adapter=adapter or DemoChangeDetectionAdapter(),
        )

    def execute(
        self,
        t1_rgb: np.ndarray,
        t2_rgb: np.ndarray,
        query: str = "",
        metadata_t1: dict[str, Any] | None = None,
        metadata_t2: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute change detection."""
        return self.adapter.run(
            t1_rgb=t1_rgb,
            t2_rgb=t2_rgb,
            query=query,
            metadata_t1=metadata_t1,
            metadata_t2=metadata_t2,
        )
