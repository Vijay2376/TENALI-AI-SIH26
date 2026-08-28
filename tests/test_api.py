"""Tests for FastAPI HTTP endpoints, error handling, and demo presets."""

def test_health_endpoint(client):
    """Test /health status and telemetry."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "TENALI AI"
    assert "adaptation_model" in data


def test_capabilities_endpoint(client):
    """Test /capabilities taxonomy and tool discovery."""
    res = client.get("/capabilities")
    assert res.status_code == 200
    data = res.json()
    assert "supported_input_modes" in data
    assert "registered_tools" in data
    assert len(data["registered_tools"]) >= 7


def test_demo_presets_endpoint(client):
    """Test listing and running built-in demo presets."""
    res = client.get("/demo/presets")
    assert res.status_code == 200
    presets = res.json()["presets"]
    assert len(presets) == 5

    # Run preset 1
    run_res = client.post("/demo/run-preset", data={"preset_id": "demo1_vqa"})
    assert run_res.status_code == 200
    data = run_res.json()
    assert data["success"] is True
    assert data["task"] == "single_image_vqa"
    assert "answer" in data
    assert len(data["execution_trace"]) > 0


def test_invalid_mode_error_handling(client, test_rasters):
    """Test validation failure for invalid mode."""
    with open(test_rasters["single"], "rb") as f:
        res = client.post(
            "/analyze",
            data={"query": "Test query", "mode": "invalid_mode_xyz"},
            files=[("images", ("test.tif", f, "image/tiff"))],
        )
    assert res.status_code == 400


def test_mismatched_image_count_error_handling(client, test_rasters):
    """Test validation failure when bi-temporal mode is sent only 1 image."""
    with open(test_rasters["single"], "rb") as f:
        res = client.post(
            "/analyze",
            data={"query": "What changed?", "mode": "bi_temporal"},
            files=[("images", ("test.tif", f, "image/tiff"))],
        )
    assert res.status_code == 400
    assert "requires exactly 2 corresponding images" in res.text


def test_analyze_htmx_bitemporal_render(client, test_rasters):
    """Test HTMX /analyze returns HTML result card with layer tabs and no split slider."""
    with open(test_rasters["t1"], "rb") as f1, open(test_rasters["t2"], "rb") as f2:
        res = client.post(
            "/analyze",
            data={"query": "What changed between these dates?", "mode": "bi_temporal"},
            files=[
                ("t1", ("t1.tif", f1, "image/tiff")),
                ("t2", ("t2.tif", f2, "image/tiff")),
            ],
            headers={"HX-Request": "true"},
        )
    assert res.status_code == 200
    html = res.text
    assert "Multi-Layer Visual Evidence" in html
    assert "layer-tab-btn" in html
    assert "Change Heatmap" in html
    assert "Focused View" in html
    assert "Multi-Layer Grid" in html
    # Ensure obsolete swipe slider is gone
    assert "split-viewer-slider" not in html
    assert "split-viewer-handle" not in html


def test_analyze_htmx_grounding_render(client, test_rasters):
    """Test HTMX /analyze returns Grounded Annotations tab and mask."""
    with open(test_rasters["single"], "rb") as f:
        res = client.post(
            "/analyze",
            data={"query": "Highlight the water body", "mode": "single"},
            files=[("images", ("single.tif", f, "image/tiff"))],
            headers={"HX-Request": "true"},
        )
    assert res.status_code == 200
    html = res.text
    assert "Grounded Annotations" in html
    assert "Original Image" in html


def test_analyze_htmx_optical_sar_render(client, test_rasters):
    """Test HTMX /analyze returns Fused Thematic Map and sensor tabs."""
    with open(test_rasters["optical"], "rb") as f1, open(test_rasters["sar"], "rb") as f2:
        res = client.post(
            "/analyze",
            data={
                "query": "Use the optical and SAR images together to identify built-up and water-covered regions.",
                "mode": "optical_sar",
            },
            files=[
                ("optical", ("optical.tif", f1, "image/tiff")),
                ("sar", ("sar.tif", f2, "image/tiff")),
            ],
            headers={"HX-Request": "true"},
        )
    assert res.status_code == 200
    html = res.text
    assert "Fused Thematic Map" in html
    assert "Cross-Modal Collage" in html

