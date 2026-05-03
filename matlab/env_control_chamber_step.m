function y = env_control_chamber_step(u)
%ENV_CONTROL_CHAMBER_STEP Discrete chamber model with temperature and RH states.
%
% u = [heater_level, fan_level, humidifier_disturbance, ice_disturbance, ...
%      temp_prev, rh_prev, dt, ambient_temp, ambient_rh, tau_temp, tau_rh, ...
%      k_heater, k_fan_cooling, k_humidifier_cooling, k_ice_cooling, ...
%      k_humidifier_rh, k_vent_rh]

heater_level = u(1);
fan_level = u(2);
humidifier_disturbance = u(3);
ice_disturbance = u(4);
temp_prev = u(5);
rh_prev = u(6);
dt = max(u(7), 1e-6);
ambient_temp = u(8);
ambient_rh = u(9);
tau_temp = max(u(10), 1e-6);
tau_rh = max(u(11), 1e-6);
k_heater = u(12);
k_fan_cooling = u(13);
k_humidifier_cooling = u(14);
k_ice_cooling = u(15);
k_humidifier_rh = u(16);
k_vent_rh = u(17);

temp_rate = ((ambient_temp - temp_prev) + ...
    k_heater * heater_level - ...
    k_fan_cooling * fan_level - ...
    k_humidifier_cooling * humidifier_disturbance - ...
    k_ice_cooling * ice_disturbance) / tau_temp;

rh_rate = ((ambient_rh - rh_prev) + ...
    k_humidifier_rh * humidifier_disturbance - ...
    k_vent_rh * fan_level) / tau_rh;

temp_next = temp_prev + dt * temp_rate;
rh_next = rh_prev + dt * rh_rate;

y = [
    temp_next;
    rh_next
];
end
