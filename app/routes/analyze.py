"""Main analysis routes for multimodal remote sensing queries."""

import shutil
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.templating import Jinja2Templates

from app.agent.agent import orchestrator
from app.config import settings
from app.schemas.requests import InputMode
from app.schemas.responses import AnalysisResponse
from app.services.reports import report_service

router = APIRouter(tags=["Analysis"])

templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


def _save_uploaded_file(upload: UploadFile) -> Path:
    """Validate and persist uploaded image with sanitized filename."""
    if not upload.filename:
        raise HTTPException(status_code=400, detail="Uploaded file missing filename.")

    suffix = Path(upload.filename).suffix.lower()
    if suffix not in settings.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{suffix}'. Allowed: {', '.join(settings.SUPPORTED_EXTENSIONS)}",
        )

    safe_name = f"up_{uuid.uuid4().hex[:8]}_{Path(upload.filename).stem[:24]}{suffix}"
    out_path = settings.UPLOAD_DIR / safe_name

    with open(out_path, "wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    return out_path


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_remote_sensing_query(
    request: Request,
    query: Annotated[str, Form()],
    mode: Annotated[str, Form()],
    images: Annotated[list[UploadFile] | None, File()] = None,
    t1: Annotated[UploadFile | None, File()] = None,
    t2: Annotated[UploadFile | None, File()] = None,
    optical: Annotated[UploadFile | None, File()] = None,
    sar: Annotated[UploadFile | None, File()] = None,
    t1_date: Annotated[str | None, Form()] = None,
    t2_date: Annotated[str | None, Form()] = None,
):
    """Primary analysis endpoint for multimodal natural language remote sensing queries."""
    try:
        input_mode = InputMode(mode)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode '{mode}'. Supported modes: single, bi_temporal, optical_sar",
        ) from None

    saved_paths: list[Path] = []

    # Collect files according to selected mode
    upload_list: list[UploadFile] = []
    if input_mode == InputMode.SINGLE:
        if images:
            for f in images:
                if f.filename:
                    upload_list.append(f)
        if not upload_list and t1 and t1.filename:
            upload_list.append(t1)
        if not upload_list and optical and optical.filename:
            upload_list.append(optical)

    elif input_mode == InputMode.BI_TEMPORAL:
        if t1 and t1.filename:
            upload_list.append(t1)
        if t2 and t2.filename:
            upload_list.append(t2)
        if len(upload_list) < 2 and images:
            for f in images:
                if f.filename and f not in upload_list:
                    upload_list.append(f)

    elif input_mode == InputMode.OPTICAL_SAR:
        if optical and optical.filename:
            upload_list.append(optical)
        if sar and sar.filename:
            upload_list.append(sar)
        if len(upload_list) < 2 and images:
            for f in images:
                if f.filename and f not in upload_list:
                    upload_list.append(f)

    if not upload_list:
        error_msg = f"No images uploaded. '{input_mode.value}' mode requires valid satellite image files."
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                request=request,
                name="partials/error_card.html",
                context={"error_message": error_msg},
                status_code=400,
            )
        raise HTTPException(status_code=400, detail=error_msg)

    if input_mode == InputMode.BI_TEMPORAL and len(upload_list) != 2:
        error_msg = f"Bi-Temporal Change analysis requires exactly 2 corresponding images (T1 and T2), but received {len(upload_list)}."
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                request=request,
                name="partials/error_card.html",
                context={"error_message": error_msg},
                status_code=400,
            )
        raise HTTPException(status_code=400, detail=error_msg)

    if input_mode == InputMode.OPTICAL_SAR and len(upload_list) != 2:
        error_msg = f"Optical + SAR analysis requires exactly 2 co-registered images (Optical and SAR), but received {len(upload_list)}."
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                request=request,
                name="partials/error_card.html",
                context={"error_message": error_msg},
                status_code=400,
            )
        raise HTTPException(status_code=400, detail=error_msg)

    # Save and validate files
    try:
        for f in upload_list:
            saved_paths.append(_save_uploaded_file(f))
    except HTTPException as e:
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                request=request,
                name="partials/error_card.html",
                context={"error_message": e.detail},
                status_code=e.status_code,
            )
        raise

    # Execute agentic pipeline
    try:
        response = orchestrator.analyze(
            query=query,
            mode=input_mode,
            image_paths=saved_paths,
            user_metadata={"t1_date": t1_date, "t2_date": t2_date},
        )
        # Persist report
        report_service.save_report(response)

    except ValueError as val_err:
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                request=request,
                name="partials/error_card.html",
                context={"error_message": str(val_err)},
                status_code=400,
            )
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:  # noqa: BLE001
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                request=request,
                name="partials/error_card.html",
                context={
                    "error_message": f"Analysis execution failed: {exc!s}",
                },
                status_code=500,
            )
        raise HTTPException(status_code=500, detail=f"Internal processing failure: {exc!s}")

    # Return HTML partial if request originated from HTMX frontend
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request,
            name="partials/result_card.html",
            context={
                "result": response,
            },
        )

    return response
