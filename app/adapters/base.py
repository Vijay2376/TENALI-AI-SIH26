"""Base adapter contract for model and algorithmic backends."""

from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    """Abstract base class for all specialist model adapters."""

    def __init__(self, name: str, execution_mode: str):
        self.name = name
        self.execution_mode = execution_mode

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the adapter logic and return structured results."""
