function y = env_control_pid_step(u)
%ENV_CONTROL_PID_STEP One discrete PID update matching the Python logic.
%
% u = [error, dt, integral_prev, prev_error_prev, has_prev_prev, ...
%      kp, ki, kd, output_limit, integral_limit]

error_value = u(1);
dt = max(u(2), 1e-6);
integral_prev = u(3);
prev_error_prev = u(4);
has_prev_prev = u(5) ~= 0;
kp = u(6);
ki = u(7);
kd = u(8);
output_limit = abs(u(9));
integral_limit = abs(u(10));

integral_value = integral_prev + error_value * dt;
integral_value = min(max(integral_value, -integral_limit), integral_limit);

derivative_value = 0.0;
if has_prev_prev
    derivative_value = (error_value - prev_error_prev) / dt;
end

output_value = kp * error_value + ki * integral_value + kd * derivative_value;
output_value = min(max(output_value, -output_limit), output_limit);

y = [
    output_value;
    integral_value;
    error_value;
    1.0
];
end
