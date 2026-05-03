function y = env_control_climate_logic(u)
%ENV_CONTROL_CLIMATE_LOGIC Climate controller actuator mapping and hysteresis.
%
% u = [temp_effort, temperature_c, temperature_setpoint_c, ...
%      humidity_pct, humidity_threshold_pct, cooling_on_above_c, ...
%      cooling_off_above_c, humidity_hysteresis_pct, ...
%      prev_temperature_cooling_active, prev_ventilation_active]

temp_effort = u(1);
temperature_c = u(2);
temperature_setpoint_c = u(3);
humidity_pct = u(4);
humidity_threshold_pct = u(5);
cooling_on_above_c = u(6);
cooling_off_above_c = u(7);
humidity_hysteresis_pct = u(8);
prev_temperature_cooling_active = u(9) ~= 0;
prev_ventilation_active = u(10) ~= 0;

upper_temp = temperature_setpoint_c + cooling_on_above_c;
lower_temp = temperature_setpoint_c + cooling_off_above_c;

if temperature_c >= upper_temp
    temperature_cooling_active = true;
elseif temperature_c <= lower_temp
    temperature_cooling_active = false;
else
    temperature_cooling_active = prev_temperature_cooling_active;
end

humidity_lower = humidity_threshold_pct - humidity_hysteresis_pct / 2.0;
humidity_upper = humidity_threshold_pct + humidity_hysteresis_pct / 2.0;

if humidity_pct > humidity_upper
    ventilation_active = true;
elseif humidity_pct < humidity_lower
    ventilation_active = false;
else
    ventilation_active = prev_ventilation_active;
end

heater_level = max(0.0, temp_effort);
if temperature_cooling_active
    heater_level = 0.0;
end

fan_level = 0.0;
if temperature_cooling_active || ventilation_active
    fan_level = 1.0;
end

y = [
    heater_level;
    fan_level;
    double(ventilation_active);
    double(temperature_cooling_active)
];
end
