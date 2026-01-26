"""
Adaptive Agent Scaling Strategies.

Enables efficient simulation of 1K to 100K+ token holders by intelligently
choosing between different agent creation strategies based on scale.
"""
from enum import Enum
from typing import Dict, List, Tuple
import logging

from app.abm.agents.cohort import AgentCohort
from app.abm.agents.token_holder import TokenHolderAgent

logger = logging.getLogger(__name__)


class ScalingStrategy(str, Enum):
    """Available scaling strategies."""
    FULL_INDIVIDUAL = "full_individual"  # 1:1 mapping (< 1K holders)
    REPRESENTATIVE_SAMPLING = "representative_sampling"  # Sample subset (1K-10K)
    META_AGENTS = "meta_agents"  # Each agent represents many (> 10K)


class AdaptiveAgentScaling:
    """
    Adaptive agent scaling system.

    Automatically chooses the best strategy based on total holder count:
    - < 1,000: Create individual agent for each holder
    - 1,000 - 10,000: Sample representative subset
    - > 10,000: Use meta-agents (each represents many holders)

    Performance targets:
    - 1K agents: ~0.05s per iteration
    - 10K agents: ~0.5s per iteration (via representative sampling)
    - 100K agents: ~0.5s per iteration (via meta-agents)
    """

    # Strategy thresholds
    FULL_INDIVIDUAL_THRESHOLD = 1000
    REPRESENTATIVE_SAMPLING_THRESHOLD = 10000

    # Configuration
    REPRESENTATIVE_SAMPLE_SIZE = 1000  # Sample size for representative sampling
    META_AGENTS_PER_COHORT = 50  # Number of meta-agents per cohort

    def __init__(self, strategy: ScalingStrategy = None):
        """
        Initialize adaptive scaling.

        Args:
            strategy: Force specific strategy (None = auto-detect)
        """
        self.forced_strategy = strategy

    def determine_strategy(self, total_holders: int) -> ScalingStrategy:
        """
        Determine optimal scaling strategy based on total holders.

        Args:
            total_holders: Total number of token holders

        Returns:
            Recommended scaling strategy
        """
        if self.forced_strategy:
            return self.forced_strategy

        if total_holders <= self.FULL_INDIVIDUAL_THRESHOLD:
            return ScalingStrategy.FULL_INDIVIDUAL

        elif total_holders <= self.REPRESENTATIVE_SAMPLING_THRESHOLD:
            return ScalingStrategy.REPRESENTATIVE_SAMPLING

        else:
            return ScalingStrategy.META_AGENTS

    def calculate_agent_counts(
        self,
        cohort_holder_counts: Dict[str, int],
        strategy: ScalingStrategy = None
    ) -> Dict[str, Tuple[int, float]]:
        """
        Calculate how many agents to create for each cohort.

        Args:
            cohort_holder_counts: Dict mapping cohort name to number of holders
            strategy: Optional strategy override

        Returns:
            Dict mapping cohort name to (num_agents, scaling_weight) tuple
        """
        total_holders = sum(cohort_holder_counts.values())

        if strategy is None:
            strategy = self.determine_strategy(total_holders)

        logger.info(
            f"Scaling strategy: {strategy} for {total_holders:,} total holders"
        )

        result = {}

        if strategy == ScalingStrategy.FULL_INDIVIDUAL:
            # 1:1 mapping - create agent for each holder
            for cohort, count in cohort_holder_counts.items():
                result[cohort] = (count, 1.0)

        elif strategy == ScalingStrategy.REPRESENTATIVE_SAMPLING:
            # Sample subset proportionally
            for cohort, count in cohort_holder_counts.items():
                # Proportional sampling (maintain cohort ratios)
                num_agents = max(
                    10,  # Minimum 10 agents per cohort
                    int(self.REPRESENTATIVE_SAMPLE_SIZE * count / total_holders)
                )

                # Scaling weight = actual holders / agents created
                scaling_weight = count / num_agents

                result[cohort] = (num_agents, scaling_weight)

        else:  # META_AGENTS
            # Fixed number of meta-agents per cohort
            for cohort, count in cohort_holder_counts.items():
                num_agents = self.META_AGENTS_PER_COHORT
                scaling_weight = count / num_agents
                result[cohort] = (num_agents, scaling_weight)

        # Log summary
        total_agents = sum(r[0] for r in result.values())
        logger.info(
            f"Agent scaling: {total_holders:,} holders → {total_agents} agents "
            f"({strategy})"
        )

        for cohort, (num_agents, weight) in result.items():
            logger.debug(
                f"  {cohort}: {num_agents} agents (weight={weight:.1f}x, "
                f"represents {cohort_holder_counts[cohort]:,} holders)"
            )

        return result

    def create_scaled_agents(
        self,
        cohort: AgentCohort,
        num_agents: int,
        total_allocation: float,
        actual_holder_count: int,
        vesting_config: Dict
    ) -> List[TokenHolderAgent]:
        """
        Create scaled agents with appropriate weights.

        Args:
            cohort: AgentCohort instance
            num_agents: Number of agents to create
            total_allocation: Total tokens allocated to cohort
            actual_holder_count: Actual number of holders represented
            vesting_config: Vesting configuration

        Returns:
            List of TokenHolderAgent instances with scaling weights
        """
        # Calculate scaling weight
        scaling_weight = actual_holder_count / num_agents

        # Create agents using cohort's method
        agents = cohort.create_agents(
            num_agents=num_agents,
            total_allocation=total_allocation,
            vesting_config=vesting_config,
            scaling_weight=scaling_weight
        )

        logger.debug(
            f"Created {len(agents)} agents for {cohort.name} "
            f"(weight={scaling_weight:.1f}x, "
            f"total_allocation={total_allocation:,.0f})"
        )

        return agents

    @classmethod
    def estimate_performance(
        cls,
        total_holders: int,
        months: int
    ) -> Dict[str, float]:
        """
        Estimate simulation performance for given scale.

        Args:
            total_holders: Total number of holders
            months: Number of months to simulate

        Returns:
            Dict with performance estimates
        """
        scaling = cls()
        strategy = scaling.determine_strategy(total_holders)

        # Estimate agent count
        if strategy == ScalingStrategy.FULL_INDIVIDUAL:
            agent_count = total_holders
        elif strategy == ScalingStrategy.REPRESENTATIVE_SAMPLING:
            agent_count = cls.REPRESENTATIVE_SAMPLE_SIZE
        else:  # META_AGENTS
            # Assume 3 cohorts average
            agent_count = cls.META_AGENTS_PER_COHORT * 3

        # Performance estimates (empirical)
        # Base: ~0.05ms per agent per iteration
        time_per_iteration = agent_count * 0.00005  # 0.05ms
        total_time = time_per_iteration * months

        # Memory estimates
        # Base: ~1KB per agent
        memory_mb = agent_count * 0.001

        return {
            "strategy": strategy,
            "estimated_agents": agent_count,
            "time_per_iteration_sec": time_per_iteration,
            "total_time_sec": total_time,
            "memory_mb": memory_mb,
            "holders_per_agent": total_holders / agent_count
        }

    @classmethod
    def get_strategy_info(cls, strategy: ScalingStrategy) -> Dict[str, str]:
        """
        Get information about a scaling strategy.

        Args:
            strategy: Scaling strategy

        Returns:
            Dict with strategy information
        """
        info = {
            ScalingStrategy.FULL_INDIVIDUAL: {
                "name": "Full Individual",
                "description": "Create one agent per holder (1:1 mapping)",
                "best_for": "< 1,000 holders",
                "accuracy": "Highest",
                "performance": "Slowest",
                "use_case": "Small projects, detailed analysis"
            },
            ScalingStrategy.REPRESENTATIVE_SAMPLING: {
                "name": "Representative Sampling",
                "description": "Sample ~1,000 representative agents",
                "best_for": "1,000 - 10,000 holders",
                "accuracy": "High",
                "performance": "Fast",
                "use_case": "Medium projects, good balance"
            },
            ScalingStrategy.META_AGENTS: {
                "name": "Meta-Agents",
                "description": "Each agent represents many holders",
                "best_for": "> 10,000 holders",
                "accuracy": "Good (statistically representative)",
                "performance": "Fastest",
                "use_case": "Large projects, quick analysis"
            }
        }

        return info.get(strategy, {})


def get_holder_count_from_buckets(
    buckets: List[Dict],
    total_supply: int
) -> Dict[str, int]:
    """
    Estimate holder counts from bucket allocations.

    This is a placeholder - in production, this would come from
    actual token holder data (e.g., blockchain snapshots).

    Args:
        buckets: List of bucket configurations
        total_supply: Total token supply

    Returns:
        Dict mapping cohort name to estimated holder count
    """
    # Simple heuristic: Assume different holder densities by cohort
    holder_density = {
        "Team": 0.0001,  # 1 holder per 10,000 tokens (concentrated)
        "VC": 0.0001,    # 1 holder per 10,000 tokens
        "Advisors": 0.0002,  # 1 holder per 5,000 tokens
        "Investors": 0.001,  # 1 holder per 1,000 tokens
        "Community": 0.01,   # 1 holder per 100 tokens (distributed)
        "Public": 0.02,      # 1 holder per 50 tokens (very distributed)
    }

    result = {}

    for bucket in buckets:
        cohort_name = bucket["bucket"]
        allocation_pct = bucket["allocation"]

        # Calculate tokens allocated
        tokens_allocated = (allocation_pct / 100.0) * total_supply

        # Estimate holders based on density
        density = holder_density.get(cohort_name, 0.001)  # Default: 1 per 1K tokens
        estimated_holders = max(1, int(tokens_allocated * density))

        result[cohort_name] = estimated_holders

    return result
