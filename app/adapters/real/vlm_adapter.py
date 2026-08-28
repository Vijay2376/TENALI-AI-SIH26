"""Real Remote Sensing VLM Adapter Stub (GeoChat, SkyEyeGPT, RSGPT).

This adapter defines the integration contract for connecting full-scale remote sensing
Vision-Language Models once weights and GPU acceleration are configured.
"""

from typing import Any

import numpy as np

from app.adapters.base import BaseAdapter
from app.schemas.trace import ExecutionMode


class RealRemoteSensingVLMAdapter(BaseAdapter):
    """Integration hook for real remote-sensing Vision-Language Models (GeoChat / SkyEyeGPT)."""

    def __init__(self, model_path_or_id: str = "GeoChat-7B"):
        super().__init__(
            name="RealRemoteSensingVLMAdapter",
            execution_mode=ExecutionMode.REAL_EO_ADAPTED.value,
        )
        self.model_id = model_path_or_id
        self.is_loaded = False

    def load_model(self):
        """Lazy load HuggingFace/Transformers weights when GPU is active."""
        # Future: AutoModelForCausalLM.from_pretrained(self.model_id, torch_dtype=torch.float16, device_map="auto")
        self.is_loaded = True

    def run(
        self,
        rgb_arr: np.ndarray,
        query: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute real remote sensing VLM inference."""
        if not self.is_loaded:
            raise NotImplementedError(
                f"Real model {self.model_id} is not loaded. Ensure GPU environment and weights are available, or use DemoVQAAdapter."
            )
        # Real model inference logic placeholder
        return {
            "answer": "Real VLM inference placeholder",
            "confidence_estimate": 0.90,
            "adapter": self.name,
            "execution_mode": self.execution_mode,
        }
