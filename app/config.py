"""Configuration management for TENALI AI."""

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file from project root if it exists
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    PROJECT_NAME: str = "TENALI AI"
    TAGLINE: str = "Ask the Earth. Understand the Change."
    SIH_ID: str = "SIH 26167"
    THEME: str = "Space Technology"
    VERSION: str = "1.0.0"

    HOST: str = "127.0.0.1"
    PORT: int = 8080
    DEBUG: bool = True

    # Mode controls
    TENALI_DEMO_MODE: bool = Field(
        default=True,
        description="When true, use deterministic demo adapters and local rule-based routing when AI keys are absent",
    )

    # Google Gemini API
    GEMINI_API_KEY: str | None = Field(
        default=None,
        description="Google Gemini API key for natural language reasoning",
    )
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Storage paths
    UPLOAD_DIR: Path = BASE_DIR / "generated" / "uploads"
    EVIDENCE_DIR: Path = BASE_DIR / "generated" / "evidence"
    REPORTS_DIR: Path = BASE_DIR / "generated" / "reports"
    DEMO_DATA_DIR: Path = BASE_DIR / "demo_data"

    # File constraints
    MAX_UPLOAD_SIZE_MB: int = 50
    SUPPORTED_EXTENSIONS: list[str] = [".tif", ".tiff", ".png", ".jpg", ".jpeg"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

# Ensure required runtime directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
settings.DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)
