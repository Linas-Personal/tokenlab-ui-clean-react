"""
Agent Cohort - Collection of agents with similar characteristics.

Cohorts represent groups like "Team", "VC", "Community" with distinct
behavioral profiles. Agents within a cohort have heterogeneous attributes
sampled from cohort-specific distributions.
"""
from dataclasses import dataclass
from typing import List, Dict, Any
import numpy as np
import logging

from app.abm.agents.token_holder import TokenHolderAgent, TokenHolderAttributes
from app.abm.vesting.vesting_schedule import VestingSchedule

logger = logging.getLogger(__name__)


@dataclass
class CohortProfile:
    """
    Statistical profile for a cohort.

    Defines distributions for sampling agent attributes.
    Uses Beta and Gamma distributions for bounded and positive-valued parameters.
    """
    # Risk tolerance: Beta(alpha, beta) distribution
    risk_alpha: float = 2.0
    risk_beta: float = 2.0

    # Hold time preference: Gamma(shape, scale) distribution
    hold_time_shape: float = 2.0
    hold_time_scale: float = 6.0  # Mean = shape * scale

    # Sell pressure: Normal(mean, std) distribution, clipped to [0, 1]
    sell_pressure_mean: float = 0.25
    sell_pressure_std: float = 0.05

    # Price sensitivity: Beta distribution
    price_sensitivity_alpha: float = 2.0
    price_sensitivity_beta: float = 2.0

    # Staking propensity: Beta distribution
    stake_alpha: float = 3.0
    stake_beta: float = 7.0  # Mean = alpha / (alpha + beta) = 0.3

    # Cliff shock multiplier
    cliff_shock_mult: float = 2.0

    # Take profit / stop loss thresholds
    take_profit_threshold: float = 0.5  # 50% gain
    stop_loss_threshold: float = -0.3  # 30% loss


# Default cohort profiles (inspired by real-world behavior)
DEFAULT_COHORT_PROFILES = {
    "Team": CohortProfile(
        risk_alpha=2, risk_beta=8,  # Low risk (mean ~0.2, long-term holders)
        hold_time_shape=2, hold_time_scale=12,  # 12-24 month hold time
        sell_pressure_mean=0.10, sell_pressure_std=0.03,  # Low selling
        price_sensitivity_alpha=2, price_sensitivity_beta=8,  # Low sensitivity
        stake_alpha=6, stake_beta=4,  # High staking (mean ~0.6)
        cliff_shock_mult=1.5
    ),
    "VC": CohortProfile(
        risk_alpha=5, risk_beta=5,  # Moderate risk (mean ~0.5)
        hold_time_shape=1.5, hold_time_scale=6,  # 6-12 month hold time
        sell_pressure_mean=0.40, sell_pressure_std=0.10,  # High selling
        price_sensitivity_alpha=6, price_sensitivity_beta=4,  # High sensitivity
        stake_alpha=3, stake_beta=7,  # Low staking (mean ~0.3)
        cliff_shock_mult=3.0  # Strong cliff shock
    ),
    "Community": CohortProfile(
        risk_alpha=5, risk_beta=3,  # Higher risk variance (mean ~0.625)
        hold_time_shape=2, hold_time_scale=4,  # 4-12 month hold time
        sell_pressure_mean=0.25, sell_pressure_std=0.08,  # Moderate selling
        price_sensitivity_alpha=5, price_sensitivity_beta=5,  # Moderate sensitivity
        stake_alpha=4, stake_beta=6,  # Moderate staking (mean ~0.4)
        cliff_shock_mult=2.0
    ),
    "Investors": CohortProfile(
        risk_alpha=6, risk_beta=4,  # Moderate risk (mean ~0.6)
        hold_time_shape=2, hold_time_scale=8,  # 8-16 month hold time
        sell_pressure_mean=0.30, sell_pressure_std=0.08,
        price_sensitivity_alpha=7, price_sensitivity_beta=3,  # High sensitivity
        stake_alpha=5, stake_beta=5,  # Moderate staking (mean ~0.5)
        cliff_shock_mult=2.5
    ),
    "Advisors": CohortProfile(
        risk_alpha=3, risk_beta=7,  # Low risk (mean ~0.3)
        hold_time_shape=2, hold_time_scale=10,  # 10-20 month hold time
        sell_pressure_mean=0.20, sell_pressure_std=0.05,
        price_sensitivity_alpha=4, price_sensitivity_beta=6,  # Moderate sensitivity
        stake_alpha=4, stake_beta=6,  # Moderate staking (mean ~0.4)
        cliff_shock_mult=1.8
    )
}


class AgentCohort:
    """
    Manages a cohort of agents with similar characteristics.

    Creates agents by sampling from cohort-specific distributions,
    resulting in heterogeneous but statistically similar agents.
    """

    def __init__(self, name: str, profile: CohortProfile, seed: int = None):
        """
        Initialize agent cohort.

        Args:
            name: Cohort name (e.g., "Team", "VC")
            profile: Statistical profile for this cohort
            seed: Random seed for reproducibility
        """
        self.name = name
        self.profile = profile
        self.seed = seed

        if seed is not None:
            self.rng = np.random.RandomState(seed)
        else:
            self.rng = np.random.RandomState()

        logger.info(
            f"Cohort '{name}' initialized with profile: "
            f"sell_pressure={profile.sell_pressure_mean:.2f}, "
            f"stake_propensity={profile.stake_alpha/(profile.stake_alpha + profile.stake_beta):.2f}"
        )

    def create_agents(
        self,
        num_agents: int,
        total_allocation: float,
        vesting_config: Dict[str, Any],
        scaling_weight: float = 1.0
    ) -> List[TokenHolderAgent]:
        """
        Create a collection of heterogeneous agents for this cohort.

        Args:
            num_agents: Number of agents to create
            total_allocation: Total tokens allocated to this cohort
            vesting_config: Vesting configuration dict
            scaling_weight: Weight for meta-agents (e.g., 1 agent represents N holders)

        Returns:
            List of TokenHolderAgent instances
        """
        agents = []
        tokens_per_agent = total_allocation / num_agents

        logger.info(
            f"Creating {num_agents} agents for cohort '{self.name}' "
            f"(total_allocation={total_allocation:,.0f}, "
            f"per_agent={tokens_per_agent:,.0f}, scaling_weight={scaling_weight})"
        )

        for i in range(num_agents):
            # Sample attributes from distributions
            attrs = self._sample_attributes(
                agent_id=f"{self.name}_{i}",
                allocation_tokens=tokens_per_agent,
                scaling_weight=scaling_weight
            )

            # Create vesting schedule
            vesting_schedule = VestingSchedule.from_bucket_config(
                vesting_config, tokens_per_agent
            )

            # Create agent
            agent = TokenHolderAgent(attrs, vesting_schedule)
            agents.append(agent)

        logger.debug(f"Created {len(agents)} agents for cohort '{self.name}'")
        return agents

    def _sample_attributes(
        self,
        agent_id: str,
        allocation_tokens: float,
        scaling_weight: float
    ) -> TokenHolderAttributes:
        """
        Sample agent attributes from cohort distributions.

        Args:
            agent_id: Unique agent identifier
            allocation_tokens: Tokens allocated to this agent
            scaling_weight: Scaling weight for meta-agents

        Returns:
            TokenHolderAttributes instance
        """
        # Risk tolerance: Beta distribution
        risk_tolerance = self.rng.beta(
            self.profile.risk_alpha,
            self.profile.risk_beta
        )

        # Hold time preference: Gamma distribution
        hold_time_preference = self.rng.gamma(
            self.profile.hold_time_shape,
            self.profile.hold_time_scale
        )

        # Sell pressure: Normal distribution, clipped to [0, 1]
        sell_pressure_base = self.rng.normal(
            self.profile.sell_pressure_mean,
            self.profile.sell_pressure_std
        )
        sell_pressure_base = np.clip(sell_pressure_base, 0.0, 1.0)

        # Price sensitivity: Beta distribution
        price_sensitivity = self.rng.beta(
            self.profile.price_sensitivity_alpha,
            self.profile.price_sensitivity_beta
        )

        # Staking propensity: Beta distribution
        staking_propensity = self.rng.beta(
            self.profile.stake_alpha,
            self.profile.stake_beta
        )

        return TokenHolderAttributes(
            agent_id=agent_id,
            cohort=self.name,
            risk_tolerance=float(risk_tolerance),
            hold_time_preference=float(hold_time_preference),
            price_sensitivity=float(price_sensitivity),
            staking_propensity=float(staking_propensity),
            allocation_tokens=allocation_tokens,
            sell_pressure_base=float(sell_pressure_base),
            cliff_shock_multiplier=self.profile.cliff_shock_mult,
            take_profit_threshold=self.profile.take_profit_threshold,
            stop_loss_threshold=self.profile.stop_loss_threshold,
            scaling_weight=scaling_weight
        )

    @classmethod
    def from_bucket_config(
        cls,
        bucket_config: Dict[str, Any],
        profile: CohortProfile = None,
        seed: int = None
    ) -> "AgentCohort":
        """
        Create cohort from bucket configuration.

        Args:
            bucket_config: Bucket config dict from API request
            profile: Optional custom profile (uses default if not provided)
            seed: Random seed

        Returns:
            AgentCohort instance
        """
        bucket_name = bucket_config["bucket"]

        # Use provided profile or default
        if profile is None:
            profile = DEFAULT_COHORT_PROFILES.get(bucket_name, DEFAULT_COHORT_PROFILES["Community"])

        return cls(bucket_name, profile, seed)

    def __repr__(self) -> str:
        return f"AgentCohort(name={self.name}, profile={self.profile})"
