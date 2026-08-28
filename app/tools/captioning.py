"""Scene Description and Land-Cover Captioning Specialist Tool."""

from typing import Any

import numpy as np

from app.adapters.base import BaseAdapter
from app.adapters.demo_vqa import DemoVQAAdapter
from app.schemas.requests import InputMode
from app.tools.base import BaseTool


class CaptioningTool(BaseTool):
    """Specialist tool for generating descriptive summaries and land-use reports of remote-sensing scenes."""

    def __init__(self, adapter: BaseAdapter | None = None):
        super().__init__(
            name="captioning_tool",
            description="Generates comprehensive natural-language scene descriptions and land-cover breakdowns",
            supported_inputs=[InputMode.SINGLE],
            adapter=adapter or DemoVQAAdapter(),
        )

    def execute(
        self,
        rgb_arr: np.ndarray,
        query: str = "Describe this scene",
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute scene captioning."""
        return self.adapter.run(rgb_arr=rgb_arr, query=query, metadata=metadata)
