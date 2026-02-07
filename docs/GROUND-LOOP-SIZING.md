# Ground Loop Sizing Guide

## Why Ground Loop

Ground loops (closed-loop geothermal boreholes) provide the most reliable long-term
heat rejection for containerized TEG systems:

- No moving parts beyond the circulating pump
- No fans, no evaporative water consumption
- Stable year-round performance regardless of ambient temperature
- 50+ year borehole life
- Minimal maintenance

## Sizing Methodology

### Heat Rejection Load

The cold-side heat rejection equals the total thermal input minus the electrical
output (which leaves the system as useful work).

```
Q_reject = Q_thermal_in - P_electrical

Example (10 kW BiTe system):
  Q_thermal_in = 1,620 TEGs x 122 W/TEG  = 197,640 W thermal
  P_electrical = 1,620 TEGs x 6.16 W/TEG =   9,979 W electrical
  Q_reject     = 197,640 - 9,979          = 187,661 W = 188 kW
```

### Borehole Thermal Capacity

| Parameter | Typical Value | Notes |
|-----------|--------------|-------|
| Borehole depth | 100-150 m (330-500 ft) | Standard vertical |
| Borehole diameter | 150 mm (6 in) | Standard rotary drill |
| Grout thermal conductivity | 0.8-1.5 W/m-K | Enhanced grout recommended |
| Soil thermal conductivity | 1.0-3.0 W/m-K | Site-specific (TRT recommended) |
| Heat rejection per meter | 40-80 W/m | Depends on soil, spacing |
| Heat rejection per borehole | 4-12 kW | 100-150m depth |

### Sizing Table

| System Size | Heat Rejection | Boreholes (@ 6 kW ea) | Total Drilling (m) | Est. Cost |
|-------------|---------------|----------------------|--------------------|-----------| 
| 5 kW_e | 94 kW_th | 16 | 2,400 | $60,000 |
| 10 kW_e | 188 kW_th | 32 | 4,800 | $120,000 |
| 25 kW_e | 470 kW_th | 78 | 11,700 | $290,000 |
| 50 kW_e | 940 kW_th | 157 | 23,500 | $590,000 |

Cost assumption: $25/ft drilled, grouted, piped ($82/m).

### Borehole Layout

```
    TYPICAL 32-BOREHOLE FIELD (10 kW system)

    Spacing: 6m (20 ft) center-to-center minimum

    O   O   O   O   O   O   O   O        O = borehole
                                           Each: 150m deep
    O   O   O   O   O   O   O   O        6 kW rejection

    O   O   O   O   O   O   O   O

    O   O   O   O   O   O   O   O

    Field size: ~42m x 18m (140ft x 60ft)
    Total area: ~760 m2 (~8,200 ft2)
```

## Long-Term Thermal Balance

Ground loops can experience thermal drift (soil temperature rising over years)
if heat is only rejected, never extracted. For TEG systems this is the normal case.

**Mitigation strategies:**
1. Oversize the borehole field by 20-30% for thermal margin
2. Use wider borehole spacing (8m instead of 6m)
3. Monitor ground temperature with sentinel boreholes
4. If available, use winter ambient to pre-cool ground (seasonal recharge)

The OpenModelica model in `modeling/openmodelica/TegPlant.mo` includes a
multi-year borehole simulation to predict thermal drift.
