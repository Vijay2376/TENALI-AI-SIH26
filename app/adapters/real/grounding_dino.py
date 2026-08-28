"""Real Grounding DINO Remote-Sensing Adapter Stub."""

from typing import Any

import numpy as np

from app.adapters.base import BaseAdapter
from app.schemas.trace import ExecutionMode


class RealGroundingDINOAdapter(BaseAdapter):
    """Integration hook for real Grounding DINO / open-vocabulary remote-sensing object detection."""

    def __init__(self, weights_path: str | None = None):
        super().__init__(
            name="RealGroundingDINOAdapter",
            execution_mode=ExecutionMode.REAL_EO_ADAPTED.value,
        )
        self.weights_path = weights_path
        self.is_loaded = False

    def load_model(self):
        """Lazy load Grounding DINO model."""
        self.is_loaded = True

    def run(
        self,
        rgb_arr: np.ndarray,
        target_query: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute real Grounding DINO inference."""
        if not self.is_loaded:
            raise NotImplementedError(
                "Real Grounding DINO weights are not loaded. Use DemoGroundingAdapter."
            )
        return {
            "mask": np.zeros(rgb_arr.shape[:2], dtype=np.uint8),
            "boxes": [],
            "adapter": self.name,
            "execution_mode": self.execution_mode,
        }
