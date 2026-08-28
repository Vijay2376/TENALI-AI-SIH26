"""End-to-End tests for all 5 mandatory SIH demonstration scenarios."""

from app.agent.agent import orchestrator
from app.schemas.requests import InputMode


def test_demo_1_single_image_vqa(test_rasters):
    """DEMO 1: Single image VQA pipeline."""
    res = orchestrator.analyze(
        query="Describe the land-cover and major objects visible in this image.",
        mode=InputMode.SINGLE,
        image_paths=[test_rasters["single"]],
    )
    assert res.success is True
    assert res.task == "single_image_vqa"
    assert "answer" in res.model_dump()
    assert 0.0 <= res.confidence_estimate <= 1.0
    assert any(s.step == "specialist_vqa" for s in res.execution_trace)


def test_demo_2_text_guided_grounding(test_rasters):
    """DEMO 2: Text-guided region grounding."""
    res = orchestrator.analyze(
        query="Highlight the water body.",
        mode=InputMode.SINGLE,
        image_paths=[test_rasters["single"]],
    )
    assert res.success is True
    assert res.task == "grounding"
    assert res.evidence.annotated_image_url is not None
    assert any(s.step == "region_grounding" for s in res.execution_trace)


def test_demo_3_bitemporal_change(test_rasters):
    """DEMO 3: Bi-temporal change detection."""
    res = orchestrator.analyze(
        query="What changed between these two dates?",
        mode=InputMode.BI_TEMPORAL,
        image_paths=[test_rasters["t1"], test_rasters["t2"]],
    )
    assert res.success is True
    assert res.task == "bi_temporal_change"
    assert res.evidence.change_map_url is not None
    assert res.evidence.statistics is not None
    assert any(s.step == "change_detection" for s in res.execution_trace)


def test_demo_4_builtup_change(test_rasters):
    """DEMO 4: Built-up change trend inference."""
    res = orchestrator.analyze(
        query="Has the built-up area increased, decreased, or remained unchanged?",
        mode=InputMode.BI_TEMPORAL,
        image_paths=[test_rasters["t1"], test_rasters["t2"]],
    )
    assert res.success is True
    assert res.task == "built_up_change"
    assert res.evidence.statistics is not None
    assert any(s.step == "change_detection" for s in res.execution_trace)


def test_demo_5_optical_sar_fusion(test_rasters):
    """DEMO 5: Optical + SAR cross-modal fusion."""
    res = orchestrator.analyze(
        query="Use the optical and SAR images together to identify built-up and water-covered regions.",
        mode=InputMode.OPTICAL_SAR,
        image_paths=[test_rasters["optical"], test_rasters["sar"]],
    )
    assert res.success is True
    assert res.task == "optical_sar_analysis"
    assert res.evidence.fused_url is not None
    assert any(s.step == "optical_analysis" for s in res.execution_trace)
    assert any(s.step == "sar_analysis" for s in res.execution_trace)
    assert any(s.step == "cross_modal_fusion" for s in res.execution_trace)
