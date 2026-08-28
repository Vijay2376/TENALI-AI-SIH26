"""TENALI AI - Interactive Vision-Language Assistant Entry Point.

Usage:
    python run.py
"""

import uvicorn

from app.config import settings


def print_banner():
    """Print startup banner and configuration info."""
    banner = f"""
================================================================================
  TENALI AI: Multimodal Remote Sensing Vision-Language Assistant
  "Ask the Earth. Understand the Change."
  Smart India Hackathon 2026 (SIH 26167) - Space Technology
================================================================================
  [+] Python-First Stack: FastAPI + Jinja2 + HTMX + Tailwind + Python
  [+] Domain Adaptation: BigEarthNet-19 Multi-Spectral Classifier Active
  [+] Specialist Tools: VQA, Grounding, Change Detection, Optical-SAR, GIS
  [+] Execution Mode: {"DEMO MODE (Deterministic Adapters)" if settings.TENALI_DEMO_MODE else "PRODUCTION AI"}
  [+] Server URL: http://{settings.HOST}:{settings.PORT}
================================================================================
"""
    print(banner)


def main():
    """Start the Uvicorn web server."""
    print_banner()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )


if __name__ == "__main__":
    main()
