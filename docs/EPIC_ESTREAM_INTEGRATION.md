# Epic: Thermogen Zero — eStream Platform Integration

## Overview

Synthesize the existing Thermogen Zero PGC hardware, thermal modeling, and controller work with the eStream platform to create a fully integrated **edge IoT microgrid solution** with hardware-attested carbon credit minting.

This epic bridges:
- **PGC repo** (this repo): Thermal modeling, heat exchanger design, container layout, cost analysis
- **ThermogenZero hardware repos**: Node (LIFCL-40), Node-HDL, PCM (iCE40), PCM-HDL, TEG-Opti hardware/HDL, Nexus MPPT
- **eStream platform** (toddrooke/estream-io): SmartCircuits, ESF, PoVC, governance, VRF Scatter

**Related Patents:**
- [US20250270450A1](https://patents.google.com/patent/US20250270450A1/) — Zero methane oil and gas production facility design
- [WO2024163685A1](https://patents.google.com/patent/WO2024163685A1/) — Thermoelectric generator

**Key Innovation:** PoVC-based carbon credit minting with hardware-attested proof of methane reduction.

## Existing Work to Synthesize

### PGC Repo (pgc/)
| Asset | Description | Status |
|-------|-------------|--------|
| `modeling/coolprop/` | TEG system model, McF-to-watts, parametric sweep | Complete |
| `modeling/openfoam/` | CFD conjugate heat transfer for HX cell | Complete |
| `modeling/openmodelica/` | System-level transient loop model | Complete |
| `costs/cost_model.py` | Programmatic cost model for 10kW+ systems | Complete |
| `container/` | 40ft container layout and thermal zoning | Draft |
| `docs/SYSTEM-ARCHITECTURE.md` | PGC energy flow and design parameters | Complete |
| `docs/GROUND-LOOP-SIZING.md` | Heat rejection sizing | Complete |

### Hardware Repos (ThermogenZero org)
| Repo | Description | Status |
|------|-------------|--------|
| `node/` | Controller Node HW (LIFCL-40 / CertusPro-NX) | Design |
| `node-hdl/` | Controller Node HDL (MPPT, PoVC, estream) | Active |
| `pcm/` | Power Conversion Module HW (iCE40 + buck + ADC) | Design |
| `pcm-hdl/` | PCM firmware (iCE40 SPI slave, PWM, ADC driver) | Active |
| `nexus-mppt-hardware/` | Nexus MPPT node HW | Design |
| `nexus-mppt-hdl/` | Nexus MPPT HDL (with eStream governance + bitstream update) | Active |
| `teg-opti-hardware/` | TEG optimizer PCB | Fabricated |
| `teg-opti-hdl/` | TEG optimizer HDL (ADS7950 SPI, PWM, I2C) | Proven |

### eStream Platform Requirements
| Capability | eStream Component | Status |
|------------|------------------|--------|
| Edge node runtime | `estream-kernel` (lightweight) | Exists, needs edge profile |
| Binary ESF encoding | ESF codec with <512 byte payloads | Needs binary mode |
| State machine execution | SmartCircuit state machine engine | Exists |
| Aggregation circuits | Fleet aggregation framework | Needs building |
| PoVC attestation | Proof of Verified Compute | Exists |
| Carbon credit minting | PoVCR circuit → L1 token | Needs building |
| Governance | ML-DSA-87 signed commands | Exists |
| VRF Scatter | Distributed replication | Exists |
| Remote bitstream update | Governance-attested FPGA updates | Designed (see nexus-mppt-hdl) |

## Components to Build

### Phase 1: ESF Schemas + Edge Runtime Profile
- [ ] `TZTelemetry` ESF schema (binary optimized, <512 bytes)
- [ ] `TZCommand` ESF schema (control commands with TTL)
- [ ] `TZAlert` ESF schema (fault codes, thresholds)
- [ ] Edge runtime profile for `estream-kernel` (reduced footprint for LIFCL-40)

### Phase 2: Site Controller SmartCircuit
- [ ] `TZSiteControllerSC` state machine (black_start → warming_up → producing → throttle → island_mode → safe_shutdown → fault)
- [ ] Threshold monitoring circuits (temp_warning, low_voltage, battery_critical)
- [ ] Bidirectional command queue with acknowledgment and TTL

### Phase 3: Fleet Aggregation + Dashboard + HMI
- [ ] `TZFleetAggregatorSC` circuit (total_power_kw, avg_battery_soc, sites_producing, sites_faulted)
- [ ] Fleet dashboard integration (eStream Console widget)
- [ ] Offline buffering layer (satellite/cellular store-and-forward)
- [ ] Operator HMI — three-layer architecture (see `microgrid/docs/HMI-DESIGN.md`)
  - [ ] Layer 1: Walk-up display array on Controller Node (9x OLED+e-ink 3×3 grid, shared SPI, 15 GPIO pins)
  - [ ] Layer 2: TZ widget modules in estream-app (React Native) on rugged Android tablet
  - [ ] Layer 3: MODBUS TCP server native in LIFCL-40 HDL (not on edge compute)
  - [ ] Controller Node network stack: estream-kernel (edge profile), WiFi AP, HAS offline buffer, satellite/cellular uplink

### Phase 4: PoVCR Carbon Credit Minting
- [ ] Hardware attestation verification (ML-DSA-87 device certs)
- [ ] Causal plausibility checks (heat_from_methane, power_from_heat)
- [ ] Carbon calculation (CH4 mass → GWP factor → tCO2e)
- [ ] L1 token minting (SPL_TOKEN_2022 or equivalent)

### Phase 5: Remote Bitstream Governance
- [ ] Synthesize `nexus-mppt-hdl/rtl/update/` governance module with eStream governance lex
- [ ] ML-DSA-87 signed bitstream delivery via QUIC/satellite
- [ ] Fleet-wide update orchestration with rollback

### Phase 6: TZ-AI SLM Intelligence (see `microgrid/docs/TZ-AI-SPEC.md`)
- [ ] AI-1: Corpus ingestion pipeline (TZ tenant config, sanitization, lex subscriptions)
- [ ] AI-2: Fault predictor + predictive maintenance models (11 anomaly categories, cascade prediction)
- [ ] AI-3: MPPT optimizer + energy dispatch models (duty cycle recommendations, dispatch scheduling)
- [ ] AI-4: TZ HQ console widgets (7 fleet-level AI widgets)
- [ ] AI-5: Carbon yield validator + fleet pattern correlator
- [ ] AI-6: RLHF pipeline + operator feedback UI (experience weighting, accuracy tracking)

## Annual Carbon Credit Potential

| Sites | Capacity Factor | CO2e per Site/Year | Total Annual Credits |
|-------|-----------------|-------------------|---------------------|
| 10 | 80% | 16.9 tCO2e | 169 tCO2e |
| 100 | 80% | 16.9 tCO2e | 1,690 tCO2e |
| 1,000 | 80% | 16.9 tCO2e | 16,900 tCO2e |

At ~$50/tCO2e (current voluntary market): **$845K/year for 1,000 sites**

## Dependencies

- [ ] eStream edge node runtime (lightweight kernel)
- [ ] Binary ESF encoder/decoder
- [ ] State machine execution engine
- [ ] PoVC framework (exists)
- [ ] Governance lex (exists)
- [ ] L1 bridge for carbon credit token minting

## Timeline (Estimate)

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1 | 2 weeks | ESF schemas + edge runtime profile |
| Phase 2 | 3 weeks | Site controller SmartCircuit |
| Phase 3 | 3 weeks | Fleet aggregation + dashboard |
| Phase 4 | 3 weeks | PoVCR carbon credit minting |
| Phase 5 | 2 weeks | Remote bitstream governance integration |
| Phase 6 | 14 weeks (~10 critical path) | TZ-AI SLM intelligence (6 models, 7 widgets, RLHF) |

## References

- `pgc/docs/SYSTEM-ARCHITECTURE.md` — PGC energy flow
- `pgc/modeling/coolprop/teg_system_model.py` — Core thermal model
- `pgc/costs/cost_model.py` — Cost analysis
- `ip/specs/OPTI-CONTROLLER-ESTREAM-SPEC.md` — eStream controller spec
- `ip/specs/REMOTE-BITSTREAM-UPDATE-DECISION.md` — Update governance design
- `nexus-mppt-hdl/docs/ESTREAM_CONTRIBUTIONS.md` — HDL eStream integration notes
- `node-hdl/` — Controller Node HDL
- `microgrid/docs/HMI-DESIGN.md` — Operator HMI architecture (Thermogen tech + O&G operator + SCADA)
- `microgrid/docs/TZ-AI-SPEC.md` — TZ-AI SLM intelligence specification (Phase 6)
- `microgrid/docs/WIDGET-SPEC.md` — Console widget specifications (19 per-site + 7 HQ AI)

---

*Epic created: 2026-02-09*
*Migrated from: estream-io/.github/epics/EPIC_THERMOGEN_ZERO.md*
*Status: Planning*
*Priority: Strategic (first edge/IoT deployment)*
