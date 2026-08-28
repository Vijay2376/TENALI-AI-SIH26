"""VQA adapter combining BigEarthNet domain adaptation and scene heuristics."""

from typing import Any

import numpy as np

from app.adapters.base import BaseAdapter
from app.image.preprocessing import extract_scene_descriptors
from app.schemas.trace import ExecutionMode
from app.services.adaptation import adaptation_service


class DemoVQAAdapter(BaseAdapter):
    """VQA Adapter powered by BigEarthNet-19 domain-adapted spectral classifier and scene metrics."""

    def __init__(self):
        super().__init__(
            name="DemoVQAAdapter",
            execution_mode=ExecutionMode.REAL_EO_ADAPTED.value,
        )

    def run(
        self,
        rgb_arr: np.ndarray,
        query: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Answer remote sensing query based on domain classification and spatial-spectral metrics."""
        # 1. Run BigEarthNet domain classifier
        prediction = adaptation_service.predict_landcover(rgb_arr)
        descriptors = extract_scene_descriptors(rgb_arr)

        query_lower = query.lower()

        # 2. Formulate grounded answer according to query intent and spectral evidence
        if "land-cover" in query_lower or "describe" in query_lower or "scene" in query_lower or "type" in query_lower:
            answer = (
                f"The remote-sensing scene is predominantly classified as '{prediction.top_class}' "
                f"with an estimated domain confidence of {prediction.confidence_estimate:.1%}. "
                f"Spectral analysis reveals {descriptors['vegetation_ratio']:.1%} vegetation density, "
                f"{descriptors['water_ratio']:.1%} water index coverage, and {descriptors['builtup_ratio']:.1%} built-up structure signatures."
            )
        elif "water" in query_lower:
            if descriptors["water_ratio"] > 0.05:
                answer = (
                    f"Water bodies are clearly identified within the scene, covering approximately "
                    f"{descriptors['water_ratio']:.1%} of the visible raster area with distinct low-reflectance absorption."
                )
            else:
                answer = (
                    f"No significant large open water bodies were detected. Water index coverage is minimal ({descriptors['water_ratio']:.1%})."
                )
        elif "built-up" in query_lower or "urban" in query_lower or "building" in query_lower:
            answer = (
                f"Built-up and structural density is estimated at {descriptors['builtup_ratio']:.1%}. "
                f"Spatial texture roughness variance is measured at {descriptors['texture_roughness']:.1f}."
            )
        elif "vegetation" in query_lower or "forest" in query_lower or "tree" in query_lower:
            answer = (
                f"Vegetation cover accounts for approximately {descriptors['vegetation_ratio']:.1%} of the scene, "
                f"consistent with BigEarthNet class '{prediction.top_class}'."
            )
        else:
            answer = (
                f"Analysis grounded in BigEarthNet remote-sensing taxonomy identifies the primary land class as "
                f"'{prediction.top_class}' (confidence estimate: {prediction.confidence_estimate:.2f})."
            )

        return {
            "answer": answer,
            "confidence_estimate": prediction.confidence_estimate,
            "top_class": prediction.top_class,
            "class_distribution": prediction.class_distribution,
            "descriptors": descriptors,
            "features_used": prediction.features_used,
            "adapter": self.name,
            "execution_mode": self.execution_mode,
        }
