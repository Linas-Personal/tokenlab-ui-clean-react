"""
Monte Carlo Simulation Engine.

Runs multiple ABM simulation trials in parallel to generate confidence bands
and probabilistic forecasts.
"""
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import numpy as np

from app.abm.engine.simulation_loop import ABMSimulationLoop, IterationResult, SimulationResults

logger = logging.getLogger(__name__)


@dataclass
class MonteCarloTrial:
    """Result from a single Monte Carlo trial."""
    trial_index: int
    global_metrics: List[Dict[str, Any]]
    final_price: float
    total_sold: float
    seed: int
    execution_time_seconds: float = 0.0


@dataclass
class MonteCarloPercentile:
    """Percentile trajectory (e.g., P10, P50, P90)."""
    percentile: float
    global_metrics: List[Dict[str, Any]]
    final_price: float
    total_sold: float


@dataclass
class MonteCarloResults:
    """Complete Monte Carlo simulation results."""
    trials: List[MonteCarloTrial] = field(default_factory=list)
    percentiles: List[MonteCarloPercentile] = field(default_factory=list)
    mean_metrics: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, float] = field(default_factory=dict)
    execution_time_seconds: float = 0.0
    config: Dict[str, Any] = field(default_factory=dict)


class MonteCarloEngine:
    """
    Monte Carlo simulation engine for ABM.

    Runs multiple trials with different random seeds in parallel
    to generate probabilistic forecasts.
    """

    def __init__(
        self,
        num_trials: int = 100,
        confidence_levels: Optional[List[float]] = None,
        seed: Optional[int] = None
    ):
        """
        Initialize Monte Carlo engine.

        Args:
            num_trials: Number of simulation trials to run
            confidence_levels: List of percentiles to calculate (default: [10, 50, 90])
            seed: Base random seed for reproducibility
        """
        self.num_trials = num_trials
        self.confidence_levels = confidence_levels or [10, 50, 90]
        self.base_seed = seed or int(time.time())
        self.rng = np.random.Generator(np.random.PCG64(self.base_seed))

        logger.info(
            f"MonteCarloEngine initialized: {num_trials} trials, "
            f"percentiles={self.confidence_levels}, seed={self.base_seed}"
        )

    async def run_monte_carlo(
        self,
        config: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> MonteCarloResults:
        """
        Run Monte Carlo simulation.

        Args:
            config: ABM simulation configuration
            progress_callback: Optional callback(completed_trials, total_trials)

        Returns:
            MonteCarloResults with trials, percentiles, and summary statistics
        """
        start_time = time.time()

        logger.info(f"Starting Monte Carlo simulation with {self.num_trials} trials...")

        trials = await self._run_parallel_trials(config, progress_callback)

        logger.info("Computing percentiles and statistics...")

        percentiles = self._compute_percentiles(trials)
        mean_metrics = self._compute_mean_trajectory(trials)
        summary = self._compute_summary_statistics(trials)

        execution_time = time.time() - start_time

        logger.info(
            f"Monte Carlo complete: {self.num_trials} trials in {execution_time:.2f}s "
            f"({execution_time/self.num_trials:.3f}s/trial)"
        )

        return MonteCarloResults(
            trials=trials,
            percentiles=percentiles,
            mean_metrics=mean_metrics,
            summary=summary,
            execution_time_seconds=execution_time,
            config=config
        )

    async def _run_parallel_trials(
        self,
        config: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> List[MonteCarloTrial]:
        """Run multiple simulation trials in parallel."""
        trial_seeds = self.rng.integers(0, 2**31, size=self.num_trials)

        tasks = []
        for trial_idx in range(self.num_trials):
            task = self._run_single_trial(trial_idx, config, int(trial_seeds[trial_idx]))
            tasks.append(task)

        trials = []
        completed = 0

        for coro in asyncio.as_completed(tasks):
            trial = await coro
            trials.append(trial)
            completed += 1

            if progress_callback:
                await progress_callback(completed, self.num_trials)

            if completed % 10 == 0 or completed == self.num_trials:
                logger.info(f"Completed {completed}/{self.num_trials} trials")

        trials.sort(key=lambda t: t.trial_index)
        return trials

    async def _run_single_trial(
        self,
        trial_idx: int,
        config: Dict[str, Any],
        seed: int
    ) -> MonteCarloTrial:
        """Run a single Monte Carlo trial."""
        trial_start = time.time()

        trial_config = config.copy()
        trial_config.setdefault("abm", {})
        trial_config["abm"]["seed"] = seed

        sim_loop = ABMSimulationLoop.from_config(trial_config)

        results = await sim_loop.run_full_simulation(
            months=trial_config["token"]["horizon_months"]
        )

        execution_time = time.time() - trial_start

        global_metrics = [
            {
                "month_index": r.month_index,
                "date": r.date,
                "price": r.price,
                "circulating_supply": r.circulating_supply,
                "total_unlocked": r.total_unlocked,
                "total_sold": r.total_sold,
                "total_staked": r.total_staked,
                "total_held": r.total_held
            }
            for r in results.global_metrics
        ]

        final_result = results.global_metrics[-1]

        return MonteCarloTrial(
            trial_index=trial_idx,
            global_metrics=global_metrics,
            final_price=final_result.price,
            total_sold=final_result.total_sold,
            seed=seed,
            execution_time_seconds=execution_time
        )

    def _compute_percentiles(self, trials: List[MonteCarloTrial]) -> List[MonteCarloPercentile]:
        """Compute percentile trajectories (P10, P50, P90)."""
        if not trials:
            return []

        num_months = len(trials[0].global_metrics)
        percentiles = []

        for percentile_value in self.confidence_levels:
            percentile_metrics = []

            for month_idx in range(num_months):
                prices = [trial.global_metrics[month_idx]["price"] for trial in trials]
                circ_supply = [trial.global_metrics[month_idx]["circulating_supply"] for trial in trials]
                total_unlocked = [trial.global_metrics[month_idx]["total_unlocked"] for trial in trials]
                total_sold = [trial.global_metrics[month_idx]["total_sold"] for trial in trials]
                total_staked = [trial.global_metrics[month_idx]["total_staked"] for trial in trials]
                total_held = [trial.global_metrics[month_idx]["total_held"] for trial in trials]

                metric = {
                    "month_index": month_idx,
                    "date": trials[0].global_metrics[month_idx]["date"],
                    "price": float(np.percentile(prices, percentile_value)),
                    "circulating_supply": float(np.percentile(circ_supply, percentile_value)),
                    "total_unlocked": float(np.percentile(total_unlocked, percentile_value)),
                    "total_sold": float(np.percentile(total_sold, percentile_value)),
                    "total_staked": float(np.percentile(total_staked, percentile_value)),
                    "total_held": float(np.percentile(total_held, percentile_value))
                }
                percentile_metrics.append(metric)

            final_prices = [trial.final_price for trial in trials]
            final_sold = [trial.total_sold for trial in trials]

            percentiles.append(MonteCarloPercentile(
                percentile=percentile_value,
                global_metrics=percentile_metrics,
                final_price=float(np.percentile(final_prices, percentile_value)),
                total_sold=float(np.percentile(final_sold, percentile_value))
            ))

        return percentiles

    def _compute_mean_trajectory(self, trials: List[MonteCarloTrial]) -> List[Dict[str, Any]]:
        """Compute mean trajectory across all trials."""
        if not trials:
            return []

        num_months = len(trials[0].global_metrics)
        mean_metrics = []

        for month_idx in range(num_months):
            prices = [trial.global_metrics[month_idx]["price"] for trial in trials]
            circ_supply = [trial.global_metrics[month_idx]["circulating_supply"] for trial in trials]
            total_unlocked = [trial.global_metrics[month_idx]["total_unlocked"] for trial in trials]
            total_sold = [trial.global_metrics[month_idx]["total_sold"] for trial in trials]
            total_staked = [trial.global_metrics[month_idx]["total_staked"] for trial in trials]
            total_held = [trial.global_metrics[month_idx]["total_held"] for trial in trials]

            metric = {
                "month_index": month_idx,
                "date": trials[0].global_metrics[month_idx]["date"],
                "price": float(np.mean(prices)),
                "circulating_supply": float(np.mean(circ_supply)),
                "total_unlocked": float(np.mean(total_unlocked)),
                "total_sold": float(np.mean(total_sold)),
                "total_staked": float(np.mean(total_staked)),
                "total_held": float(np.mean(total_held))
            }
            mean_metrics.append(metric)

        return mean_metrics

    def _compute_summary_statistics(self, trials: List[MonteCarloTrial]) -> Dict[str, float]:
        """Compute summary statistics across all trials."""
        final_prices = [trial.final_price for trial in trials]
        total_sold_list = [trial.total_sold for trial in trials]

        return {
            "num_trials": len(trials),
            "mean_final_price": float(np.mean(final_prices)),
            "std_final_price": float(np.std(final_prices)),
            "min_final_price": float(np.min(final_prices)),
            "max_final_price": float(np.max(final_prices)),
            "p10_final_price": float(np.percentile(final_prices, 10)),
            "p50_final_price": float(np.percentile(final_prices, 50)),
            "p90_final_price": float(np.percentile(final_prices, 90)),
            "mean_total_sold": float(np.mean(total_sold_list)),
            "std_total_sold": float(np.std(total_sold_list)),
            "coefficient_of_variation": float(np.std(final_prices) / np.mean(final_prices)) if np.mean(final_prices) > 0 else 0.0
        }
