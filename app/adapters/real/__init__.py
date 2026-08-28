"""Real Remote Sensing Deep Learning Model Integration Adapters."""

from app.adapters.real.change_former import RealChangeFormerAdapter
from app.adapters.real.grounding_dino import RealGroundingDINOAdapter
from app.adapters.real.vlm_adapter import RealRemoteSensingVLMAdapter

__all__ = [
    "RealChangeFormerAdapter",
    "RealGroundingDINOAdapter",
    "RealRemoteSensingVLMAdapter",
]
