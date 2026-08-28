"""Health check and capabilities discovery endpoints."""

from fastapi import APIRouter

from app.agent.registry import tool_registry
from app.config import settings
from app.schemas.trace import ExecutionMode, TaskType
from app.services.adaptation import BIGEARTHNET_19_CLASSES
from app.services.gemini import gemini_service

router = APIRouter(tags=["System"])


@router.get("/health")
def get_health():
    """System health check and engine readiness telemetry."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "sih_id": settings.SIH_ID,
        "version": settings.VERSION,
        "demo_mode": settings.TENALI_DEMO_MODE,
        "gemini_connected": gemini_service.is_available(),
        "adaptation_model": "BigEarthNet-19 Domain Classifier (Sentinel-2 / CORINE adapted)",
        "tool_count": len(tool_registry.list_tools()),
    }


@router.get("/capabilities")
def get_capabilities():
    """Discover supported modalities, task types, specialist tools, and taxonomy."""
    return {
        "supported_input_modes": ["single", "bi_temporal", "optical_sar"],
        "supported_formats": settings.SUPPORTED_EXTENSIONS,
        "task_types": [t.value for t in TaskType],
        "execution_modes": [m.value for m in ExecutionMode],
        "registered_tools": tool_registry.list_tools(),
        "domain_adaptation": {
            "taxonomy": "BigEarthNet-19 Nomenclature",
            "class_count": len(BIGEARTHNET_19_CLASSES),
            "classes": BIGEARTHNET_19_CLASSES,
        },
    }
