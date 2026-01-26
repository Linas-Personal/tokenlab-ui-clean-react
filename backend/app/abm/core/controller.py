"""
ABM Controller Base Class.

Inspired by TokenLab's controller pattern where all components inherit from
a base controller with execute(), link(), and reset() methods.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
import logging

logger = logging.getLogger(__name__)


class ABMController(ABC):
    """
    Base class for all ABM components.

    All controllers (agents, pricing, staking, treasury, etc.) inherit from this
    and implement the execute() method for their specific behavior.

    The controller pattern enables:
    1. Dependency injection via link()
    2. State management via reset()
    3. Iteration-based execution
    4. Async-first design
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize controller.

        Args:
            config: Configuration dictionary specific to this controller
        """
        self.config = config or {}
        self.dependencies: Dict[Type, Any] = {}
        self.iteration: int = 0

    def link(self, dependency_type: Type, instance: Any) -> None:
        """
        Link a dependency to this controller.

        Example:
            agent.link(TokenEconomy, token_economy_instance)

        Args:
            dependency_type: The type/class of the dependency
            instance: The actual instance to inject
        """
        self.dependencies[dependency_type] = instance
        logger.debug(f"{self.__class__.__name__} linked to {dependency_type.__name__}")

    def get_dependency(self, dependency_type: Type) -> Any:
        """
        Get a linked dependency.

        Args:
            dependency_type: The type of dependency to retrieve

        Returns:
            The linked instance

        Raises:
            KeyError: If dependency not linked
        """
        if dependency_type not in self.dependencies:
            raise KeyError(
                f"{self.__class__.__name__} requires {dependency_type.__name__} "
                f"but it was not linked. Call link() first."
            )
        return self.dependencies[dependency_type]

    def reset(self) -> None:
        """
        Reset controller state to initial conditions.

        Used for Monte Carlo simulations where the same controller
        is reused across multiple trials.
        """
        self.iteration = 0

    @abstractmethod
    async def execute(self) -> Any:
        """
        Execute one iteration of this controller's logic.

        This is called once per simulation timestep (typically monthly).
        All controllers must implement this method.

        Returns:
            Result of execution (type varies by controller)
        """
        pass

    def snapshot_state(self) -> Dict[str, Any]:
        """
        Capture current state for persistence/resumption.

        Override this method to include controller-specific state.

        Returns:
            Dictionary containing serializable state
        """
        return {
            "iteration": self.iteration,
            "config": self.config
        }

    def restore_state(self, state: Dict[str, Any]) -> None:
        """
        Restore state from snapshot.

        Override this method to restore controller-specific state.

        Args:
            state: State dictionary from snapshot_state()
        """
        self.iteration = state.get("iteration", 0)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(iteration={self.iteration})"
