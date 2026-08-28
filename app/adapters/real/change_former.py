"""Real Siamese ChangeFormer Adapter Stub."""

from typing import Any

import numpy as np

from app.adapters.base import BaseAdapter
from app.schemas.trace import ExecutionMode


class RealChangeFormerAdapter(BaseAdapter):
    """Integration hook for transformer-based Siamese ChangeFormer model."""

    def __init__(self, weights_path: str | None = None):
        super().__init__(
            name="RealChangeFormerAdapter",
            execution_mode=ExecutionMode.REAL_EO_ADAPTED.value,
        )
        self.weights_path = weights_path
        self.is_loaded = False

    def load_model(self):
        """Lazy load ChangeFormer PyTorch checkpoint."""
        self.is_loaded = True

    def run(
        self,
        t1_rgb: np.ndarray,
        t2_rgb: np.ndarray,
        query: str = "",
        metadata_t1: dict[str, Any] | None = None,
        metadata_t2: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute real ChangeFormer inference."""
        if not self.is_loaded:
            raise NotImplementedError(
                "Real ChangeFormer weights are not loaded. Use DemoChangeDetectionAdapter."
            )
        return {
            "change_mask": np.zeros(t1_rgb.shape[:2], dtype=np.uint8),
            "adapter": self.name,
            "execution_mode": self.execution_mode,
        }
