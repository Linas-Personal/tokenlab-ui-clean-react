"""
TokenLab Vesting & Allocation Simulator - Gradio UI

A comprehensive web interface for analyzing token vesting schedules and sell pressure.

Usage:
    python apps/vesting_gradio_app.py

Then open http://localhost:7860 in your browser.
"""

import json
import tempfile
import os
from datetime import datetime
from typing import List, Tuple, Optional

import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt

from tokenlab_abm.analytics.vesting_simulator import (
    VestingSimulator,
    VestingSimulatorAdvanced,
    validate_config
)


# =============================================================================
# DEFAULT TEMPLATES
# =============================================================================

DEFAULT_TEMPLATE = [
    ["Team", 20, 0, 12, 36],
    ["Seed", 10, 10, 6, 18],
    ["Private", 15, 15, 3, 12],
    ["Treasury", 30, 0, 0, 48],
    ["Liquidity", 25, 100, 0, 0]
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_config_from_ui(
    # Token setup
    token_name: str,
    total_supply: float,
    start_date: str,
    horizon_months: int,
    allocation_mode: str,
    simulation_mode: str,
    # Vesting table
    vesting_table: pd.DataFrame,
    # Assumptions
    sell_pressure: str,
    avg_daily_volume: Optional[float],
    # Cliff shock
    cliff_shock_enabled: bool,
    cliff_shock_multiplier: float,
    cliff_shock_buckets: str,
    # Price trigger
    price_trigger_enabled: bool,
    price_source: str,
    price_scenario: str,
    take_profit: float,
    stop_loss: float,
    extra_sell: float,
    # Relock
    relock_enabled: bool,
    relock_pct: float,
    lock_duration: int,
    # Tier 2: Staking
    tier2_staking_enabled: bool,
    tier2_staking_apy: float,
    tier2_staking_capacity: float,
    tier2_staking_lockup: int,
    tier2_staking_rewards: bool,
    # Tier 2: Pricing
    tier2_pricing_enabled: bool,
    tier2_pricing_model: str,
    tier2_pricing_initial: float,
    tier2_pricing_elasticity: float,
    # Tier 2: Treasury
    tier2_treasury_enabled: bool,
    tier2_treasury_hold: float,
    tier2_treasury_liquidity: float,
    tier2_treasury_buyback: float,
    # Tier 2: Volume
    tier2_volume_enabled: bool,
    tier2_volume_turnover: float,
    # Tier 3: Cohorts
    tier3_cohorts_enabled: bool,
    tier3_cohort_profiles: str,
    # Tier 3: Monte Carlo
    tier3_mc_enabled: bool,
    tier3_mc_trials: int,
    tier3_mc_variance: float
) -> dict:
    """Create configuration dictionary from UI inputs."""

    # Parse sell pressure level
    sell_pressure_level = sell_pressure.lower().split("(")[0].strip()

    # Parse vesting table
    buckets = []
    for _, row in vesting_table.iterrows():
        if pd.isna(row.iloc[0]) or row.iloc[0] == "":
            continue  # Skip empty rows

        bucket = {
            "bucket": str(row.iloc[0]),
            "allocation": float(row.iloc[1]) if not pd.isna(row.iloc[1]) else 0,
            "tge_unlock_pct": float(row.iloc[2]) if not pd.isna(row.iloc[2]) else 0,
            "cliff_months": int(row.iloc[3]) if not pd.isna(row.iloc[3]) else 0,
            "vesting_months": int(row.iloc[4]) if not pd.isna(row.iloc[4]) else 0,
            "unlock_type": "linear"
        }
        buckets.append(bucket)

    # Parse cliff shock buckets (comma-separated string)
    cliff_shock_bucket_list = []
    if cliff_shock_buckets and cliff_shock_buckets.strip():
        cliff_shock_bucket_list = [b.strip() for b in cliff_shock_buckets.split(",")]

    config = {
        "token": {
            "name": token_name,
            "total_supply": int(total_supply),
            "start_date": start_date,
            "horizon_months": int(horizon_months),
            "allocation_mode": allocation_mode.lower(),
            "simulation_mode": simulation_mode.lower()
        },
        "assumptions": {
            "sell_pressure_level": sell_pressure_level,
            "avg_daily_volume_tokens": float(avg_daily_volume) if avg_daily_volume else None
        },
        "behaviors": {
            "cliff_shock": {
                "enabled": cliff_shock_enabled,
                "multiplier": float(cliff_shock_multiplier),
                "buckets": cliff_shock_bucket_list
            },
            "price_trigger": {
                "enabled": price_trigger_enabled,
                "source": price_source.lower(),
                "scenario": price_scenario.lower() if price_scenario else None,
                "take_profit": float(take_profit),
                "stop_loss": float(stop_loss),
                "extra_sell_addon": float(extra_sell),
                "uploaded_price_series": None
            },
            "relock": {
                "enabled": relock_enabled,
                "relock_pct": float(relock_pct),
                "lock_duration_months": int(lock_duration)
            }
        },
        "buckets": buckets
    }

    # Add Tier 2 configuration
    if simulation_mode and str(simulation_mode).lower() in ["tier2", "tier3"]:
        # Parse cohort profiles (bucket:profile,bucket:profile)
        cohort_profile_dict = {}
        if tier3_cohort_profiles and str(tier3_cohort_profiles).strip():
            for pair in tier3_cohort_profiles.split(","):
                if ":" in pair:
                    bucket, profile = pair.split(":", 1)
                    cohort_profile_dict[bucket.strip()] = profile.strip()

        config["tier2"] = {
            "staking": {
                "enabled": tier2_staking_enabled,
                "apy": float(tier2_staking_apy),
                "capacity": float(tier2_staking_capacity),
                "lockup": int(tier2_staking_lockup),
                "include_rewards": tier2_staking_rewards
            },
            "pricing": {
                "enabled": tier2_pricing_enabled,
                "model": str(tier2_pricing_model).lower() if tier2_pricing_model else "constant",
                "initial_price": float(tier2_pricing_initial) if tier2_pricing_initial else 1.0,
                "elasticity": float(tier2_pricing_elasticity) if tier2_pricing_elasticity else 0.5
            },
            "treasury": {
                "enabled": tier2_treasury_enabled,
                "hold_pct": float(tier2_treasury_hold),
                "liquidity_pct": float(tier2_treasury_liquidity),
                "buyback_pct": float(tier2_treasury_buyback)
            },
            "volume": {
                "enabled": tier2_volume_enabled,
                "turnover_rate": float(tier2_volume_turnover)
            }
        }

    # Add Tier 3 configuration
    if simulation_mode and str(simulation_mode).lower() == "tier3":
        config["tier3"] = {
            "cohorts": {
                "enabled": tier3_cohorts_enabled,
                "bucket_profiles": cohort_profile_dict
            },
            "monte_carlo": {
                "enabled": tier3_mc_enabled,
                "num_trials": int(tier3_mc_trials),
                "variance_level": float(tier3_mc_variance)
            }
        }

    return config


def run_simulation_from_ui(*args) -> Tuple:
    """Run simulation from UI inputs and return results."""

    try:
        # Create config from UI inputs
        try:
            config = create_config_from_ui(*args)
        except Exception as e:
            raise ValueError(f"Config creation failed: {str(e)}")

        # Validate config
        warnings = validate_config(config)
        warning_text = ""
        if warnings:
            warning_text = "⚠️ Warnings:\n" + "\n".join(f"• {w}" for w in warnings)

        # Run simulation with appropriate simulator
        mode = config["token"].get("simulation_mode", "tier1")
        if isinstance(mode, str):
            mode = mode.lower()

        try:
            if mode in ["tier2", "tier3"]:
                simulator = VestingSimulatorAdvanced(config, mode=mode)
            else:
                simulator = VestingSimulator(config, mode="tier1")
        except Exception as e:
            raise ValueError(f"Simulator initialization failed: {str(e)}")

        try:
            df_bucket, df_global = simulator.run_simulation()
        except Exception as e:
            raise ValueError(f"Simulation execution failed: {str(e)}")

        # Generate charts
        try:
            figs = simulator.make_charts(df_bucket, df_global)
        except Exception as e:
            raise ValueError(f"Chart generation failed: {str(e)}")

        # Generate summary cards
        cards = simulator.summary_cards

        # Format summary cards as markdown
        card1_text = f"""**Max Monthly Unlock**
{cards['max_unlock_tokens']:,.0f} tokens
Month {cards['max_unlock_month']}"""

        card2_text = f"""**Max Monthly Sell**
{cards['max_sell_tokens']:,.0f} tokens
Month {cards['max_sell_month']}"""

        circ_12 = f"{cards['circ_12_pct']:.1f}%" if cards['circ_12_pct'] is not None else "N/A"
        circ_24 = f"{cards['circ_24_pct']:.1f}%" if cards['circ_24_pct'] is not None else "N/A"
        card3_text = f"""**Circulating Supply**
Month 12: {circ_12}
Month 24: {circ_24}
End: {cards['circ_end_pct']:.1f}%"""

        # Export CSVs to temp directory
        temp_dir = tempfile.mkdtemp()
        csv1_path, csv2_path = simulator.export_csvs(temp_dir)

        # Export PDF
        pdf_path = os.path.join(temp_dir, "vesting_report.pdf")
        simulator.export_pdf(pdf_path)

        # Export config JSON
        json_path = os.path.join(temp_dir, "config.json")
        with open(json_path, "w") as f:
            f.write(simulator.to_json())

        return (
            warning_text,
            figs[0], figs[1], figs[2],
            card1_text, card2_text, card3_text,
            csv1_path, csv2_path, pdf_path, json_path,
            gr.update(visible=True)  # Show results section
        )

    except Exception as e:
        error_text = f"❌ Error: {str(e)}"
        return (
            error_text,
            None, None, None,
            "Error", "Error", "Error",
            None, None, None, None,
            gr.update(visible=False)
        )


def load_template() -> pd.DataFrame:
    """Load default vesting template."""
    return pd.DataFrame(
        DEFAULT_TEMPLATE,
        columns=["Bucket", "Allocation", "TGE %", "Cliff (mo)", "Vesting (mo)"]
    )


def add_row(current_table: pd.DataFrame) -> pd.DataFrame:
    """Add empty row to vesting table."""
    new_row = pd.DataFrame([["", 0, 0, 0, 0]], columns=current_table.columns)
    return pd.concat([current_table, new_row], ignore_index=True)


def clear_table() -> pd.DataFrame:
    """Clear vesting table."""
    return pd.DataFrame(columns=["Bucket", "Allocation", "TGE %", "Cliff (mo)", "Vesting (mo)"])


def import_config(file) -> Tuple:
    """Import configuration from JSON file."""
    if file is None:
        return tuple([gr.update()] * 20)  # No changes

    try:
        with open(file.name, "r") as f:
            config = json.load(f)

        # Extract token setup
        token_name = config["token"].get("name", "TokenA")
        total_supply = config["token"]["total_supply"]
        start_date = config["token"]["start_date"]
        horizon_months = config["token"]["horizon_months"]
        allocation_mode = config["token"]["allocation_mode"].capitalize()

        # Extract vesting table
        buckets = config["buckets"]
        vesting_data = []
        for bucket in buckets:
            vesting_data.append([
                bucket["bucket"],
                bucket["allocation"],
                bucket["tge_unlock_pct"],
                bucket["cliff_months"],
                bucket["vesting_months"]
            ])
        vesting_table = pd.DataFrame(
            vesting_data,
            columns=["Bucket", "Allocation", "TGE %", "Cliff (mo)", "Vesting (mo)"]
        )

        # Extract assumptions
        sell_pressure_map = {"low": "Low (10%)", "medium": "Medium (25%)", "high": "High (50%)"}
        sell_pressure = sell_pressure_map.get(config["assumptions"]["sell_pressure_level"], "Medium (25%)")
        avg_daily_volume = config["assumptions"]["avg_daily_volume_tokens"]

        # Extract behaviors
        cliff_shock = config["behaviors"].get("cliff_shock", {})
        cliff_shock_enabled = cliff_shock.get("enabled", False)
        cliff_shock_multiplier = cliff_shock.get("multiplier", 3.0)
        cliff_shock_buckets = ", ".join(cliff_shock.get("buckets", []))

        price_trigger = config["behaviors"].get("price_trigger", {})
        price_trigger_enabled = price_trigger.get("enabled", False)
        price_source = price_trigger.get("source", "flat").capitalize()
        price_scenario = price_trigger.get("scenario", "uptrend")
        if price_scenario:
            price_scenario = price_scenario.capitalize()
        take_profit = price_trigger.get("take_profit", 0.5)
        stop_loss = price_trigger.get("stop_loss", -0.3)
        extra_sell = price_trigger.get("extra_sell_addon", 0.2)

        relock = config["behaviors"].get("relock", {})
        relock_enabled = relock.get("enabled", False)
        relock_pct = relock.get("relock_pct", 0.3)
        lock_duration = relock.get("lock_duration_months", 6)

        return (
            token_name, total_supply, start_date, horizon_months, allocation_mode,
            vesting_table,
            sell_pressure, avg_daily_volume,
            cliff_shock_enabled, cliff_shock_multiplier, cliff_shock_buckets,
            price_trigger_enabled, price_source, price_scenario, take_profit, stop_loss, extra_sell,
            relock_enabled, relock_pct, lock_duration
        )

    except Exception as e:
        gr.Warning(f"Failed to import config: {str(e)}")
        return tuple([gr.update()] * 20)


# =============================================================================
# GRADIO UI
# =============================================================================

def create_ui():
    """Create Gradio UI."""

    with gr.Blocks(title="TokenLab Vesting Simulator") as app:
        gr.Markdown("""
        # 🪙 TokenLab Vesting & Allocation Simulator

        Analyze token vesting schedules and expected sell pressure with deterministic modeling.
        """)

        # =====================================================================
        # TAB A: TOKEN SETUP
        # =====================================================================

        with gr.Tab("📊 Token Setup"):
            with gr.Row():
                with gr.Column():
                    token_name = gr.Textbox(
                        label="Token Name",
                        value="TokenA",
                        placeholder="e.g., TokenA"
                    )
                    total_supply = gr.Number(
                        label="Total Supply",
                        value=1_000_000_000,
                        precision=0
                    )

                with gr.Column():
                    start_date = gr.Textbox(
                        label="TGE / Start Date (YYYY-MM-DD)",
                        value="2026-01-01"
                    )
                    horizon_months = gr.Dropdown(
                        label="Simulation Horizon (months)",
                        choices=[12, 24, 36, 48, 60],
                        value=36
                    )

            allocation_mode = gr.Radio(
                label="Allocation Mode",
                choices=["Percent", "Tokens"],
                value="Percent"
            )

            gr.Markdown("---")
            simulation_mode = gr.Radio(
                label="Simulation Mode",
                choices=["Tier1", "Tier2", "Tier3"],
                value="Tier1",
                info="Tier1: Deterministic | Tier2: Dynamic TokenLab | Tier3: Monte Carlo + Cohorts"
            )

        # =====================================================================
        # TAB B: VESTING TABLE
        # =====================================================================

        with gr.Tab("📅 Vesting Schedule"):
            gr.Markdown("""
            Define vesting schedules for each allocation bucket.

            - **Bucket**: Name of allocation (Team, Investors, etc.)
            - **Allocation**: Amount in % or tokens (based on Allocation Mode)
            - **TGE %**: Percentage unlocked at TGE (0-100)
            - **Cliff (mo)**: Months before vesting starts
            - **Vesting (mo)**: Linear vesting duration after cliff
            """)

            vesting_table = gr.Dataframe(
                value=load_template(),
                headers=["Bucket", "Allocation", "TGE %", "Cliff (mo)", "Vesting (mo)"],
                datatype=["str", "number", "number", "number", "number"],
                row_count="dynamic",
                column_count=(5, "fixed"),
                interactive=True,
                wrap=True
            )

            with gr.Row():
                load_template_btn = gr.Button("📋 Load Template", variant="secondary")
                add_row_btn = gr.Button("➕ Add Row", variant="secondary")
                clear_btn = gr.Button("🗑️ Clear Table", variant="secondary")

            # Button actions
            load_template_btn.click(fn=load_template, outputs=[vesting_table])
            add_row_btn.click(fn=add_row, inputs=[vesting_table], outputs=[vesting_table])
            clear_btn.click(fn=clear_table, outputs=[vesting_table])

        # =====================================================================
        # TAB C: ASSUMPTIONS & BEHAVIORS
        # =====================================================================

        with gr.Tab("⚙️ Assumptions & Behaviors"):
            gr.Markdown("### Base Assumptions")

            with gr.Row():
                sell_pressure = gr.Dropdown(
                    label="Sell Pressure Level",
                    choices=["Low (10%)", "Medium (25%)", "High (50%)"],
                    value="Medium (25%)",
                    info="Percentage of unlocked tokens expected to be sold"
                )
                avg_daily_volume = gr.Number(
                    label="Avg Daily Volume (optional)",
                    value=None,
                    precision=0,
                    info="Average daily trading volume in tokens"
                )

            gr.Markdown("---")
            gr.Markdown("### Behavioral Modifiers")

            # Cliff Shock
            with gr.Accordion("🔥 Cliff Shock", open=False):
                gr.Markdown("""
                Stress-test first unlock after cliff with increased sell pressure.
                """)
                cliff_shock_enabled = gr.Checkbox(label="Enable Cliff Shock", value=False)
                with gr.Row():
                    cliff_shock_multiplier = gr.Slider(
                        label="Sell Pressure Multiplier",
                        minimum=1.0,
                        maximum=5.0,
                        value=3.0,
                        step=0.1
                    )
                    cliff_shock_buckets = gr.Textbox(
                        label="Apply to Buckets (comma-separated)",
                        placeholder="e.g., Team, Seed",
                        value=""
                    )

            # Price Trigger
            with gr.Accordion("📈 Price-Triggered Selling", open=False):
                gr.Markdown("""
                Model stop-loss / take-profit behavior based on price movements.
                """)
                price_trigger_enabled = gr.Checkbox(label="Enable Price Triggers", value=False)
                price_source = gr.Radio(
                    label="Price Source",
                    choices=["Flat", "Scenario"],
                    value="Flat"
                )
                price_scenario = gr.Radio(
                    label="Price Scenario (if enabled)",
                    choices=["Uptrend", "Downtrend", "Volatile"],
                    value="Uptrend",
                    visible=False
                )
                with gr.Row():
                    take_profit = gr.Slider(
                        label="Take-Profit Threshold",
                        minimum=0.1,
                        maximum=2.0,
                        value=0.5,
                        step=0.1,
                        info="Trigger at +X% vs TGE price"
                    )
                    stop_loss = gr.Slider(
                        label="Stop-Loss Threshold",
                        minimum=-0.9,
                        maximum=-0.1,
                        value=-0.3,
                        step=0.1,
                        info="Trigger at -X% vs TGE price"
                    )
                extra_sell = gr.Slider(
                    label="Extra Sell Pressure Add-On",
                    minimum=0.0,
                    maximum=0.5,
                    value=0.2,
                    step=0.05,
                    info="Additional sell % when triggered"
                )

                # Show scenario selector when source is "Scenario"
                price_source.change(
                    fn=lambda x: gr.update(visible=(x == "Scenario")),
                    inputs=[price_source],
                    outputs=[price_scenario]
                )

            # Relock / Staking
            with gr.Accordion("🔒 Relock / Staking Delay", open=False):
                gr.Markdown("""
                Simulate tokens being relocked or staked, delaying market impact.
                """)
                relock_enabled = gr.Checkbox(label="Enable Relock", value=False)
                with gr.Row():
                    relock_pct = gr.Slider(
                        label="Relock Percentage",
                        minimum=0.0,
                        maximum=1.0,
                        value=0.3,
                        step=0.05,
                        info="% of unlocked tokens relocked"
                    )
                    lock_duration = gr.Dropdown(
                        label="Lock Duration (months)",
                        choices=[3, 6, 12],
                        value=6
                    )

        # =====================================================================
        # TAB D: TIER 2/3 ADVANCED CONFIGURATION
        # =====================================================================

        with gr.Tab("🚀 Advanced (Tier 2/3)"):
            gr.Markdown("""
            ### Tier 2/3 Advanced Features

            **Tier 2** adds dynamic TokenLab integration:
            - Dynamic staking with APY incentives
            - Price-supply feedback via bonding curves
            - Treasury strategies (hold/liquidity/buyback)
            - Dynamic volume calculation

            **Tier 3** adds uncertainty analysis:
            - Monte Carlo simulation with parameter noise
            - Cohort-based behavior modeling
            """)

            # Tier 2: Staking
            with gr.Accordion("💰 Dynamic Staking (Tier 2)", open=False):
                gr.Markdown("""
                Replace simple relock with APY-based staking model.
                """)
                tier2_staking_enabled = gr.Checkbox(label="Enable Dynamic Staking", value=False)
                with gr.Row():
                    tier2_staking_apy = gr.Slider(
                        label="Staking APY",
                        minimum=0.0,
                        maximum=0.50,
                        value=0.15,
                        step=0.01,
                        info="Annual percentage yield for staking"
                    )
                    tier2_staking_capacity = gr.Slider(
                        label="Capacity (% of Circulating)",
                        minimum=0.0,
                        maximum=1.0,
                        value=0.60,
                        step=0.05,
                        info="Max % of circulating that can stake"
                    )
                with gr.Row():
                    tier2_staking_lockup = gr.Dropdown(
                        label="Lockup Duration (months)",
                        choices=[3, 6, 12, 24],
                        value=6
                    )
                    tier2_staking_rewards = gr.Checkbox(
                        label="Include Staking Rewards",
                        value=True,
                        info="Generate yield (increases supply)"
                    )

            # Tier 2: Pricing
            with gr.Accordion("📈 Dynamic Pricing (Tier 2)", open=False):
                gr.Markdown("""
                Price responds to circulating supply changes.
                """)
                tier2_pricing_enabled = gr.Checkbox(label="Enable Dynamic Pricing", value=False)
                with gr.Row():
                    tier2_pricing_model = gr.Radio(
                        label="Pricing Model",
                        choices=["Constant", "Linear", "Bonding_Curve"],
                        value="Bonding_Curve"
                    )
                    tier2_pricing_initial = gr.Number(
                        label="Initial Price ($)",
                        value=1.0,
                        precision=2
                    )
                tier2_pricing_elasticity = gr.Slider(
                    label="Price Elasticity",
                    minimum=0.0,
                    maximum=1.0,
                    value=0.5,
                    step=0.05,
                    info="Sensitivity to supply changes"
                )

            # Tier 2: Treasury
            with gr.Accordion("🏦 Treasury Strategies (Tier 2)", open=False):
                gr.Markdown("""
                Treasury deployment: hold, provide liquidity, or buyback.
                """)
                tier2_treasury_enabled = gr.Checkbox(label="Enable Treasury Management", value=False)
                with gr.Row():
                    tier2_treasury_hold = gr.Slider(
                        label="Hold %",
                        minimum=0.0,
                        maximum=1.0,
                        value=0.3,
                        step=0.05
                    )
                    tier2_treasury_liquidity = gr.Slider(
                        label="Liquidity %",
                        minimum=0.0,
                        maximum=1.0,
                        value=0.5,
                        step=0.05
                    )
                    tier2_treasury_buyback = gr.Slider(
                        label="Buyback %",
                        minimum=0.0,
                        maximum=1.0,
                        value=0.2,
                        step=0.05
                    )

            # Tier 2: Volume
            with gr.Accordion("📊 Dynamic Volume (Tier 2)", open=False):
                gr.Markdown("""
                Calculate trading volume based on circulating supply and liquidity.
                """)
                tier2_volume_enabled = gr.Checkbox(label="Enable Dynamic Volume", value=False)
                tier2_volume_turnover = gr.Slider(
                    label="Daily Turnover Rate",
                    minimum=0.001,
                    maximum=0.10,
                    value=0.01,
                    step=0.001,
                    info="% of circulating traded daily"
                )

            gr.Markdown("---")
            gr.Markdown("### Tier 3: Uncertainty Analysis")

            # Tier 3: Cohorts
            with gr.Accordion("👥 Cohort Behaviors (Tier 3)", open=False):
                gr.Markdown("""
                Different buckets have different behavior profiles.

                **Profiles:**
                - `high_stake`: Team, long-term holders (70% stake, 30% sell)
                - `high_sell`: VCs, short-term holders (10% stake, 90% sell)
                - `balanced`: Community (40% stake, 60% sell)
                - `treasury`: Treasury (handled separately)
                """)
                tier3_cohorts_enabled = gr.Checkbox(label="Enable Cohort Behaviors", value=False)
                tier3_cohort_profiles = gr.Textbox(
                    label="Bucket Profiles (bucket:profile,bucket:profile)",
                    placeholder="e.g., Team:high_stake,Seed:high_sell,Private:high_sell",
                    value="",
                    info="Map buckets to behavior profiles"
                )

            # Tier 3: Monte Carlo
            with gr.Accordion("🎲 Monte Carlo Simulation (Tier 3)", open=False):
                gr.Markdown("""
                Run multiple trials with parameter noise to generate uncertainty bands.
                """)
                tier3_mc_enabled = gr.Checkbox(label="Enable Monte Carlo", value=False)
                with gr.Row():
                    tier3_mc_trials = gr.Slider(
                        label="Number of Trials",
                        minimum=10,
                        maximum=500,
                        value=100,
                        step=10
                    )
                    tier3_mc_variance = gr.Slider(
                        label="Variance Level",
                        minimum=0.01,
                        maximum=0.30,
                        value=0.10,
                        step=0.01,
                        info="Parameter noise level"
                    )

        # =====================================================================
        # TAB E: RESULTS
        # =====================================================================

        with gr.Tab("📊 Results"):
            run_btn = gr.Button("🚀 Run Simulation", variant="primary", size="lg")

            warnings_box = gr.Markdown(value="", visible=True)

            results_section = gr.Column(visible=False)
            with results_section:
                gr.Markdown("### Summary Metrics")
                with gr.Row():
                    card1 = gr.Markdown(value="")
                    card2 = gr.Markdown(value="")
                    card3 = gr.Markdown(value="")

                gr.Markdown("### Visualizations")

                with gr.Row():
                    chart1 = gr.Plot(label="Unlock Schedule by Bucket")
                    chart2 = gr.Plot(label="Circulating Supply Over Time")

                chart3 = gr.Plot(label="Expected Monthly Sell Pressure")

                gr.Markdown("### Exports")
                with gr.Row():
                    csv1_file = gr.File(label="📄 Bucket Schedule CSV")
                    csv2_file = gr.File(label="📄 Global Metrics CSV")
                    pdf_file = gr.File(label="📑 PDF Report")
                    json_file = gr.File(label="⚙️ Config JSON")

        # =====================================================================
        # CONFIG IMPORT/EXPORT
        # =====================================================================

        gr.Markdown("---")
        with gr.Row():
            import_file = gr.File(label="📥 Import Configuration", file_types=[".json"])
            gr.Markdown("👈 Import a saved configuration to restore all settings")

        # =====================================================================
        # EVENT HANDLERS
        # =====================================================================

        # Run simulation
        run_btn.click(
            fn=run_simulation_from_ui,
            inputs=[
                # Token setup
                token_name, total_supply, start_date, horizon_months, allocation_mode, simulation_mode,
                # Vesting table
                vesting_table,
                # Assumptions
                sell_pressure, avg_daily_volume,
                # Cliff shock
                cliff_shock_enabled, cliff_shock_multiplier, cliff_shock_buckets,
                # Price trigger
                price_trigger_enabled, price_source, price_scenario, take_profit, stop_loss, extra_sell,
                # Relock
                relock_enabled, relock_pct, lock_duration,
                # Tier 2: Staking
                tier2_staking_enabled, tier2_staking_apy, tier2_staking_capacity, tier2_staking_lockup, tier2_staking_rewards,
                # Tier 2: Pricing
                tier2_pricing_enabled, tier2_pricing_model, tier2_pricing_initial, tier2_pricing_elasticity,
                # Tier 2: Treasury
                tier2_treasury_enabled, tier2_treasury_hold, tier2_treasury_liquidity, tier2_treasury_buyback,
                # Tier 2: Volume
                tier2_volume_enabled, tier2_volume_turnover,
                # Tier 3: Cohorts
                tier3_cohorts_enabled, tier3_cohort_profiles,
                # Tier 3: Monte Carlo
                tier3_mc_enabled, tier3_mc_trials, tier3_mc_variance
            ],
            outputs=[
                warnings_box,
                chart1, chart2, chart3,
                card1, card2, card3,
                csv1_file, csv2_file, pdf_file, json_file,
                results_section
            ]
        )

        # Import config
        import_file.change(
            fn=import_config,
            inputs=[import_file],
            outputs=[
                token_name, total_supply, start_date, horizon_months, allocation_mode,
                vesting_table,
                sell_pressure, avg_daily_volume,
                cliff_shock_enabled, cliff_shock_multiplier, cliff_shock_buckets,
                price_trigger_enabled, price_source, price_scenario, take_profit, stop_loss, extra_sell,
                relock_enabled, relock_pct, lock_duration
            ]
        )

    return app


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    app = create_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        theme=gr.themes.Soft()
    )
