"""Spatial Analysis and Coordinate/Geometry Specialist Tool."""

from typing import Any

from app.adapters.base import BaseAdapter
from app.schemas.requests import InputMode
from app.schemas.responses import RegionBox
from app.tools.base import BaseTool


class DummySpatialAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("SpatialGeometryProcessor", "GIS PROCESSING")

    def run(self, **kwargs) -> dict[str, Any]:
        return {}


class SpatialAnalysisTool(BaseTool):
    """Specialist tool for computing bounding boxes, geospatial extents, and centroid positions."""

    def __init__(self):
        super().__init__(
            name="spatial_analysis_tool",
            description="Performs geometric, spatial coordinate, and bounding box analysis",
            supported_inputs=[InputMode.SINGLE, InputMode.BI_TEMPORAL, InputMode.OPTICAL_SAR],
            adapter=DummySpatialAdapter(),
        )

    def execute(
        self,
        boxes: list[RegionBox],
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> list[RegionBox]:
        """Enrich bounding boxes with approximate geospatial coordinates if transform exists."""
        if not metadata or not metadata.get("bounds"):
            return boxes

        bounds = metadata["bounds"]  # [min_x, min_y, max_x, max_y]
        width = metadata.get("width", 1000)
        height = metadata.get("height", 1000)

        min_x, min_y, max_x, max_y = bounds

        enriched: list[RegionBox] = []
        for b in boxes:
            # Map pixel coordinates to approximate geographic coordinates
            geo_xmin = min_x + (b.xmin / float(width)) * (max_x - min_x)
            geo_xmax = min_x + (b.xmax / float(width)) * (max_x - min_x)
            geo_ymax = max_y - (b.ymin / float(height)) * (max_y - min_y)
            geo_ymin = max_y - (b.ymax / float(height)) * (max_y - min_y)

            b_copy = b.model_copy()
            b_copy.approx_geo_coords = {
                "min_lon": round(geo_xmin, 6),
                "min_lat": round(geo_ymin, 6),
                "max_lon": round(geo_xmax, 6),
                "max_lat": round(geo_ymax, 6),
            }
            enriched.append(b_copy)

        return enriched
