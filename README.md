# PGC -- Power Generating Combustor

Thermal modeling, heat exchanger design, container layout, and cost analysis for thermoelectric generator (TEG) power plants.

## What's in this repo

| Directory | Contents |
|-----------|----------|
| `bench/` | Benchtop test plans, photos, BOMs (legacy Alphabet PGC data) |
| `docs/` | System architecture, ground loop sizing |
| `heat-exchanger/` | HX design reference and notes |
| `container/` | 40ft container layout and thermal zoning |
| `modeling/coolprop/` | CoolProp + Python thermal-hydraulic calculator and McF-to-watts model |
| `modeling/openfoam/` | OpenFOAM CFD case for single HX cell (conjugate heat transfer) |
| `modeling/openmodelica/` | OpenModelica system-level loop model (transient, ground loop) |
| `costs/` | Programmatic cost model for 10 kW+ systems |

## Quick Start -- CoolProp Models

```bash
pip install -r requirements.txt

# Run the core thermal model (prints summary table + saves plots)
python modeling/coolprop/teg_system_model.py

# McF-to-watts-to-cost calculator
python modeling/coolprop/mcf_to_watts.py

# Full parametric sweep (TEG count, temps, fuel cost)
python modeling/coolprop/sweep.py
```

## Quick Start -- OpenFOAM

Requires [OpenFOAM v2312+](https://www.openfoam.com/).

```bash
cd modeling/openfoam/hx_cell
./Allrun
```

## Quick Start -- OpenModelica

Requires [OpenModelica 1.22+](https://openmodelica.org/).

```bash
cd modeling/openmodelica
omc simulate.mos
```

## Related Repositories

| Repo | Description |
|------|-------------|
| [thermogenzero/node](https://github.com/thermogenzero/node) | Controller Node hardware (LIFCL-40 / CertusPro-NX) |
| [thermogenzero/node-hdl](https://github.com/thermogenzero/node-hdl) | Controller Node HDL (MPPT, PoVC, estream) |
| [thermogenzero/pcm](https://github.com/thermogenzero/pcm) | Power Conversion Module hardware (iCE40 + buck + ADC) |
| [thermogenzero/pcm-hdl](https://github.com/thermogenzero/pcm-hdl) | PCM firmware (iCE40 SPI slave, PWM, ADC driver) |

## Related Documents (other repos)

- [HEAT-EXCHANGER-SPEC-V1.md](https://github.com/synergythermogen/engineering) -- Full HX engineering spec (SynergyThermogen)
- [10KW-SYSTEM-COST-ANALYSIS.md](https://github.com/thermogenzero/ip) -- Per-tier BOM + 10 kW rollup
- [TEG-CHANNEL-ARCHITECTURE-TRADE-STUDY.md](https://github.com/thermogenzero/ip) -- 3-tier architecture decision

## License

Proprietary -- Thermogen Zero / Synergy Carbon
