#!/usr/bin/env python3
"""
mcf_to_watts.py  --  Natural gas (McF) to electrical watts to cost calculator.

Converts fuel input through the full energy chain:
    McF/day  ->  BTU  ->  kWh_thermal  ->  HX delivery  ->  TEG electrical
              ->  minus parasitic loads  ->  net kW_e  ->  $/kWh_e

Sweeps gas prices ($2.50, $4.00, $6.00 per McF) and system targets (10, 25, 50 kW).

Usage:
    python mcf_to_watts.py
    python mcf_to_watts.py --teg-type thermonamic --hot-temp 350
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

import numpy as np

# Import the core thermal model
from teg_system_model import (
    SystemConfig, run_model, TEG_CATALOG,
    MARLOW_TG1_1008, THERMONAMIC_PB12611, ALPHABET_PB_ENHANCED,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BTU_PER_MCF = 1_020_000.0          # 1 McF natural gas = 1,020,000 BTU
KWH_PER_BTU = 0.000293071          # 1 BTU = 0.000293071 kWh
KWH_THERMAL_PER_MCF = BTU_PER_MCF * KWH_PER_BTU   # ~299.1 kWh_th
HOURS_PER_DAY = 24.0

# Gas price points ($/McF)
GAS_PRICES = [2.50, 4.00, 6.00]

# Target system sizes (kW_e net)
TARGETS_KW = [10, 25, 50]


# ---------------------------------------------------------------------------
# Burner model
# ---------------------------------------------------------------------------

@dataclass
class BurnerSpec:
    """Low-NOx burner specification."""
    efficiency: float = 0.88        # 88% thermal efficiency (85-92% range)
    pipe_loss_fraction: float = 0.05  # 5% heat loss in hot piping

    @property
    def delivery_efficiency(self) -> float:
        """Fraction of fuel energy delivered to HX hot side."""
        return self.efficiency * (1.0 - self.pipe_loss_fraction)


DEFAULT_BURNER = BurnerSpec()


# ---------------------------------------------------------------------------
# McF calculator
# ---------------------------------------------------------------------------

@dataclass
class McfResult:
    """Results for a single operating point."""
    # Inputs
    teg_type: str
    teg_count: int
    hot_temp_c: float
    cold_temp_c: float

    # Energy chain
    mcf_per_day: float = 0.0
    thermal_input_kw: float = 0.0
    hx_delivery_kw: float = 0.0
    gross_electrical_kw: float = 0.0
    parasitic_kw: float = 0.0
    net_electrical_kw: float = 0.0

    # Efficiency
    burner_efficiency: float = 0.0
    teg_efficiency: float = 0.0
    system_efficiency: float = 0.0      # fuel-to-net-electric

    # Heat rejection
    heat_rejection_kw: float = 0.0

    # Costs at each gas price
    cost_per_kwh: dict = None      # {price: $/kWh}
    fuel_cost_per_day: dict = None  # {price: $/day}

    def __post_init__(self):
        if self.cost_per_kwh is None:
            self.cost_per_kwh = {}
        if self.fuel_cost_per_day is None:
            self.fuel_cost_per_day = {}


def mcf_for_target(target_kw: float, teg_type: str = "marlow",
                   hot_temp: float = 200.0, cold_temp: float = 40.0,
                   burner: BurnerSpec = DEFAULT_BURNER) -> McfResult:
    """Calculate McF/day needed for a target net electrical output.

    Works backwards from target kW_e to required fuel input.
    """
    teg = TEG_CATALOG.get(teg_type, MARLOW_TG1_1008)

    # Auto-select fluid
    if hot_temp > 220:
        fluid = "therminol"
    else:
        fluid = "water_glycol"

    # Binary search for TEG count that achieves target
    lo, hi = 10, 50_000
    best_cfg = None
    best_result = None

    for _ in range(30):
        mid = (lo + hi) // 2
        # Round to nearest 36 (PCM board size)
        mid_rounded = max(36, round(mid / 36) * 36)

        cfg = SystemConfig(
            teg_count=mid_rounded,
            teg_spec=teg,
            hot_fluid=fluid,
            cold_fluid=fluid,
            hot_inlet_c=hot_temp,
            cold_inlet_c=cold_temp,
        )
        r = run_model(cfg)

        if r.net_electrical_kw < target_kw:
            lo = mid + 1
        else:
            hi = mid
            best_cfg = cfg
            best_result = r

    if best_result is None:
        # Use upper bound
        cfg = SystemConfig(
            teg_count=round(hi / 36) * 36,
            teg_spec=teg,
            hot_fluid=fluid,
            cold_fluid=fluid,
            hot_inlet_c=hot_temp,
            cold_inlet_c=cold_temp,
        )
        best_result = run_model(cfg)
        best_cfg = cfg

    r = best_result

    # Calculate fuel input required
    # net_electrical = gross_electrical - parasitic
    # gross_electrical comes from total_heat_input * teg_efficiency
    # total_heat_input = fuel_thermal * burner.delivery_efficiency
    # fuel_thermal = McF/day * KWH_THERMAL_PER_MCF / 24h * 1000 (to get W... no)
    #
    # Actually: total_heat_input_w is what the model computed.
    # fuel_thermal_kw = total_heat_input_kw / burner.delivery_efficiency
    # mcf_per_day = fuel_thermal_kw * 24 / KWH_THERMAL_PER_MCF

    total_heat_kw = r.total_heat_input_w / 1000.0
    fuel_thermal_kw = total_heat_kw / burner.delivery_efficiency
    mcf_per_day = fuel_thermal_kw * HOURS_PER_DAY / KWH_THERMAL_PER_MCF

    parasitic_kw = (r.pump_power_total_w + r.fan_power_w + r.electronics_w) / 1000.0

    result = McfResult(
        teg_type=teg_type,
        teg_count=best_cfg.teg_count,
        hot_temp_c=hot_temp,
        cold_temp_c=cold_temp,
        mcf_per_day=mcf_per_day,
        thermal_input_kw=fuel_thermal_kw,
        hx_delivery_kw=total_heat_kw,
        gross_electrical_kw=r.gross_electrical_w / 1000.0,
        parasitic_kw=parasitic_kw,
        net_electrical_kw=r.net_electrical_kw / 1000.0,
        burner_efficiency=burner.delivery_efficiency,
        teg_efficiency=r.teg_efficiency,
        system_efficiency=(r.net_electrical_w / 1000.0) / fuel_thermal_kw if fuel_thermal_kw > 0 else 0,
        heat_rejection_kw=r.total_heat_rejection_w / 1000.0,
    )

    # Cost at each gas price
    for price in GAS_PRICES:
        daily_fuel_cost = mcf_per_day * price
        daily_kwh_produced = r.net_electrical_kw * HOURS_PER_DAY
        cost_per_kwh = daily_fuel_cost / daily_kwh_produced if daily_kwh_produced > 0 else float("inf")
        result.cost_per_kwh[price] = cost_per_kwh
        result.fuel_cost_per_day[price] = daily_fuel_cost

    return result


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_energy_chain(res: McfResult) -> None:
    """Print the full energy conversion chain."""
    print(f"\n  McF/day:                {res.mcf_per_day:8.1f}")
    print(f"  Fuel thermal (kW):      {res.thermal_input_kw:8.1f}")
    print(f"  Burner delivery eff:    {res.burner_efficiency * 100:8.1f} %")
    print(f"  HX delivery (kW_th):    {res.hx_delivery_kw:8.1f}")
    print(f"  TEG efficiency:         {res.teg_efficiency * 100:8.2f} %")
    print(f"  Gross electrical (kW):  {res.gross_electrical_kw:8.2f}")
    print(f"  Parasitic loads (kW):   {res.parasitic_kw:8.2f}")
    print(f"  NET ELECTRICAL (kW):    {res.net_electrical_kw:8.2f}")
    print(f"  System fuel->elec eff:  {res.system_efficiency * 100:8.2f} %")
    print(f"  Heat rejection (kW):    {res.heat_rejection_kw:8.1f}")


def print_full_report(scenarios: list[dict]) -> None:
    """Print the complete McF-to-watts report."""
    print("=" * 80)
    print("  McF-TO-WATTS-TO-COST ANALYSIS")
    print("  Natural Gas -> Low-NOx Burner -> TEG Array -> Net Electrical")
    print("=" * 80)

    print(f"\n  Energy Constants:")
    print(f"    1 McF = {BTU_PER_MCF:,.0f} BTU = {KWH_THERMAL_PER_MCF:.1f} kWh_th")
    print(f"    Burner efficiency: {DEFAULT_BURNER.efficiency * 100:.0f}%")
    print(f"    Pipe losses: {DEFAULT_BURNER.pipe_loss_fraction * 100:.0f}%")
    print(f"    Net delivery: {DEFAULT_BURNER.delivery_efficiency * 100:.1f}%")

    for scenario in scenarios:
        label = scenario["label"]
        teg_type = scenario["teg_type"]
        hot_temp = scenario["hot_temp"]
        cold_temp = scenario["cold_temp"]
        teg_name = TEG_CATALOG[teg_type].name

        print(f"\n\n{'─' * 80}")
        print(f"  SCENARIO: {label}")
        print(f"  TEG: {teg_name}")
        print(f"  Hot: {hot_temp} C  /  Cold: {cold_temp} C")
        print(f"{'─' * 80}")

        results = []
        for target in TARGETS_KW:
            res = mcf_for_target(target, teg_type, hot_temp, cold_temp)
            results.append(res)

        # Summary table header
        print(f"\n  {'Target':>8s}  {'TEGs':>6s}  {'McF/d':>7s}  "
              f"{'Gross':>7s}  {'Net':>7s}  {'Reject':>7s}  "
              f"{'$2.50':>8s}  {'$4.00':>8s}  {'$6.00':>8s}")
        print(f"  {'(kW)':>8s}  {'':>6s}  {'':>7s}  "
              f"{'(kW)':>7s}  {'(kW)':>7s}  {'(kW)':>7s}  "
              f"{'($/kWh)':>8s}  {'($/kWh)':>8s}  {'($/kWh)':>8s}")
        print(f"  {'─' * 76}")

        for target, res in zip(TARGETS_KW, results):
            c250 = res.cost_per_kwh.get(2.50, 0)
            c400 = res.cost_per_kwh.get(4.00, 0)
            c600 = res.cost_per_kwh.get(6.00, 0)
            print(f"  {target:>8d}  {res.teg_count:>6d}  {res.mcf_per_day:>7.1f}  "
                  f"{res.gross_electrical_kw:>7.2f}  {res.net_electrical_kw:>7.2f}  "
                  f"{res.heat_rejection_kw:>7.0f}  "
                  f"${c250:>7.4f}  ${c400:>7.4f}  ${c600:>7.4f}")

        # Detail for 10kW target
        print(f"\n  --- Detail: {TARGETS_KW[0]} kW target ---")
        print_energy_chain(results[0])

        # Daily fuel cost
        print(f"\n  --- Daily Fuel Cost ({TARGETS_KW[0]} kW) ---")
        for price in GAS_PRICES:
            daily = results[0].fuel_cost_per_day.get(price, 0)
            monthly = daily * 30
            yearly = daily * 365
            print(f"    @ ${price:.2f}/McF:  ${daily:>7.2f}/day  "
                  f"${monthly:>8.0f}/month  ${yearly:>9.0f}/year")


def main():
    parser = argparse.ArgumentParser(description="McF to Watts to Cost calculator")
    parser.add_argument("--teg-type", choices=list(TEG_CATALOG.keys()),
                        default=None,
                        help="Single TEG type to analyze (default: all)")
    parser.add_argument("--hot-temp", type=float, default=None)
    parser.add_argument("--cold-temp", type=float, default=None)
    args = parser.parse_args()

    if args.teg_type:
        # Single scenario
        hot = args.hot_temp or (200.0 if args.teg_type == "marlow" else 350.0)
        cold = args.cold_temp or (40.0 if args.teg_type == "marlow" else 100.0)
        scenarios = [{
            "label": f"{args.teg_type} @ {hot}C",
            "teg_type": args.teg_type,
            "hot_temp": hot,
            "cold_temp": cold,
        }]
    else:
        # Default: compare all TEG types
        scenarios = [
            {
                "label": "BiTe 200 C (current Marlow)",
                "teg_type": "marlow",
                "hot_temp": 200.0,
                "cold_temp": 40.0,
            },
            {
                "label": "PbTe Hybrid 350 C (Thermonamic)",
                "teg_type": "thermonamic",
                "hot_temp": 350.0,
                "cold_temp": 100.0,
            },
            {
                "label": "PbTe Hybrid 320 C (Thermonamic, derated for life)",
                "teg_type": "thermonamic",
                "hot_temp": 320.0,
                "cold_temp": 100.0,
            },
            {
                "label": "Pb-enhanced Alphabet 400 C (estimated)",
                "teg_type": "alphabet",
                "hot_temp": 400.0,
                "cold_temp": 100.0,
            },
        ]

    print_full_report(scenarios)


if __name__ == "__main__":
    main()
