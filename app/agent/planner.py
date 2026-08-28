"""Dynamic task execution planning for agentic orchestration."""

from dataclasses import dataclass

from app.agent.router import RoutedIntent
from app.schemas.trace import TaskType


@dataclass
class PlanStep:
    """A planned execution stage."""

    step_name: str
    tool_name: str | None
    description: str


class TaskPlanner:
    """Generates an auditable execution sequence for a given routed intent."""

    def create_plan(self, intent: RoutedIntent) -> list[PlanStep]:
        """Construct multi-step workflow sequence based on task type."""
        plan: list[PlanStep] = [
            PlanStep(
                step_name="input_validation",
                tool_name=None,
                description="Validate image formats, dimensions, and radiometric integrity",
            ),
            PlanStep(
                step_name="query_understanding",
                tool_name=None,
                description=f"Route query intent using {intent.router_engine}",
            ),
        ]

        if intent.task_type in [TaskType.BI_TEMPORAL_CHANGE, TaskType.BUILT_UP_CHANGE]:
            plan.extend(
                [
                    PlanStep(
                        step_name="change_detection",
                        tool_name="change_detection_tool",
                        description="Execute multi-temporal differential analysis and adaptive thresholding",
                    ),
                    PlanStep(
                        step_name="change_statistics",
                        tool_name="change_statistics_tool",
                        description="Quantify changed area, pixel percentage, and trend direction",
                    ),
                    PlanStep(
                        step_name="spatial_analysis",
                        tool_name="spatial_analysis_tool",
                        description="Enrich change clusters with bounding boxes and geospatial bounds",
                    ),
                    PlanStep(
                        step_name="evidence_generation",
                        tool_name="evidence_generation_tool",
                        description="Render T1, T2, change heatmap, and composite overlays",
                    ),
                    PlanStep(
                        step_name="answer_synthesis",
                        tool_name=None,
                        description="Synthesize grounded answer with quantitative metrics",
                    ),
                ]
            )

        elif intent.task_type == TaskType.OPTICAL_SAR_ANALYSIS:
            plan.extend(
                [
                    PlanStep(
                        step_name="optical_analysis",
                        tool_name="optical_sar_tool",
                        description="Process optical multi-spectral features and spectral indices",
                    ),
                    PlanStep(
                        step_name="sar_analysis",
                        tool_name="optical_sar_tool",
                        description="Process SAR radar backscatter and double-bounce reflection signatures",
                    ),
                    PlanStep(
                        step_name="cross_modal_fusion",
                        tool_name="optical_sar_tool",
                        description="Synergistically fuse optical and radar layers into thematic map",
                    ),
                    PlanStep(
                        step_name="evidence_generation",
                        tool_name="evidence_generation_tool",
                        description="Render Optical, SAR, Fused thematic map, and side-by-side view",
                    ),
                    PlanStep(
                        step_name="answer_synthesis",
                        tool_name=None,
                        description="Synthesize cross-modal grounded reasoning",
                    ),
                ]
            )

        elif intent.task_type == TaskType.GROUNDING:
            plan.extend(
                [
                    PlanStep(
                        step_name="region_grounding",
                        tool_name="grounding_tool",
                        description=f"Segment and isolate '{intent.target_entity}' features",
                    ),
                    PlanStep(
                        step_name="spatial_analysis",
                        tool_name="spatial_analysis_tool",
                        description="Calculate bounding boxes, areas, and geographic bounds",
                    ),
                    PlanStep(
                        step_name="evidence_generation",
                        tool_name="evidence_generation_tool",
                        description="Compose semi-transparent masks and annotated overlays",
                    ),
                    PlanStep(
                        step_name="answer_synthesis",
                        tool_name=None,
                        description="Summarize detected region locations and confidence",
                    ),
                ]
            )

        else:  # SINGLE_IMAGE_VQA or CAPTIONING
            plan.extend(
                [
                    PlanStep(
                        step_name="specialist_vqa",
                        tool_name="vqa_tool",
                        description="Run BigEarthNet domain adaptation and spectral scene reasoning",
                    ),
                    PlanStep(
                        step_name="evidence_generation",
                        tool_name="evidence_generation_tool",
                        description="Generate normalized high-contrast visual preview",
                    ),
                    PlanStep(
                        step_name="answer_synthesis",
                        tool_name=None,
                        description="Synthesize domain-adapted grounded response",
                    ),
                ]
            )

        return plan


planner = TaskPlanner()
