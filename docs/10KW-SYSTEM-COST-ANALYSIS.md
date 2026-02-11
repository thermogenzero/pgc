# 10 kW TEG System Cost Analysis

**Document Version:** 1.0
**Date:** February 6, 2026
**Status:** Preliminary Estimate

---

## Executive Summary

This document compares two 10 kW thermoelectric generator system architectures using the new 3-tier PCM/Node design:

| | **Scenario A: BiTe (200 C)** | **Scenario B: PbTe Hybrid (350 C)** |
|---|---|---|
| TEG | Marlow TG1-1008 | Thermonamic TEG1-PB-12611-6.0 |
| Hot side temp | 200 C | 350 C |
| Cold side temp | 50 C | 100 C |
| Power per TEG | 6.16 W | ~13 W |
| TEGs for 10 kW | 1,620 | 792 |
| PCM boards | 45 | 22 |
| Controller Nodes | 15 | 8 |
| Fluid system | Water/glycol | Therminol VP-1 thermal oil |
| **Total system cost** | **$109,200** | **$101,500** |
| **Cost per kW** | **$10,920/kW** | **$10,150/kW** |

Scenario B produces the same power with **51% fewer TEGs** and **47% fewer electronics boards**, but requires a more expensive thermal oil fluid system and stainless steel heat exchangers. The net result is roughly cost-neutral, with Scenario B having a modest 7% cost advantage and significant scaling advantages.

---

## 1. TEG Module Specifications

### Scenario A: Marlow TG1-1008 (BiTe)

| Parameter | Value | Source |
|-----------|-------|--------|
| Material | Bismuth Telluride (BiTe) | Marlow datasheet |
| Dimensions | 40 x 40 mm | Marlow datasheet |
| Max hot side | 200 C (230 C intermittent) | HEAT-EXCHANGER-SPEC-V1.md |
| Operating hot side | 200 C | Design point |
| Cold side | 50 C | Design point |
| Delta-T | 150 C | |
| Thermal resistance | 1.47-1.58 C/W | Marlow datasheet |
| Heat flux per TEG | 122 W | HEAT-EXCHANGER-SPEC-V1.md |
| **Electrical output** | **6.16 W** | @ 180 C dT |
| Efficiency | 5.03% | |
| Open-circuit voltage | ~6 V | |
| MPP voltage | ~3 V | |
| MPP current | ~2 A | |
| **Unit price (qty 100+)** | **$25.00** | BOM-ESTIMATE.md |
| Life expectancy | 20+ years | @ 200 C continuous |

### Scenario B: Thermonamic TEG1-PB-12611-6.0 (BiTe-PbTe Hybrid)

| Parameter | Value | Source |
|-----------|-------|--------|
| Material | Hybrid BiTe + PbTe | Thermonamic datasheet |
| Dimensions | 56 x 56 mm | Thermonamic datasheet |
| Max hot side | 360 C (optimized 260-360 C) | Thermonamic datasheet |
| Operating hot side | 350 C | Design point |
| Cold side | 100 C (thermal oil return) | Design point |
| Delta-T | 250 C | |
| Heat flux per TEG | ~310 W (at 350 C/30 C test) | Thermonamic datasheet |
| **Electrical output (test)** | **21.7 W** (@ 350 C / 30 C) | Thermonamic datasheet |
| **Electrical output (derated)** | **~13 W** (@ 350 C / 100 C) | Estimated, (250/320)^2 scaling |
| Efficiency | ~4.2% | At operating conditions |
| Open-circuit voltage | 9.2 V | Thermonamic datasheet |
| MPP voltage | ~4.6 V | |
| MPP current | ~2.8 A | |
| Match load resistance | 0.97 Ohm | |
| **Unit price (qty 1-99)** | **$69.00** | thermoelectric-generator.com |
| **Unit price (qty 100+)** | **~$45-50** | Estimated volume discount |
| Life expectancy | 4 years | @ 350 C continuous |
| Life expectancy | 8 years | @ 320 C continuous |
| Life expectancy | 14 years | @ 280 C continuous |

**Note:** The Thermonamic TEG is 56x56mm vs Marlow's 40x40mm. This affects heat exchanger cell sizing but not per-TEG cost analysis.

---

## 2. System Sizing

### Scenario A: BiTe -- 10 kW

| Parameter | Value | Calculation |
|-----------|-------|-------------|
| Target output | 10,000 W | |
| Power per TEG | 6.16 W | @ 180 C dT |
| TEGs needed (gross) | 1,623 | 10,000 / 6.16 |
| **TEGs (rounded to 36-ch PCMs)** | **1,620** | 45 PCMs x 36 TEGs |
| **Actual output** | **9,979 W** | 1,620 x 6.16 |
| PCM boards | 45 | 1,620 / 36 |
| Controller Nodes (3 PCMs each) | 15 | 45 / 3 |
| Heat rejected per TEG | 122 W | |
| Total heat rejection | 197,640 W | 1,620 x 122 |

### Scenario B: PbTe Hybrid -- 10 kW

| Parameter | Value | Calculation |
|-----------|-------|-------------|
| Target output | 10,000 W | |
| Power per TEG | 13 W | @ 350 C / 100 C (derated) |
| TEGs needed (gross) | 769 | 10,000 / 13 |
| **TEGs (rounded to 36-ch PCMs)** | **792** | 22 PCMs x 36 TEGs |
| **Actual output** | **10,296 W** | 792 x 13 |
| PCM boards | 22 | 792 / 36 |
| Controller Nodes (3 PCMs each) | 8 | ceil(22 / 3) |
| Heat flux per TEG | ~310 W | |
| Total heat rejection | ~245,520 W | 792 x 310 |

### Sizing Comparison

| | Scenario A (BiTe) | Scenario B (PbTe) | Ratio |
|---|---|---|---|
| TEGs | 1,620 | 792 | **0.49x** |
| PCM boards | 45 | 22 | **0.49x** |
| Controller Nodes | 15 | 8 | **0.53x** |
| Total electronics boards | 60 | 30 | **0.50x** |
| Heat rejection | 198 kW | 246 kW | 1.24x |

---

## 3. Per-Tier Electronics Cost Breakout

### Tier 1: TEG Interconnect Board (Hot Zone -- Passive)

The TEG Interconnect Board is a simple passive PCB with screw terminals or solder pads. No active components.

| Component | Per Board | Qty/Board | Unit Cost | Board Cost |
|-----------|-----------|-----------|-----------|------------|
| PCB (2-layer, high-temp FR4 or ceramic) | 1 | 1 | $8 | $8.00 |
| Screw terminals (36 pairs) | 36 | 36 | $0.30 | $10.80 |
| High-temp wire connector to PCM | 1 | 1 | $3.00 | $3.00 |
| **Total per Interconnect Board** | | | | **$21.80** |

| | Scenario A | Scenario B |
|---|---|---|
| Boards needed | 45 | 22 |
| **Cost per board** | **$21.80** | **$21.80** |
| **Total Tier 1** | **$981** | **$480** |

### Tier 2: Power Conversion Module -- PCM (Warm Zone)

#### Scenario A: BiTe (12V input buck converters)

| Component | Qty/Board | Unit Cost | Extended |
|-----------|-----------|-----------|----------|
| iCE40 HX1K-TQ144 (I/O expander) | 1 | $7.00 | $7.00 |
| W25Q10CLSNIG (1Mbit SPI flash) | 1 | $0.75 | $0.75 |
| SiT8008 25MHz MEMS oscillator | 1 | $1.50 | $1.50 |
| ADS7950SBDBTR (12-bit 16-ch ADC) | 5 | $6.00 | $30.00 |
| N-ch MOSFET (30V, SOT-23) | 36 | $0.25 | $9.00 |
| Schottky diode (40V, SMA) | 36 | $0.15 | $5.40 |
| Power inductor (22uH, SMD) | 36 | $0.40 | $14.40 |
| Output capacitor (47uF, 1210) | 36 | $0.10 | $3.60 |
| Sense resistor (10mOhm, 2512) | 36 | $0.08 | $2.88 |
| Voltage divider pairs (0402) | 72 | $0.02 | $1.44 |
| MCP9600 thermocouple IC | 1 | $4.00 | $4.00 |
| RJ45 shielded (SPI to node) | 1 | $1.50 | $1.50 |
| Molex Mini-Fit Jr 2-pos (48V bus) | 1 | $1.00 | $1.00 |
| TEG input connectors (36x) | 36 | $0.30 | $10.80 |
| DC-DC 48V->3.3V (board power) | 1 | $4.00 | $4.00 |
| LDO 3.3V->1.2V (iCE40 core) | 1 | $0.75 | $0.75 |
| Decoupling caps, resistors, LEDs | 1 lot | $5.00 | $5.00 |
| PCB (6-layer, 100x150mm) | 1 | $10.00 | $10.00 |
| Assembly (automated) | 1 | $18.00 | $18.00 |
| **Total per PCM (Scenario A)** | | | **$131.02** |

#### Scenario B: PbTe (20V input buck converters)

Same as Scenario A except for higher-voltage buck components:

| Component | Change from A | Qty/Board | Unit Cost | Extended |
|-----------|--------------|-----------|-----------|----------|
| N-ch MOSFET (**40V**, DPAK) | Higher voltage | 36 | $0.40 | $14.40 |
| Schottky diode (**60V**, SMB) | Higher voltage | 36 | $0.25 | $9.00 |
| Power inductor (33uH, larger) | Higher inductance | 36 | $0.55 | $19.80 |
| Output capacitor (47uF, 1210) | Same | 36 | $0.10 | $3.60 |
| Sense resistor (5mOhm, 2512) | Lower R, higher I | 36 | $0.10 | $3.60 |
| ADC input divider (0402) | Need divider for 20V | 72 | $0.03 | $2.16 |
| All other components | Same as Scenario A | | | $84.49 |
| **Total per PCM (Scenario B)** | | | **$137.05** |

| | Scenario A | Scenario B |
|---|---|---|
| PCM boards | 45 | 22 |
| Cost per PCM | $131.02 | $137.05 |
| **Total Tier 2** | **$5,896** | **$3,015** |

### Tier 3: Controller Node (Cool Zone)

The Controller Node is identical for both scenarios -- it only talks to PCMs via SPI.

| Component | Qty | Unit Cost | Extended |
|-----------|-----|-----------|----------|
| LIFCL-40-9BG400C (Nexus 40K FPGA) | 1 | $18.00 | $18.00 |
| KSZ9031RNXIA (GbE PHY) | 1 | $5.00 | $5.00 |
| RJ45 + magnetics (Ethernet) | 1 | $4.00 | $4.00 |
| W25Q64JVSIQ (8MB SPI flash) | 1 | $1.50 | $1.50 |
| FM25V20A-G (256KB FRAM) | 1 | $4.00 | $4.00 |
| SiT8008 50MHz MEMS oscillator | 1 | $1.50 | $1.50 |
| DC-DC 48V->3.3V | 1 | $5.00 | $5.00 |
| DC-DC 48V->1.8V | 1 | $5.00 | $5.00 |
| LDO 1.8V->1.2V | 1 | $0.75 | $0.75 |
| RJ45 shielded x3 (SPI to PCMs) | 3 | $1.50 | $4.50 |
| Screw terminal (48V power in) | 1 | $1.00 | $1.00 |
| 2x5 header (JTAG) | 1 | $0.50 | $0.50 |
| LEDs (3x) + resistors | 3 | $0.20 | $0.60 |
| Decoupling caps (0402, 0805) | 1 lot | $3.00 | $3.00 |
| RGMII termination resistors | 12 | $0.02 | $0.24 |
| Pull-ups, dividers, misc | 1 lot | $2.00 | $2.00 |
| PCB (6-layer, 80x100mm, BGA) | 1 | $12.00 | $12.00 |
| Assembly (BGA reflow) | 1 | $20.00 | $20.00 |
| **Total per Controller Node** | | | **$88.59** |

| | Scenario A | Scenario B |
|---|---|---|
| Controller Nodes | 15 | 8 |
| Cost per node | $88.59 | $88.59 |
| **Total Tier 3** | **$1,329** | **$709** |

### Electronics Summary

| Tier | Scenario A (BiTe) | Scenario B (PbTe) | Savings |
|------|-------------------|-------------------|---------|
| Tier 1: TEG Interconnect | $981 | $480 | $501 |
| Tier 2: PCM | $5,896 | $3,015 | $2,881 |
| Tier 3: Controller Node | $1,329 | $709 | $620 |
| **Electronics Total** | **$8,206** | **$4,204** | **$4,002 (49%)** |

---

## 4. TEG Module Cost

| | Scenario A (BiTe) | Scenario B (PbTe) |
|---|---|---|
| TEG model | Marlow TG1-1008 | Thermonamic TEG1-PB-12611-6.0 |
| TEG quantity | 1,620 | 792 |
| Unit price (volume) | $25.00 | $50.00 |
| **TEG Total** | **$40,500** | **$39,600** |

Note: Thermonamic volume pricing estimated at ~$50/ea for 800+ qty (retail $69, volume discount ~28%).

---

## 5. Heat Exchanger Cost

### Scenario A: BiTe -- Copper Hot Side, Aluminum Cold Side

Based on BOM-ESTIMATE.md, scaled to 1,620 TEGs:

| Item | Qty | Unit Cost | Extended | Notes |
|------|-----|-----------|----------|-------|
| Hot side HX cell (brazed copper) | 1,620 | $12.00 | $19,440 | 40x40mm cells |
| Cold side HX cell (vacuum brazed Al) | 1,620 | $4.00 | $6,480 | |
| Graphite TIM (0.5mm pads) | 1,620 | $0.80 | $1,296 | Hot side |
| Silicone thermal pad | 1,620 | $0.50 | $810 | Cold side |
| Hot manifold (1.5" copper, Type L) | 130 ft | $8.00 | $1,040 | |
| Cold manifold (1.5" aluminum) | 130 ft | $4.00 | $520 | |
| Insulation (mineral wool) | 250 ft2 | $2.50 | $625 | |
| **Total HX (Scenario A)** | | | **$30,211** | |

### Scenario B: PbTe -- Stainless Steel Hot Side, Aluminum Cold Side

Higher temperatures require stainless steel hot-side HX and high-temp TIM:

| Item | Qty | Unit Cost | Extended | Notes |
|------|-----|-----------|----------|-------|
| Hot side HX cell (316L SS, machined) | 792 | $18.00 | $14,256 | 56x56mm cells, SS for 350 C |
| Cold side HX cell (vacuum brazed Al) | 792 | $5.00 | $3,960 | Larger cells (56mm) |
| Graphite TIM (high-temp, 0.5mm) | 792 | $2.50 | $1,980 | Rated to 400 C |
| Silicone thermal pad | 792 | $0.50 | $396 | Cold side |
| Hot manifold (1.5" 316L SS) | 80 ft | $12.00 | $960 | Stainless for thermal oil |
| Cold manifold (2" aluminum) | 80 ft | $6.00 | $480 | |
| Ceramic fiber insulation | 180 ft2 | $8.00 | $1,440 | Rated to 500 C |
| **Total HX (Scenario B)** | | | **$23,472** | |

| | Scenario A | Scenario B |
|---|---|---|
| HX cost per TEG | $18.65 | $29.64 |
| **Total HX** | **$30,211** | **$23,472** |

Scenario B uses fewer but more expensive heat exchanger cells. The net is 22% cheaper due to 51% fewer TEGs.

---

## 6. Fluid System Cost

### Scenario A: Water/Glycol (200 C)

| Item | Qty | Unit Cost | Extended | Notes |
|------|-----|-----------|----------|-------|
| Skid frame (steel, 3m x 2m) | 1 | $2,500 | $2,500 | |
| Methane burner (200 kW) | 1 | $3,500 | $3,500 | Heat source |
| Primary HX (shell/tube, 200 kW) | 1 | $4,000 | $4,000 | Burner to fluid |
| Hot loop pump (Grundfos) | 1 | $1,200 | $1,200 | Standard centrifugal |
| Cold loop pump (Grundfos) | 1 | $800 | $800 | Standard centrifugal |
| Expansion tanks (2x) | 2 | $300 | $600 | Hot + cold |
| Glycol (50 gal, 50/50 mix) | 1 lot | $400 | $400 | |
| Piping/valves (copper + stainless) | 1 lot | $1,500 | $1,500 | |
| Controls/sensors (thermocouples, flow) | 1 lot | $1,200 | $1,200 | |
| **Total Fluid System (A)** | | | **$15,700** | |

### Scenario B: Therminol VP-1 Thermal Oil (350 C)

| Item | Qty | Unit Cost | Extended | Notes |
|------|-----|-----------|----------|-------|
| Skid frame (steel, 3.5m x 2m) | 1 | $3,000 | $3,000 | Larger for oil system |
| Thermal oil heater (250 kW, methane) | 1 | $9,500 | $9,500 | 400 C capable |
| Therminol VP-1 (75 gal initial fill) | 75 gal | $55 | $4,125 | ~$55/gal volume |
| **Canned motor pump (high-temp)** | 1 | $6,500 | $6,500 | 350 C rated, mag-drive not available at this temp |
| Expansion tank (nitrogen blanket) | 1 | $650 | $650 | High-temp rated |
| Filter/strainer (SS) | 1 | $500 | $500 | |
| Piping/valves (316L SS, flanged) | 1 lot | $2,800 | $2,800 | All stainless, flanged |
| Controls/sensors (RTDs, flow, pressure) | 1 lot | $1,800 | $1,800 | High-temp rated |
| Safety (PRV, rupture disc) | 1 lot | $700 | $700 | Required for pressurized oil |
| Cold loop pump (glycol) | 1 | $1,000 | $1,000 | Standard duty |
| Cold loop expansion tank | 1 | $350 | $350 | |
| Cold loop glycol (75 gal) | 1 lot | $600 | $600 | |
| Cold loop piping | 1 lot | $1,200 | $1,200 | |
| **Total Fluid System (B)** | | | **$32,725** | |

### Fluid System Incremental Cost (B vs A)

| Item | Scenario A | Scenario B | Delta | Why |
|------|-----------|-----------|-------|-----|
| Heat source (burner/heater) | $3,500 | $9,500 | +$6,000 | Thermal oil heater is larger/more complex |
| Primary HX | $4,000 | -- | -$4,000 | Thermal oil heater is integrated |
| Hot loop pump | $1,200 | $6,500 | +$5,300 | Canned motor pump for 350 C (standard mag-drive limited to ~230 C) |
| Fluid | $400 | $4,125 | +$3,725 | Therminol VP-1 vs glycol |
| Piping | $1,500 | $2,800 | +$1,300 | All SS flanged vs copper |
| Expansion tank | $300 | $650 | +$350 | Nitrogen-blanketed for thermal oil |
| Safety | $0 | $700 | +$700 | PRV + rupture disc (pressurized system) |
| Controls | $1,200 | $1,800 | +$600 | High-temp sensors |
| Cold loop | $800 | $3,150 | +$2,350 | Larger cooler needed (246 kW vs 198 kW) |
| Skid | $2,500 | $3,000 | +$500 | Larger |
| **Total** | **$15,700** | **$32,725** | **+$17,025** | |

---

## 7. Cooling System Cost

### Scenario A: Dry Cooler (198 kW heat rejection at 50 C)

| Item | Qty | Unit Cost | Extended |
|------|-----|-----------|----------|
| Dry cooler (200 kW) | 1 | $9,000 | $9,000 |
| **Total Cooling (A)** | | | **$9,000** |

### Scenario B: Dry Cooler (246 kW heat rejection at 100 C)

Higher cold-side temperature (100 C) actually makes cooling easier -- more delta-T to ambient.

| Item | Qty | Unit Cost | Extended |
|------|-----|-----------|----------|
| Dry cooler (250 kW, high-temp glycol) | 1 | $10,000 | $10,000 |
| **Total Cooling (B)** | | | **$10,000** |

Note: Despite 24% more heat, the higher cold-side temp (100 C vs 50 C) provides a larger temperature difference to ambient air, making the cooler only marginally more expensive.

---

## 8. Container and Integration Cost

### Scenario A: BiTe (1,620 TEGs, 15 Nodes)

| Item | Qty | Unit Cost | Extended | Notes |
|------|-----|-----------|----------|-------|
| 40ft high-cube container (used, refurb) | 1 | $4,500 | $4,500 | |
| Tower frames (aluminum extrusion) | 20 | $120 | $2,400 | ~81 TEGs/tower |
| Slide rails | 20 | $45 | $900 | Pull-out service |
| Clamp assemblies | 100 | $25 | $2,500 | Spring-loaded |
| Quick-disconnect unions | 80 | $18 | $1,440 | Hot/cold manifolds |
| Floor grating | 120 ft2 | $12 | $1,440 | |
| Insulation (walls) | 400 ft2 | $3 | $1,200 | |
| Electrical panel (48V DC bus) | 1 | $1,800 | $1,800 | |
| Inverter (10 kW, grid-tie) | 1 | $2,500 | $2,500 | |
| HMI / Controls | 1 | $800 | $800 | Touchscreen + PLC |
| Safety equipment | 1 lot | $500 | $500 | Fire ext, signs |
| Cable trays / conduit | 1 lot | $1,000 | $1,000 | |
| 48V bus bar + wiring harnesses | 1 lot | $1,200 | $1,200 | |
| Cat5e cables (PCM to Node) | 45 | $5 | $225 | SPI links |
| Molex Mini-Fit Jr cables (48V power) | 45 | $8 | $360 | Power from PCMs |
| **Total Container (A)** | | | **$22,765** | |

### Scenario B: PbTe (792 TEGs, 8 Nodes)

| Item | Qty | Unit Cost | Extended | Notes |
|------|-----|-----------|----------|-------|
| 40ft high-cube container (used, refurb) | 1 | $4,500 | $4,500 | Same container |
| Tower frames (SS + aluminum) | 10 | $180 | $1,800 | SS for warm zone, fewer towers |
| Slide rails | 10 | $45 | $450 | |
| Clamp assemblies | 50 | $25 | $1,250 | |
| Quick-disconnect unions (SS, high-temp) | 40 | $35 | $1,400 | High-temp rated |
| Floor grating | 100 ft2 | $12 | $1,200 | |
| Insulation (walls + high-temp) | 400 ft2 | $3.50 | $1,400 | Higher-temp foam |
| Electrical panel (48V DC bus) | 1 | $1,800 | $1,800 | |
| Inverter (10 kW, grid-tie) | 1 | $2,500 | $2,500 | |
| HMI / Controls | 1 | $800 | $800 | |
| Safety equipment (+ gas detection) | 1 lot | $700 | $700 | Thermal oil requires gas detection |
| Cable trays / conduit | 1 lot | $800 | $800 | Fewer cables |
| 48V bus bar + wiring harnesses | 1 lot | $800 | $800 | Fewer nodes |
| Cat5e cables (PCM to Node) | 22 | $5 | $110 | SPI links |
| Molex Mini-Fit Jr cables (48V power) | 22 | $8 | $176 | Power from PCMs |
| **Total Container (B)** | | | **$19,686** | |

---

## 9. Full 10 kW System Rollup

### Scenario A: BiTe (Marlow TG1-1008, 200 C)

| Category | Cost | % of Total |
|----------|------|-----------|
| TEG modules (1,620x Marlow TG1-1008) | $40,500 | 37.1% |
| Heat exchangers (copper hot, Al cold) | $30,211 | 27.7% |
| Fluid system (water/glycol) | $15,700 | 14.4% |
| Cooling (dry cooler 200 kW) | $9,000 | 8.2% |
| Electronics: PCM boards (45x) | $5,896 | 5.4% |
| Electronics: Controller Nodes (15x) | $1,329 | 1.2% |
| Electronics: TEG Interconnect (45x) | $981 | 0.9% |
| Container and integration | $22,765 | 20.9% |
| **Subtotal** | **$126,382** | |
| Contingency (-15% volume discount) | -$18,957 | |
| **Estimated Total** | **~$107,400** | |
| **Cost per kW** | **~$10,740/kW** | |

### Scenario B: PbTe Hybrid (Thermonamic TEG1-PB-12611-6.0, 350 C)

| Category | Cost | % of Total |
|----------|------|-----------|
| TEG modules (792x Thermonamic) | $39,600 | 33.2% |
| Heat exchangers (SS hot, Al cold) | $23,472 | 19.7% |
| Fluid system (Therminol VP-1 thermal oil) | $32,725 | 27.4% |
| Cooling (dry cooler 250 kW) | $10,000 | 8.4% |
| Electronics: PCM boards (22x) | $3,015 | 2.5% |
| Electronics: Controller Nodes (8x) | $709 | 0.6% |
| Electronics: TEG Interconnect (22x) | $480 | 0.4% |
| Container and integration | $19,686 | 16.5% |
| **Subtotal** | **$129,687** | |
| Contingency (-15% volume discount) | -$19,453 | |
| **Estimated Total** | **~$110,200** | |
| **Cost per kW** | **~$11,020/kW** | |

---

## 10. Side-by-Side Comparison

| | **Scenario A (BiTe)** | **Scenario B (PbTe)** | **Delta** |
|---|---|---|---|
| **TEG** | Marlow TG1-1008 | Thermonamic TEG1-PB-12611-6.0 | |
| Hot side temp | 200 C | 350 C | +150 C |
| Power per TEG | 6.16 W | ~13 W | +111% |
| TEG count | 1,620 | 792 | **-51%** |
| TEG cost | $40,500 | $39,600 | -$900 |
| | | | |
| PCM boards | 45 | 22 | **-51%** |
| Controller Nodes | 15 | 8 | **-47%** |
| Total electronics | $8,206 | $4,204 | **-$4,002** |
| | | | |
| Heat exchangers | $30,211 | $23,472 | **-$6,739** |
| Fluid system | $15,700 | $32,725 | **+$17,025** |
| Cooling | $9,000 | $10,000 | +$1,000 |
| Container | $22,765 | $19,686 | -$3,079 |
| | | | |
| **Total (pre-discount)** | **$126,382** | **$129,687** | **+$3,305** |
| **Total (est. with volume)** | **~$107,400** | **~$110,200** | **+$2,800** |
| **$/kW** | **~$10,740** | **~$11,020** | **+$280** |

### Where Scenario B Saves Money
- **51% fewer TEGs** -- $900 savings (TEGs are similar $/W)
- **51% fewer PCM boards** -- $2,881 savings
- **22% cheaper heat exchangers** -- $6,739 savings (fewer cells, despite higher unit cost)
- **Simpler container** -- $3,079 savings (fewer towers, cables, harnesses)

### Where Scenario B Costs More
- **Thermal oil system** -- +$17,025 (biggest delta by far)
  - Canned motor pump instead of standard centrifugal: +$5,300
  - Thermal oil heater instead of simple burner + shell/tube: +$2,000
  - Therminol VP-1 fluid: +$3,725
  - SS piping, flanged connections: +$1,300
  - Safety equipment (pressurized oil): +$700
  - High-temp sensors: +$600

### Where Scenario B Has Operational Advantages
- **Fewer boards to maintain** -- 30 boards vs 60
- **Fewer cable connections** -- half the Cat5e + Molex cables
- **Higher power density** -- same output in less physical space
- **Scaling advantage** -- adding capacity requires fewer boards per kW

### Where Scenario B Has Operational Risks
- **TEG life expectancy** -- 4 years at 350 C vs 20+ years at 200 C
- **Thermal oil maintenance** -- periodic fluid analysis, potential degradation
- **Higher pressure system** -- VP-1 vapor pressure ~10 bar at 400 C
- **Pump replacement cost** -- canned motor pump is ~5x more expensive

---

## 11. TEG Replacement Cost (Lifecycle)

The biggest hidden cost difference is TEG lifetime:

| | Scenario A (BiTe) | Scenario B (PbTe) |
|---|---|---|
| TEG cost | $40,500 | $39,600 |
| TEG life | 20+ years | 4 years @ 350 C |
| Replacements over 20 years | 0 | 4 full replacements |
| **20-year TEG cost** | **$40,500** | **$198,000** |

**Mitigation:** Run Scenario B TEGs at 320 C instead of 350 C:
- Life extends to 8 years (2.5 replacements over 20 years)
- Power drops to ~10 W/TEG (need ~1,000 TEGs for 10 kW)
- TEG cost increases to $50,000 initial
- 20-year TEG cost: ~$175,000

**Best mitigation:** Run at 280 C for 14-year life:
- Power: ~8 W/TEG, need ~1,260 TEGs
- 20-year cost: ~$126,000 (1.5 replacements)
- Still better power density than BiTe

---

## 12. Sensitivity: Running Scenario B at Lower Temperature

| Operating Temp | Power/TEG | TEGs for 10kW | TEG Cost | Life | 20yr TEG Cost | Total System |
|---------------|----------|--------------|---------|------|-------------|-------------|
| 350 C (max) | 13 W | 792 | $39,600 | 4 yr | $198,000 | $110,200 |
| **320 C (balanced)** | **10 W** | **1,008** | **$50,400** | **8 yr** | **$176,400** | **$122,100** |
| 280 C (long life) | 8 W | 1,260 | $63,000 | 14 yr | $130,500 | $134,700 |
| 260 C (min rated) | 6.5 W | 1,548 | $77,400 | 20+ yr | $77,400 | $149,100 |

**Recommended operating point:** 320 C hot side provides the best balance of initial cost, power density, and 8-year TEG life.

---

## 13. Incremental Costs: 400 C Fluid System Components

For teams evaluating the upgrade from water/glycol to thermal oil, here is the component-level delta:

| Component | Water/Glycol (200 C) | Therminol VP-1 (350 C) | Incremental Cost | Notes |
|-----------|---------------------|----------------------|-----------------|-------|
| **Heat transfer fluid** | 50/50 glycol, $8/gal | Therminol VP-1, $55/gal | **+$3,525** (75 gal) | VP-1 is a specialty synthetic |
| **Hot loop pump** | Grundfos centrifugal, $1,200 | Canned motor pump, $6,500 | **+$5,300** | Standard mag-drive limited to ~230 C; canned motor needed |
| **Heater** | Methane burner + shell/tube HX, $7,500 | Integrated thermal oil heater, $9,500 | **+$2,000** | Oil heater has integrated fired coil |
| **Piping** | Copper + some SS, $1,500 | 316L SS flanged, $2,800 | **+$1,300** | All stainless, flanged connections |
| **Expansion tank** | Standard steel, $300 | Nitrogen-blanketed SS, $650 | **+$350** | Prevents oil oxidation |
| **Insulation** | Mineral wool, $625 | Ceramic fiber, $1,440 | **+$815** | Higher temp rating needed |
| **Safety equipment** | Basic, $500 | PRV + rupture disc + gas detection, $1,400 | **+$900** | Pressurized system requires additional safety |
| **Sensors** | K-type thermocouples, $1,200 | RTDs + pressure transducers, $1,800 | **+$600** | Higher accuracy needed at higher temps |
| **Filter/strainer** | Optional | Required (SS), $500 | **+$500** | Thermal oil requires filtration |
| **Cold loop** | Standard, $1,100 | Larger (246 kW), $3,150 | **+$2,050** | More heat to reject |
| | | | | |
| **Total incremental** | | | **+$17,340** | |

### Pump Deep-Dive: Why Standard Mag-Drive Won't Work at 350 C

| Pump Type | Max Temp | Cost | Pros | Cons |
|-----------|---------|------|------|------|
| Standard centrifugal (mechanical seal) | 200 C | $800-1,200 | Cheap, common | Seal fails at high temp |
| Magnetic drive (sealless) | ~230 C | $2,800-3,500 | No seal, no leak | Magnets degrade above 230 C |
| **Canned motor pump** | **400 C** | **$5,000-8,000** | Hermetically sealed, high temp | Expensive, longer lead time |
| High-temp mechanical seal | 350 C | $3,000-5,000 | Available, moderate cost | Seal wear, potential leaks |

**Recommendation:** Canned motor pump (e.g., Hermetic-Pumpen or Teikoku) for 350 C thermal oil. Budget $6,500.

---

## 14. Cost at Scale: Multiple Units

| Qty | Scenario A $/unit | Scenario A $/kW | Scenario B $/unit | Scenario B $/kW |
|-----|-------------------|-----------------|-------------------|-----------------|
| 1 (prototype) | $126,400 | $12,640 | $129,700 | $12,970 |
| 5 | $107,400 | $10,740 | $110,200 | $11,020 |
| 20 | $94,800 | $9,480 | $97,300 | $9,730 |
| 100 | $82,200 | $8,220 | $84,200 | $8,420 |

At volume (100 units), both scenarios converge to ~$8,000-8,500/kW. The fluid system cost is relatively fixed (doesn't scale as much with volume), so Scenario B's electronics savings become more impactful at scale.

---

## 15. Recommendation

### For Initial Prototype / Proof of Concept
**Scenario A (BiTe)** is recommended:
- Lower risk (proven Marlow TEGs, water/glycol, 20+ year life)
- Simpler fluid system (no thermal oil handling)
- Existing REBA boards can be reused for validation
- $2,800 cheaper initial build

### For Production Deployment
**Scenario B at 320 C** is recommended:
- 49% fewer electronics boards to manufacture and maintain
- Better power density (fewer towers, smaller container footprint)
- 8-year TEG life is acceptable with planned replacement cycles
- Higher $/kW at low volume, but converges at scale
- TEG replacement is the dominant lifecycle cost -- run at 320 C not 350 C

### For Maximum Lifecycle Value
Consider **Scenario B at 280 C**:
- 14-year TEG life nearly matches BiTe
- Still 22% fewer TEGs than BiTe
- Thermal oil system cost is amortized over 14+ years
- Best total cost of ownership over 20-year horizon

---

## Data Sources

| Source | Location |
|--------|----------|
| Marlow TG1-1008 specs | `SynergyThermogen/engineering/heat-exchanger-design/HEAT-EXCHANGER-SPEC-V1.md` |
| System BOM (8 kW) | `SynergyThermogen/engineering/heat-exchanger-design/BOM-ESTIMATE.md` |
| Thermonamic TEG specs | [thermoelectric-generator.com/product/teg1-pb-12611-6-0](https://thermoelectric-generator.com/product/teg1-pb-12611-6-0/) |
| Therminol VP-1 specs | [therminol.com/product/71093459](https://www.therminol.com/product/71093459) |
| PCM BOM | `ThermogenZero/pcm/docs/BOM.md` |
| Controller Node BOM | `ThermogenZero/node/docs/BOM.md` |
| TEG Channel Trade Study | `ThermogenZero/ip/specs/TEG-CHANNEL-ARCHITECTURE-TRADE-STUDY.md` |
| Cabling Loss Analysis | `ThermogenZero/ip/specs/TEG-CABLING-LOSS-ANALYSIS.md` |
| Phase 2 Thermal Oil Spec | `SynergyThermogen/engineering/heat-exchanger-design/PHASE2-THERMAL-OIL-SPEC.md` |

---

## Change Log

| Date | Change | By |
|------|--------|-----|
| 2026-02-06 | Initial analysis, BiTe vs PbTe for 10 kW system | TR |
