#!/usr/bin/env python3
"""
sweep.py  --  Parametric sweep of TEG system performance.

Sweeps:
  - TEG count: 500 to 8,000
  - Hot-side temperature: 200 C (Marlow), 320 C (PbTe derated), 400 C (Alphabet Pb)
  - Gas price: $2.50, $4.00, $6.00 per McF

Outputs tables and (optionally) matplotlib plots.

Usage:
    python sweep.py
    python sweep.py --no-plot    # tables only, no matplotlib
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

import numpy as np

from teg_system_model import (
    SystemConfig, run_model, TEG_CATALOG,
    MARLOW_TG1_1008, THERMONAMIC_PB12611, ALPHABET_PB_ENHANCED,
)
from mcf_to_watts import (
    DEFAULT_BURNER, KWH_THERMAL_PER_MCF, HOURS_PER_DAY, GAS_PRICES,
)

# ---------------------------------------------------------------------------
# Sweep configurations
# ---------------------------------------------------------------------------

SCENARIOS = [
    {
        "label": "Marlow BiTe 200C",
        "teg_type": "marlow",
        "hot_temp": 200.0,
        "cold_temp": 40.0,
        "marker": "o",
        "color": "tab:blue",
    },
    {
        "label": "Thermonamic PbTe 320C",
        "teg_type": "thermonamic",
        "hot_temp": 320.0,
        "cold_temp": 100.0,
        "marker": "s",
        "color": "tab:orange",
    },
    {
        "label": "Alphabet Pb 400C",
        "teg_type": "alphabet",
        "hot_temp": 400.0,
        "cold_temp": 100.0,
        "marker": "^",
        "color": "tab:red",
    },
]

TEG_COUNTS = np.array([500, 750, 1000, 1500, 2000, 3000, 4000, 5000, 6000, 8000])

# Ground loop sizing constants
BOREHOLE_DEPTH_M = 150.0
HEAT_PER_BOREHOLE_KW = 6.0          # conservative, 40 W/m * 150m
BOREHOLE_COST_PER_M = 82.0          # $82/m (~$25/ft)


# ---------------------------------------------------------------------------
# Sweep engine
# ---------------------------------------------------------------------------

@dataclass
class SweepPoint:
    teg_count: int
    net_kw: float
    gross_kw: float
    heat_rejection_kw: float
    mcf_per_day: float
    parasitic_kw: float
    teg_efficiency: float
    system_efficiency: float
    flow_rate_gpm: float
    boreholes: int
    borehole_cost_usd: float
    cost_per_kwh: dict   # {gas_price: $/kWh}


def sweep_scenario(scenario: dict) -> list[SweepPoint]:
    """Run the model across all TEG counts for one scenario."""
    teg_spec = TEG_CATALOG[scenario["teg_type"]]
    hot_temp = scenario["hot_temp"]
    cold_temp = scenario["cold_temp"]

    fluid = "therminol" if hot_temp > 220 else "water_glycol"
    burner = DEFAULT_BURNER

    points = []
    for n in TEG_COUNTS:
        n_rounded = max(36, int(round(n / 36) * 36))

        cfg = SystemConfig(
            teg_count=n_rounded,
            teg_spec=teg_spec,
            hot_fluid=fluid,
            cold_fluid=fluid,
            hot_inlet_c=hot_temp,
            cold_inlet_c=cold_temp,
        )
        r = run_model(cfg)

        total_heat_kw = r.total_heat_input_w / 1000.0
        fuel_thermal_kw = total_heat_kw / burner.delivery_efficiency
        mcf_day = fuel_thermal_kw * HOURS_PER_DAY / KWH_THERMAL_PER_MCF
        parasitic_kw = (r.pump_power_total_w + r.fan_power_w + r.electronics_w) / 1000.0

        # Ground loop sizing
        reject_kw = r.total_heat_rejection_w / 1000.0
        boreholes = int(np.ceil(reject_kw / HEAT_PER_BOREHOLE_KW))
        borehole_cost = boreholes * BOREHOLE_DEPTH_M * BOREHOLE_COST_PER_M

        # Cost per kWh at each gas price
        daily_kwh = r.net_electrical_kw * HOURS_PER_DAY
        cpkwh = {}
        for price in GAS_PRICES:
            daily_fuel = mcf_day * price
            cpkwh[price] = daily_fuel / daily_kwh if daily_kwh > 0 else float("inf")

        system_eff = (r.net_electrical_w / 1000.0) / fuel_thermal_kw if fuel_thermal_kw > 0 else 0

        points.append(SweepPoint(
            teg_count=n_rounded,
            net_kw=r.net_electrical_kw,
            gross_kw=r.gross_electrical_w / 1000.0,
            heat_rejection_kw=reject_kw,
            mcf_per_day=mcf_day,
            parasitic_kw=parasitic_kw,
            teg_efficiency=r.teg_efficiency,
            system_efficiency=system_eff,
            flow_rate_gpm=r.hot_flow_rate_gpm,
            boreholes=boreholes,
            borehole_cost_usd=borehole_cost,
            cost_per_kwh=cpkwh,
        ))

    return points


# ---------------------------------------------------------------------------
# Table output
# ---------------------------------------------------------------------------

def print_sweep_table(label: str, points: list[SweepPoint]) -> None:
    """Print a sweep results table."""
    print(f"\n{'=' * 110}")
    print(f"  {label}")
    print(f"{'=' * 110}")
    print(f"  {'TEGs':>6s}  {'Net kW':>7s}  {'Gross kW':>8s}  "
          f"{'McF/d':>6s}  {'Flow':>6s}  {'Reject':>7s}  "
          f"{'Holes':>5s}  {'Hole $':>9s}  "
          f"{'@$2.50':>8s}  {'@$4.00':>8s}  {'@$6.00':>8s}")
    print(f"  {'':>6s}  {'':>7s}  {'':>8s}  "
          f"{'':>6s}  {'(GPM)':>6s}  {'(kW)':>7s}  "
          f"{'':>5s}  {'':>9s}  "
          f"{'$/kWh':>8s}  {'$/kWh':>8s}  {'$/kWh':>8s}")
    print(f"  {'─' * 106}")

    for p in points:
        print(f"  {p.teg_count:>6d}  {p.net_kw:>7.1f}  {p.gross_kw:>8.1f}  "
              f"{p.mcf_per_day:>6.1f}  {p.flow_rate_gpm:>6.0f}  {p.heat_rejection_kw:>7.0f}  "
              f"{p.boreholes:>5d}  ${p.borehole_cost_usd:>8,.0f}  "
              f"${p.cost_per_kwh[2.50]:>7.4f}  "
              f"${p.cost_per_kwh[4.00]:>7.4f}  "
              f"${p.cost_per_kwh[6.00]:>7.4f}")


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_sweeps(all_results: dict[str, list[SweepPoint]], scenarios: list[dict]) -> None:
    """Generate matplotlib plots for the sweep results."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n  [matplotlib not installed -- skipping plots]")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("TEG System Parametric Sweep", fontsize=14)

    # Plot 1: TEG count vs Net kW
    ax = axes[0, 0]
    for sc in scenarios:
        pts = all_results[sc["label"]]
        x = [p.teg_count for p in pts]
        y = [p.net_kw for p in pts]
        ax.plot(x, y, marker=sc["marker"], color=sc["color"], label=sc["label"])
    ax.set_xlabel("TEG Count")
    ax.set_ylabel("Net Electrical Output (kW)")
    ax.set_title("Scale: TEGs vs Power")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Plot 2: McF/day vs Net kW
    ax = axes[0, 1]
    for sc in scenarios:
        pts = all_results[sc["label"]]
        x = [p.mcf_per_day for p in pts]
        y = [p.net_kw for p in pts]
        ax.plot(x, y, marker=sc["marker"], color=sc["color"], label=sc["label"])
    ax.set_xlabel("Natural Gas (McF/day)")
    ax.set_ylabel("Net Electrical Output (kW)")
    ax.set_title("Fuel Consumption vs Power")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Plot 3: Net kW vs $/kWh (at $4.00/McF)
    ax = axes[1, 0]
    for sc in scenarios:
        pts = all_results[sc["label"]]
        x = [p.net_kw for p in pts]
        y = [p.cost_per_kwh[4.00] for p in pts]
        ax.plot(x, y, marker=sc["marker"], color=sc["color"], label=sc["label"])
    ax.set_xlabel("Net Electrical Output (kW)")
    ax.set_ylabel("Fuel Cost ($/kWh @ $4.00/McF)")
    ax.set_title("Cost vs Scale")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Plot 4: Net kW vs Ground Loop Boreholes
    ax = axes[1, 1]
    for sc in scenarios:
        pts = all_results[sc["label"]]
        x = [p.net_kw for p in pts]
        y = [p.boreholes for p in pts]
        ax.plot(x, y, marker=sc["marker"], color=sc["color"], label=sc["label"])
    ax.set_xlabel("Net Electrical Output (kW)")
    ax.set_ylabel("Ground Loop Boreholes (150m each)")
    ax.set_title("Heat Rejection: Borehole Count")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    outfile = "sweep_results.png"
    plt.savefig(outfile, dpi=150)
    print(f"\n  Plots saved to: {outfile}")
    plt.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="TEG system parametric sweep")
    parser.add_argument("--no-plot", action="store_true",
                        help="Skip plot generation")
    args = parser.parse_args()

    all_results = {}
    for sc in SCENARIOS:
        points = sweep_scenario(sc)
        all_results[sc["label"]] = points
        print_sweep_table(sc["label"], points)

    # Cross-scenario comparison at specific targets
    print(f"\n\n{'=' * 80}")
    print(f"  CROSS-SCENARIO COMPARISON")
    print(f"{'=' * 80}")

    for target_kw in [10, 25, 50]:
        print(f"\n  --- Target: {target_kw} kW net ---")
        print(f"  {'Scenario':<30s}  {'TEGs':>6s}  {'McF/d':>6s}  "
              f"{'Holes':>5s}  {'@$4/McF':>8s}")
        print(f"  {'─' * 62}")

        for sc in SCENARIOS:
            pts = all_results[sc["label"]]
            # Find closest point to target
            closest = min(pts, key=lambda p: abs(p.net_kw - target_kw))
            print(f"  {sc['label']:<30s}  {closest.teg_count:>6d}  "
                  f"{closest.mcf_per_day:>6.1f}  "
                  f"{closest.boreholes:>5d}  "
                  f"${closest.cost_per_kwh[4.00]:>7.4f}")

    if not args.no_plot:
        plot_sweeps(all_results, SCENARIOS)


if __name__ == "__main__":
    main()
