"""Unit tests for specialist remote-sensing tools and adapters."""

import numpy as np

from app.schemas.requests import InputMode
from app.schemas.responses import RegionBox
from app.tools.captioning import CaptioningTool
from app.tools.change_detection import ChangeDetectionTool
from app.tools.change_statistics import ChangeStatisticsTool
from app.tools.evidence import EvidenceGenerationTool
from app.tools.grounding import GroundingTool
from app.tools.optical_sar import OpticalSARFusionTool
from app.tools.spatial_analysis import SpatialAnalysisTool
from app.tools.vqa import VQATool


def test_vqa_tool():
    """Test VQA tool execution."""
    tool = VQATool()
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    res = tool.execute(rgb_arr=img, query="Describe land cover")
    assert "answer" in res
    assert "confidence_estimate" in res
    assert res["confidence_estimate"] > 0.0


def test_grounding_tool():
    """Test Grounding tool mask and box extraction."""
    tool = GroundingTool()
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[20:60, 20:60, 2] = 200  # Blue water patch
    res = tool.execute(rgb_arr=img, target_query="Highlight the water body")
    assert "mask" in res
    assert "boxes" in res
    assert res["target_label"] == "Water Body"


def test_change_detection_tool():
    """Test bi-temporal differential change detection."""
    tool = ChangeDetectionTool()
    t1 = np.zeros((100, 100, 3), dtype=np.uint8)
    t2 = np.zeros((100, 100, 3), dtype=np.uint8)
    t2[30:70, 30:70, :] = 255  # Changed patch

    res = tool.execute(t1_rgb=t1, t2_rgb=t2, query="What changed?")
    assert "change_mask" in res
    assert "statistics" in res
    assert res["statistics"].changed_pixels > 0
    assert res["statistics"].changed_percent > 0.0


def test_optical_sar_tool():
    """Test dual-stream optical + SAR cross-modal tool."""
    tool = OpticalSARFusionTool()
    opt = np.zeros((100, 100, 3), dtype=np.uint8)
    sar = np.zeros((100, 100, 3), dtype=np.uint8)
    res = tool.execute(optical_rgb=opt, sar_rgb=sar, query="Fuse optical and SAR")
    assert res["optical_processed"] is True
    assert res["sar_processed"] is True
    assert "fused_thematic_map" in res
    assert "fusion_summary" in res


def test_spatial_analysis_tool():
    """Test spatial coordinate enrichment of bounding boxes."""
    tool = SpatialAnalysisTool()
    box = RegionBox(box_id=1, label="Water Body", xmin=100, ymin=100, xmax=200, ymax=200, confidence_estimate=0.9)
    metadata = {
        "bounds": [77.5, 12.8, 77.7, 13.0],
        "width": 1000,
        "height": 1000,
    }
    enriched = tool.execute(boxes=[box], metadata=metadata)
    assert len(enriched) == 1
    assert enriched[0].approx_geo_coords is not None
    assert "min_lon" in enriched[0].approx_geo_coords
    assert "min_lat" in enriched[0].approx_geo_coords


def test_captioning_tool():
    """Test scene captioning tool."""
    tool = CaptioningTool()
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    res = tool.execute(rgb_arr=img, query="Provide scene overview")
    assert "answer" in res
    assert "confidence_estimate" in res


def test_change_statistics_tool():
    """Test quantitative change statistics tool."""
    tool = ChangeStatisticsTool()
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[10:30, 10:30] = 1  # 400 pixels changed
    metadata = {"resolution": [10.0, 10.0]}
    stats = tool.execute(change_mask=mask, total_pixels=10000, metadata=metadata, trend="increased")
    assert stats.changed_pixels == 400
    assert stats.changed_percent == 4.0
    assert stats.trend == "increased"
    assert stats.approx_changed_area_ha is not None


def test_evidence_generation_tool():
    """Test multi-layer visual evidence tool."""
    tool = EvidenceGenerationTool()
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    mask = np.zeros((100, 100), dtype=np.uint8)
    evidence = tool.execute(
        mode=InputMode.SINGLE,
        rgb_primary=img,
        mask=mask,
        target_name="Test Region",
    )
    assert evidence.annotated_image_url is not None
    assert evidence.mask_image_url is not None
    assert "mask" in evidence.layers

