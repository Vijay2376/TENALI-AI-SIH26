"""Demo presets and synthetic scenario endpoints."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.templating import Jinja2Templates

from app.agent.agent import orchestrator
from app.config import settings
from app.schemas.requests import InputMode
from app.services.reports import report_service

router = APIRouter(prefix="/demo", tags=["Demo"])

templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


DEMO_PRESETS = [
    {
        "id": "demo1_vqa",
        "title": "Demo 1: Single Image VQA",
        "mode": "single",
        "query": "Describe the land-cover and major objects visible in this image.",
        "files": ["single/reservoir_water.tif"],
        "description": "Domain-adapted land-cover classification and spectral scene metrics via BigEarthNet-19 taxonomy.",
    },
    {
        "id": "demo2_grounding",
        "title": "Demo 2: Text-Guided Region Grounding",
        "mode": "single",
        "query": "Highlight the water body.",
        "files": ["single/reservoir_water.tif"],
        "description": "Spectral index thresholding and morphological contour extraction with bounding boxes.",
    },
    {
        "id": "demo3_change",
        "title": "Demo 3: Bi-Temporal Change Detection",
        "mode": "bi_temporal",
        "query": "What changed between these two dates?",
        "files": ["bi_temporal/expansion_t1.tif", "bi_temporal/expansion_t2.tif"],
        "description": "Differential multi-band analysis, adaptive thresholding, and change heatmap generation.",
    },
    {
        "id": "demo4_builtup",
        "title": "Demo 4: Built-up Structural Change",
        "mode": "bi_temporal",
        "query": "Has the built-up area increased, decreased, or remained unchanged?",
        "files": ["bi_temporal/expansion_t1.tif", "bi_temporal/expansion_t2.tif"],
        "description": "Multi-temporal texture gradient and reflectance trend inference.",
    },
    {
        "id": "demo5_optical_sar",
        "title": "Demo 5: Optical + SAR Fusion",
        "mode": "optical_sar",
        "query": "Use the optical and SAR images together to identify built-up and water-covered regions.",
        "files": ["optical_sar/harbor_optical.tif", "optical_sar/harbor_sar.tif"],
        "description": "Dual-stream feature extraction combining optical spectral albedo with radar backscatter.",
    },
]


@router.get("/presets")
def list_presets():
    """List all available pre-packaged remote-sensing demo presets."""
    return {"presets": DEMO_PRESETS}


@router.post("/run-preset")
async def run_demo_preset(
    request: Request,
    preset_id: Annotated[str, Form()],
):
    """Execute a pre-configured demo preset using generated sample rasters."""
    matched = next((p for p in DEMO_PRESETS if p["id"] == preset_id), None)
    if not matched:
        raise HTTPException(status_code=404, detail=f"Demo preset '{preset_id}' not found.")

    # Resolve file paths
    image_paths = [settings.DEMO_DATA_DIR / f for f in matched["files"]]
    for p in image_paths:
        if not p.exists():
            # Regenerate if missing
            from demo_data.generator import create_demo_datasets
            create_demo_datasets(settings.DEMO_DATA_DIR)
            break

    try:
        response = orchestrator.analyze(
            query=str(matched["query"]),
            mode=InputMode(str(matched["mode"])),
            image_paths=image_paths,
            user_metadata={"preset_id": preset_id, "preset_title": matched["title"]},
        )
        report_service.save_report(response)

    except Exception as exc:  # noqa: BLE001
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                request=request,
                name="partials/error_card.html",
                context={
                    "error_message": f"Preset execution error: {exc!s}",
                },
                status_code=500,
            )
        raise HTTPException(status_code=500, detail=str(exc))

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request,
            name="partials/result_card.html",
            context={
                "result": response,
            },
        )

    return response
