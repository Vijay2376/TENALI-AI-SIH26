"""Specialist Tool Registry for TENALI AI."""

from typing import Any

from app.schemas.requests import InputMode
from app.tools.base import BaseTool
from app.tools.captioning import CaptioningTool
from app.tools.change_detection import ChangeDetectionTool
from app.tools.change_statistics import ChangeStatisticsTool
from app.tools.evidence import EvidenceGenerationTool
from app.tools.grounding import GroundingTool
from app.tools.optical_sar import OpticalSARFusionTool
from app.tools.spatial_analysis import SpatialAnalysisTool
from app.tools.vqa import VQATool


class ToolRegistry:
    """Central registry of specialist remote sensing tools."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Initialize and register default tools."""
        self.register(VQATool())
        self.register(GroundingTool())
        self.register(CaptioningTool())
        self.register(ChangeDetectionTool())
        self.register(ChangeStatisticsTool())
        self.register(OpticalSARFusionTool())
        self.register(SpatialAnalysisTool())
        self.register(EvidenceGenerationTool())

    def register(self, tool: BaseTool):
        """Register a specialist tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        """Retrieve tool by name."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered in ToolRegistry.")
        return self._tools[name]

    def list_tools(self) -> list[dict[str, Any]]:
        """List all registered tools and metadata."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "supported_inputs": [m.value for m in t.supported_inputs],
                "adapter": t.adapter.name,
                "execution_mode": t.adapter.execution_mode,
            }
            for t in self._tools.values()
        ]

    def get_tools_for_mode(self, mode: InputMode) -> list[BaseTool]:
        """Filter tools supported for a given input configuration."""
        return [t for t in self._tools.values() if mode in t.supported_inputs]


# Global Tool Registry Singleton
tool_registry = ToolRegistry()
