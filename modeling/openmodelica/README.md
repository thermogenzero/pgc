# OpenModelica -- TEG Plant System Model

## Prerequisites

- [OpenModelica 1.22+](https://openmodelica.org/download/)
- Modelica Standard Library (included with OpenModelica)

## What This Models

Full system-level model of the PGC thermal loop:

```
    Burner  ->  Hot Pipe  ->  Hot HX  ->  TEG Array  ->  Cold HX  ->  Cold Pipe
       ^                                                                    |
       |                                                                    v
    Fuel Input                                              Heat Rejection Sink
    (McF/day)                                     (Ground Loop or Dry Cooler)
```

### Components

| Component | Modelica Class | Description |
|-----------|---------------|-------------|
| `Burner` | `TegPlant.Burner` | Fuel -> thermal power, efficiency parameter |
| `HotPipe` | `TegPlant.Pipe` | Insulated hot-side pipe with heat loss |
| `HotHX` | `TegPlant.HeatExchanger` | Effectiveness-NTU model |
| `TEGArray` | `TegPlant.TEGArray` | N TEGs in parallel, Seebeck + thermal resistance |
| `ColdHX` | `TegPlant.HeatExchanger` | Cold-side heat exchanger |
| `ColdPipe` | `TegPlant.Pipe` | Cold-side return pipe |
| `GroundLoop` | `TegPlant.GroundLoop` | Multi-borehole ground heat exchanger |
| `DryCooler` | `TegPlant.DryCooler` | Air-side heat rejection with fan |
| `Pump` | `TegPlant.Pump` | Centrifugal pump with efficiency curve |

## Running

### Command line (omc)

```bash
omc simulate.mos
```

### OMEdit (GUI)

1. Open `TegPlant.mo` in OMEdit
2. Simulate with default parameters
3. Plot temperature traces and power output

## Key Outputs

- `tegArray.P_electrical` -- total TEG electrical output (W)
- `tegArray.T_hot` -- TEG hot-side temperature (K)
- `tegArray.T_cold` -- TEG cold-side temperature (K)
- `groundLoop.T_soil` -- soil temperature over time (K)
- `hotPump.P_shaft` -- pump power consumption (W)
- System COP: electrical out / fuel in

## Simulation Scenarios

The default simulation runs for 1 year (31,536,000 seconds) to capture:
- Startup transient (first few hours)
- Seasonal ambient temperature variation
- Ground loop thermal drift

Edit `simulate.mos` to change duration or parameters.
