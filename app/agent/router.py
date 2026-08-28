"""Dual-engine Query Intent Router for TENALI AI."""

from dataclasses import dataclass
from typing import Any

from app.schemas.requests import InputMode
from app.schemas.trace import TaskType
from app.services.gemini import gemini_service


@dataclass
class RoutedIntent:
    """Structured intent routed from user query."""

    task_type: TaskType
    target_entity: str | None
    recommended_tools: list[str]
    router_engine: str  # "Gemini LLM Router" | "Deterministic Rule Router"
    reasoning: str


class IntentRouter:
    """Routes natural language queries and multimodal inputs to specific task specifications."""

    def route(
        self,
        query: str,
        mode: InputMode,
        metadata: dict[str, Any] | None = None,
    ) -> RoutedIntent:
        """Determine task type and required specialist toolchain."""
        query_str = query.strip()
        query_lower = query_str.lower()

        # 1. Attempt LLM routing if Gemini is available
        if gemini_service.is_available():
            llm_res = gemini_service.classify_intent_with_llm(
                query=query_str, mode=mode.value, metadata=metadata
            )
            if llm_res and "task_type" in llm_res:
                try:
                    task_enum = TaskType(llm_res["task_type"])
                    return RoutedIntent(
                        task_type=task_enum,
                        target_entity=llm_res.get("target_entity"),
                        recommended_tools=llm_res.get("requires_tools", []),
                        router_engine="Gemini LLM Router",
                        reasoning=llm_res.get(
                            "reasoning", "Classified via Google Gemini NLP engine"
                        ),
                    )
                except ValueError:
                    pass

        # 2. Deterministic Pattern Router (SIH Benchmark / Offline Demo Mode)
        if mode == InputMode.BI_TEMPORAL:
            if "built-up" in query_lower or "urban" in query_lower or "increase" in query_lower or "decrease" in query_lower:
                return RoutedIntent(
                    task_type=TaskType.BUILT_UP_CHANGE,
                    target_entity="built-up structures",
                    recommended_tools=[
                        "change_detection_tool",
                        "change_statistics_tool",
                        "spatial_analysis_tool",
                        "evidence_generation_tool",
                    ],
                    router_engine="Deterministic Rule Router",
                    reasoning="Bi-temporal input paired with built-up change query semantics",
                )
            else:
                return RoutedIntent(
                    task_type=TaskType.BI_TEMPORAL_CHANGE,
                    target_entity="landscape change",
                    recommended_tools=[
                        "change_detection_tool",
                        "change_statistics_tool",
                        "spatial_analysis_tool",
                        "evidence_generation_tool",
                    ],
                    router_engine="Deterministic Rule Router",
                    reasoning="Bi-temporal pair with general temporal change query",
                )

        elif mode == InputMode.OPTICAL_SAR:
            return RoutedIntent(
                task_type=TaskType.OPTICAL_SAR_ANALYSIS,
                target_entity="optical + SAR cross-modal features",
                recommended_tools=[
                    "optical_sar_tool",
                    "spatial_analysis_tool",
                    "evidence_generation_tool",
                ],
                router_engine="Deterministic Rule Router",
                reasoning="Dual-sensor Optical and SAR co-registered input configuration",
            )

        else:  # InputMode.SINGLE
            # Grounding detection verbs
            grounding_verbs = ["highlight", "locate", "show", "where", "find", "segment", "box", "detect", "point out"]
            if any(v in query_lower for v in grounding_verbs):
                # Extract target entity
                target_entity = query_str
                for v in grounding_verbs:
                    if v in query_lower:
                        parts = query_lower.split(v, 1)
                        if len(parts) > 1 and parts[1].strip():
                            target_entity = parts[1].strip().strip(".?!")
                        break

                return RoutedIntent(
                    task_type=TaskType.GROUNDING,
                    target_entity=target_entity,
                    recommended_tools=[
                        "grounding_tool",
                        "spatial_analysis_tool",
                        "evidence_generation_tool",
                    ],
                    router_engine="Deterministic Rule Router",
                    reasoning=f"Spatial localization query targeting '{target_entity}'",
                )

            if "land-cover" in query_lower or "object" in query_lower or "what" in query_lower or "is there" in query_lower or "how many" in query_lower:
                return RoutedIntent(
                    task_type=TaskType.SINGLE_IMAGE_VQA,
                    target_entity=query_str,
                    recommended_tools=[
                        "vqa_tool",
                        "spatial_analysis_tool",
                        "evidence_generation_tool",
                    ],
                    router_engine="Deterministic Rule Router",
                    reasoning="Single image visual question answering query",
                )

            elif "caption" in query_lower:
                return RoutedIntent(
                    task_type=TaskType.CAPTIONING,
                    target_entity="scene overview",
                    recommended_tools=[
                        "captioning_tool",
                        "spatial_analysis_tool",
                        "evidence_generation_tool",
                    ],
                    router_engine="Deterministic Rule Router",
                    reasoning="Scene captioning request",
                )

            else:
                return RoutedIntent(
                    task_type=TaskType.SINGLE_IMAGE_VQA,
                    target_entity=query_str,
                    recommended_tools=[
                        "vqa_tool",
                        "spatial_analysis_tool",
                        "evidence_generation_tool",
                    ],
                    router_engine="Deterministic Rule Router",
                    reasoning="Single image visual question answering query",
                )


router = IntentRouter()
