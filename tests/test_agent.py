"""Tests for agent routing, task planning, and domain adaptation classification."""

import numpy as np

from app.agent.planner import planner
from app.agent.registry import tool_registry
from app.agent.router import router
from app.schemas.requests import InputMode
from app.schemas.trace import TaskType
from app.services.adaptation import BIGEARTHNET_19_CLASSES, adaptation_service


def test_intent_routing_single_image():
    """Test deterministic routing for single image VQA and grounding queries."""
    # VQA
    res_vqa = router.route("What land-cover is visible in this scene?", InputMode.SINGLE)
    assert res_vqa.task_type == TaskType.SINGLE_IMAGE_VQA

    # Grounding
    res_ground = router.route("Highlight the water body.", InputMode.SINGLE)
    assert res_ground.task_type == TaskType.GROUNDING
    assert res_ground.target_entity is not None and "water" in res_ground.target_entity.lower()


def test_intent_routing_bitemporal():
    """Test routing for bi-temporal and built-up change queries."""
    res_change = router.route("What changed between these two dates?", InputMode.BI_TEMPORAL)
    assert res_change.task_type == TaskType.BI_TEMPORAL_CHANGE

    res_builtup = router.route("Has the built-up area increased, decreased, or remained unchanged?", InputMode.BI_TEMPORAL)
    assert res_builtup.task_type == TaskType.BUILT_UP_CHANGE


def test_intent_routing_optical_sar():
    """Test routing for optical + SAR cross-modal queries."""
    res_optsar = router.route("Use optical and SAR together to identify water bodies.", InputMode.OPTICAL_SAR)
    assert res_optsar.task_type == TaskType.OPTICAL_SAR_ANALYSIS


def test_tool_registry():
    """Test tool registry registration and lookup."""
    tools = tool_registry.list_tools()
    assert len(tools) >= 7
    vqa_tool = tool_registry.get("vqa_tool")
    assert vqa_tool is not None
    assert vqa_tool.name == "vqa_tool"


def test_domain_adaptation_service():
    """Test the BigEarthNet domain adapted classification model."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:, :, 1] = 170  # Green dominant
    pred = adaptation_service.predict_landcover(img)
    assert pred.top_class in BIGEARTHNET_19_CLASSES
    assert 0.0 <= pred.confidence_estimate <= 1.0
    assert len(pred.class_distribution) > 0


def test_task_planner():
    """Test task execution planning for different intents."""
    intent_vqa = router.route("What land-cover is visible in this scene?", InputMode.SINGLE)
    plan_vqa = planner.create_plan(intent_vqa)
    assert len(plan_vqa) >= 3
    assert any(step.step_name == "specialist_vqa" for step in plan_vqa)

    intent_change = router.route("What changed between these two dates?", InputMode.BI_TEMPORAL)
    plan_change = planner.create_plan(intent_change)
    assert any(step.step_name == "change_detection" for step in plan_change)
    assert any(step.step_name == "change_statistics" for step in plan_change)
