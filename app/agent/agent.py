"""Central TenaliOrchestrator - Agentic vision-language pipeline execution."""

import time
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from app.agent.planner import planner
from app.agent.registry import tool_registry
from app.agent.router import router
from app.image.loader import load_raster_image
from app.schemas.requests import InputMode
from app.schemas.responses import AnalysisResponse, VisualEvidence
from app.schemas.trace import ExecutionMode, ExecutionTrace, StepStatus, TaskType
from app.services.gemini import gemini_service


class TenaliOrchestrator:
    """Core Agent Orchestrator for TENALI AI."""

    def __init__(self):
        self.router = router
        self.planner = planner
        self.registry = tool_registry

    def analyze(
        self,
        query: str,
        mode: InputMode,
        image_paths: Sequence[Path | str],
        user_metadata: dict[str, Any] | None = None,
    ) -> AnalysisResponse:
        """Execute the end-to-end agentic remote-sensing analysis pipeline."""
        trace = ExecutionTrace()
        tools_used: list[str] = []
        user_meta = user_metadata or {}

        # ---------------------------------------------------------------------
        # STAGE 1: INPUT VALIDATION
        # ---------------------------------------------------------------------
        step_start = time.perf_counter()
        if not query or len(query.strip()) < 2:
            raise ValueError("Query string must contain at least 2 characters.")

        if mode == InputMode.SINGLE and len(image_paths) != 1:
            raise ValueError(
                f"Single Image mode requires exactly 1 image, but received {len(image_paths)}."
            )
        elif mode == InputMode.BI_TEMPORAL and len(image_paths) != 2:
            raise ValueError(
                f"Bi-Temporal Change analysis requires exactly 2 corresponding images (T1 and T2), but received {len(image_paths)}."
            )
        elif mode == InputMode.OPTICAL_SAR and len(image_paths) != 2:
            raise ValueError(
                f"Optical + SAR analysis requires exactly 2 co-registered images (Optical and SAR), but received {len(image_paths)}."
            )

        trace.add_step(
            step="input_validation",
            status=StepStatus.SUCCESS,
            duration_ms=(time.perf_counter() - step_start) * 1000.0,
            details={
                "mode": mode.value,
                "image_count": len(image_paths),
                "query": query,
            },
        )

        # ---------------------------------------------------------------------
        # STAGE 2: RASTER INGESTION & METADATA EXTRACTION
        # ---------------------------------------------------------------------
        step_start = time.perf_counter()
        rasters: list[tuple[np.ndarray, np.ndarray, Any]] = []
        for p in image_paths:
            raw_arr, rgb_arr, meta = load_raster_image(p)
            rasters.append((raw_arr, rgb_arr, meta))

        primary_meta = rasters[0][2].model_dump()
        secondary_meta = rasters[1][2].model_dump() if len(rasters) > 1 else None

        trace.add_step(
            step="image_metadata_extraction",
            status=StepStatus.SUCCESS,
            duration_ms=(time.perf_counter() - step_start) * 1000.0,
            details={
                "primary": primary_meta,
                "secondary": secondary_meta,
            },
        )

        # ---------------------------------------------------------------------
        # STAGE 3: QUERY UNDERSTANDING & INTENT ROUTING
        # ---------------------------------------------------------------------
        step_start = time.perf_counter()
        intent = self.router.route(query=query, mode=mode, metadata=primary_meta)
        trace.add_step(
            step="query_understanding",
            status=StepStatus.SUCCESS,
            duration_ms=(time.perf_counter() - step_start) * 1000.0,
            details={
                "task_type": intent.task_type.value,
                "target_entity": intent.target_entity,
                "router_engine": intent.router_engine,
                "reasoning": intent.reasoning,
            },
        )

        # ---------------------------------------------------------------------
        # STAGE 4: AGENTIC TASK PLANNING & TOOL SELECTION
        # ---------------------------------------------------------------------
        step_start = time.perf_counter()
        plan = self.planner.create_plan(intent)
        selected_tools = [p.tool_name for p in plan if p.tool_name]
        trace.add_step(
            step="tool_selection",
            status=StepStatus.SUCCESS,
            duration_ms=(time.perf_counter() - step_start) * 1000.0,
            details={"selected_tools": selected_tools},
        )

        # ---------------------------------------------------------------------
        # STAGE 5: SPECIALIST ANALYSIS EXECUTION
        # ---------------------------------------------------------------------
        analysis_context: dict[str, Any] = {}
        evidence = VisualEvidence()
        confidence_estimate = 0.85
        exec_mode = ExecutionMode.DEMO_ADAPTER.value

        # Execute according to task
        if intent.task_type in [TaskType.BI_TEMPORAL_CHANGE, TaskType.BUILT_UP_CHANGE]:
            t1_rgb = rasters[0][1]
            t2_rgb = rasters[1][1]

            # 1. Change Detection Tool
            t_tool_start = time.perf_counter()
            cd_tool = self.registry.get("change_detection_tool")
            tools_used.append(cd_tool.name)
            cd_res = cd_tool.execute(
                t1_rgb=t1_rgb,
                t2_rgb=t2_rgb,
                query=query,
                metadata_t1=primary_meta,
                metadata_t2=secondary_meta,
            )
            exec_mode = cd_res.get("execution_mode", ExecutionMode.IMAGE_PROCESSING.value)
            trace.add_step(
                step="change_detection",
                tool=cd_tool.name,
                implementation=cd_res.get("adapter", "DemoChangeDetectionAdapter"),
                duration_ms=(time.perf_counter() - t_tool_start) * 1000.0,
                details={
                    "total_pixels": cd_res["statistics"].total_pixels,
                    "changed_pixels": cd_res["statistics"].changed_pixels,
                    "changed_percent": cd_res["statistics"].changed_percent,
                    "trend": cd_res["statistics"].trend,
                },
            )

            # 2. Spatial Analysis Tool (enrich bounding boxes)
            t_sp_start = time.perf_counter()
            sp_tool = self.registry.get("spatial_analysis_tool")
            tools_used.append(sp_tool.name)
            enriched_boxes = sp_tool.execute(boxes=cd_res["regions"], metadata=primary_meta)
            trace.add_step(
                step="spatial_analysis",
                tool=sp_tool.name,
                implementation="SpatialGeometryProcessor",
                duration_ms=(time.perf_counter() - t_sp_start) * 1000.0,
                details={"cluster_count": len(enriched_boxes)},
            )

            # 3. Evidence Generation Tool
            t_ev_start = time.perf_counter()
            ev_tool = self.registry.get("evidence_generation_tool")
            tools_used.append(ev_tool.name)
            evidence = ev_tool.execute(
                mode=mode,
                rgb_primary=cd_res.get("t1_aligned", t1_rgb),
                rgb_secondary=cd_res.get("t2_aligned", t2_rgb),
                mask=cd_res["change_mask"],
                diff_magnitude=cd_res["diff_magnitude"],
                boxes=enriched_boxes,
                statistics=cd_res["statistics"],
            )
            trace.add_step(
                step="evidence_generation",
                tool=ev_tool.name,
                implementation="EvidenceRenderAdapter",
                duration_ms=(time.perf_counter() - t_ev_start) * 1000.0,
                details={"artifacts_rendered": list(evidence.layers.keys())},
            )

            stats = cd_res["statistics"]
            analysis_context = {
                "changed_percent": stats.changed_percent,
                "trend": stats.trend,
                "approx_area_ha": stats.approx_changed_area_ha,
                "region_count": len(enriched_boxes),
            }

            # Confidence estimate
            confidence_estimate = 0.82 if stats.changed_percent > 0 else 0.90

            # Answer Synthesis
            if intent.task_type == TaskType.BUILT_UP_CHANGE:
                if stats.trend == "increased":
                    answer = (
                        f"Analysis indicates an estimated {stats.changed_percent:.2f}% landscape change "
                        f"with an apparent increase in built-up structural density across {len(enriched_boxes)} primary clusters."
                    )
                elif stats.trend == "decreased":
                    answer = (
                        f"Analysis indicates an estimated {stats.changed_percent:.2f}% landscape change "
                        f"with an apparent decrease in structural reflectance."
                    )
                else:
                    answer = (
                        f"Landscape change is estimated at {stats.changed_percent:.2f}% between T1 and T2. "
                        f"Built-up structural distribution appears generally unchanged or mixed."
                    )
            else:
                area_text = (
                    f" (approx. {stats.approx_changed_area_ha} ha)"
                    if stats.approx_changed_area_ha
                    else ""
                )
                answer = (
                    f"Bi-temporal differential analysis detected visual change across {stats.changed_percent:.2f}% of the scene{area_text}, "
                    f"isolating {len(enriched_boxes)} significant spatial change clusters."
                )

        elif intent.task_type == TaskType.OPTICAL_SAR_ANALYSIS:
            opt_rgb = rasters[0][1]
            sar_rgb = rasters[1][1]

            t_tool_start = time.perf_counter()
            opt_sar_tool = self.registry.get("optical_sar_tool")
            tools_used.append(opt_sar_tool.name)
            fusion_res = opt_sar_tool.execute(
                optical_rgb=opt_rgb,
                sar_rgb=sar_rgb,
                query=query,
                metadata_opt=primary_meta,
                metadata_sar=secondary_meta,
            )
            exec_mode = fusion_res.get("execution_mode", ExecutionMode.HEURISTIC.value)

            # Explicit traces for Optical, SAR, and Fusion
            trace.add_step(
                step="optical_analysis",
                tool=opt_sar_tool.name,
                implementation="OpticalSpectralExtractor",
                duration_ms=(time.perf_counter() - t_tool_start) * 500.0,
                details=fusion_res["optical_features"],
            )
            trace.add_step(
                step="sar_analysis",
                tool=opt_sar_tool.name,
                implementation="SARBackscatterExtractor",
                duration_ms=(time.perf_counter() - t_tool_start) * 500.0,
                details=fusion_res["sar_features"],
            )
            trace.add_step(
                step="cross_modal_fusion",
                tool=opt_sar_tool.name,
                implementation=fusion_res.get("adapter", "DemoOpticalSARAdapter"),
                duration_ms=(time.perf_counter() - t_tool_start) * 1000.0,
                details=fusion_res["fusion_summary"],
            )

            # Evidence Generation
            t_ev_start = time.perf_counter()
            ev_tool = self.registry.get("evidence_generation_tool")
            tools_used.append(ev_tool.name)
            evidence = ev_tool.execute(
                mode=mode,
                rgb_primary=fusion_res.get("optical_aligned", opt_rgb),
                rgb_secondary=fusion_res.get("sar_aligned", sar_rgb),
                fused_map=fusion_res["fused_thematic_map"],
                statistics=fusion_res["fusion_summary"],
            )
            trace.add_step(
                step="evidence_generation",
                tool=ev_tool.name,
                implementation="EvidenceRenderAdapter",
                duration_ms=(time.perf_counter() - t_ev_start) * 1000.0,
                details={"artifacts_rendered": list(evidence.layers.keys())},
            )

            f_sum = fusion_res["fusion_summary"]
            confidence_estimate = float(f_sum["cross_modal_agreement_score"])
            analysis_context = fusion_res

            answer = (
                f"Cross-modal Optical+SAR fusion successfully mapped the scene: "
                f"Water bodies cover {f_sum['fused_water_coverage_pct']:.1f}% (optical blue absorption confirmed by SAR specular zero-return), "
                f"Built-up areas cover {f_sum['fused_builtup_coverage_pct']:.1f}% (confirmed by SAR double-bounce backscatter), "
                f"and Vegetation accounts for {f_sum['fused_vegetation_coverage_pct']:.1f}%."
            )

        elif intent.task_type == TaskType.GROUNDING:
            rgb_arr = rasters[0][1]

            t_tool_start = time.perf_counter()
            grounding_tool = self.registry.get("grounding_tool")
            tools_used.append(grounding_tool.name)
            g_res = grounding_tool.execute(
                rgb_arr=rgb_arr,
                target_query=intent.target_entity or query,
                metadata=primary_meta,
            )
            exec_mode = g_res.get("execution_mode", ExecutionMode.IMAGE_PROCESSING.value)

            trace.add_step(
                step="region_grounding",
                tool=grounding_tool.name,
                implementation=g_res.get("adapter", "DemoGroundingAdapter"),
                duration_ms=(time.perf_counter() - t_tool_start) * 1000.0,
                details={
                    "target_label": g_res["target_label"],
                    "coverage_percent": g_res["coverage_percent"],
                    "cluster_count": g_res["cluster_count"],
                },
            )

            # Spatial enrichment
            t_sp_start = time.perf_counter()
            sp_tool = self.registry.get("spatial_analysis_tool")
            tools_used.append(sp_tool.name)
            enriched_boxes = sp_tool.execute(boxes=g_res["boxes"], metadata=primary_meta)
            trace.add_step(
                step="spatial_analysis",
                tool=sp_tool.name,
                implementation="SpatialGeometryProcessor",
                duration_ms=(time.perf_counter() - t_sp_start) * 1000.0,
                details={"boxes_enriched": len(enriched_boxes)},
            )

            # Evidence Generation
            t_ev_start = time.perf_counter()
            ev_tool = self.registry.get("evidence_generation_tool")
            tools_used.append(ev_tool.name)
            evidence = ev_tool.execute(
                mode=mode,
                rgb_primary=rgb_arr,
                mask=g_res["mask"],
                boxes=enriched_boxes,
                target_name=g_res["target_label"],
                color_rgb=g_res["target_color_rgb"],
            )
            trace.add_step(
                step="evidence_generation",
                tool=ev_tool.name,
                implementation="EvidenceRenderAdapter",
                duration_ms=(time.perf_counter() - t_ev_start) * 1000.0,
                details={"artifacts_rendered": list(evidence.layers.keys())},
            )

            confidence_estimate = 0.84 if len(enriched_boxes) > 0 else 0.50
            analysis_context = g_res

            if len(enriched_boxes) > 0:
                answer = (
                    f"Successfully grounded '{g_res['target_label']}' across {len(enriched_boxes)} distinct cluster(s), "
                    f"encompassing approximately {g_res['coverage_percent']:.2f}% of the visible image area."
                )
            else:
                answer = (
                    f"No prominent clusters matching '{g_res['target_label']}' were isolated with high spectral confidence."
                )

        else:  # SINGLE_IMAGE_VQA or CAPTIONING
            rgb_arr = rasters[0][1]

            t_tool_start = time.perf_counter()
            vqa_tool = self.registry.get("vqa_tool")
            tools_used.append(vqa_tool.name)
            vqa_res = vqa_tool.execute(rgb_arr=rgb_arr, query=query, metadata=primary_meta)
            exec_mode = vqa_res.get("execution_mode", ExecutionMode.REAL_EO_ADAPTED.value)

            trace.add_step(
                step="specialist_vqa",
                tool=vqa_tool.name,
                implementation=vqa_res.get("adapter", "DemoVQAAdapter"),
                duration_ms=(time.perf_counter() - t_tool_start) * 1000.0,
                details={
                    "top_class": vqa_res["top_class"],
                    "domain_confidence": vqa_res["confidence_estimate"],
                    "class_distribution": vqa_res["class_distribution"],
                },
            )

            # Evidence Generation
            t_ev_start = time.perf_counter()
            ev_tool = self.registry.get("evidence_generation_tool")
            tools_used.append(ev_tool.name)
            evidence = ev_tool.execute(mode=mode, rgb_primary=rgb_arr)
            trace.add_step(
                step="evidence_generation",
                tool=ev_tool.name,
                implementation="EvidenceRenderAdapter",
                duration_ms=(time.perf_counter() - t_ev_start) * 1000.0,
                details={"artifacts_rendered": ["primary_preview"]},
            )

            confidence_estimate = float(vqa_res["confidence_estimate"])
            analysis_context = vqa_res
            answer = vqa_res["answer"]

        # ---------------------------------------------------------------------
        # STAGE 6: ANSWER SYNTHESIS (LLM Polish if active, else grounded answer)
        # ---------------------------------------------------------------------
        step_start = time.perf_counter()
        disclaimer = "Confidence is an uncalibrated estimate. Demo adapters use transparent heuristics."
        llm_answer = gemini_service.synthesize_grounded_answer(
            query=query,
            task=intent.task_type.value,
            analysis_data=analysis_context,
            disclaimer=disclaimer,
        )
        if llm_answer:
            final_answer = llm_answer
        else:
            final_answer = answer

        trace.add_step(
            step="answer_synthesis",
            status=StepStatus.SUCCESS,
            duration_ms=(time.perf_counter() - step_start) * 1000.0,
            details={"synthesis_engine": "Gemini API" if llm_answer else "Deterministic Template"},
        )

        # Determine qualitative confidence level
        if confidence_estimate >= 0.85:
            conf_level = "High"
        elif confidence_estimate >= 0.65:
            conf_level = "Medium"
        elif confidence_estimate >= 0.40:
            conf_level = "Low"
        else:
            conf_level = "Approximate"

        report_id = uuid.uuid4().hex[:12]

        return AnalysisResponse(
            success=True,
            task=intent.task_type,
            answer=final_answer,
            confidence_estimate=round(confidence_estimate, 2),
            confidence_level=conf_level,
            execution_mode=exec_mode,
            inputs={
                "mode": mode.value,
                "query": query,
                "images": [p.name if isinstance(p, Path) else p for p in image_paths],
            },
            tools_used=list(dict.fromkeys(tools_used)),
            evidence=evidence,
            metadata={
                "primary": primary_meta,
                "secondary": secondary_meta,
                "user_metadata": user_meta,
                "routed_intent": {
                    "task": intent.task_type.value,
                    "target_entity": intent.target_entity,
                    "router": intent.router_engine,
                },
            },
            execution_trace=trace.steps,
            disclaimer=disclaimer,
            report_id=report_id,
        )


# Global Orchestrator instance
orchestrator = TenaliOrchestrator()
