"""
ABM Simulation Loop - Main Orchestrator.

Coordinates iteration execution, feedback loops, and result collection.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Awaitable
from datetime import datetime, timedelta
import logging

from app.abm.core.controller import ABMController
from app.abm.agents.token_holder import TokenHolderAgent
from app.abm.dynamics.token_economy import TokenEconomy
from app.abm.dynamics.pricing import PricingModel, create_pricing_controller
from app.abm.engine.parallel_execution import execute_agents_parallel, aggregate_agent_actions, aggregate_by_cohort

logger = logging.getLogger(__name__)


@dataclass
class IterationResult:
    """Result data for one simulation iteration."""
    month_index: int
    date: str
    price: float
    circulating_supply: float
    total_unlocked: float
    total_sold: float
    total_staked: float
    total_held: float

    # Cohort-level breakdown (optional)
    cohort_results: Optional[Dict[str, Dict[str, float]]] = None


@dataclass
class SimulationResults:
    """Complete simulation results."""
    global_metrics: List[IterationResult] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    execution_time_seconds: float = 0.0
    warnings: List[str] = field(default_factory=list)


class ABMSimulationLoop:
    """
    Main ABM simulation orchestrator.

    Responsibilities:
    1. Initialize all components (agents, pricing, staking, treasury)
    2. Run iteration loop:
       - Execute all agents in parallel
       - Aggregate actions
       - Update token economy
       - Run pricing (FEEDBACK LOOP)
       - Run staking/treasury
       - Store results
    3. Manage progress callbacks
    """

    def __init__(
        self,
        agents: List[TokenHolderAgent],
        token_economy: TokenEconomy,
        pricing_controller: ABMController,
        staking_controller: Optional[ABMController] = None,
        treasury_controller: Optional[ABMController] = None,
        start_date: datetime = None,
        store_cohort_details: bool = True
    ):
        """
        Initialize simulation loop.

        Args:
            agents: List of token holder agents
            token_economy: Token economy state manager
            pricing_controller: Pricing model controller
            staking_controller: Optional staking pool controller
            treasury_controller: Optional treasury controller
            start_date: Simulation start date
            store_cohort_details: Whether to store cohort-level breakdown
        """
        self.agents = agents
        self.token_economy = token_economy
        self.pricing_controller = pricing_controller
        self.staking_controller = staking_controller
        self.treasury_controller = treasury_controller
        self.start_date = start_date or datetime.now()
        self.store_cohort_details = store_cohort_details

        # Link dependencies
        self._link_dependencies()

        # Results storage
        self.results: List[IterationResult] = []
        self.warnings: List[str] = []

        logger.info(
            f"ABMSimulationLoop initialized: "
            f"{len(agents)} agents, "
            f"pricing={pricing_controller.__class__.__name__}, "
            f"staking={staking_controller is not None}, "
            f"treasury={treasury_controller is not None}"
        )

    def _link_dependencies(self) -> None:
        """Link dependencies between components."""
        # All agents need access to TokenEconomy
        for agent in self.agents:
            agent.link(TokenEconomy, self.token_economy)

        # Pricing controller needs TokenEconomy
        self.pricing_controller.link(TokenEconomy, self.token_economy)

        # Optional controllers
        if self.staking_controller:
            self.staking_controller.link(TokenEconomy, self.token_economy)

        if self.treasury_controller:
            self.treasury_controller.link(TokenEconomy, self.token_economy)

        logger.debug("Dependencies linked")

    async def run_full_simulation(
        self,
        months: int,
        progress_callback: Optional[Callable[[int, int], Awaitable[None]]] = None
    ) -> SimulationResults:
        """
        Run complete simulation for specified number of months.

        Args:
            months: Number of months to simulate
            progress_callback: Optional async callback(current_month, total_months)

        Returns:
            SimulationResults
        """
        import time
        start_time = time.time()

        logger.info(f"Starting ABM simulation for {months} months...")

        for month_idx in range(months):
            # Run one iteration
            result = await self.run_iteration(month_idx)
            self.results.append(result)

            # Progress callback
            if progress_callback:
                await progress_callback(month_idx + 1, months)

            # Log progress
            if (month_idx + 1) % 12 == 0 or month_idx == months - 1:
                logger.info(
                    f"Completed month {month_idx + 1}/{months}: "
                    f"price=${result.price:.4f}, "
                    f"circ_supply={result.circulating_supply:,.0f}, "
                    f"sold={result.total_sold:,.0f}"
                )

        execution_time = time.time() - start_time

        logger.info(
            f"Simulation complete: {months} months in {execution_time:.2f}s "
            f"({execution_time/months:.3f}s/month)"
        )

        return SimulationResults(
            global_metrics=self.results,
            config=self._get_simulation_config(),
            execution_time_seconds=execution_time,
            warnings=self.warnings
        )

    async def run_iteration(self, month_index: int) -> IterationResult:
        """
        Run one simulation iteration (one month).

        This is the core ABM loop with feedback:
        1. Reset monthly pressures
        2. Execute all agents → aggregate actions
        3. Update circulating supply
        4. Run pricing (FEEDBACK: agent actions → price)
        5. Run staking/treasury
        6. Store results

        Args:
            month_index: Current month number (0-indexed)

        Returns:
            IterationResult for this month
        """
        # 1. Reset monthly aggregates
        self.token_economy.reset_monthly_pressures()

        # 2. Execute all agents in parallel
        agent_actions = await execute_agents_parallel(self.agents, batch_size=100)

        # 3. Aggregate actions (apply scaling weights)
        aggregated = aggregate_agent_actions(agent_actions)
        cohort_aggregated = aggregate_by_cohort(agent_actions, self.agents) if self.store_cohort_details else None

        # 4. Update token economy state with aggregates
        self.token_economy.total_sell_pressure = aggregated["total_sell"]
        self.token_economy.total_stake_pressure = aggregated["total_stake"]
        self.token_economy.total_unlock_this_month = aggregated["total_sell"] + aggregated["total_stake"] + aggregated["total_hold"]

        # Net change in circulating supply (unlocks - staking)
        net_supply_change = aggregated["total_sell"] + aggregated["total_hold"]  # Staking removes from circulation
        self.token_economy.update_circulating_supply(net_supply_change)

        # 5. FEEDBACK LOOP: Run pricing based on agent actions
        new_price = await self.pricing_controller.execute()
        self.token_economy.update_price(new_price)

        # 6. Update transaction volume (for EOE pricing)
        self.token_economy.transactions_value_in_fiat = aggregated["total_sell"] * new_price

        # 7. Run staking pool (if enabled)
        staking_metrics = None
        if self.staking_controller:
            staking_metrics = await self.staking_controller.execute(aggregated["total_stake"])

        # 8. Run treasury (if enabled)
        treasury_metrics = None
        if self.treasury_controller:
            treasury_metrics = await self.treasury_controller.execute(
                sell_volume_tokens=aggregated["total_sell"],
                current_price=new_price
            )

        # 9. Increment iteration counter
        self.token_economy.iteration += 1

        # 10. Create result record
        current_date = self.start_date + timedelta(days=30 * month_index)

        result = IterationResult(
            month_index=month_index,
            date=current_date.strftime("%Y-%m-%d"),
            price=new_price,
            circulating_supply=self.token_economy.circulating_supply,
            total_unlocked=self.token_economy.total_unlock_this_month,
            total_sold=aggregated["total_sell"],
            total_staked=aggregated["total_stake"],
            total_held=aggregated["total_hold"],
            cohort_results=cohort_aggregated
        )

        return result

    def _get_simulation_config(self) -> Dict[str, Any]:
        """
        Get simulation configuration summary.

        Returns:
            Configuration dictionary
        """
        return {
            "num_agents": len(self.agents),
            "pricing_model": self.pricing_controller.__class__.__name__,
            "has_staking": self.staking_controller is not None,
            "has_treasury": self.treasury_controller is not None,
            "start_date": self.start_date.isoformat()
        }

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "ABMSimulationLoop":
        """
        Factory method to create simulation loop from configuration.

        This will be the main entry point from the API.

        Args:
            config: Configuration dictionary

        Returns:
            ABMSimulationLoop instance
        """
        from app.abm.agents.cohort import AgentCohort, DEFAULT_COHORT_PROFILES
        from app.abm.dynamics.token_economy import TokenEconomy, TokenEconomyConfig
        from datetime import datetime

        # Extract config sections
        token_config = config["token"]
        buckets_config = config["buckets"]
        abm_config = config.get("abm", {})

        # Create token economy
        token_economy = TokenEconomy(TokenEconomyConfig(
            total_supply=token_config["total_supply"],
            initial_price=abm_config.get("initial_price", 1.0),
            initial_circulating_supply=0.0
        ))

        # Create agents from buckets (cohorts) with adaptive scaling
        from app.abm.agents.scaling import (
            AdaptiveAgentScaling,
            ScalingStrategy,
            get_holder_count_from_buckets
        )

        # Determine scaling strategy
        agent_granularity = abm_config.get("agent_granularity", "adaptive")

        if agent_granularity == "full_individual":
            forced_strategy = ScalingStrategy.FULL_INDIVIDUAL
        elif agent_granularity == "meta_agents":
            forced_strategy = ScalingStrategy.META_AGENTS
        else:
            forced_strategy = None  # Auto-detect

        scaling = AdaptiveAgentScaling(strategy=forced_strategy)

        # Estimate holder counts from buckets
        holder_counts = get_holder_count_from_buckets(
            buckets_config,
            token_config["total_supply"]
        )

        # Calculate agent counts with scaling weights
        agent_counts = scaling.calculate_agent_counts(holder_counts)

        # Create agents for each cohort
        all_agents = []
        for bucket in buckets_config:
            bucket_name = bucket["bucket"]
            allocation_pct = bucket["allocation"]

            # Get cohort profile
            profile = DEFAULT_COHORT_PROFILES.get(bucket_name, DEFAULT_COHORT_PROFILES["Community"])
            cohort = AgentCohort(bucket_name, profile, seed=abm_config.get("seed"))

            # Get agent count and scaling weight
            num_agents, scaling_weight = agent_counts.get(
                bucket_name,
                (abm_config.get("agents_per_cohort", 50), 1.0)
            )

            total_allocation = (allocation_pct / 100.0) * token_config["total_supply"]
            actual_holder_count = holder_counts.get(bucket_name, num_agents)

            # Create scaled agents
            agents = scaling.create_scaled_agents(
                cohort=cohort,
                num_agents=num_agents,
                total_allocation=total_allocation,
                actual_holder_count=actual_holder_count,
                vesting_config=bucket
            )
            all_agents.extend(agents)

        logger.info(f"Created {len(all_agents)} total agents across {len(buckets_config)} cohorts")

        # Create pricing controller
        pricing_model = PricingModel(abm_config.get("pricing_model", "eoe"))
        pricing_controller = create_pricing_controller(
            pricing_model,
            abm_config.get("pricing_config", {})
        )

        # Create staking/treasury controllers (Phase 3)
        staking_controller = None
        treasury_controller = None

        if abm_config.get("enable_staking", False):
            from app.abm.dynamics.staking import StakingPool, StakingConfig

            staking_config_dict = abm_config.get("staking_config", {})
            staking_config = StakingConfig(
                base_apy=staking_config_dict.get("base_apy", 0.12),
                max_capacity_pct=staking_config_dict.get("max_capacity_pct", 0.5),
                lockup_months=staking_config_dict.get("lockup_months", 6),
                reward_source=staking_config_dict.get("reward_source", "emission")
            )
            staking_controller = StakingPool(staking_config, config["token"]["total_supply"])
            logger.info("Staking pool enabled")

        if abm_config.get("enable_treasury", False):
            from app.abm.dynamics.treasury import TreasuryController, TreasuryConfig

            treasury_config_dict = abm_config.get("treasury_config", {})
            treasury_config = TreasuryConfig(
                initial_balance_pct=treasury_config_dict.get("initial_balance_pct", 0.15),
                transaction_fee_pct=treasury_config_dict.get("transaction_fee_pct", 0.02),
                hold_pct=treasury_config_dict.get("hold_pct", 0.50),
                liquidity_pct=treasury_config_dict.get("liquidity_pct", 0.30),
                buyback_pct=treasury_config_dict.get("buyback_pct", 0.20),
                burn_bought_tokens=treasury_config_dict.get("burn_bought_tokens", True)
            )
            treasury_controller = TreasuryController(treasury_config, config["token"]["total_supply"])
            logger.info("Treasury controller enabled")

        # Parse start date
        start_date = datetime.strptime(token_config["start_date"], "%Y-%m-%d")

        return cls(
            agents=all_agents,
            token_economy=token_economy,
            pricing_controller=pricing_controller,
            staking_controller=staking_controller,
            treasury_controller=treasury_controller,
            start_date=start_date,
            store_cohort_details=abm_config.get("store_cohort_details", True)
        )
