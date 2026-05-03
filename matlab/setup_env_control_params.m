function params = setup_env_control_params()
%SETUP_ENV_CONTROL_PARAMS Define parameters for the Simulink comparison model.

params.sample_time = 1.0;
params.stop_time = 1800;

params.setpoints.temperature_c = 23.0;
params.setpoints.humidity_pct = 65.0;

params.pid.kp = 0.35;
params.pid.ki = 0.03;
params.pid.kd = 0.10;
params.pid.output_limit = 1.0;
params.pid.integral_limit = 10.0;

params.fuzzy.base_kp = 0.35;
params.fuzzy.base_ki = 0.03;
params.fuzzy.base_kd = 0.10;
params.fuzzy.output_limit = 1.0;
params.fuzzy.integral_limit = 10.0;
params.fuzzy.error_scale = 5.0;
params.fuzzy.delta_scale = 2.0;

params.logic.cooling_on_above = 0.5;
params.logic.cooling_off_above = 0.0;
params.logic.humidity_hysteresis = 4.0;

% Use a representative starting point between the PID and fuzzy runs.
params.plant.initial_temp_c = 20.5;
params.plant.ambient_temp_c = 22.0;
% Thermal tuning based on the provided logs:
% - both runs needed roughly 3 to 3.5 minutes to approach 23 C
% - the heater must overcome a persistent humidifier/ventilation penalty
% - fan-assisted cooling should be strong enough to create repeated cooling cycles
params.plant.tau_temp_s = 210.0;
params.plant.k_heater = 8.0;
params.plant.k_fan_cooling = 4.5;
params.plant.k_humidifier_cooling = 0.3;
params.plant.k_ice_cooling = 6.0;

% Humidity tuning based on the provided logs:
% - RH rises rapidly toward ~80% when the humidifier is active
% - ventilation can pull RH back under the 65% threshold within tens of seconds
% - fan cycling is therefore a dominant coupling path between RH and temperature
params.plant.initial_rh_pct = 60.0;
params.plant.ambient_rh_pct = 58.0;
params.plant.tau_rh_s = 140.0;
params.plant.k_humidifier_rh = 24.0;
params.plant.k_vent_rh = 24.0;

params.disturbance.humidifier_on = 1.0;
params.disturbance.ice_step_time_s = 600.0;
params.disturbance.ice_step_amplitude = 1.0;

assignin("base", "params", params);
end
