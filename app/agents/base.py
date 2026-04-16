"""Abstract base type for all pipeline agents."""

from abc import ABC, abstractmethod
from typing import Any


class Agent(ABC):
    """Agents read and update a shared mutable `state` dict between pipeline steps."""

    name: str = "agent"

    @abstractmethod
    async def run(self, state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Execute one agent step and return the updated `state`."""
        raise NotImplementedError
