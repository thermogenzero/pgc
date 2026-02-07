# Cost Models

## Reference Document

The detailed 10 kW cost analysis (BiTe vs PbTe) lives in:

- **File:** `../../ThermogenZero/ip/specs/10KW-SYSTEM-COST-ANALYSIS.md`
- **Covers:** Per-tier BOM, heat exchanger, fluid system, cooling, container, lifecycle

## Programmatic Model

`cost_model.py` implements the same cost analysis as a parametric Python model:

```bash
python cost_model.py
```

### What it calculates

- Per-tier electronics cost (TEG interconnect, PCM, Controller Node)
- TEG module cost at volume pricing
- Heat exchanger cost (copper vs stainless)
- Fluid system cost (water/glycol vs thermal oil)
- Cooling system cost (dry cooler vs ground loop)
- Container and integration
- Full system rollup at 10 kW, 25 kW, 50 kW targets
- Lifecycle cost including TEG replacement
- Cost per kW and cost per kWh over system life
