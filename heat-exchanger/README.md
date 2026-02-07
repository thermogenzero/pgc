# Heat Exchanger Design

## Reference Specification

The full heat exchanger engineering specification lives in the SynergyThermogen repo:

- **Repo:** [synergythermogen/engineering](https://github.com/synergythermogen/engineering)
- **File:** `heat-exchanger-design/HEAT-EXCHANGER-SPEC-V1.md`
- **Local path:** `../../SynergyThermogen/engineering/heat-exchanger-design/HEAT-EXCHANGER-SPEC-V1.md`

## Summary

Architecture: vertical header with parallel fin channels (brazed copper for hot side).

### Single TEG Cell Geometry

```
    9 parallel channels, 3mm gap, 1mm copper fins
    40mm x 40mm face (matches Marlow TG1-1008)

    ┌──────────────────────────────────┐
    │  ▓  ▓  ▓  ▓  ▓  ▓  ▓  ▓  ▓  ▓  │   10 fins (1mm each)
    │     3mm channels (x9)            │   9 channels (3mm each)
    │  Border walls: 1.5mm x 2        │   Total: 40mm
    └──────────────────────────────────┘
```

### Thermal Resistance Chain (per TEG @ 122 W)

| Stage | Delta-T |
|-------|---------|
| Hot fluid -> fin (convection) | 9.3 C |
| Through copper fin | < 0.1 C |
| Fin -> TEG (TIM, graphite) | 7.6 C |
| Through TEG | 180 C |
| TEG -> cold fin (TIM, silicone) | 9.1 C |
| Cold fin -> cold fluid | 8.8 C |
| **Total** | **~215 C** |

### Panel Configurations

| Config | TEGs | Electrical | Heat Flow |
|--------|------|-----------|-----------|
| Single panel | 12 | 74 W | 1,469 W |
| Single panel | 16 | 99 W | 1,958 W |
| Tower (5 panels) | 80 | 500 W | 9,800 W |

## CAD Drawings

See `../../SynergyThermogen/engineering/heat-exchanger-design/cad-drawings/` for:
- DWG-001: TEG cell cutaway
- DWG-002: 12-TEG panel assembly
- DWG-003: Vertical tower module
- DWG-004: Container floor plan
