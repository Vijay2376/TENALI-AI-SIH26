"""Text-Guided Region Grounding Specialist Tool."""

from typing import Any

import numpy as np

from app.adapters.base import BaseAdapter
from app.adapters.demo_grounding import DemoGroundingAdapter
from app.schemas.requests import InputMode
from app.tools.base import BaseTool


class GroundingTool(BaseTool):
    """Specialist tool for locating and segmenting text-specified geographic objects and features."""

    def __init__(self, adapter: BaseAdapter | None = None):
        super().__init__(
            name="grounding_tool",
            description="Locates, segments, and bounds target objects/land features specified in queries",
            supported_inputs=[InputMode.SINGLE],
            adapter=adapter or DemoGroundingAdapter(),
        )

    def execute(
        self,
        rgb_arr: np.ndarray,
        target_query: str,
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute text-guided grounding."""
        return self.adapter.run(
            rgb_arr=rgb_arr, target_query=target_query, metadata=metadata
        )
