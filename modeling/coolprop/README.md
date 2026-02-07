# CoolProp + Python Thermal Models

## Prerequisites

```bash
pip install -r ../../requirements.txt
```

## Scripts

### `teg_system_model.py` -- Core Thermal-Hydraulic Calculator

Models the complete heat transfer chain from hot fluid through the HX fins, TIM,
TEG, cold-side TIM, cold HX, to cold fluid. Uses CoolProp for real fluid properties
at operating temperature and pressure.

```bash
python teg_system_model.py
```

**Outputs:**
- Per-TEG thermal resistance breakdown
- Required flow rates (hot and cold loops)
- Pressure drop through HX channels
- Pump power (parasitic)
- Net electrical output
- Summary table printed to terminal

### `mcf_to_watts.py` -- Fuel-to-Power-to-Cost

Converts natural gas input (McF/day) through the full energy chain to net
electrical output and levelized cost.

```bash
python mcf_to_watts.py
```

**Outputs:**
- McF/day required for 10 kW, 25 kW, 50 kW targets
- $/kWh at $2.50, $4.00, $6.00 per McF
- Sensitivity table and plot

### `sweep.py` -- Parametric Sweep

Sweeps TEG count (500-8,000), hot-side temperature (200/320/400 C), and gas price
to generate system-level trade curves.

```bash
python sweep.py
```

**Outputs:**
- TEG count vs net kW
- McF/day vs net kW
- $/kWh vs system scale
- Ground loop borehole count vs system size
