"""Base controller for ABM components with dependency injection."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
import logging

logger = logging.getLogger(__name__)


class ABMController(ABC):
    """Base class for agents, pricing, staking, treasury controllers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.dependencies: Dict[Type, Any] = {}
        self.iteration = 0

    def link(self, dependency_type: Type, instance: Any) -> None:
        self.dependencies[dependency_type] = instance
        logger.debug(f"{self.__class__.__name__} linked to {dependency_type.__name__}")

    def get_dependency(self, dependency_type: Type) -> Any:
        if dependency_type not in self.dependencies:
            raise KeyError(
                f"{self.__class__.__name__} requires {dependency_type.__name__} "
                f"but it was not linked. Call link() first."
            )
        return self.dependencies[dependency_type]

    def reset(self) -> None:
        """Reset state for Monte Carlo trials."""
        self.iteration = 0

    @abstractmethod
    async def execute(self) -> Any:
        """Execute one timestep."""
        pass

    def snapshot_state(self) -> Dict[str, Any]:
        return {"iteration": self.iteration, "config": self.config}

    def restore_state(self, state: Dict[str, Any]) -> None:
        self.iteration = state.get("iteration", 0)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(iteration={self.iteration})"
