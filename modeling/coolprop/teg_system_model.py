#!/usr/bin/env python3
"""
teg_system_model.py  --  CoolProp-based TEG system thermal-hydraulic model.

Models the full heat-transfer chain:
    Hot fluid -> HX fin channels -> TIM -> TEG -> TIM -> Cold HX -> Cold fluid

Uses CoolProp for real fluid properties (water/glycol, Therminol VP-1 approx).
Geometry from HEAT-EXCHANGER-SPEC-V1.md (SynergyThermogen/engineering).

Usage:
    python teg_system_model.py
    python teg_system_model.py --teg-count 1620 --hot-temp 200 --cold-temp 50
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass, field
from typing import Optional

try:
    import CoolProp.CoolProp as CP
except ImportError:
    CP = None
    print("WARNING: CoolProp not installed. Using fallback fluid properties.")
    print("         Install with: pip install CoolProp")

import numpy as np

# ---------------------------------------------------------------------------
# TEG data
# ---------------------------------------------------------------------------

@dataclass
class TEGSpec:
    """Thermoelectric generator module specification."""
    name: str
    width_m: float          # module face width (m)
    height_m: float         # module face height (m)
    r_thermal: float        # thermal resistance (C/W)
    max_hot_c: float        # max continuous hot-side (C)
    seebeck_v_per_k: float  # approximate Seebeck coefficient (V/K) for pair
    internal_r_ohm: float   # internal resistance at operating point (Ohm)
    price_usd: float        # unit price at qty 100+
    life_years: float       # expected life at rated temp

    def electrical_output(self, dt_c: float) -> dict:
        """Estimate electrical output at a given delta-T across the TEG.

        Uses a simple quadratic fit calibrated to datasheet points.
        Returns dict with power_w, voltage_v, current_a, efficiency.
        """
        # Seebeck voltage
        v_oc = self.seebeck_v_per_k * dt_c
        # At MPP, V = Voc/2, I = Voc/(2*Ri)
        v_mpp = v_oc / 2.0
        i_mpp = v_oc / (2.0 * self.internal_r_ohm)
        p_mpp = v_mpp * i_mpp

        # Heat flow through TEG
        q_teg = dt_c / self.r_thermal if self.r_thermal > 0 else 0.0
        eff = p_mpp / q_teg if q_teg > 0 else 0.0

        return {
            "power_w": p_mpp,
            "voltage_v": v_mpp,
            "current_a": i_mpp,
            "heat_flux_w": q_teg,
            "efficiency": eff,
        }


# Pre-defined TEG specifications
MARLOW_TG1_1008 = TEGSpec(
    name="Marlow TG1-1008 (BiTe)",
    width_m=0.040,
    height_m=0.040,
    r_thermal=1.52,       # average of 1.47-1.58
    max_hot_c=200.0,
    seebeck_v_per_k=0.033,  # ~6V Voc at 180K dT -> 0.033 V/K
    internal_r_ohm=1.5,     # calibrated to give ~6.16W at 180K dT
    price_usd=25.00,
    life_years=20.0,
)

THERMONAMIC_PB12611 = TEGSpec(
    name="Thermonamic TEG1-PB-12611 (PbTe hybrid)",
    width_m=0.056,
    height_m=0.056,
    r_thermal=0.95,        # estimated from 310W heat flux at 320K dT
    max_hot_c=360.0,
    seebeck_v_per_k=0.029,  # 9.2V Voc at 320K dT -> 0.029 V/K
    internal_r_ohm=0.97,
    price_usd=50.00,
    life_years=8.0,         # at 320C continuous
)

ALPHABET_PB_ENHANCED = TEGSpec(
    name="Alphabet PowerCard Pb-enhanced (est.)",
    width_m=0.040,
    height_m=0.040,
    r_thermal=1.10,        # estimated improvement over BiTe
    max_hot_c=400.0,
    seebeck_v_per_k=0.035,
    internal_r_ohm=1.2,
    price_usd=65.00,       # from bench test BOM
    life_years=10.0,        # estimated with Pb enhancement
)

TEG_CATALOG = {
    "marlow": MARLOW_TG1_1008,
    "thermonamic": THERMONAMIC_PB12611,
    "alphabet": ALPHABET_PB_ENHANCED,
}

# ---------------------------------------------------------------------------
# HX geometry (from HEAT-EXCHANGER-SPEC-V1.md Section 3)
# ---------------------------------------------------------------------------

@dataclass
class HXGeometry:
    """Heat exchanger fin channel geometry for a single TEG cell."""
    n_channels: int = 9         # parallel channels per TEG
    channel_width_m: float = 0.003   # 3 mm
    channel_height_m: float = 0.040  # 40 mm (matches TEG)
    channel_length_m: float = 0.040  # 40 mm (flow path)
    fin_thickness_m: float = 0.001   # 1 mm copper
    fin_conductivity: float = 385.0  # W/m-K (C110 copper)
    n_fins: int = 10

    # Manifold
    manifold_id_m: float = 0.038     # 1.5" ID

    # TIM properties
    hot_tim_k: float = 7.5          # W/m-K (flexible graphite, mid-range)
    hot_tim_thickness_m: float = 0.000375   # 0.375 mm average
    cold_tim_k: float = 4.5         # W/m-K (silicone thermal pad)
    cold_tim_thickness_m: float = 0.0005    # 0.5 mm

    @property
    def hydraulic_diameter(self) -> float:
        """Hydraulic diameter of a single fin channel (m)."""
        a = self.channel_width_m * self.channel_height_m
        p = 2.0 * (self.channel_width_m + self.channel_height_m)
        return 4.0 * a / p

    @property
    def channel_area(self) -> float:
        """Cross-sectional area of a single fin channel (m^2)."""
        return self.channel_width_m * self.channel_height_m

    @property
    def total_flow_area(self) -> float:
        """Total flow area for all channels in one TEG cell (m^2)."""
        return self.n_channels * self.channel_area

    @property
    def teg_contact_area(self) -> float:
        """TEG-to-HX contact area (m^2). Uses full face since fins span it."""
        # The contact area between the HX base and the TEG face
        return self.channel_length_m * (
            self.n_channels * self.channel_width_m
            + self.n_fins * self.fin_thickness_m
        )

    @property
    def wetted_area_per_channel(self) -> float:
        """Wetted (convective) area inside one fin channel (m^2)."""
        return 2.0 * (self.channel_width_m + self.channel_height_m) * self.channel_length_m


# ---------------------------------------------------------------------------
# Fluid property helpers
# ---------------------------------------------------------------------------

def water_glycol_props(temp_c: float, pressure_pa: float = 200_000.0) -> dict:
    """Get water/glycol (50/50) properties at temperature.

    Uses CoolProp for pure water with manual corrections for glycol mix,
    or hardcoded fallbacks if CoolProp is not available.
    """
    if CP is not None:
        try:
            t_k = temp_c + 273.15
            # CoolProp IncompressibleMixture for ethylene glycol
            fluid = "INCOMP::MEG[0.5]"  # 50% mono-ethylene glycol
            rho = CP.PropsSI("D", "T", t_k, "P", pressure_pa, fluid)
            cp = CP.PropsSI("C", "T", t_k, "P", pressure_pa, fluid)
            mu = CP.PropsSI("V", "T", t_k, "P", pressure_pa, fluid)
            k = CP.PropsSI("L", "T", t_k, "P", pressure_pa, fluid)
            pr = cp * mu / k
            return {"rho": rho, "cp": cp, "mu": mu, "k": k, "pr": pr,
                    "name": "Water/Glycol 50/50"}
        except Exception:
            pass  # fall through to hardcoded

    # Fallback: approximate properties at ~80 C bulk (reasonable mid-point)
    return {
        "rho": 1040.0,    # kg/m^3
        "cp": 3400.0,     # J/kg-K
        "mu": 0.0008,     # Pa-s
        "k": 0.40,        # W/m-K
        "pr": 6.8,
        "name": "Water/Glycol 50/50 (fallback)",
    }


def thermal_oil_props(temp_c: float, pressure_pa: float = 200_000.0) -> dict:
    """Approximate Therminol VP-1 properties at temperature.

    CoolProp does not include Therminol, so we use a polynomial fit from
    the Therminol VP-1 datasheet (valid 12-400 C).
    """
    t = temp_c
    # Polynomial fits from Therminol VP-1 technical bulletin
    rho = 1078.0 - 0.85 * t            # kg/m^3
    cp = 1510.0 + 2.5 * t              # J/kg-K
    # Viscosity (mPa-s) -- exponential fit
    if t > 20:
        mu = 0.001 * math.exp(5.25 - 0.02 * t)  # rough fit
    else:
        mu = 0.004  # near room temp
    mu = max(mu, 0.0002)  # floor at high temp
    k = 0.137 - 0.00005 * t            # W/m-K (decreases with temp)
    k = max(k, 0.08)
    pr = cp * mu / k

    return {
        "rho": rho, "cp": cp, "mu": mu, "k": k, "pr": pr,
        "name": "Therminol VP-1 (polynomial fit)",
    }


def get_fluid_props(fluid_type: str, temp_c: float) -> dict:
    """Get fluid properties by type name."""
    if fluid_type in ("water_glycol", "glycol", "water"):
        return water_glycol_props(temp_c)
    elif fluid_type in ("therminol", "thermal_oil", "vp1"):
        return thermal_oil_props(temp_c)
    else:
        raise ValueError(f"Unknown fluid type: {fluid_type}")


# ---------------------------------------------------------------------------
# Convection and pressure-drop correlations
# ---------------------------------------------------------------------------

def nusselt_dittus_boelter(re: float, pr: float, heating: bool = True) -> float:
    """Dittus-Boelter correlation for turbulent pipe flow.

    Nu = 0.023 * Re^0.8 * Pr^n
    n = 0.4 (heating), 0.3 (cooling)
    Valid for Re > 6000, 0.6 < Pr < 160.
    """
    n = 0.4 if heating else 0.3
    if re < 2300:
        # Laminar: Nu ~ 3.66 for constant wall temp in rectangular channel
        return 3.66
    elif re < 6000:
        # Transition: linear interpolation
        nu_lam = 3.66
        nu_turb = 0.023 * re**0.8 * pr**n
        frac = (re - 2300) / (6000 - 2300)
        return nu_lam + frac * (nu_turb - nu_lam)
    else:
        return 0.023 * re**0.8 * pr**n


def friction_factor(re: float, roughness_m: float = 1e-6,
                    d_h: float = 0.005) -> float:
    """Darcy friction factor (Moody). Colebrook for turbulent, 64/Re for laminar."""
    if re < 2300:
        return 64.0 / max(re, 1.0)
    else:
        # Colebrook-White (iterative)
        eps_d = roughness_m / d_h
        f = 0.02  # initial guess
        for _ in range(20):
            rhs = -2.0 * math.log10(eps_d / 3.7 + 2.51 / (re * math.sqrt(f)))
            f_new = 1.0 / rhs**2
            if abs(f_new - f) < 1e-8:
                break
            f = f_new
        return f


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------

@dataclass
class SystemConfig:
    """Full system configuration."""
    teg_count: int = 1620
    teg_spec: TEGSpec = field(default_factory=lambda: MARLOW_TG1_1008)
    hx: HXGeometry = field(default_factory=HXGeometry)

    hot_fluid: str = "water_glycol"
    cold_fluid: str = "water_glycol"
    hot_inlet_c: float = 200.0       # hot fluid inlet to HX
    cold_inlet_c: float = 40.0       # cold fluid inlet to HX
    target_dt_fluid_c: float = 10.0  # fluid temp change across HX

    # TEGs per panel and panels per tower
    tegs_per_panel: int = 16
    panels_per_tower: int = 5

    # Pump efficiency
    pump_efficiency: float = 0.65

    # Pipe lengths (m) for pressure-drop estimate
    hot_pipe_length_m: float = 30.0
    cold_pipe_length_m: float = 30.0
    pipe_id_m: float = 0.038         # 1.5" schedule 40


@dataclass
class ModelResults:
    """Results from a single model run."""
    # TEG performance
    dt_across_teg_c: float = 0.0
    power_per_teg_w: float = 0.0
    heat_per_teg_w: float = 0.0
    teg_efficiency: float = 0.0
    teg_voltage_v: float = 0.0
    teg_current_a: float = 0.0

    # System totals
    total_teg_count: int = 0
    gross_electrical_w: float = 0.0
    total_heat_input_w: float = 0.0
    total_heat_rejection_w: float = 0.0

    # Fluid / flow
    hot_fluid_name: str = ""
    hot_flow_rate_m3s: float = 0.0
    hot_flow_rate_gpm: float = 0.0
    hot_velocity_channel_ms: float = 0.0
    hot_reynolds: float = 0.0
    hot_nusselt: float = 0.0
    hot_h_conv: float = 0.0        # W/m^2-K

    cold_fluid_name: str = ""
    cold_flow_rate_m3s: float = 0.0
    cold_flow_rate_gpm: float = 0.0

    # Pressure drop
    hot_dp_channel_pa: float = 0.0
    hot_dp_manifold_pa: float = 0.0
    hot_dp_pipe_pa: float = 0.0
    hot_dp_total_pa: float = 0.0
    cold_dp_total_pa: float = 0.0

    # Parasitic
    pump_power_hot_w: float = 0.0
    pump_power_cold_w: float = 0.0
    pump_power_total_w: float = 0.0
    fan_power_w: float = 0.0        # if dry cooler
    electronics_w: float = 0.0

    # Net
    net_electrical_w: float = 0.0
    net_electrical_kw: float = 0.0
    parasitic_fraction: float = 0.0

    # Thermal resistances (per TEG, C/W)
    r_hot_conv: float = 0.0
    r_hot_tim: float = 0.0
    r_teg: float = 0.0
    r_cold_tim: float = 0.0
    r_cold_conv: float = 0.0
    r_total: float = 0.0

    # Temperatures
    t_hot_fluid_avg_c: float = 0.0
    t_hot_fin_surface_c: float = 0.0
    t_teg_hot_c: float = 0.0
    t_teg_cold_c: float = 0.0
    t_cold_fin_surface_c: float = 0.0
    t_cold_fluid_avg_c: float = 0.0


def run_model(cfg: SystemConfig) -> ModelResults:
    """Run the thermal-hydraulic model for the given configuration."""
    r = ModelResults()
    r.total_teg_count = cfg.teg_count
    hx = cfg.hx
    teg = cfg.teg_spec

    # ---- Fluid properties at bulk average temp ----
    t_hot_avg = cfg.hot_inlet_c - cfg.target_dt_fluid_c / 2.0
    t_cold_avg = cfg.cold_inlet_c + cfg.target_dt_fluid_c / 2.0

    hot_props = get_fluid_props(cfg.hot_fluid, t_hot_avg)
    cold_props = get_fluid_props(cfg.cold_fluid, t_cold_avg)
    r.hot_fluid_name = hot_props["name"]
    r.cold_fluid_name = cold_props["name"]
    r.t_hot_fluid_avg_c = t_hot_avg
    r.t_cold_fluid_avg_c = t_cold_avg

    # ---- Estimate heat per TEG (first pass: use TEG R_th) ----
    # Approximate: hot fluid avg - cold fluid avg spans the total resistance chain
    dt_total = t_hot_avg - t_cold_avg

    # Thermal resistances per TEG (C/W)
    # 1) Hot convection: need flow rate first, so iterate

    # First estimate Q per TEG from TEG R_th alone as starting point
    q_teg_est = dt_total / (teg.r_thermal * 1.5)  # rough, ~2/3 of dT is across TEG

    # Flow rate: total heat / (rho * Cp * dT_fluid)
    total_heat_est = q_teg_est * cfg.teg_count
    hot_mass_flow = total_heat_est / (hot_props["cp"] * cfg.target_dt_fluid_c)  # kg/s
    hot_vol_flow = hot_mass_flow / hot_props["rho"]  # m^3/s

    # Per-TEG flow (assuming all TEGs in parallel through their own channels)
    vol_per_teg = hot_vol_flow / cfg.teg_count
    velocity = vol_per_teg / hx.total_flow_area  # m/s in each channel

    # Reynolds
    dh = hx.hydraulic_diameter
    re = hot_props["rho"] * velocity * dh / hot_props["mu"]
    r.hot_reynolds = re

    # Nusselt and convection coefficient
    nu = nusselt_dittus_boelter(re, hot_props["pr"], heating=False)
    r.hot_nusselt = nu
    h_hot = nu * hot_props["k"] / dh
    r.hot_h_conv = h_hot

    # Hot-side convection resistance per TEG
    a_wetted = hx.wetted_area_per_channel * hx.n_channels
    r_hot_conv = 1.0 / (h_hot * a_wetted) if h_hot > 0 else 999.0

    # TIM resistances
    a_contact = hx.teg_contact_area
    r_hot_tim = hx.hot_tim_thickness_m / (hx.hot_tim_k * a_contact)
    r_cold_tim = hx.cold_tim_thickness_m / (hx.cold_tim_k * a_contact)

    # TEG thermal resistance
    r_teg = teg.r_thermal

    # Cold-side convection (assume similar geometry, similar flow, similar h)
    cold_vel_est = vol_per_teg / hx.total_flow_area  # approximate
    re_cold = cold_props["rho"] * cold_vel_est * dh / cold_props["mu"]
    nu_cold = nusselt_dittus_boelter(re_cold, cold_props["pr"], heating=True)
    h_cold = nu_cold * cold_props["k"] / dh
    r_cold_conv = 1.0 / (h_cold * a_wetted) if h_cold > 0 else 999.0

    # Total thermal resistance chain
    r_total = r_hot_conv + r_hot_tim + r_teg + r_cold_tim + r_cold_conv

    # Store resistances
    r.r_hot_conv = r_hot_conv
    r.r_hot_tim = r_hot_tim
    r.r_teg = r_teg
    r.r_cold_tim = r_cold_tim
    r.r_cold_conv = r_cold_conv
    r.r_total = r_total

    # ---- Iterate to converge Q and flow rate ----
    for _ in range(10):
        q_per_teg = dt_total / r_total
        total_heat = q_per_teg * cfg.teg_count

        hot_mass_flow = total_heat / (hot_props["cp"] * cfg.target_dt_fluid_c)
        hot_vol_flow = hot_mass_flow / hot_props["rho"]
        vol_per_teg = hot_vol_flow / cfg.teg_count
        velocity = vol_per_teg / hx.total_flow_area

        re = hot_props["rho"] * velocity * dh / hot_props["mu"]
        nu = nusselt_dittus_boelter(re, hot_props["pr"], heating=False)
        h_hot = nu * hot_props["k"] / dh
        r_hot_conv_new = 1.0 / (h_hot * a_wetted) if h_hot > 0 else 999.0

        # Also iterate cold side
        cold_mass_flow = total_heat / (cold_props["cp"] * cfg.target_dt_fluid_c)
        cold_vol_flow = cold_mass_flow / cold_props["rho"]
        cold_vol_per_teg = cold_vol_flow / cfg.teg_count
        cold_vel = cold_vol_per_teg / hx.total_flow_area
        re_cold = cold_props["rho"] * cold_vel * dh / cold_props["mu"]
        nu_cold = nusselt_dittus_boelter(re_cold, cold_props["pr"], heating=True)
        h_cold = nu_cold * cold_props["k"] / dh
        r_cold_conv_new = 1.0 / (h_cold * a_wetted) if h_cold > 0 else 999.0

        r_total = r_hot_conv_new + r_hot_tim + r_teg + r_cold_tim + r_cold_conv_new
        r.r_hot_conv = r_hot_conv_new
        r.r_cold_conv = r_cold_conv_new
        r.r_total = r_total

    # ---- Final values ----
    r.heat_per_teg_w = q_per_teg
    r.total_heat_input_w = total_heat

    # Temperature profile
    r.t_hot_fin_surface_c = t_hot_avg - q_per_teg * r.r_hot_conv
    r.t_teg_hot_c = r.t_hot_fin_surface_c - q_per_teg * r.r_hot_tim
    r.t_teg_cold_c = r.t_teg_hot_c - q_per_teg * r.r_teg
    r.t_cold_fin_surface_c = r.t_teg_cold_c - q_per_teg * r.r_cold_tim

    # Delta-T across TEG
    r.dt_across_teg_c = r.t_teg_hot_c - r.t_teg_cold_c

    # TEG electrical performance
    teg_perf = teg.electrical_output(r.dt_across_teg_c)
    r.power_per_teg_w = teg_perf["power_w"]
    r.teg_efficiency = teg_perf["efficiency"]
    r.teg_voltage_v = teg_perf["voltage_v"]
    r.teg_current_a = teg_perf["current_a"]

    r.gross_electrical_w = r.power_per_teg_w * cfg.teg_count
    r.total_heat_rejection_w = r.total_heat_input_w - r.gross_electrical_w

    # Flow rates
    r.hot_flow_rate_m3s = hot_vol_flow
    r.hot_flow_rate_gpm = hot_vol_flow * 15850.3  # m^3/s -> GPM
    r.hot_velocity_channel_ms = velocity
    r.hot_reynolds = re
    r.hot_nusselt = nu
    r.hot_h_conv = h_hot

    r.cold_flow_rate_m3s = cold_vol_flow
    r.cold_flow_rate_gpm = cold_vol_flow * 15850.3

    # ---- Pressure drop ----
    # Channel pressure drop (Darcy-Weisbach)
    f_hot = friction_factor(re, d_h=dh)
    r.hot_dp_channel_pa = f_hot * (hx.channel_length_m / dh) * 0.5 * hot_props["rho"] * velocity**2

    # Manifold pressure drop (estimate: velocity in manifold header)
    n_towers = max(1, cfg.teg_count // (cfg.tegs_per_panel * cfg.panels_per_tower))
    manifold_area = math.pi * (hx.manifold_id_m / 2.0)**2
    manifold_vel = hot_vol_flow / manifold_area if manifold_area > 0 else 0.0
    re_manifold = hot_props["rho"] * manifold_vel * hx.manifold_id_m / hot_props["mu"]
    f_manifold = friction_factor(re_manifold, d_h=hx.manifold_id_m)
    # Assume ~2m of manifold per tower
    manifold_length = n_towers * 2.0
    r.hot_dp_manifold_pa = (f_manifold * (manifold_length / hx.manifold_id_m)
                            * 0.5 * hot_props["rho"] * manifold_vel**2)

    # Pipe pressure drop
    pipe_area = math.pi * (cfg.pipe_id_m / 2.0)**2
    pipe_vel = hot_vol_flow / pipe_area if pipe_area > 0 else 0.0
    re_pipe = hot_props["rho"] * pipe_vel * cfg.pipe_id_m / hot_props["mu"]
    f_pipe = friction_factor(re_pipe, d_h=cfg.pipe_id_m)
    r.hot_dp_pipe_pa = (f_pipe * (cfg.hot_pipe_length_m / cfg.pipe_id_m)
                        * 0.5 * hot_props["rho"] * pipe_vel**2)

    r.hot_dp_total_pa = r.hot_dp_channel_pa + r.hot_dp_manifold_pa + r.hot_dp_pipe_pa

    # Cold side: similar (simplified)
    r.cold_dp_total_pa = r.hot_dp_total_pa * 0.9  # slightly lower viscosity

    # ---- Pump power ----
    r.pump_power_hot_w = (r.hot_dp_total_pa * hot_vol_flow) / cfg.pump_efficiency
    r.pump_power_cold_w = (r.cold_dp_total_pa * cold_vol_flow) / cfg.pump_efficiency
    r.pump_power_total_w = r.pump_power_hot_w + r.pump_power_cold_w

    # Fan power (dry cooler estimate: ~15 W per kW rejected)
    r.fan_power_w = r.total_heat_rejection_w / 1000.0 * 15.0

    # Electronics (Controller Nodes + PCMs)
    n_pcms = max(1, cfg.teg_count // 36)
    n_nodes = max(1, n_pcms // 3)
    r.electronics_w = n_pcms * 1.5 + n_nodes * 3.0  # estimated

    # ---- Net output ----
    total_parasitic = r.pump_power_total_w + r.fan_power_w + r.electronics_w
    r.net_electrical_w = r.gross_electrical_w - total_parasitic
    r.net_electrical_kw = r.net_electrical_w / 1000.0
    r.parasitic_fraction = total_parasitic / r.gross_electrical_w if r.gross_electrical_w > 0 else 0.0

    return r


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def print_results(cfg: SystemConfig, r: ModelResults) -> None:
    """Print a formatted summary of model results."""
    teg = cfg.teg_spec

    print("=" * 72)
    print(f"  TEG SYSTEM MODEL -- {teg.name}")
    print(f"  {r.total_teg_count} TEGs, hot inlet {cfg.hot_inlet_c} C, "
          f"cold inlet {cfg.cold_inlet_c} C")
    print("=" * 72)

    print(f"\n--- TEG Performance (per module) ---")
    print(f"  Delta-T across TEG:    {r.dt_across_teg_c:8.1f} C")
    print(f"  Heat flux per TEG:     {r.heat_per_teg_w:8.1f} W")
    print(f"  Electrical output:     {r.power_per_teg_w:8.2f} W")
    print(f"  MPP voltage:           {r.teg_voltage_v:8.2f} V")
    print(f"  MPP current:           {r.teg_current_a:8.2f} A")
    print(f"  TEG efficiency:        {r.teg_efficiency * 100:8.2f} %")

    print(f"\n--- Temperature Profile (per TEG) ---")
    print(f"  Hot fluid (avg):       {r.t_hot_fluid_avg_c:8.1f} C")
    print(f"  Hot fin surface:       {r.t_hot_fin_surface_c:8.1f} C")
    print(f"  TEG hot side:          {r.t_teg_hot_c:8.1f} C")
    print(f"  TEG cold side:         {r.t_teg_cold_c:8.1f} C")
    print(f"  Cold fin surface:      {r.t_cold_fin_surface_c:8.1f} C")
    print(f"  Cold fluid (avg):      {r.t_cold_fluid_avg_c:8.1f} C")

    print(f"\n--- Thermal Resistance Chain (per TEG, C/W) ---")
    print(f"  Hot convection:        {r.r_hot_conv:8.3f}")
    print(f"  Hot TIM (graphite):    {r.r_hot_tim:8.3f}")
    print(f"  TEG module:            {r.r_teg:8.3f}")
    print(f"  Cold TIM (silicone):   {r.r_cold_tim:8.3f}")
    print(f"  Cold convection:       {r.r_cold_conv:8.3f}")
    print(f"  TOTAL:                 {r.r_total:8.3f}")
    print(f"  TEG fraction:          {r.r_teg / r.r_total * 100:8.1f} %")

    print(f"\n--- Flow Rates ---")
    print(f"  Hot fluid:  {r.hot_fluid_name}")
    print(f"    Volume flow:         {r.hot_flow_rate_gpm:8.1f} GPM "
          f"({r.hot_flow_rate_m3s * 1000:6.2f} L/s)")
    print(f"    Channel velocity:    {r.hot_velocity_channel_ms:8.3f} m/s")
    print(f"    Reynolds number:     {r.hot_reynolds:8.0f}")
    print(f"    Nusselt number:      {r.hot_nusselt:8.1f}")
    print(f"    h (convection):      {r.hot_h_conv:8.0f} W/m2-K")
    print(f"  Cold fluid: {r.cold_fluid_name}")
    print(f"    Volume flow:         {r.cold_flow_rate_gpm:8.1f} GPM")

    print(f"\n--- Pressure Drop (hot side) ---")
    print(f"  Fin channels:          {r.hot_dp_channel_pa:8.0f} Pa "
          f"({r.hot_dp_channel_pa / 6895:5.2f} psi)")
    print(f"  Manifold:              {r.hot_dp_manifold_pa:8.0f} Pa "
          f"({r.hot_dp_manifold_pa / 6895:5.2f} psi)")
    print(f"  Piping:                {r.hot_dp_pipe_pa:8.0f} Pa "
          f"({r.hot_dp_pipe_pa / 6895:5.2f} psi)")
    print(f"  TOTAL:                 {r.hot_dp_total_pa:8.0f} Pa "
          f"({r.hot_dp_total_pa / 6895:5.2f} psi)")

    print(f"\n--- System Totals ---")
    print(f"  Total TEGs:            {r.total_teg_count:>8d}")
    print(f"  Total heat input:      {r.total_heat_input_w / 1000:8.1f} kW")
    print(f"  Total heat rejection:  {r.total_heat_rejection_w / 1000:8.1f} kW")
    print(f"  Gross electrical:      {r.gross_electrical_w / 1000:8.2f} kW")
    print(f"  Pump power (hot):      {r.pump_power_hot_w:8.1f} W")
    print(f"  Pump power (cold):     {r.pump_power_cold_w:8.1f} W")
    print(f"  Fan power (est):       {r.fan_power_w:8.1f} W")
    print(f"  Electronics:           {r.electronics_w:8.1f} W")
    print(f"  Total parasitic:       {r.pump_power_total_w + r.fan_power_w + r.electronics_w:8.1f} W")
    print(f"  Parasitic fraction:    {r.parasitic_fraction * 100:8.1f} %")
    print(f"  ──────────────────────────────────")
    print(f"  NET ELECTRICAL OUTPUT:  {r.net_electrical_kw:7.2f} kW")
    print("=" * 72)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_config_from_args(args) -> SystemConfig:
    """Build a SystemConfig from CLI args."""
    teg = TEG_CATALOG.get(args.teg_type, MARLOW_TG1_1008)

    # Auto-select fluid based on temperature
    if args.hot_temp > 220:
        hot_fluid = "therminol"
        cold_fluid = "therminol"
    else:
        hot_fluid = "water_glycol"
        cold_fluid = "water_glycol"

    return SystemConfig(
        teg_count=args.teg_count,
        teg_spec=teg,
        hot_fluid=hot_fluid,
        cold_fluid=cold_fluid,
        hot_inlet_c=args.hot_temp,
        cold_inlet_c=args.cold_temp,
        target_dt_fluid_c=args.dt_fluid,
    )


def main():
    parser = argparse.ArgumentParser(
        description="TEG system thermal-hydraulic model (CoolProp)")
    parser.add_argument("--teg-count", type=int, default=1620,
                        help="Number of TEGs (default: 1620)")
    parser.add_argument("--teg-type", choices=list(TEG_CATALOG.keys()),
                        default="marlow",
                        help="TEG type (default: marlow)")
    parser.add_argument("--hot-temp", type=float, default=200.0,
                        help="Hot fluid inlet temperature C (default: 200)")
    parser.add_argument("--cold-temp", type=float, default=40.0,
                        help="Cold fluid inlet temperature C (default: 40)")
    parser.add_argument("--dt-fluid", type=float, default=10.0,
                        help="Target fluid temperature change across HX (default: 10)")
    args = parser.parse_args()

    cfg = build_config_from_args(args)
    results = run_model(cfg)
    print_results(cfg, results)

    # Also run quick comparison if default
    if args.teg_count == 1620 and args.teg_type == "marlow":
        print("\n\n")
        cfg2 = SystemConfig(
            teg_count=792,
            teg_spec=THERMONAMIC_PB12611,
            hot_fluid="therminol",
            cold_fluid="therminol",
            hot_inlet_c=350.0,
            cold_inlet_c=100.0,
        )
        r2 = run_model(cfg2)
        print_results(cfg2, r2)


if __name__ == "__main__":
    main()
