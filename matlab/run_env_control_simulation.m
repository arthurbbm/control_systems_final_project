function sim_out = run_env_control_simulation()
%RUN_ENV_CONTROL_SIMULATION Build, run, and plot the Simulink comparison model.

addpath(fileparts(mfilename("fullpath")));
params = setup_env_control_params();
model_name = build_env_control_model();

sim_out = sim(model_name, "StopTime", num2str(params.stop_time));

pid_temperature = evalin("base", "PID_temperature");
pid_humidity = evalin("base", "PID_humidity");
pid_heater = evalin("base", "PID_heater");
pid_fan = evalin("base", "PID_fan");

fuzzy_temperature = evalin("base", "FuzzyPID_temperature");
fuzzy_humidity = evalin("base", "FuzzyPID_humidity");
fuzzy_heater = evalin("base", "FuzzyPID_heater");
fuzzy_fan = evalin("base", "FuzzyPID_fan");

figure("Name", "Embedded Climate Control Comparison", "Color", "w");

subplot(4, 1, 1);
plot(pid_temperature.time, pid_temperature.signals.values, "LineWidth", 1.6);
hold on;
plot(fuzzy_temperature.time, fuzzy_temperature.signals.values, "--", "LineWidth", 1.6);
yline(params.setpoints.temperature_c, ":", "Setpoint");
grid on;
ylabel("Temp (C)");
title("Temperature Response");
legend("PID", "Fuzzy-PID", "Location", "best");

subplot(4, 1, 2);
plot(pid_humidity.time, pid_humidity.signals.values, "LineWidth", 1.6);
hold on;
plot(fuzzy_humidity.time, fuzzy_humidity.signals.values, "--", "LineWidth", 1.6);
yline(params.setpoints.humidity_pct, ":", "RH threshold");
grid on;
ylabel("RH (%)");
title("Relative Humidity Response");
legend("PID lane", "Fuzzy-PID lane", "Location", "best");

subplot(4, 1, 3);
plot(pid_heater.time, pid_heater.signals.values, "LineWidth", 1.6);
hold on;
plot(fuzzy_heater.time, fuzzy_heater.signals.values, "--", "LineWidth", 1.6);
grid on;
ylabel("Heater cmd");
title("Heater Command");
legend("PID", "Fuzzy-PID", "Location", "best");

subplot(4, 1, 4);
plot(pid_fan.time, pid_fan.signals.values, "LineWidth", 1.6);
hold on;
plot(fuzzy_fan.time, fuzzy_fan.signals.values, "--", "LineWidth", 1.6);
grid on;
ylabel("Fan cmd");
xlabel("Time (s)");
title("Fan Command");
legend("PID", "Fuzzy-PID", "Location", "best");
end
