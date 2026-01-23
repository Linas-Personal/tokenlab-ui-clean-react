

# =============================================================================
# TIER 2 & 3: ADVANCED TOKENLAB INTEGRATION
# =============================================================================

class VestingTokenEconomy:
    """
    Lightweight TokenEconomy wrapper for vesting simulator.

    Provides minimal TokenLab API surface for pricing/treasury/staking
    without full agent-based simulation overhead.
    """

    def __init__(self, config: Dict):
        """Initialize vesting token economy."""
        self.config = config
        self.supply = config["token"]["total_supply"]
        self.circulating_supply = 0.0
        self.expected_circulating = 0.0
        self.price = 1.0
        self.initial_price = 1.0
        self.iteration = 0
        self.token = config["token"].get("name", "TokenA")
        self.fiat = "$"

        # Historical stores
        self._supply_store = [self.supply]
        self._circulating_store = [0.0]
        self._price_store = [self.price]
        self._iteration_store = [0]

        # Tier 2 components
        self.pricing_controller = None
        self.treasury = None
        self.staking_capacity_used = 0.0
        self.staking_capacity_max = 0.0

    def change_supply(self, delta: float):
        """Change total supply (e.g., from buybacks)."""
        self.supply += delta
        self.supply = max(0, self.supply)

    def update_price(self, new_price: float):
        """Update current price."""
        self.price = max(0.0001, new_price)

    def update_circulating(self, new_circulating: float):
        """Update circulating supply."""
        self.expected_circulating = new_circulating
        self.circulating_supply = new_circulating

    def advance_iteration(self):
        """Move to next iteration/month."""
        self.iteration += 1
        self._supply_store.append(self.supply)
        self._circulating_store.append(self.circulating_supply)
        self._price_store.append(self.price)
        self._iteration_store.append(self.iteration)

    def reset(self):
        """Reset state for Monte Carlo trials."""
        self.supply = self.config["token"]["total_supply"]
        self.circulating_supply = 0.0
        self.expected_circulating = 0.0
        self.price = self.initial_price
        self.iteration = 0
        self.staking_capacity_used = 0.0

        self._supply_store = [self.supply]
        self._circulating_store = [0.0]
        self._price_store = [self.price]
        self._iteration_store = [0]


class DynamicStakingController:
    """
    Dynamic staking with APY incentives and capacity limits.

    Replaces simple relock with realistic staking behavior:
    - APY-based participation incentives
    - Capacity limits (max % of circulating can stake)
    - Yield generation (optional)
    - Maturity tracking
    """

    def __init__(self, config: Dict, vesting_economy):
        """Initialize dynamic staking controller."""
        self.config = config
        self.vesting_economy = vesting_economy
        self.staking_config = config.get("tier2", {}).get("staking", {})

        # Staking schedule: {maturity_month: amount}
        self.staking_schedule = {}

        # Historical tracking
        self._staked_this_month = []
        self._matured_this_month = []
        self._capacity_used = []
        self._participation_rate = []

    def calculate_participation_rate(self, month_index: int) -> float:
        """
        Calculate staking participation rate based on incentives.

        Higher APY → higher participation
        Lower capacity remaining → lower participation
        """
        if not self.staking_config.get("enabled", False):
            return 0.0

        base_apy = self.staking_config.get("apy", 0.15)
        capacity_pct = self.staking_config.get("capacity", 0.60)

        # Calculate current capacity usage
        circulating = self.vesting_economy.circulating_supply
        if circulating == 0:
            return 0.0

        max_stakeable = circulating * capacity_pct
        current_staked = self.vesting_economy.staking_capacity_used
        capacity_remaining = max(0, max_stakeable - current_staked)
        capacity_utilization = current_staked / max_stakeable if max_stakeable > 0 else 0

        # Base participation from APY (normalized to 20% APY = 1.0 factor)
        apy_factor = min(1.0, base_apy / 0.20)

        # Reduce participation as capacity fills up
        capacity_factor = max(0, 1.0 - capacity_utilization)

        # Early adopter bonus (higher participation in early months)
        early_bonus = max(0, 1.2 - (month_index * 0.02))

        # Combined participation rate
        participation = apy_factor * capacity_factor * early_bonus * 0.7
        participation = min(1.0, max(0.0, participation))

        return participation

    def apply_staking(self, unlocked_amount: float, month_index: int) -> Tuple[float, float]:
        """
        Apply staking to newly unlocked tokens.

        Returns:
            (free_amount, staked_amount)
        """
        if not self.staking_config.get("enabled", False):
            return unlocked_amount, 0.0

        participation_rate = self.calculate_participation_rate(month_index)
        lockup_months = self.staking_config.get("lockup", 6)

        # Calculate stake amount
        staked_amount = unlocked_amount * participation_rate
        free_amount = unlocked_amount - staked_amount

        # Update capacity tracking
        self.vesting_economy.staking_capacity_used += staked_amount

        # Schedule maturity (with yield if enabled)
        maturity_month = month_index + lockup_months
        if maturity_month not in self.staking_schedule:
            self.staking_schedule[maturity_month] = 0.0

        # Add staking yield if configured
        if self.staking_config.get("include_rewards", True):
            apy = self.staking_config.get("apy", 0.15)
            yield_amount = staked_amount * apy * (lockup_months / 12.0)
            total_maturity = staked_amount + yield_amount
            self.staking_schedule[maturity_month] += total_maturity

            # Yield increases total supply
            self.vesting_economy.change_supply(yield_amount)
        else:
            self.staking_schedule[maturity_month] += staked_amount

        self._staked_this_month.append(staked_amount)
        self._participation_rate.append(participation_rate)

        return free_amount, staked_amount

    def get_matured_stake(self, month_index: int) -> float:
        """Get staked tokens maturing this month."""
        matured = self.staking_schedule.get(month_index, 0.0)
        if matured > 0:
            del self.staking_schedule[month_index]
            self.vesting_economy.staking_capacity_used -= matured
            self.vesting_economy.staking_capacity_used = max(0, self.vesting_economy.staking_capacity_used)

        self._matured_this_month.append(matured)
        return matured

    def reset(self):
        """Reset for Monte Carlo trials."""
        self.staking_schedule = {}
        self._staked_this_month = []
        self._matured_this_month = []
        self._capacity_used = []
        self._participation_rate = []


class DynamicPricingController:
    """
    Dynamic pricing based on circulating supply.

    Uses bonding curve or linear demand curve to calculate price
    based on current circulating supply.
    """

    def __init__(self, config: Dict, vesting_economy):
        """Initialize dynamic pricing controller."""
        self.config = config
        self.vesting_economy = vesting_economy
        self.pricing_config = config.get("tier2", {}).get("pricing", {})

        self.initial_price = self.pricing_config.get("initial_price", 1.0)
        self.max_supply = vesting_economy.supply

        # Historical tracking
        self._prices = []

    def calculate_price(self, circulating_supply: float) -> float:
        """
        Calculate price based on circulating supply.

        Models:
        - constant: Fixed price (Tier 1 behavior)
        - linear: P = P0 * (1 - elasticity * (S/S_max))
        - bonding_curve: P = P0 * (S_max / S) ^ elasticity
        """
        if not self.pricing_config.get("enabled", False):
            return self.initial_price

        model = self.pricing_config.get("model", "constant")

        if model == "constant":
            price = self.initial_price

        elif model == "linear":
            elasticity = self.pricing_config.get("elasticity", 0.5)
            supply_ratio = circulating_supply / self.max_supply if self.max_supply > 0 else 0
            price = self.initial_price * (1 - elasticity * supply_ratio)
            price = max(0.01, price)

        elif model == "bonding_curve":
            elasticity = self.pricing_config.get("elasticity", 0.5)
            if circulating_supply == 0:
                price = self.initial_price * 10
            else:
                price = self.initial_price * (self.max_supply / circulating_supply) ** elasticity
                price = max(0.01, min(price, self.initial_price * 100))

        else:
            price = self.initial_price

        self._prices.append(price)
        return price

    def reset(self):
        """Reset for Monte Carlo trials."""
        self._prices = []


class TreasuryStrategyController:
    """
    Treasury management with deployment strategies.

    Handles:
    - Hold: Keep tokens in treasury
    - Liquidity: Deploy to DEX (counts as circulating)
    - Buyback: Remove from supply
    """

    def __init__(self, config: Dict, vesting_economy):
        """Initialize treasury controller."""
        self.config = config
        self.vesting_economy = vesting_economy
        self.treasury_config = config.get("tier2", {}).get("treasury", {})

        # Treasury holdings
        self.holdings = 0.0

        # Historical tracking
        self._holdings_store = []
        self._deployed_liquidity = []
        self._buyback_executed = []

    def add_tokens(self, amount: float):
        """Add tokens to treasury."""
        self.holdings += amount

    def deploy_strategy(self, month_index: int) -> Tuple[float, float, float]:
        """
        Execute treasury deployment strategy.

        Returns:
            (held_amount, liquidity_amount, buyback_amount)
        """
        if not self.treasury_config.get("enabled", False):
            return 0, 0, 0

        if self.holdings == 0:
            return 0, 0, 0

        hold_pct = self.treasury_config.get("hold_pct", 0.3)
        liquidity_pct = self.treasury_config.get("liquidity_pct", 0.5)
        buyback_pct = self.treasury_config.get("buyback_pct", 0.2)

        # Normalize if sum != 1.0
        total_pct = hold_pct + liquidity_pct + buyback_pct
        if total_pct > 0:
            hold_pct /= total_pct
            liquidity_pct /= total_pct
            buyback_pct /= total_pct

        # Deploy
        held = self.holdings * hold_pct
        liquidity = self.holdings * liquidity_pct
        buyback = self.holdings * buyback_pct

        # Execute buyback (removes from supply)
        if buyback > 0:
            self.vesting_economy.change_supply(-buyback)

        # Reset holdings after deployment
        self.holdings = 0

        # Track
        self._holdings_store.append(held)
        self._deployed_liquidity.append(liquidity)
        self._buyback_executed.append(buyback)

        return held, liquidity, buyback

    def reset(self):
        """Reset for Monte Carlo trials."""
        self.holdings = 0.0
        self._holdings_store = []
        self._deployed_liquidity = []
        self._buyback_executed = []


class DynamicVolumeCalculator:
    """
    Dynamic volume calculation based on circulating supply and liquidity.

    Volume = base_turnover * circulating * liquidity_multiplier
    """

    def __init__(self, config: Dict):
        """Initialize volume calculator."""
        self.config = config
        self.volume_config = config.get("tier2", {}).get("volume", {})

    def calculate_volume(self, circulating_supply: float, liquidity_deployed: float) -> float:
        """
        Calculate dynamic trading volume.

        Args:
            circulating_supply: Current circulating tokens
            liquidity_deployed: Liquidity from treasury

        Returns:
            Daily trading volume in tokens
        """
        if not self.volume_config.get("enabled", False):
            # Fall back to static volume
            return self.config["assumptions"].get("avg_daily_volume_tokens", 1_000_000) or 1_000_000

        # Base turnover rate (% of circulating traded daily)
        turnover_rate = self.volume_config.get("turnover_rate", 0.01)
        base_volume = circulating_supply * turnover_rate

        # Liquidity multiplier (more liquidity → more volume)
        if circulating_supply > 0 and liquidity_deployed > 0:
            liquidity_ratio = liquidity_deployed / circulating_supply
            liquidity_multiplier = (liquidity_ratio ** 0.5)
        else:
            liquidity_multiplier = 0.1

        volume = base_volume * max(0.1, liquidity_multiplier)
        return max(100_000, volume)


class MonteCarloRunner:
    """
    Monte Carlo simulation runner with parameter noise.

    Runs multiple trials with randomized parameters to generate
    uncertainty bands (P10, P50, P90).
    """

    def __init__(self, base_config: Dict, variance_level: float = 0.10):
        """
        Initialize Monte Carlo runner.

        Args:
            base_config: Base configuration
            variance_level: Noise level (0.10 = 10% variance)
        """
        self.base_config = base_config
        self.variance_level = variance_level

    def apply_noise(self, config: Dict, seed: int) -> Dict:
        """
        Apply parameter noise to configuration.

        Randomizes:
        - Cliff timing (±1-2 months)
        - TGE unlock % (±5%)
        - Vesting duration (±10%)
        - Sell pressure (±5%)
        """
        np.random.seed(seed)
        noisy_config = copy.deepcopy(config)

        for bucket in noisy_config["buckets"]:
            # Cliff timing noise
            cliff_noise = np.random.normal(0, 1.5 * self.variance_level)
            bucket["cliff_months"] = int(max(0, bucket["cliff_months"] + cliff_noise))

            # TGE unlock noise
            tge_noise = np.random.normal(0, 5 * self.variance_level)
            bucket["tge_unlock_pct"] = np.clip(
                bucket["tge_unlock_pct"] + tge_noise,
                0, 100
            )

            # Vesting duration noise
            vest_noise = np.random.normal(0, 2 * self.variance_level)
            bucket["vesting_months"] = int(max(0, bucket["vesting_months"] + vest_noise))

        # Sell pressure noise
        sell_pressure_map = {"low": 0.10, "medium": 0.25, "high": 0.50}
        base_sell = sell_pressure_map[noisy_config["assumptions"]["sell_pressure_level"]]
        sell_noise = np.random.normal(0, 0.05 * self.variance_level)
        noisy_sell = np.clip(base_sell + sell_noise, 0.05, 0.95)

        # Map back to level
        if noisy_sell < 0.175:
            noisy_config["assumptions"]["sell_pressure_level"] = "low"
        elif noisy_sell < 0.375:
            noisy_config["assumptions"]["sell_pressure_level"] = "medium"
        else:
            noisy_config["assumptions"]["sell_pressure_level"] = "high"

        return noisy_config

    def run(self, num_trials: int = 100, mode: str = "tier2") -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Run Monte Carlo simulation.

        Args:
            num_trials: Number of trials to run
            mode: Simulation mode (tier1, tier2, tier3)

        Returns:
            (df_stats, df_all_trials)
        """
        all_results = []

        for trial in range(num_trials):
            # Create noisy configuration
            noisy_config = self.apply_noise(self.base_config, trial)

            # Run simulation
            simulator = VestingSimulatorAdvanced(noisy_config, mode=mode)
            _, df_global = simulator.run_simulation()

            # Tag with trial number
            df_global["trial"] = trial
            all_results.append(df_global)

        # Combine all trials
        df_combined = pd.concat(all_results, ignore_index=True)

        # Calculate statistics per month
        quantile_10 = lambda x: x.quantile(0.10)
        quantile_90 = lambda x: x.quantile(0.90)

        df_stats = df_combined.groupby("month_index").agg({
            "total_unlocked": [quantile_10, "median", quantile_90, "mean", "std"],
            "total_expected_sell": [quantile_10, "median", quantile_90, "mean", "std"],
            "expected_circulating_total": [quantile_10, "median", quantile_90, "mean", "std"],
            "expected_circulating_pct": [quantile_10, "median", quantile_90, "mean", "std"],
        })

        # Flatten column names
        df_stats.columns = ["_".join(col).strip() for col in df_stats.columns.values]
        df_stats = df_stats.reset_index()

        return df_stats, df_combined


class CohortBehaviorController:
    """
    Cohort-based behavior modeling.

    Different buckets have different behavior profiles:
    - Team: High stake, low sell
    - VCs: High sell, low stake
    - Community: Medium stake, medium sell
    """

    BEHAVIOR_PROFILES = {
        "high_stake": {
            "stake_pct": 0.70,
            "sell_pct": 0.30,
            "description": "Team, long-term holders"
        },
        "high_sell": {
            "stake_pct": 0.10,
            "sell_pct": 0.90,
            "description": "VCs, short-term holders"
        },
        "balanced": {
            "stake_pct": 0.40,
            "sell_pct": 0.60,
            "description": "Community, balanced"
        },
        "treasury": {
            "stake_pct": 0.00,
            "sell_pct": 0.00,
            "description": "Treasury (handled separately)"
        }
    }

    def __init__(self, config: Dict):
        """Initialize cohort behavior controller."""
        self.config = config
        self.cohort_config = config.get("tier3", {}).get("cohorts", {})

        # Bucket -> profile mapping
        self.bucket_profiles = self.cohort_config.get("bucket_profiles", {})

    def get_behavior_multiplier(self, bucket_name: str) -> float:
        """
        Get sell pressure multiplier for bucket based on cohort profile.

        Returns:
            Multiplier to apply to base sell pressure
        """
        if not self.cohort_config.get("enabled", False):
            return 1.0

        profile_name = self.bucket_profiles.get(bucket_name, "balanced")
        profile = self.BEHAVIOR_PROFILES.get(profile_name, self.BEHAVIOR_PROFILES["balanced"])

        # Convert sell_pct to multiplier
        # If profile says 90% sell and base is 25%, multiplier = 90/25 = 3.6
        base_sell = SELL_PRESSURE_LEVELS[self.config["assumptions"]["sell_pressure_level"]]
        target_sell = profile["sell_pct"]

        multiplier = target_sell / base_sell if base_sell > 0 else 1.0
        return multiplier


# =============================================================================
# EXTENDED VESTING SIMULATOR (TIER 2/3)
# =============================================================================

class VestingSimulatorAdvanced(VestingSimulator):
    """
    Extended vesting simulator with Tier 2 and Tier 3 features.

    Tier 2:
    - Dynamic staking with APY and capacity
    - Price-supply feedback via bonding curves
    - Treasury strategies (hold/liquidity/buyback)
    - Dynamic volume calculation

    Tier 3:
    - Monte Carlo uncertainty analysis
    - Cohort-based behaviors
    """

    def __init__(self, config: Dict, mode: str = "tier1"):
        """
        Initialize advanced vesting simulator.

        Args:
            config: Configuration dictionary
            mode: "tier1", "tier2", or "tier3"
        """
        super().__init__(config, mode)

        # Initialize Tier 2/3 components
        self.vesting_economy = None
        self.staking_controller = None
        self.pricing_controller = None
        self.treasury_controller = None
        self.volume_calculator = None
        self.cohort_controller = None

        if mode in ["tier2", "tier3"]:
            self._initialize_advanced_components()

    def _initialize_advanced_components(self):
        """Initialize Tier 2/3 components."""
        # Create vesting economy wrapper
        self.vesting_economy = VestingTokenEconomy(self.config)

        # Tier 2 components
        self.staking_controller = DynamicStakingController(self.config, self.vesting_economy)
        self.pricing_controller = DynamicPricingController(self.config, self.vesting_economy)
        self.treasury_controller = TreasuryStrategyController(self.config, self.vesting_economy)
        self.volume_calculator = DynamicVolumeCalculator(self.config)

        # Tier 3 components
        if self.mode == "tier3":
            self.cohort_controller = CohortBehaviorController(self.config)

    def run_simulation(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Run advanced vesting simulation with Tier 2/3 features.

        Returns:
            (df_bucket, df_global) - per-bucket and aggregate dataframes
        """
        if self.mode == "tier1":
            # Use parent Tier 1 implementation
            return super().run_simulation()

        # Initialize bucket controllers
        bucket_controllers = []
        for bucket_cfg in self.config["buckets"]:
            controller = VestingBucketController(bucket_cfg, self.config)
            bucket_controllers.append(controller)

        # Generate price series (if not using dynamic pricing)
        price_series = self._generate_price_series() if not self.pricing_controller.pricing_config.get("enabled", False) else None

        # Simulation loop
        bucket_rows = []
        global_rows = []

        for month_index in range(self.horizon + 1):
            month_date = self.start_date + relativedelta(months=month_index)

            # Month start: check for matured stakes
            matured_stake = 0.0
            if self.staking_controller:
                matured_stake = self.staking_controller.get_matured_stake(month_index)

            # Process each bucket
            month_total_unlocked = matured_stake
            month_total_sell = 0.0
            liquidity_deployed = 0.0

            for controller in bucket_controllers:
                bucket_name = controller.bucket_name

                # Get price (dynamic or from series)
                if self.pricing_controller and self.pricing_controller.pricing_config.get("enabled", False):
                    current_price = self.pricing_controller.calculate_price(self.vesting_economy.circulating_supply)
                    self.vesting_economy.update_price(current_price)
                else:
                    current_price = price_series[month_index] if price_series else self.initial_price

                # Execute bucket vesting
                unlocked = controller.execute(month_index, current_price, self.initial_price)

                # Apply cohort behavior multiplier (Tier 3)
                sell_multiplier = 1.0
                if self.cohort_controller:
                    sell_multiplier = self.cohort_controller.get_behavior_multiplier(bucket_name)

                # Handle treasury bucket specially
                if bucket_name.lower() == "treasury" and self.treasury_controller:
                    self.treasury_controller.add_tokens(unlocked)
                    held, liquidity, buyback = self.treasury_controller.deploy_strategy(month_index)
                    liquidity_deployed += liquidity
                    expected_sell = 0.0  # Treasury doesn't sell directly
                else:
                    # Apply staking (Tier 2)
                    if self.staking_controller and month_index > 0:
                        free_amount, staked_amount = self.staking_controller.apply_staking(unlocked, month_index)
                    else:
                        free_amount = unlocked
                        staked_amount = 0.0

                    # Calculate expected sell with cohort multiplier
                    base_sell_pressure = controller.sell_pressure
                    adjusted_sell_pressure = min(1.0, base_sell_pressure * sell_multiplier)
                    expected_sell = free_amount * adjusted_sell_pressure

                month_total_unlocked += unlocked
                month_total_sell += expected_sell

                # Get bucket state
                hist = controller.get_history()
                unlocked_cumulative = hist["unlocked_cumulative"][-1]
                locked_remaining = hist["locked_remaining"][-1]

                # Store bucket row
                bucket_rows.append({
                    "month_index": month_index,
                    "date": month_date.strftime("%Y-%m-%d"),
                    "bucket": bucket_name,
                    "allocation": controller.allocation,
                    "unlocked_this_month": unlocked,
                    "unlocked_cumulative": unlocked_cumulative,
                    "locked_remaining": locked_remaining,
                    "sell_pressure": controller.sell_pressure,
                    "expected_sell": expected_sell,
                    "expected_circulating_cumulative": unlocked_cumulative
                })

            # Update global circulating supply
            new_circulating = self.expected_circulating + month_total_unlocked
            if self.treasury_controller:
                new_circulating += liquidity_deployed  # Liquidity counts as circulating

            self.expected_circulating = new_circulating
            self.vesting_economy.update_circulating(new_circulating)

            # Calculate dynamic volume (Tier 2)
            if self.volume_calculator:
                avg_daily_volume = self.volume_calculator.calculate_volume(
                    new_circulating, liquidity_deployed
                )
            else:
                avg_daily_volume = self.config["assumptions"].get("avg_daily_volume_tokens", 1_000_000) or 1_000_000

            # Store global row
            circulating_pct = (new_circulating / self.total_supply * 100) if self.total_supply > 0 else 0
            sell_volume_ratio = (month_total_sell / avg_daily_volume) if avg_daily_volume > 0 else 0

            global_rows.append({
                "month_index": month_index,
                "date": month_date.strftime("%Y-%m-%d"),
                "total_unlocked": month_total_unlocked,
                "total_expected_sell": month_total_sell,
                "expected_circulating_total": new_circulating,
                "expected_circulating_pct": circulating_pct,
                "sell_volume_ratio": sell_volume_ratio,
                "current_price": self.vesting_economy.price if self.vesting_economy else self.initial_price,
                "liquidity_deployed": liquidity_deployed
            })

            # Advance economy iteration
            if self.vesting_economy:
                self.vesting_economy.advance_iteration()

        # Convert to DataFrames
        df_bucket = pd.DataFrame(bucket_rows)
        df_global = pd.DataFrame(global_rows)

        # Store results
        self.df_bucket = df_bucket
        self.df_global = df_global

        return df_bucket, df_global

    def make_charts(self) -> List:
        """
        Generate charts with Tier 2/3 enhancements.

        Adds:
        - Price evolution chart (if dynamic pricing)
        - Staking capacity chart (if dynamic staking)
        """
        if self.df_bucket is None or self.df_global is None:
            raise ValueError("No simulation results. Call run_simulation() first.")

        # Call parent method for base charts
        base_charts = super().make_charts()

        # Add Tier 2/3 specific charts
        if self.mode in ["tier2", "tier3"]:
            # Chart 4: Price Evolution (if dynamic pricing)
            if self.pricing_controller and self.pricing_controller.pricing_config.get("enabled", False):
                fig4 = self._make_price_chart()
                base_charts.append(fig4)

            # Chart 5: Staking Dynamics (if dynamic staking)
            if self.staking_controller and self.staking_controller.staking_config.get("enabled", False):
                fig5 = self._make_staking_chart()
                base_charts.append(fig5)

        return base_charts

    def _make_price_chart(self):
        """Generate price evolution chart."""
        fig, ax = plt.subplots(figsize=(12, 5))

        ax.plot(
            self.df_global["month_index"],
            self.df_global["current_price"],
            marker="o",
            linewidth=2,
            color="#2E86AB"
        )

        ax.set_xlabel("Month", fontsize=12)
        ax.set_ylabel("Price ($)", fontsize=12)
        ax.set_title("Price Evolution (Dynamic Pricing)", fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)

        return fig

    def _make_staking_chart(self):
        """Generate staking dynamics chart."""
        fig, ax = plt.subplots(figsize=(12, 5))

        # Calculate staking metrics from history
        staked_amounts = self.staking_controller._staked_this_month
        participation_rates = self.staking_controller._participation_rate

        months = range(len(staked_amounts))

        ax2 = ax.twinx()

        # Bar: Staked amounts
        ax.bar(months, staked_amounts, alpha=0.6, color="#06A77D", label="Staked Amount")

        # Line: Participation rate
        ax2.plot(months, [r * 100 for r in participation_rates], marker="o",
                 linewidth=2, color="#D90368", label="Participation Rate")

        ax.set_xlabel("Month", fontsize=12)
        ax.set_ylabel("Tokens Staked", fontsize=12, color="#06A77D")
        ax2.set_ylabel("Participation Rate (%)", fontsize=12, color="#D90368")
        ax.set_title("Staking Dynamics", fontsize=14, fontweight="bold")

        ax.tick_params(axis='y', labelcolor="#06A77D")
        ax2.tick_params(axis='y', labelcolor="#D90368")

        ax.grid(True, alpha=0.3)

        # Legends
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

        return fig

    def run_monte_carlo(self, num_trials: int = 100) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Run Monte Carlo simulation (Tier 3).

        Args:
            num_trials: Number of trials

        Returns:
            (df_stats, df_all_trials)
        """
        if self.mode != "tier3":
            raise ValueError("Monte Carlo requires mode='tier3'")

        runner = MonteCarloRunner(self.config, variance_level=0.10)
        return runner.run(num_trials, mode="tier3")

    def export_csvs(self, output_dir: str = "./output") -> Tuple[str, str]:
        """Export results with Tier 2/3 columns."""
        return super().export_csvs(output_dir)

    def export_pdf(self, output_path: str = "./vesting_report.pdf") -> str:
        """Export PDF report with Tier 2/3 charts."""
        return super().export_pdf(output_path)
