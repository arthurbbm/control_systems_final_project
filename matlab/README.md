# MATLAB / Simulink Files

This folder contains helper functions and scripts for building and simulating a comparison model of the chamber controller.

## Files

- `setup_env_control_params.m`: parameter definitions for the plant and controllers
- `env_control_pid_step.m`: discrete PID step matching the Python controller logic
- `env_control_fuzzy_pid_step.m`: fuzzy-PID gain-scheduled step matching the Python controller logic
- `env_control_climate_logic.m`: heater/fan mapping with temperature and humidity hysteresis
- `env_control_chamber_step.m`: simplified chamber temperature/RH state update
- `build_env_control_model.m`: builds the Simulink diagram programmatically
- `run_env_control_simulation.m`: builds the model, runs the simulation, and plots the results
- `build_env_control_simplified_model.m`: builds a cleaner report-friendly Simulink model
- `run_env_control_simplified_simulation.m`: opens and runs the simplified model
- `build_env_control_report_models.m`: builds conceptual report-only PID and fuzzy-PID diagrams
- `open_env_control_report_models.m`: opens the conceptual report diagrams

## Recommended Usage

From MATLAB:

```matlab
cd('path_to_this_project/matlab')
run_env_control_simulation
```

This will:

1. load the default parameters
2. generate `env_control_compare.slx`
3. open the Simulink model
4. run the simulation
5. plot PID and fuzzy-PID responses

For the simplified top-level diagram:

```matlab
cd('path_to_this_project/matlab')
run_env_control_simplified_simulation
```

This version keeps the visible model much cleaner by grouping the logic into three main subsystems per lane:

1. `Controller`
2. `ClimateLogic`
3. `ChamberPlant`

For conceptual report-only diagrams:

```matlab
cd('path_to_this_project/matlab')
open_env_control_report_models
```

This creates two very clean top-level models:

1. `env_control_report_pid.slx`
2. `env_control_report_fuzzy.slx`

These are intended for screenshots in the report, not detailed simulation fidelity.

## Modeling Notes

The scripts use a first-order thermal model and a first-order humidity model:

- temperature is increased by the heater
- temperature is reduced by the fan, humidifier cooling effect, and ice disturbance
- relative humidity is increased by the humidifier disturbance
- relative humidity is reduced by ventilation

The humidifier is modeled as a disturbance because the real hardware could not be turned on programmatically and had to be manually activated.
