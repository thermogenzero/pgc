# TZ Power Generating Combustor (PGC) — Integration Plan with eStream v0.8.1

> **Version:** 1.1.0  
> **Date:** 2026-02-11  
> **Status:** Active  
> **eStream Baseline:** v0.8.1  
> **Carbon Credits:** [SynergyCarbon](https://github.com/synergycarbon) `povc-carbon` (PoVCR minting platform)  
> **Master Spec:** [ESTREAM_CONTROLS_SPEC.md](../../microgrid/docs/ESTREAM_CONTROLS_SPEC.md)

---

## 1. Scope

The PGC (Power Generating Combustor) is the thermoelectric generator power plant, controlled from the 48V DIN-rail TZ chassis. This plan covers the TZ integration points with eStream for:

1. **Thermal zone monitoring** — hot/cold fluid loops mapped to `tz.teg.thermal.*` lex topics
2. **Burner control integration** — gas consumption and combustion data mapped to `tz.gas.*` streams
3. **System-level safety interlocks** — mapped to `tz.faults.*`
4. **Carbon credit calculation** — CH4 mass → GWP factor → tCO2e via `tz.carbon.*`, minted on SynergyCarbon
5. **TZ-AI corpus** — CoolProp/OpenFOAM simulation outputs as training data

---

## 2. Thermal Zone Monitoring

### 2.1 Thermal Zones

The PGC separates into thermal zones. The TZ chassis (48V DIN-rail telco node) is located in the cool zone, away from the heat source.

```
┌────────────────────────────────────────────────────────────────┐
│  HOT ZONE              SERVICE ZONE             COOL ZONE      │
│  200-400°C             ambient                  <85°C          │
│                                                                 │
│  Hot manifold          TEG towers               TZ Chassis     │
│  Burner / heat source  Cold manifold            (DIN-rail)     │
│                        PCMs (warm zone,         Controller Node │
│                         85-125°C)                              │
│                                                 48V bus bar    │
│                                                 Display panel  │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 Sensor Mapping to Lex Topics

| Sensor | Location | Type | Range | Interface | Lex Topic |
|--------|----------|------|-------|-----------|-----------|
| T_hot_supply | Hot manifold outlet | RTD PT1000 | 0-450°C | Modbus RTU (BMS) | `tz.teg.thermal.profile.hot_side_avg_c` |
| T_hot_return | Hot manifold return | RTD PT1000 | 0-450°C | Modbus RTU (BMS) | `tz.teg.thermal.profile.hot_return_c` |
| T_cold_supply | Cold manifold outlet | RTD PT1000 | 0-100°C | Modbus RTU (BMS) | `tz.teg.thermal.profile.cold_side_avg_c` |
| T_cold_return | Cold manifold return | RTD PT1000 | 0-100°C | Modbus RTU (BMS) | `tz.teg.thermal.profile.cold_return_c` |
| T_ambient | Container exterior | RTD PT100 | -40-60°C | Modbus RTU (BMS) | `tz.system.identity.ambient_c` |
| T_burner_exhaust | Burner stack | K-type TC | 0-800°C | Modbus RTU (burner PLC) | `tz.gas.exhaust_temp_c` |
| Flow_hot | Hot loop pump | Turbine flow meter | 0-50 L/min | 4-20 mA → Modbus | `tz.teg.thermal.profile.flow_lpm` |
| Flow_cold | Cold loop pump | Turbine flow meter | 0-100 L/min | 4-20 mA → Modbus | `tz.teg.thermal.profile.cold_flow_lpm` |
| P_hot | Hot loop pressure | Pressure transducer | 0-10 bar | 4-20 mA → Modbus | `tz.teg.thermal.profile.hot_pressure_bar` |
| P_cold | Cold loop pressure | Pressure transducer | 0-6 bar | 4-20 mA → Modbus | `tz.teg.thermal.profile.cold_pressure_bar` |

### 2.3 Delta-T Calculation

The primary performance metric is the temperature difference across the TEG array:

```
delta_T = T_hot_supply - T_cold_supply
```

Published to `tz.teg.thermal.profile.delta_t_c` at 1 Hz. The SmartCircuit state machine uses this for:
- `WarmingUp → Producing` transition (delta_T > 80°C sustained 60s)
- `Producing → Throttle` transition (T_hot > 380°C or T_cold > 90°C)

### 2.4 Thermal Efficiency

```
Q_hot (kW_th) = flow_lpm × 60 × ρ × Cp × (T_hot_supply - T_hot_return)
                where ρ = fluid density (kg/L), Cp = specific heat (kJ/kg·°C)

Q_cold (kW_th) = flow_lpm × 60 × ρ × Cp × (T_cold_return - T_cold_supply)

η_teg = P_electrical / Q_hot

Published to: tz.teg.power.summary.efficiency_pct
```

---

## 3. Burner Control Integration

### 3.1 Gas Consumption Monitoring

| Sensor | Type | Range | Interface | Lex Topic |
|--------|------|-------|-----------|-----------|
| Gas flow meter | Orifice/turbine | 0-10 McF/day | 4-20 mA → Modbus | `tz.gas.consumption.mcf_per_day` |
| Gas pressure | Pressure transducer | 0-50 PSI | 4-20 mA → Modbus | `tz.gas.consumption.pressure_psi` |
| Gas temperature | RTD | -40-60°C | Modbus | `tz.gas.consumption.temp_c` |
| Burner status | PLC discrete | On/Off/Fault | Modbus coil | `tz.gas.burner_status` |
| Flame detector | UV/IR sensor | Active/Inactive | Modbus discrete | `tz.gas.flame_detected` |
| Burner modulation | PLC register | 0-100% | Modbus holding | `tz.gas.modulation_pct` |

### 3.2 Gas Data Processing

```
// Volumetric flow to mass flow
gas_volume_m3 = gas_flow_mcf_day × 28.3168 / 86400  // m³/s
gas_mass_kg_s = gas_volume_m3 × density_kg_m3        // density ≈ 0.6567 kg/m³ at STP

// Energy content
btu_per_hour = gas_flow_mcf_day × 1_020_000 / 24     // 1,020,000 BTU/McF for natural gas
kwh_thermal_per_day = gas_flow_mcf_day × 299          // 299 kWh_th/McF

// Published at 1-minute intervals
tz.gas.consumption.mcf_per_day     = gas_flow_mcf_day
tz.gas.consumption.btu_per_hour    = btu_per_hour
tz.gas.consumption.kwh_th_per_day  = kwh_thermal_per_day
tz.gas.efficiency.kwh_e_per_mcf    = total_power_kwh / gas_flow_mcf_day
```

### 3.3 Avoided Flaring Calculation

```
// Gas that would have been flared
tz.gas.savings.avoided_flaring_mcf = gas_flow_mcf_day  // All gas consumed is gas not flared
tz.gas.savings.avoided_co2_kg      = gas_flow_mcf_day × 0.6567 × 28.3168 × 2.75
                                     // 2.75 kg CO2 per kg CH4 if flared (complete combustion)
```

---

## 4. System-Level Safety Interlocks

### 4.1 Safety Events Mapping

| Event | Source | Severity | Action | Lex Topic |
|-------|--------|----------|--------|-----------|
| High hot-side temp | T_hot_supply > 400°C | Fatal | Burner shutoff, EPO all TEGs | `tz.faults.safety` |
| High cold-side temp | T_cold_supply > 95°C | Critical | Increase cooling, reduce load | `tz.faults.safety` |
| Low flow (hot) | Flow_hot < 5 L/min | Critical | Throttle TEGs, alert operator | `tz.faults.safety` |
| Low flow (cold) | Flow_cold < 10 L/min | Critical | Throttle TEGs, alert operator | `tz.faults.safety` |
| High pressure (hot) | P_hot > 8 bar | Critical | Reduce pump speed | `tz.faults.safety` |
| Flame loss | Flame detector inactive | Fatal | Close gas valve, safe shutdown | `tz.faults.safety` |
| Gas leak detected | Gas detector alarm | Fatal | Close gas valve, EPO, ventilate | `tz.faults.safety` |
| Smoke detected | Smoke detector alarm | Fatal | Safe shutdown, alert operator | `tz.faults.safety` |
| Enclosure open (hot zone) | Door/panel switch | Warning | Alert operator | `tz.faults.active` |
| Pump failure | Motor current = 0 | Critical | Switch to backup pump | `tz.faults.active` |

### 4.2 Interlock Logic

The PGC safety interlocks are implemented in the burner PLC (hardwired safety chain) and monitored by the eStream site controller via Modbus TCP (Layer 3 HMI / `estream-industrial` gateway).

```
Hardwired safety chain (non-programmable):
  Gas valve → [flame detector AND temp_ok AND pressure_ok AND no_gas_leak] → open

Software interlocks (SmartCircuit monitoring):
  site_controller monitors PLC status via Modbus
  → If PLC reports fault → transition to SafeShutdown or Fault state
  → Publish to tz.faults.* lex topics
```

The eStream layer **does not replace** the hardwired safety chain. It adds monitoring, alerting, and audit logging on top of the existing safety system.

---

## 5. Carbon Credit Calculation

### 5.1 Methodology

ThermogenZero uses an EPA AP-42 based methodology for calculating avoided methane emissions:

```
Step 1: Quantify methane consumed
  CH4_volume_m3 = gas_flow_mcf × 28.3168
  CH4_mass_kg   = CH4_volume_m3 × 0.6567    // density at STP

Step 2: Calculate GHG equivalence
  CO2e_avoided_kg = CH4_mass_kg × GWP_factor
    where GWP_factor = 28  (IPCC AR5, 100-year horizon)
          GWP_factor = 84  (IPCC AR5, 20-year horizon)
  
  tCO2e = CO2e_avoided_kg / 1000

Step 3: Subtract parasitic emissions
  // Burner produces CO2 during combustion:
  CO2_from_combustion_kg = CH4_mass_kg × (44/16)  // stoichiometric
  // But this is CO2, not CH4 — much lower GWP (1 vs 28)
  
  Net_tCO2e = (CH4_mass_kg × 28 - CO2_from_combustion_kg × 1) / 1000
            = (CH4_mass_kg × (28 - 44/16)) / 1000
            = (CH4_mass_kg × 25.25) / 1000

Step 4: Apply verification discount
  // PoVC witness provides 95% confidence
  Verified_tCO2e = Net_tCO2e × 0.95  // 5% conservative discount
```

### 5.2 Carbon Calculation Streams

| Lex Topic | Value | Update Rate | Retention |
|-----------|-------|-------------|-----------|
| `tz.carbon.accrual.total_tco2e` | Running total tCO2e | 1 min | Forever |
| `tz.carbon.accrual.period_tco2e` | Current period (daily) | 1 min | 90 days |
| `tz.carbon.accrual.gas_consumed_mcf` | Gas input | 1 min | 1 year |
| `tz.carbon.accrual.ch4_mass_kg` | CH4 mass | 1 min | 1 year |
| `tz.carbon.accrual.net_co2e_kg` | Net CO2e avoided | 1 min | 1 year |
| `tz.carbon.certificates.latest` | Latest minted certificate | On mint | Forever |
| `tz.carbon.certificates.total_minted` | Total certificates minted | On mint | Forever |
| `tz.carbon.projection.monthly_tco2e` | 30-day projection | 1 hour | 90 days |
| `tz.carbon.projection.annual_tco2e` | 12-month projection | 1 day | 1 year |

### 5.3 PoVCR Integration

The carbon calculation feeds into the PoVCR (Proof of Verified Compute Result) pipeline:

```
Gas meter reading (1 min interval)
    │
    ▼
Carbon calculator (on Controller Node or cloud)
    │
    ├──→ tz.carbon.accrual.* (running totals)
    │
    ▼
PoVC witness generation (on Controller Node LIFCL-40)
    │ Bundles power + gas readings into Merkle tree
    │
    ▼
SynergyCarbon PoVCR Minter (cloud SmartCircuit, povc-carbon platform)
    │ Verifies witness quorum, validates energy claims
    │
    ▼
L1 token mint (carbon credit NFT via SynergyCarbon)
    │
    ▼
tz.carbon.certificates.latest (lex topic)
```

---

## 6. TZ-AI Corpus Integration

### 6.1 Thermal Simulation Data

CoolProp and OpenFOAM simulation outputs serve as training corpus for TZ-AI models:

| Data Source | Format | Size | AI Model | Lex Topic |
|------------|--------|------|----------|-----------|
| CoolProp fluid properties | JSON/CSV | ~100 KB per run | Energy Dispatch | `tz.ai.corpus.thermal` |
| OpenFOAM CFD results | VTK/CSV | ~10 MB per sim | Predictive Maintenance | `tz.ai.corpus.cfd` |
| TEG characterization curves | CSV | ~1 MB per TEG type | MPPT Optimizer | `tz.ai.corpus.teg_curves` |
| Historical operational data | ESF binary | ~50 MB/day | All models | StreamSight archive |
| Fault event history | Structured | ~1 MB/month | Fault Predictor | `tz.faults.history` |

### 6.2 Model Training Pipeline

```
Historical data (StreamSight) + Simulation data (CoolProp/OpenFOAM)
    │
    ▼
Corpus ingestion (ESN-AI pipeline, Phase 6)
    │
    ▼
6 specialized models:
  1. Predictive Maintenance — component degradation curves
  2. MPPT Optimizer — optimal P&O parameters per thermal condition
  3. Energy Dispatch — TEG/solar/battery allocation
  4. Fault Predictor — cascade failure patterns
  5. Carbon Validator — yield anomaly detection
  6. Fleet Correlator — cross-site performance patterns
    │
    ▼
Model outputs → tz.ai.predictions.*, tz.ai.recommendations.*
    │
    ▼
Operator feedback → tz.ai.rlhf.feedback (RLHF loop)
```

### 6.3 Key Training Features (from PGC)

| Feature | Source | Relevance |
|---------|--------|-----------|
| Hot fluid temperature profile | T_hot_supply/return over time | Burner ramp behavior |
| Cold fluid temperature response | T_cold_supply/return over time | Heat rejection effectiveness |
| Gas consumption per kWh_e | Gas flow / power output | Overall system efficiency |
| Delta-T vs power curve | delta_T vs total_power_w | TEG characterization |
| Ambient temperature effect | T_ambient vs efficiency | Seasonal performance |
| Pump flow rate vs delta-T | Flow rates vs thermal performance | Pump sizing validation |
| Fault sequences | Time-ordered fault events | Cascade pattern learning |

---

## 7. Modbus Integration Path

The PGC has existing Modbus RTU devices (burner PLC, BMS, pump VFDs) that are bridged to eStream via the `estream-industrial` MODBUS TCP gateway:

```
Burner PLC (Modbus RTU, RS485)
    │
    ▼
Modbus RTU → TCP bridge (native on Controller Node FPGA)
    │
    ▼
estream-industrial MODBUS TCP client (on Controller Node)
    │
    ▼
Stream Emitter → tz.gas.*, tz.teg.thermal.* lex topics
    │
    ▼
StreamSight → Console → TZ-AI
```

The existing industrial sensors do not need to change. The `estream-industrial` gateway reads their registers and publishes to lex topics.

---

## 8. Implementation Timeline

| Phase | Week | Deliverable | Dependencies |
|-------|------|------------|-------------|
| Phase 1 | 1-2 | Document all PGC sensor points and Modbus registers | Burner PLC register map |
| Phase 1 | 2-3 | Configure `estream-industrial` for PGC Modbus devices | Edge gateway running |
| Phase 2 | 4-6 | Thermal monitoring streams active (tz.teg.thermal.*) | Modbus bridge operational |
| Phase 2 | 6-7 | Gas consumption streams active (tz.gas.*) | Gas meter integrated |
| Phase 3 | 8-9 | Container safety interlocks monitored via SmartCircuit | Site controller operational |
| Phase 4 | 14 | Carbon credit calculation pipeline | PoVC witnesses flowing |
| Phase 6 | 19-20 | TZ-AI corpus ingestion (CoolProp/OpenFOAM) | ESN-AI pipeline available |
| Phase 6 | 21-32 | Model training and deployment | Corpus ingested |

---

## 9. Cross-References

| Document | Repo | Purpose |
|----------|------|---------|
| [SYSTEM-ARCHITECTURE.md](SYSTEM-ARCHITECTURE.md) | pgc | PGC system architecture |
| [EPIC_ESTREAM_INTEGRATION.md](EPIC_ESTREAM_INTEGRATION.md) | pgc | Original 6-phase epic |
| [ESTREAM_CONTROLS_SPEC.md](../../microgrid/docs/ESTREAM_CONTROLS_SPEC.md) | microgrid | Master controls spec |
| [ESTREAM_CONTROLS_PLAN.md](../../node/docs/ESTREAM_CONTROLS_PLAN.md) | node | Controller Node firmware |
| [TZ-AI-SPEC.md](../../microgrid/docs/TZ-AI-SPEC.md) | microgrid | TZ-AI model specifications |
| [WIDGET-SPEC.md](../../microgrid/docs/WIDGET-SPEC.md) | microgrid | Console widget specifications |
