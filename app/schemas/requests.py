"""Request schemas for TENALI AI."""

from enum import Enum

from pydantic import BaseModel, Field


class InputMode(str, Enum):
    """Input configuration modes."""

    SINGLE = "single"
    BI_TEMPORAL = "bi_temporal"
    OPTICAL_SAR = "optical_sar"


class ModalityType(str, Enum):
    """Sensor modalities."""

    OPTICAL = "optical"
    MULTISPECTRAL = "multispectral"
    SAR = "sar"
    HYPERSPECTRAL = "hyperspectral"
    UNKNOWN = "unknown"


class AnalysisForm(BaseModel):
    """Payload for analysis validation."""

    query: str = Field(..., min_length=2, description="Natural-language question")
    mode: InputMode = Field(default=InputMode.SINGLE, description="Input mode")
    t1_date: str | None = Field(default=None, description="Optional T1 date/label")
    t2_date: str | None = Field(default=None, description="Optional T2 date/label")
    modality: ModalityType = Field(default=ModalityType.UNKNOWN)
