#!/usr/bin/env python3
"""
cost_model.py  --  Programmatic 10 kW TEG system cost analysis.

Implements the full cost model from 10KW-SYSTEM-COST-ANALYSIS.md as
parameterized Python code so we can sweep system sizes, TEG types, and
compute lifecycle costs.

Usage:
    python cost_model.py
    python cost_model.py --target-kw 25
    python cost_model.py --teg marlow --target-kw 50
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# TEG specs
# ---------------------------------------------------------------------------

@dataclass
class TEGCost:
    name: str
    power_w: float           # electrical output at design point
    unit_price: float        # at qty 100+
    heat_flux_w: float       # thermal heat through TEG
    life_years: float        # at rated temp
    cell_size_mm: float      # TEG face dimension (square)
    hot_temp_c: float
    cold_temp_c: float
    fluid_type: str          # "water_glycol" or "therminol"
    hx_material: str         # "copper" or "stainless"


MARLOW = TEGCost(
    name="Marlow TG1-1008 (BiTe)",
    power_w=6.16, unit_price=25.00, heat_flux_w=122.0,
    life_years=20.0, cell_size_mm=40, hot_temp_c=200, cold_temp_c=50,
    fluid_type="water_glycol", hx_material="copper",
)

THERMONAMIC = TEGCost(
    name="Thermonamic TEG1-PB-12611 (PbTe)",
    power_w=13.0, unit_price=50.00, heat_flux_w=310.0,
    life_years=8.0, cell_size_mm=56, hot_temp_c=350, cold_temp_c=100,
    fluid_type="therminol", hx_material="stainless",
)

THERMONAMIC_DERATED = TEGCost(
    name="Thermonamic (PbTe @ 320C derated)",
    power_w=10.5, unit_price=50.00, heat_flux_w=270.0,
    life_years=8.0, cell_size_mm=56, hot_temp_c=320, cold_temp_c=100,
    fluid_type="therminol", hx_material="stainless",
)

ALPHABET_PB = TEGCost(
    name="Alphabet Pb-enhanced (est.)",
    power_w=19.0, unit_price=65.00, heat_flux_w=280.0,
    life_years=10.0, cell_size_mm=40, hot_temp_c=400, cold_temp_c=100,
    fluid_type="therminol", hx_material="stainless",
)

TEG_OPTIONS = {
    "marlow": MARLOW,
    "thermonamic": THERMONAMIC,
    "thermonamic_derated": THERMONAMIC_DERATED,
    "alphabet": ALPHABET_PB,
}

# ---------------------------------------------------------------------------
# Per-board cost constants
# ---------------------------------------------------------------------------

TEGS_PER_PCM = 36
PCMS_PER_NODE = 3

# Tier 1: TEG Interconnect (passive)
INTERCONNECT_COST = 21.80

# Tier 2: PCM
PCM_COST_BITE = 131.02     # 12V buck components
PCM_COST_PBTE = 137.05     # 20V+ buck components

# Tier 3: Controller Node
NODE_COST = 88.59

# ---------------------------------------------------------------------------
# HX costs per TEG cell
# ---------------------------------------------------------------------------

@dataclass
class HXCosts:
    hot_cell: float          # per TEG
    cold_cell: float         # per TEG
    hot_tim: float           # per TEG
    cold_tim: float          # per TEG
    hot_manifold_per_ft: float
    cold_manifold_per_ft: float
    insulation_per_ft2: float
    manifold_ft_per_teg: float  # linear feet of manifold per TEG

HX_COPPER = HXCosts(
    hot_cell=12.00, cold_cell=4.00, hot_tim=0.80, cold_tim=0.50,
    hot_manifold_per_ft=8.00, cold_manifold_per_ft=4.00,
    insulation_per_ft2=2.50, manifold_ft_per_teg=0.08,
)

HX_STAINLESS = HXCosts(
    hot_cell=18.00, cold_cell=5.00, hot_tim=2.50, cold_tim=0.50,
    hot_manifold_per_ft=12.00, cold_manifold_per_ft=6.00,
    insulation_per_ft2=8.00, manifold_ft_per_teg=0.10,
)

# ---------------------------------------------------------------------------
# Fluid system costs
# ---------------------------------------------------------------------------

FLUID_WATER_GLYCOL = {
    "skid": 2500, "heater": 3500, "primary_hx": 4000,
    "hot_pump": 1200, "cold_pump": 800, "expansion": 600,
    "fluid": 400, "piping": 1500, "controls": 1200,
    "safety": 0,
}

FLUID_THERMINOL = {
    "skid": 3000, "heater": 9500, "primary_hx": 0,  # integrated
    "hot_pump": 6500, "cold_pump": 1000, "expansion": 650 + 350,
    "fluid": 4125, "piping": 2800 + 1200, "controls": 1800,
    "safety": 700,
}

# ---------------------------------------------------------------------------
# Cooling system
# ---------------------------------------------------------------------------

DRY_COOLER_COST_PER_KW = 45.0   # $/kW rejected (200-250 kW units)
GROUND_LOOP_COST_PER_BOREHOLE = 150 * 82  # 150m * $82/m
GROUND_LOOP_KW_PER_BOREHOLE = 6.0

# ---------------------------------------------------------------------------
# Container / integration
# ---------------------------------------------------------------------------

CONTAINER_FIXED = {
    "container": 4500,
    "electrical_panel": 1800,
    "inverter_per_kw": 250,
    "hmi": 800,
    "safety": 500,
    "cable_trays": 1000,
}

# Variable costs (per tower / per PCM / etc)
TOWER_COST_COPPER = 120.0
TOWER_COST_SS = 180.0
SLIDE_RAIL = 45.0
CLAMP_PER_TOWER = 5 * 25   # ~5 clamp assemblies per tower
QD_UNION_COST = 18.0       # quick-disconnect
QD_UNION_SS = 35.0
FLOOR_GRATING_PER_FT2 = 12.0
WALL_INSULATION_PER_FT2 = 3.0
WALL_INSULATION_SS_PER_FT2 = 3.50
CAT5E_CABLE = 5.0
MOLEX_CABLE = 8.0
BUS_BAR_BASE = 800.0
BUS_BAR_PER_NODE = 25.0


# ---------------------------------------------------------------------------
# System cost calculator
# ---------------------------------------------------------------------------

@dataclass
class SystemCost:
    """Full system cost breakdown."""
    teg_name: str = ""
    target_kw: float = 0.0
    teg_count: int = 0
    pcm_count: int = 0
    node_count: int = 0
    tower_count: int = 0

    # Line items
    teg_cost: float = 0.0
    tier1_cost: float = 0.0
    tier2_cost: float = 0.0
    tier3_cost: float = 0.0
    electronics_total: float = 0.0

    hx_cells_cost: float = 0.0
    hx_manifold_cost: float = 0.0
    hx_insulation_cost: float = 0.0
    hx_total: float = 0.0

    fluid_total: float = 0.0
    cooling_total: float = 0.0
    container_total: float = 0.0

    subtotal: float = 0.0
    volume_discount: float = 0.0
    estimated_total: float = 0.0
    cost_per_kw: float = 0.0

    # Heat
    heat_rejection_kw: float = 0.0
    boreholes_needed: int = 0
    ground_loop_cost: float = 0.0

    # Lifecycle
    teg_replacements_20yr: int = 0
    lifecycle_teg_cost_20yr: float = 0.0
    lifecycle_total_20yr: float = 0.0
    lifecycle_cost_per_kwh: float = 0.0


def calculate_system_cost(teg: TEGCost, target_kw: float = 10.0,
                          cooling: str = "dry",
                          volume_discount_pct: float = 0.15) -> SystemCost:
    """Calculate full system cost for a given TEG type and target power."""
    r = SystemCost()
    r.teg_name = teg.name
    r.target_kw = target_kw

    target_w = target_kw * 1000.0

    # Sizing
    tegs_raw = math.ceil(target_w / teg.power_w)
    r.pcm_count = math.ceil(tegs_raw / TEGS_PER_PCM)
    r.teg_count = r.pcm_count * TEGS_PER_PCM   # round up to full boards
    r.node_count = math.ceil(r.pcm_count / PCMS_PER_NODE)
    tegs_per_tower = 80  # 5 panels x 16 TEGs
    r.tower_count = math.ceil(r.teg_count / tegs_per_tower)

    # TEG cost
    r.teg_cost = r.teg_count * teg.unit_price

    # Electronics
    r.tier1_cost = r.pcm_count * INTERCONNECT_COST
    pcm_unit = PCM_COST_BITE if teg.fluid_type == "water_glycol" else PCM_COST_PBTE
    r.tier2_cost = r.pcm_count * pcm_unit
    r.tier3_cost = r.node_count * NODE_COST
    r.electronics_total = r.tier1_cost + r.tier2_cost + r.tier3_cost

    # Heat exchanger
    hx = HX_COPPER if teg.hx_material == "copper" else HX_STAINLESS
    r.hx_cells_cost = r.teg_count * (hx.hot_cell + hx.cold_cell + hx.hot_tim + hx.cold_tim)
    manifold_ft = r.teg_count * hx.manifold_ft_per_teg
    r.hx_manifold_cost = manifold_ft * (hx.hot_manifold_per_ft + hx.cold_manifold_per_ft)
    insulation_ft2 = manifold_ft * 2.0  # rough: 2 ft2 insulation per ft of manifold
    r.hx_insulation_cost = insulation_ft2 * hx.insulation_per_ft2
    r.hx_total = r.hx_cells_cost + r.hx_manifold_cost + r.hx_insulation_cost

    # Fluid system
    fluid = FLUID_WATER_GLYCOL if teg.fluid_type == "water_glycol" else FLUID_THERMINOL
    # Scale heater cost with target power (base is 10kW / ~200kW thermal)
    scale_factor = max(1.0, target_kw / 10.0)
    r.fluid_total = sum(fluid.values())
    # Scale pump and heater for larger systems
    if scale_factor > 1.5:
        r.fluid_total += (scale_factor - 1.0) * (fluid["heater"] * 0.3 + fluid["hot_pump"] * 0.2)

    # Cooling
    r.heat_rejection_kw = r.teg_count * teg.heat_flux_w / 1000.0
    if cooling == "ground":
        r.boreholes_needed = math.ceil(r.heat_rejection_kw / GROUND_LOOP_KW_PER_BOREHOLE)
        r.ground_loop_cost = r.boreholes_needed * GROUND_LOOP_COST_PER_BOREHOLE
        r.cooling_total = r.ground_loop_cost
    else:
        r.cooling_total = r.heat_rejection_kw * DRY_COOLER_COST_PER_KW

    # Container / integration
    is_ss = teg.hx_material == "stainless"
    tower_unit = TOWER_COST_SS if is_ss else TOWER_COST_COPPER
    qd_unit = QD_UNION_SS if is_ss else QD_UNION_COST

    container_var = (
        r.tower_count * (tower_unit + SLIDE_RAIL + CLAMP_PER_TOWER)
        + r.tower_count * 4 * qd_unit          # 4 QD unions per tower (hot in/out, cold in/out)
        + r.tower_count * 6 * FLOOR_GRATING_PER_FT2  # ~6 ft2 per tower
        + 400 * (WALL_INSULATION_SS_PER_FT2 if is_ss else WALL_INSULATION_PER_FT2)
        + r.pcm_count * CAT5E_CABLE
        + r.pcm_count * MOLEX_CABLE
        + BUS_BAR_BASE + r.node_count * BUS_BAR_PER_NODE
    )
    container_fixed = (
        CONTAINER_FIXED["container"]
        + CONTAINER_FIXED["electrical_panel"]
        + target_kw * CONTAINER_FIXED["inverter_per_kw"]
        + CONTAINER_FIXED["hmi"]
        + CONTAINER_FIXED["safety"]
        + CONTAINER_FIXED["cable_trays"]
    )
    r.container_total = container_fixed + container_var

    # Rollup
    r.subtotal = (r.teg_cost + r.electronics_total + r.hx_total
                  + r.fluid_total + r.cooling_total + r.container_total)
    r.volume_discount = r.subtotal * volume_discount_pct
    r.estimated_total = r.subtotal - r.volume_discount
    actual_kw = r.teg_count * teg.power_w / 1000.0
    r.cost_per_kw = r.estimated_total / actual_kw if actual_kw > 0 else 0

    # Lifecycle (20 years)
    system_life = 20.0
    if teg.life_years >= system_life:
        r.teg_replacements_20yr = 0
    else:
        r.teg_replacements_20yr = math.ceil(system_life / teg.life_years) - 1
    r.lifecycle_teg_cost_20yr = r.teg_cost * (1 + r.teg_replacements_20yr)
    r.lifecycle_total_20yr = r.estimated_total + r.teg_replacements_20yr * r.teg_cost

    # Levelized cost ($/kWh over 20 years, 90% uptime)
    annual_kwh = actual_kw * 8760 * 0.90
    total_kwh_20yr = annual_kwh * system_life
    r.lifecycle_cost_per_kwh = r.lifecycle_total_20yr / total_kwh_20yr if total_kwh_20yr > 0 else 0

    return r


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_cost(r: SystemCost) -> None:
    """Print a formatted cost breakdown."""
    actual_kw = r.teg_count * (r.teg_cost / r.teg_count if r.teg_count > 0 else 0)

    print(f"\n{'=' * 70}")
    print(f"  {r.teg_name}")
    print(f"  Target: {r.target_kw:.0f} kW  |  TEGs: {r.teg_count}  |  "
          f"PCMs: {r.pcm_count}  |  Nodes: {r.node_count}")
    print(f"{'=' * 70}")

    print(f"\n  {'Category':<40s}  {'Cost':>12s}  {'% Total':>8s}")
    print(f"  {'─' * 62}")

    items = [
        ("TEG modules", r.teg_cost),
        ("  Tier 1: TEG Interconnect", r.tier1_cost),
        ("  Tier 2: PCM boards", r.tier2_cost),
        ("  Tier 3: Controller Nodes", r.tier3_cost),
        ("Electronics subtotal", r.electronics_total),
        ("Heat exchangers", r.hx_total),
        ("Fluid system", r.fluid_total),
        ("Cooling system", r.cooling_total),
        ("Container & integration", r.container_total),
    ]

    for label, val in items:
        pct = val / r.subtotal * 100 if r.subtotal > 0 else 0
        if label.startswith("  "):
            print(f"    {label:<38s}  ${val:>11,.0f}  {pct:>7.1f}%")
        else:
            print(f"  {label:<40s}  ${val:>11,.0f}  {pct:>7.1f}%")

    print(f"  {'─' * 62}")
    print(f"  {'SUBTOTAL':<40s}  ${r.subtotal:>11,.0f}")
    print(f"  {'Volume discount (15%)':<40s}  -${r.volume_discount:>10,.0f}")
    print(f"  {'ESTIMATED TOTAL':<40s}  ${r.estimated_total:>11,.0f}")
    print(f"  {'Cost per kW':<40s}  ${r.cost_per_kw:>11,.0f}/kW")

    print(f"\n  --- Heat Rejection ---")
    print(f"  Heat to reject: {r.heat_rejection_kw:.0f} kW")
    if r.boreholes_needed > 0:
        print(f"  Ground loop: {r.boreholes_needed} boreholes, "
              f"${r.ground_loop_cost:,.0f}")
    else:
        print(f"  Dry cooler: ${r.cooling_total:,.0f}")

    print(f"\n  --- 20-Year Lifecycle ---")
    print(f"  TEG replacements: {r.teg_replacements_20yr}x "
          f"(TEG life: {r.lifecycle_teg_cost_20yr / r.teg_count:.0f}$/TEG total)" 
          if r.teg_count > 0 else "")
    print(f"  Lifecycle TEG cost: ${r.lifecycle_teg_cost_20yr:,.0f}")
    print(f"  Lifecycle total: ${r.lifecycle_total_20yr:,.0f}")
    print(f"  Levelized cost: ${r.lifecycle_cost_per_kwh:.4f}/kWh "
          f"(90% uptime, 20 years)")


def print_comparison(results: list[SystemCost]) -> None:
    """Print a side-by-side comparison table."""
    print(f"\n\n{'=' * 90}")
    print(f"  SIDE-BY-SIDE COMPARISON")
    print(f"{'=' * 90}")

    header = f"  {'Metric':<30s}"
    for r in results:
        short = r.teg_name.split("(")[0].strip()[:18]
        header += f"  {short:>16s}"
    print(header)
    print(f"  {'─' * (30 + 18 * len(results))}")

    rows = [
        ("TEG count", [f"{r.teg_count:,}" for r in results]),
        ("PCM boards", [f"{r.pcm_count}" for r in results]),
        ("Controller Nodes", [f"{r.node_count}" for r in results]),
        ("Towers", [f"{r.tower_count}" for r in results]),
        ("", [""]*len(results)),
        ("TEG cost", [f"${r.teg_cost:,.0f}" for r in results]),
        ("Electronics", [f"${r.electronics_total:,.0f}" for r in results]),
        ("Heat exchangers", [f"${r.hx_total:,.0f}" for r in results]),
        ("Fluid system", [f"${r.fluid_total:,.0f}" for r in results]),
        ("Cooling", [f"${r.cooling_total:,.0f}" for r in results]),
        ("Container", [f"${r.container_total:,.0f}" for r in results]),
        ("", [""]*len(results)),
        ("TOTAL (est.)", [f"${r.estimated_total:,.0f}" for r in results]),
        ("$/kW", [f"${r.cost_per_kw:,.0f}" for r in results]),
        ("", [""]*len(results)),
        ("Heat rejection (kW)", [f"{r.heat_rejection_kw:.0f}" for r in results]),
        ("", [""]*len(results)),
        ("TEG replacements/20yr", [f"{r.teg_replacements_20yr}" for r in results]),
        ("Lifecycle total/20yr", [f"${r.lifecycle_total_20yr:,.0f}" for r in results]),
        ("Levelized $/kWh", [f"${r.lifecycle_cost_per_kwh:.4f}" for r in results]),
    ]

    for label, vals in rows:
        line = f"  {label:<30s}"
        for v in vals:
            line += f"  {v:>16s}"
        print(line)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="TEG system cost model")
    parser.add_argument("--teg", choices=list(TEG_OPTIONS.keys()), default=None,
                        help="Single TEG type (default: compare all)")
    parser.add_argument("--target-kw", type=float, default=10.0,
                        help="Target net electrical output (kW)")
    parser.add_argument("--cooling", choices=["dry", "ground"], default="dry",
                        help="Cooling system type")
    args = parser.parse_args()

    if args.teg:
        teg = TEG_OPTIONS[args.teg]
        r = calculate_system_cost(teg, args.target_kw, args.cooling)
        print_cost(r)
    else:
        # Compare all TEG types
        results = []
        for name, teg in TEG_OPTIONS.items():
            r = calculate_system_cost(teg, args.target_kw, args.cooling)
            print_cost(r)
            results.append(r)

        print_comparison(results)

        # Also show scaling
        print(f"\n\n{'=' * 70}")
        print(f"  SCALING ANALYSIS (Marlow BiTe, dry cooler)")
        print(f"{'=' * 70}")
        print(f"  {'Target':>8s}  {'TEGs':>6s}  {'PCMs':>5s}  {'Nodes':>5s}  "
              f"{'Total $':>10s}  {'$/kW':>8s}  {'$/kWh 20yr':>10s}")
        print(f"  {'─' * 66}")
        for kw in [5, 10, 25, 50]:
            r = calculate_system_cost(MARLOW, kw, "dry")
            print(f"  {kw:>6d} kW  {r.teg_count:>6d}  {r.pcm_count:>5d}  "
                  f"{r.node_count:>5d}  ${r.estimated_total:>9,.0f}  "
                  f"${r.cost_per_kw:>7,.0f}  ${r.lifecycle_cost_per_kwh:>9.4f}")


if __name__ == "__main__":
    main()
