"""Structured response models for TENALI AI."""

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.trace import ExecutionMode, ExecutionStep, TaskType


class RasterMetadata(BaseModel):
    """Extracted raster and geospatial metadata."""

    filename: str
    format: str
    width: int
    height: int
    bands: int
    dtype: str
    crs: str | None = None
    bounds: list[float] | None = None
    resolution: list[float] | None = None
    file_size_kb: float = 0.0
    modality: str = "optical"
    approximate_center: list[float] | None = None
    footprint_geojson: dict[str, Any] | None = None


class RegionBox(BaseModel):
    """Grounding or change bounding box."""

    box_id: int
    xmin: int
    ymin: int
    xmax: int
    ymax: int
    label: str
    confidence_estimate: float = 0.85
    area_pixels: int = 0
    approx_geo_coords: dict[str, float] | None = None


class ChangeStatistics(BaseModel):
    """Calculated change detection statistics."""

    total_pixels: int = 0
    changed_pixels: int = 0
    changed_percent: float = 0.0
    trend: str = "unchanged"  # "increased", "decreased", "unchanged", "mixed_change"
    approx_changed_area_ha: float | None = None
    approx_changed_area_sqkm: float | None = None
    region_count: int = 0
    is_approximate: bool = True


class VisualEvidence(BaseModel):
    """Visual evidence artifacts generated during analysis."""

    primary_image_url: str | None = None
    secondary_image_url: str | None = None
    annotated_image_url: str | None = None
    mask_image_url: str | None = None
    change_map_url: str | None = None
    composite_url: str | None = None
    optical_url: str | None = None
    sar_url: str | None = None
    fused_url: str | None = None
    collage_url: str | None = None
    regions: list[RegionBox] = Field(default_factory=list)
    statistics: ChangeStatistics | dict[str, Any] | None = None
    layers: dict[str, str] = Field(default_factory=dict)
    footprint_geojson: dict[str, Any] | None = None


class AnalysisResponse(BaseModel):
    """Comprehensive API response contract for /analyze."""

    success: bool = True
    task: TaskType | str = TaskType.SINGLE_IMAGE_VQA
    answer: str = Field(..., description="Synthesized grounded answer")
    confidence_estimate: float = Field(
        ..., ge=0.0, le=1.0, description="Estimated confidence score (0.0 - 1.0)"
    )
    confidence_level: str = Field(
        default="Medium", description="Qualitative estimate: High | Medium | Low | Heuristic"
    )
    execution_mode: ExecutionMode | str = ExecutionMode.DEMO_ADAPTER
    inputs: dict[str, Any] = Field(default_factory=dict)
    tools_used: list[str] = Field(default_factory=list)
    evidence: VisualEvidence = Field(default_factory=VisualEvidence)
    metadata: dict[str, Any] = Field(default_factory=dict)
    execution_trace: list[ExecutionStep] = Field(default_factory=list)
    disclaimer: str = Field(
        default="Confidence is an uncalibrated estimate. Demo adapters use transparent heuristics.",
        description="Technical honesty notice",
    )
    report_id: str | None = None
    error: str | None = None
