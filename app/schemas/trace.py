"""Execution trace schemas and telemetry models."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Supported task types in TENALI AI."""

    SINGLE_IMAGE_VQA = "single_image_vqa"
    GROUNDING = "grounding"
    CAPTIONING = "captioning"
    BI_TEMPORAL_CHANGE = "bi_temporal_change"
    BUILT_UP_CHANGE = "built_up_change"
    OPTICAL_SAR_ANALYSIS = "optical_sar_analysis"
    SPATIAL_ANALYSIS = "spatial_analysis"
    UNKNOWN = "unknown"


class ExecutionMode(str, Enum):
    """Categorization of model/adapter implementation."""

    REAL_EO_ADAPTED = "REAL EO ADAPTED MODEL"
    IMAGE_PROCESSING = "IMAGE PROCESSING"
    HEURISTIC = "HEURISTIC"
    DEMO_ADAPTER = "DEMO ADAPTER"
    LLM_ASSISTED = "LLM-ASSISTED"
    APPROXIMATE = "APPROXIMATE / DEMO-DERIVED"


class StepStatus(str, Enum):
    """Status of an execution step."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionStep(BaseModel):
    """Individual auditable step in the agent workflow."""

    step: str = Field(..., description="Name of the workflow stage")
    status: StepStatus = Field(default=StepStatus.SUCCESS)
    tool: str | None = Field(default=None, description="Tool name if applicable")
    implementation: str | None = Field(
        default=None, description="Adapter or class name"
    )
    duration_ms: float = Field(default=0.0, description="Duration in milliseconds")
    details: dict[str, Any] | str | None = Field(
        default=None, description="Structured step metadata"
    )


class ExecutionTrace(BaseModel):
    """Full execution trace of the analysis pipeline."""

    steps: list[ExecutionStep] = Field(default_factory=list)
    total_duration_ms: float = Field(default=0.0)

    def add_step(
        self,
        step: str,
        status: StepStatus = StepStatus.SUCCESS,
        tool: str | None = None,
        implementation: str | None = None,
        duration_ms: float = 0.0,
        details: dict[str, Any] | str | None = None,
    ) -> ExecutionStep:
        """Helper to append an execution step."""
        item = ExecutionStep(
            step=step,
            status=status,
            tool=tool,
            implementation=implementation,
            duration_ms=round(duration_ms, 2),
            details=details,
        )
        self.steps.append(item)
        self.total_duration_ms = round(self.total_duration_ms + duration_ms, 2)
        return item
