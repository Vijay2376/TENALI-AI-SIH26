"""FastAPI Application Entry Point for TENALI AI."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes import analyze, demo, health, web


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=f"{settings.TAGLINE} ({settings.SIH_ID})",
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Static Directory Mounts
    static_dir = Path(__file__).resolve().parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    (static_dir / "css").mkdir(parents=True, exist_ok=True)
    (static_dir / "js").mkdir(parents=True, exist_ok=True)
    (static_dir / "images").mkdir(parents=True, exist_ok=True)

    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.mount(
        "/evidence",
        StaticFiles(directory=str(settings.EVIDENCE_DIR)),
        name="evidence",
    )
    app.mount(
        "/uploads",
        StaticFiles(directory=str(settings.UPLOAD_DIR)),
        name="uploads",
    )

    # Register Routers
    app.include_router(health.router)
    app.include_router(analyze.router)
    app.include_router(demo.router)
    app.include_router(web.router)

    # Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
                "disclaimer": "An internal execution error occurred in the agentic workflow.",
            },
        )

    return app


app = create_app()
