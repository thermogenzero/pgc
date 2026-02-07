/**
 * TegPlant.mo -- System-level Modelica model of a containerized TEG power plant.
 *
 * Components:
 *   Burner, Pipe, HeatExchanger, TEGArray, GroundLoop, DryCooler, Pump
 *
 * This is a lumped-parameter model suitable for:
 *   - System sizing and pump selection
 *   - Transient startup / shutdown behavior
 *   - Long-term ground loop thermal drift
 *   - Seasonal ambient temperature effects
 *
 * Fluid: water-glycol (50/50) or thermal oil (switch via parameter)
 * TEG: configurable count, Seebeck model calibrated to Marlow TG1-1008
 *
 * Author: Thermogen Zero / PGC repo
 * Date:   February 2026
 */

package TegPlant

  // -----------------------------------------------------------------------
  // Connectors
  // -----------------------------------------------------------------------
  connector FluidPort "Fluid port (temperature + mass flow)"
    Modelica.Units.SI.Temperature T "Fluid temperature (K)";
    flow Modelica.Units.SI.MassFlowRate m_flow "Mass flow rate (kg/s)";
  end FluidPort;

  connector HeatPort "Thermal port"
    Modelica.Units.SI.Temperature T "Temperature (K)";
    flow Modelica.Units.SI.HeatFlowRate Q_flow "Heat flow (W)";
  end HeatPort;

  // -----------------------------------------------------------------------
  // Burner
  // -----------------------------------------------------------------------
  model Burner "Low-NOx gas burner converting fuel to thermal power"
    parameter Real efficiency = 0.88 "Thermal efficiency (0..1)";
    parameter Real fuel_mcf_per_day = 20.0 "Natural gas input (McF/day)";
    parameter Real BTU_per_McF = 1020000 "Energy content of 1 McF";
    parameter Real J_per_BTU = 1055.06 "Joules per BTU";

    FluidPort port_out "Hot fluid output";
    Modelica.Units.SI.Power Q_thermal "Thermal output (W)";
    Modelica.Units.SI.Power Q_fuel "Fuel input (W)";

  equation
    Q_fuel = fuel_mcf_per_day / 86400.0 * BTU_per_McF * J_per_BTU;
    Q_thermal = Q_fuel * efficiency;
    // The burner heats the fluid flowing through it
    port_out.T = 273.15 + 200;  // Hot outlet temp (default 200 C)
    // Mass flow is set by the pump (not constrained here)
  end Burner;

  // -----------------------------------------------------------------------
  // Pipe (with heat loss)
  // -----------------------------------------------------------------------
  model Pipe "Insulated pipe segment with heat loss to ambient"
    parameter Modelica.Units.SI.Length L = 15 "Pipe length (m)";
    parameter Modelica.Units.SI.Diameter D = 0.038 "Inner diameter (m)";
    parameter Real U_insulation = 2.0 "Insulation U-value (W/m2-K)";
    parameter Modelica.Units.SI.Temperature T_ambient = 298.15 "Ambient (K)";

    FluidPort port_in;
    FluidPort port_out;
    Modelica.Units.SI.Power Q_loss "Heat loss to ambient (W)";

  equation
    // Heat loss through insulation
    Q_loss = U_insulation * Modelica.Constants.pi * D * L *
             (0.5 * (port_in.T + port_out.T) - T_ambient);

    // Energy balance (lumped)
    // Assume fluid Cp ~ 3400 J/kg-K
    port_in.m_flow + port_out.m_flow = 0;  // mass conservation
    port_out.T = port_in.T - Q_loss / (abs(port_in.m_flow) * 3400 + 1e-6);
  end Pipe;

  // -----------------------------------------------------------------------
  // Heat Exchanger (effectiveness-NTU)
  // -----------------------------------------------------------------------
  model HeatExchanger "Counter-flow heat exchanger (effectiveness-NTU)"
    parameter Integer N_teg = 1620 "Number of TEGs (sets heat transfer area)";
    parameter Real A_per_teg = 0.0016 "Heat transfer area per TEG cell (m2)";
    parameter Real U_overall = 4100 "Overall heat transfer coeff (W/m2-K)";

    FluidPort hot_in "Hot fluid inlet";
    FluidPort hot_out "Hot fluid outlet";
    HeatPort teg_face "TEG contact face";

    Modelica.Units.SI.Power Q_transfer "Heat transferred (W)";
    Real effectiveness "HX effectiveness";

  equation
    // Simplified: Q = U * A * LMTD (or effectiveness * Qmax)
    Q_transfer = U_overall * (N_teg * A_per_teg) *
                 (0.5 * (hot_in.T + hot_out.T) - teg_face.T);

    // Energy balance on hot side
    hot_in.m_flow + hot_out.m_flow = 0;
    hot_out.T = hot_in.T - Q_transfer / (abs(hot_in.m_flow) * 3400 + 1e-6);

    // Heat to TEG face
    teg_face.Q_flow = -Q_transfer;

    effectiveness = Q_transfer / (abs(hot_in.m_flow) * 3400 *
                    (hot_in.T - teg_face.T) + 1e-6);
  end HeatExchanger;

  // -----------------------------------------------------------------------
  // TEG Array
  // -----------------------------------------------------------------------
  model TEGArray "Array of thermoelectric generators"
    parameter Integer N = 1620 "Number of TEGs";
    parameter Real R_thermal = 1.52 "Thermal resistance per TEG (K/W)";
    parameter Real alpha = 0.033 "Seebeck coefficient (V/K)";
    parameter Real R_internal = 1.5 "Internal resistance per TEG (Ohm)";

    HeatPort hot_face "Hot-side thermal connection";
    HeatPort cold_face "Cold-side thermal connection";

    Modelica.Units.SI.Temperature T_hot "Hot-side TEG temperature (K)";
    Modelica.Units.SI.Temperature T_cold "Cold-side TEG temperature (K)";
    Modelica.Units.SI.TemperatureDifference dT "Delta-T across TEGs";
    Modelica.Units.SI.Power P_electrical "Total electrical output (W)";
    Modelica.Units.SI.Power Q_hot "Total heat into hot side (W)";
    Modelica.Units.SI.Power Q_cold "Total heat out of cold side (W)";
    Real V_mpp "MPP voltage per TEG (V)";
    Real I_mpp "MPP current per TEG (A)";
    Real efficiency "TEG conversion efficiency";

  equation
    T_hot = hot_face.T;
    T_cold = cold_face.T;
    dT = T_hot - T_cold;

    // Heat flow through TEG array
    Q_hot = N * dT / R_thermal;
    hot_face.Q_flow = Q_hot;

    // Electrical output (matched load, P = Voc^2 / (4*Ri))
    V_mpp = alpha * dT / 2;
    I_mpp = alpha * dT / (2 * R_internal);
    P_electrical = N * V_mpp * I_mpp;

    // Cold side rejects the remainder
    Q_cold = Q_hot - P_electrical;
    cold_face.Q_flow = -Q_cold;

    efficiency = if Q_hot > 0 then P_electrical / Q_hot else 0;
  end TEGArray;

  // -----------------------------------------------------------------------
  // Ground Loop (multi-borehole)
  // -----------------------------------------------------------------------
  model GroundLoop "Closed-loop vertical borehole ground heat exchanger"
    parameter Integer N_boreholes = 32 "Number of boreholes";
    parameter Modelica.Units.SI.Length depth = 150 "Borehole depth (m)";
    parameter Real R_borehole = 0.10 "Thermal resistance per meter (K-m/W)";
    parameter Modelica.Units.SI.Temperature T_ground_initial = 288.15
      "Undisturbed ground temperature (K), ~15 C";
    parameter Real soil_capacity = 2.0e6
      "Volumetric heat capacity of soil (J/m3-K)";
    parameter Real influence_radius = 3.0
      "Thermal influence radius per borehole (m)";

    FluidPort port_in "Warm fluid from cold-side HX";
    FluidPort port_out "Cooled fluid returning to cold-side HX";
    Modelica.Units.SI.Temperature T_soil(start = T_ground_initial)
      "Average soil temperature around boreholes (K)";
    Modelica.Units.SI.Power Q_rejected "Heat rejected to ground (W)";

  equation
    // Heat rejection: Q = (T_fluid_avg - T_soil) / R_total
    Q_rejected = N_boreholes * depth *
                 (0.5 * (port_in.T + port_out.T) - T_soil) / R_borehole;

    // Mass conservation
    port_in.m_flow + port_out.m_flow = 0;

    // Fluid cooling
    port_out.T = port_in.T - Q_rejected / (abs(port_in.m_flow) * 3400 + 1e-6);

    // Soil temperature drift (simplified lumped model)
    // Soil volume per borehole: pi * r^2 * depth
    der(T_soil) = Q_rejected /
                  (N_boreholes * Modelica.Constants.pi *
                   influence_radius^2 * depth * soil_capacity);
  end GroundLoop;

  // -----------------------------------------------------------------------
  // Dry Cooler
  // -----------------------------------------------------------------------
  model DryCooler "Air-cooled heat rejection (forced convection)"
    parameter Real UA = 5000 "Overall UA value (W/K)";
    parameter Real fan_power_per_kw = 15 "Fan power per kW rejected (W/kW)";

    FluidPort port_in;
    FluidPort port_out;
    Modelica.Units.SI.Temperature T_ambient "Ambient air temperature (K)";
    Modelica.Units.SI.Power Q_rejected "Heat rejected (W)";
    Modelica.Units.SI.Power P_fan "Fan power consumption (W)";

  equation
    T_ambient = 298.15 + 10 * sin(2 * Modelica.Constants.pi * time / 31536000);
    // Sinusoidal seasonal variation: 25 C +/- 10 C

    Q_rejected = UA * (0.5 * (port_in.T + port_out.T) - T_ambient);
    port_in.m_flow + port_out.m_flow = 0;
    port_out.T = port_in.T - Q_rejected / (abs(port_in.m_flow) * 3400 + 1e-6);
    P_fan = Q_rejected / 1000 * fan_power_per_kw;
  end DryCooler;

  // -----------------------------------------------------------------------
  // Pump
  // -----------------------------------------------------------------------
  model Pump "Centrifugal pump with efficiency"
    parameter Modelica.Units.SI.MassFlowRate m_flow_design = 2.0
      "Design mass flow rate (kg/s)";
    parameter Modelica.Units.SI.Pressure dp_design = 50000
      "Design pressure rise (Pa)";
    parameter Real eta = 0.65 "Pump efficiency";

    FluidPort port_in;
    FluidPort port_out;
    Modelica.Units.SI.Power P_shaft "Shaft power consumption (W)";

  equation
    port_in.m_flow = m_flow_design;
    port_out.m_flow = -m_flow_design;
    port_out.T = port_in.T;  // Pump assumed adiabatic
    P_shaft = abs(port_in.m_flow) * dp_design / (port_in.m_flow * 1040) / eta;
    // Simplified: P = V_dot * dp / eta, V_dot = m_flow / rho
  end Pump;

  // -----------------------------------------------------------------------
  // System Model
  // -----------------------------------------------------------------------
  model System "Complete PGC system with all components"
    // System parameters
    parameter Integer N_teg = 1620 "Total TEG count";
    parameter Real fuel_mcf_day = 20 "Fuel input (McF/day)";
    parameter Integer N_boreholes = 32 "Ground loop boreholes";

    // Component instances
    Burner burner(fuel_mcf_per_day = fuel_mcf_day);
    Pipe hotPipe(L = 15, T_ambient = 298.15);
    HeatExchanger hotHX(N_teg = N_teg);
    TEGArray tegArray(N = N_teg);
    HeatExchanger coldHX(N_teg = N_teg, U_overall = 3800);
    Pipe coldPipe(L = 15, T_ambient = 298.15);
    GroundLoop groundLoop(N_boreholes = N_boreholes);
    Pump hotPump(m_flow_design = 2.0, dp_design = 50000);
    Pump coldPump(m_flow_design = 2.0, dp_design = 40000);

    // Outputs
    Modelica.Units.SI.Power P_net "Net electrical output (W)";
    Modelica.Units.SI.Power P_parasitic "Total parasitic loads (W)";
    Real system_efficiency "Fuel-to-net-electric efficiency";

  equation
    // Hot loop: Burner -> hotPipe -> hotHX -> hotPump -> back to burner
    connect(burner.port_out, hotPipe.port_in);
    connect(hotPipe.port_out, hotHX.hot_in);
    // hotHX.hot_out loops back via hotPump
    connect(hotHX.hot_out, hotPump.port_in);

    // TEG thermal connections
    connect(hotHX.teg_face, tegArray.hot_face);
    connect(tegArray.cold_face, coldHX.teg_face);

    // Cold loop: coldHX -> coldPipe -> groundLoop -> coldPump -> back
    connect(coldHX.hot_in, coldPump.port_out);
    // coldHX hot_in is actually the cold-side fluid inlet
    connect(coldHX.hot_out, coldPipe.port_in);
    connect(coldPipe.port_out, groundLoop.port_in);
    connect(groundLoop.port_out, coldPump.port_in);

    // System outputs
    P_parasitic = hotPump.P_shaft + coldPump.P_shaft;
    P_net = tegArray.P_electrical - P_parasitic;
    system_efficiency = if burner.Q_fuel > 0 then P_net / burner.Q_fuel else 0;
  end System;

end TegPlant;
