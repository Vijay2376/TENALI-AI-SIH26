"""Base tool interface definition."""

from abc import ABC, abstractmethod
from typing import Any

from app.adapters.base import BaseAdapter
from app.schemas.requests import InputMode


class BaseTool(ABC):
    """Abstract base class for all specialist remote-sensing tools."""

    def __init__(
        self,
        name: str,
        description: str,
        supported_inputs: list[InputMode],
        adapter: BaseAdapter,
    ):
        self.name = name
        self.description = description
        self.supported_inputs = supported_inputs
        self.adapter = adapter

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the tool with given inputs."""
