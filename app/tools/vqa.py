"""Visual Question Answering Specialist Tool."""

from typing import Any

import numpy as np

from app.adapters.base import BaseAdapter
from app.adapters.demo_vqa import DemoVQAAdapter
from app.schemas.requests import InputMode
from app.tools.base import BaseTool


class VQATool(BaseTool):
    """Specialist tool for answering natural-language queries regarding satellite imagery."""

    def __init__(self, adapter: BaseAdapter | None = None):
        super().__init__(
            name="vqa_tool",
            description="Performs visual question answering on single remote sensing images",
            supported_inputs=[InputMode.SINGLE],
            adapter=adapter or DemoVQAAdapter(),
        )

    def execute(
        self,
        rgb_arr: np.ndarray,
        query: str,
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute VQA reasoning."""
        return self.adapter.run(rgb_arr=rgb_arr, query=query, metadata=metadata)
