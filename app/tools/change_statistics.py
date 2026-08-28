"""Change Statistics Specialist Tool."""

from typing import Any

import numpy as np

from app.adapters.base import BaseAdapter
from app.schemas.requests import InputMode
from app.schemas.responses import ChangeStatistics
from app.tools.base import BaseTool


class DummyChangeStatsAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("ChangeStatisticsProcessor", "IMAGE PROCESSING")

    def run(self, **kwargs) -> dict[str, Any]:
        return {}


class ChangeStatisticsTool(BaseTool):
    """Specialist tool for computing quantitative change metrics, percentages, and areas."""

    def __init__(self):
        super().__init__(
            name="change_statistics_tool",
            description="Calculates changed pixel percentages, trends, and geospatial area estimates",
            supported_inputs=[InputMode.BI_TEMPORAL],
            adapter=DummyChangeStatsAdapter(),
        )

    def execute(
        self,
        change_mask: np.ndarray,
        total_pixels: int,
        metadata: dict[str, Any] | None = None,
        trend: str = "unchanged",
        **kwargs,
    ) -> ChangeStatistics:
        """Compute change statistics from binary mask and metadata."""
        changed_pixels = int(np.count_nonzero(change_mask))
        changed_percent = round((changed_pixels / float(total_pixels + 1e-5)) * 100.0, 2)

        approx_ha = None
        approx_sqkm = None
        if metadata and metadata.get("resolution"):
            res = metadata["resolution"]
            if isinstance(res, (list, tuple)) and len(res) >= 2:
                pixel_area_m2 = abs(float(res[0]) * float(res[1]))
                total_area_m2 = changed_pixels * pixel_area_m2
                approx_ha = round(total_area_m2 / 10000.0, 2)
                approx_sqkm = round(total_area_m2 / 1000000.0, 4)

        return ChangeStatistics(
            total_pixels=total_pixels,
            changed_pixels=changed_pixels,
            changed_percent=changed_percent,
            trend=trend,
            approx_changed_area_ha=approx_ha,
            approx_changed_area_sqkm=approx_sqkm,
            is_approximate=True,
        )
