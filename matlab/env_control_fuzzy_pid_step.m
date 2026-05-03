function y = env_control_fuzzy_pid_step(u)
%ENV_CONTROL_FUZZY_PID_STEP Gain-scheduled PID matching the Python logic.
%
% u = [error, dt, integral_prev, prev_error_prev, has_prev_prev, ...
%      base_kp, base_ki, base_kd, output_limit, integral_limit, ...
%      error_scale, delta_scale]

error_value = u(1);
dt = max(u(2), 1e-6);
integral_prev = u(3);
prev_error_prev = u(4);
has_prev_prev = u(5) ~= 0;
base_kp = u(6);
base_ki = u(7);
base_kd = u(8);
output_limit = abs(u(9));
integral_limit = abs(u(10));
error_scale = max(abs(u(11)), 1e-6);
delta_scale = max(abs(u(12)), 1e-6);

integral_value = integral_prev + error_value * dt;
integral_value = min(max(integral_value, -integral_limit), integral_limit);

derivative_value = 0.0;
if has_prev_prev
    derivative_value = (error_value - prev_error_prev) / dt;
end

normalized_error = min(max(error_value / error_scale, -1.0), 1.0);
normalized_delta = min(max(derivative_value / delta_scale, -1.0), 1.0);

magnitude_value = abs(normalized_error);
trend_value = abs(normalized_delta);

kp_factor = min(max(1.0 + 0.7 * magnitude_value, 0.5), 2.0);
ki_factor = 1.0 - 0.5 * trend_value;
kd_factor = min(max(1.0 + 0.8 * trend_value, 0.5), 2.0);

if normalized_error * normalized_delta < 0.0
    ki_factor = ki_factor + 0.2;
end

ki_factor = min(max(ki_factor, 0.2), 1.5);

kp_value = base_kp * kp_factor;
ki_value = base_ki * ki_factor;
kd_value = base_kd * kd_factor;

output_value = kp_value * error_value + ki_value * integral_value + kd_value * derivative_value;
output_value = min(max(output_value, -output_limit), output_limit);

y = [
    output_value;
    integral_value;
    error_value;
    1.0
];
end
