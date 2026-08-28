"""Web UI dashboard and report viewing routes."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.routes.demo import DEMO_PRESETS
from app.services.reports import report_service

router = APIRouter(tags=["Web UI"])

templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/", response_class=HTMLResponse)
def index_dashboard(request: Request):
    """Serve the TENALI AI main Earth Observation intelligence console."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "tagline": settings.TAGLINE,
            "sih_id": settings.SIH_ID,
            "demo_mode": settings.TENALI_DEMO_MODE,
            "presets": DEMO_PRESETS,
        },
    )


@router.get("/reports/{report_id}", response_class=HTMLResponse)
def view_html_report(request: Request, report_id: str):
    """View standalone printable HTML analysis report."""
    data = report_service.get_report(report_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis report not found.")

    from app.schemas.responses import AnalysisResponse
    resp = AnalysisResponse(**data)
    html_content = report_service.generate_html_report(resp)
    return HTMLResponse(content=html_content)


@router.get("/reports/{report_id}/json", response_class=JSONResponse)
def view_json_report(report_id: str):
    """Download analysis report data in JSON format."""
    data = report_service.get_report(report_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis report not found.")
    return data
