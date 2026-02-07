# PGC System Architecture

## Overview

The Power Generating Combustor (PGC) is a containerized thermoelectric generator
power plant that converts waste gas (or any heat source) into electricity via TEGs.

```
    FUEL (McF/day)
         │
         ▼
    ┌──────────────┐
    │  LOW-NOx      │   Efficiency: 85-92%
    │  BURNER       │   Input: natural gas, wellhead gas, biogas
    │               │   Output: 200-400 C hot fluid
    └──────┬───────┘
           │
    Hot fluid loop (water/glycol or thermal oil)
           │
           ▼
    ┌──────────────────────────────────────────────────────┐
    │                   TEG ARRAY                           │
    │                                                       │
    │   ┌─────────┐  ┌─────────┐       ┌─────────┐       │
    │   │ Tower 1 │  │ Tower 2 │  ...  │ Tower N │       │
    │   │ 80 TEGs │  │ 80 TEGs │       │ 80 TEGs │       │
    │   │ 500 W   │  │ 500 W   │       │ 500 W   │       │
    │   └────┬────┘  └────┬────┘       └────┬────┘       │
    │        │             │                 │             │
    │        └─────────────┴────────┬────────┘             │
    │                               │                      │
    │                        48 V DC Bus                    │
    └───────────────────────────────┬──────────────────────┘
                                    │
                             Net electrical
                               output
           │
    Cold fluid loop
           │
           ▼
    ┌──────────────────────────────────────────┐
    │          HEAT REJECTION                   │
    │                                           │
    │   Option A: Dry cooler (fans)            │
    │   Option B: Ground loop (boreholes)      │
    │   Option C: Absorption chiller           │
    │   Option D: Hybrid (A + B or A + C)      │
    │                                           │
    └──────────────────────────────────────────┘
```

## Energy Flow

```
    1 McF natural gas
         │
         │  1,020,000 BTU  =  299 kWh thermal
         │
         ▼
    Burner (88% eff)
         │
         │  263 kWh thermal to fluid
         │  (~5% pipe losses)
         │
         ▼
    250 kWh to HX hot side
         │
         ├──── TEG electrical output: ~5% eff ──── 12.5 kWh_e
         │
         └──── Heat to cold side: ~237.5 kWh thermal
                    │
                    ▼
              Heat rejection (ground loop / dry cooler)
                    │
              Parasitic loads: pumps (~0.5 kW), fans (~0.3 kW),
                               electronics (~0.1 kW)
                    │
              Net output: ~11.6 kWh_e per McF
```

## Key Design Parameters

| Parameter | BiTe (200 C) | PbTe Hybrid (350 C) | Pb-Alphabet (400 C) |
|-----------|-------------|---------------------|---------------------|
| Hot-side temp | 200 C | 350 C | 400 C |
| Cold-side temp | 50 C | 100 C | 100 C |
| TEG delta-T | 150 C | 250 C | 300 C |
| TEG efficiency | ~5% | ~4.2% | ~6.5% (est) |
| Power per TEG | 6.16 W | ~13 W | ~19 W (est) |
| TEGs for 10 kW | 1,620 | 792 | ~526 |
| Fluid system | Water/glycol | Therminol VP-1 | Therminol VP-1 |
| HX material | Copper | Stainless steel | Stainless steel |
| TEG lifetime | 20+ years | 4-14 years | TBD |

## Thermal Zones (Container)

```
    40ft HIGH-CUBE CONTAINER (12.0m x 2.4m x 2.9m)

    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │  HOT ZONE            SERVICE AISLE          COOL ZONE           │
    │  (insulated)         (walk-through)         (electronics)       │
    │                                                                  │
    │  Hot manifold     TEG towers face        Controller Nodes       │
    │  Burner return    service aisle          48V bus bar            │
    │  200-400 C        Cold manifold          Power conditioning    │
    │                   accessible             Network switch         │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
```
