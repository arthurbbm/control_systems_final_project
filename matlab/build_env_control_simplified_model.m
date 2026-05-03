function model_name = build_env_control_simplified_model()
%BUILD_ENV_CONTROL_SIMPLIFIED_MODEL Build a report-friendly Simulink diagram.

addpath(fileparts(mfilename("fullpath")));
params = setup_env_control_params();
model_name = "env_control_simplified_compare";
model_path = fullfile(fileparts(mfilename("fullpath")), model_name + ".slx");

if bdIsLoaded(model_name)
    close_system(model_name, 0);
end

if exist(model_path, "file")
    delete(model_path);
end

load_system("simulink");
new_system(model_name);
set_param(model_name, "StopTime", num2str(params.stop_time));
set_param(model_name, "Solver", "FixedStepDiscrete");
set_param(model_name, "FixedStep", num2str(params.sample_time));

create_lane(model_name, "PID", [60 80 760 380], "env_control_pid_step(u)");
create_lane(model_name, "FuzzyPID", [60 430 760 730], "env_control_fuzzy_pid_step(u)");

save_system(model_name, model_path);
open_system(model_name);
end

function create_lane(model_name, lane_name, area, controller_expr)
prefix = lane_name + "_";

add_block("simulink/Sources/Constant", block(model_name, prefix + "TempSetpoint"), ...
    "Value", "params.setpoints.temperature_c", ...
    "Position", [area(1) area(2) area(1)+70 area(2)+30]);
add_block("simulink/Sources/Constant", block(model_name, prefix + "HumidityThreshold"), ...
    "Value", "params.setpoints.humidity_pct", ...
    "Position", [area(1) area(2)+50 area(1)+70 area(2)+80]);
add_block("simulink/Sources/Constant", block(model_name, prefix + "HumidifierDist"), ...
    "Value", "params.disturbance.humidifier_on", ...
    "Position", [area(1) area(2)+100 area(1)+70 area(2)+130]);
add_block("simulink/Sources/Step", block(model_name, prefix + "IceDist"), ...
    "Time", "params.disturbance.ice_step_time_s", ...
    "Before", "0", ...
    "After", "params.disturbance.ice_step_amplitude", ...
    "Position", [area(1) area(2)+150 area(1)+70 area(2)+180]);

add_block("simulink/Ports & Subsystems/Subsystem", block(model_name, prefix + "Controller"), ...
    "Position", [area(1)+140 area(2)+10 area(1)+280 area(2)+90]);
add_block("simulink/Ports & Subsystems/Subsystem", block(model_name, prefix + "ClimateLogic"), ...
    "Position", [area(1)+340 area(2)+10 area(1)+500 area(2)+100]);
add_block("simulink/Ports & Subsystems/Subsystem", block(model_name, prefix + "ChamberPlant"), ...
    "Position", [area(1)+560 area(2)+10 area(1)+740 area(2)+110]);

add_block("simulink/Sinks/Scope", block(model_name, prefix + "Scope"), ...
    "NumInputPorts", "4", ...
    "Position", [area(1)+800 area(2)+10 area(1)+850 area(2)+130]);

build_controller_subsystem(model_name, prefix + "Controller", controller_expr, lane_name == "PID");
build_climate_logic_subsystem(model_name, prefix + "ClimateLogic");
build_chamber_subsystem(model_name, prefix + "ChamberPlant");

add_line(model_name, prefix + "TempSetpoint/1", prefix + "Controller/1", "autorouting", "on");
add_line(model_name, prefix + "ChamberPlant/1", prefix + "Controller/2", "autorouting", "on");

add_line(model_name, prefix + "Controller/1", prefix + "ClimateLogic/1", "autorouting", "on");
add_line(model_name, prefix + "ChamberPlant/1", prefix + "ClimateLogic/2", "autorouting", "on");
add_line(model_name, prefix + "TempSetpoint/1", prefix + "ClimateLogic/3", "autorouting", "on");
add_line(model_name, prefix + "ChamberPlant/2", prefix + "ClimateLogic/4", "autorouting", "on");
add_line(model_name, prefix + "HumidityThreshold/1", prefix + "ClimateLogic/5", "autorouting", "on");

add_line(model_name, prefix + "ClimateLogic/1", prefix + "ChamberPlant/1", "autorouting", "on");
add_line(model_name, prefix + "ClimateLogic/2", prefix + "ChamberPlant/2", "autorouting", "on");
add_line(model_name, prefix + "HumidifierDist/1", prefix + "ChamberPlant/3", "autorouting", "on");
add_line(model_name, prefix + "IceDist/1", prefix + "ChamberPlant/4", "autorouting", "on");

add_line(model_name, prefix + "ChamberPlant/1", prefix + "Scope/1", "autorouting", "on");
add_line(model_name, prefix + "ChamberPlant/2", prefix + "Scope/2", "autorouting", "on");
add_line(model_name, prefix + "ClimateLogic/1", prefix + "Scope/3", "autorouting", "on");
add_line(model_name, prefix + "ClimateLogic/2", prefix + "Scope/4", "autorouting", "on");
end

function build_controller_subsystem(model_name, subsystem_name, controller_expr, is_pid)
open_system(block(model_name, subsystem_name));
delete_contents(block(model_name, subsystem_name));

add_block("simulink/Sources/In1", block(model_name, subsystem_name + "/TempSetpoint"), "Position", [30 30 60 50]);
add_block("simulink/Sources/In1", block(model_name, subsystem_name + "/Temperature"), "Position", [30 80 60 100]);
add_block("simulink/Sinks/Out1", block(model_name, subsystem_name + "/TempEffort"), "Position", [500 55 530 75]);
add_block("simulink/Math Operations/Sum", block(model_name, subsystem_name + "/Error"), ...
    "Inputs", "+-", "Position", [90 40 120 70]);
add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/SampleTime"), ...
    "Value", "params.sample_time", "Position", [80 110 130 140]);
add_block("simulink/Discrete/Unit Delay", block(model_name, subsystem_name + "/IntegralState"), ...
    "InitialCondition", "0", "SampleTime", "params.sample_time", "Position", [150 100 180 130]);
add_block("simulink/Discrete/Unit Delay", block(model_name, subsystem_name + "/PrevErrorState"), ...
    "InitialCondition", "0", "SampleTime", "params.sample_time", "Position", [150 145 180 175]);
add_block("simulink/Discrete/Unit Delay", block(model_name, subsystem_name + "/HasPrevState"), ...
    "InitialCondition", "0", "SampleTime", "params.sample_time", "Position", [150 190 180 220]);

if is_pid
    add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/Kp"), "Value", "params.pid.kp", "Position", [80 240 130 270]);
    add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/Ki"), "Value", "params.pid.ki", "Position", [80 280 130 310]);
    add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/Kd"), "Value", "params.pid.kd", "Position", [80 320 130 350]);
    add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/OutputLimit"), "Value", "params.pid.output_limit", "Position", [80 360 130 390]);
    add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/IntegralLimit"), "Value", "params.pid.integral_limit", "Position", [80 400 130 430]);
    add_block("simulink/Signal Routing/Mux", block(model_name, subsystem_name + "/Mux"), ...
        "Inputs", "10", "Position", [250 80 270 310]);
else
    add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/BaseKp"), "Value", "params.fuzzy.base_kp", "Position", [80 240 130 270]);
    add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/BaseKi"), "Value", "params.fuzzy.base_ki", "Position", [80 280 130 310]);
    add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/BaseKd"), "Value", "params.fuzzy.base_kd", "Position", [80 320 130 350]);
    add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/OutputLimit"), "Value", "params.fuzzy.output_limit", "Position", [80 360 130 390]);
    add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/IntegralLimit"), "Value", "params.fuzzy.integral_limit", "Position", [80 400 130 430]);
    add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/ErrorScale"), "Value", "params.fuzzy.error_scale", "Position", [80 440 130 470]);
    add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/DeltaScale"), "Value", "params.fuzzy.delta_scale", "Position", [80 480 130 510]);
    add_block("simulink/Signal Routing/Mux", block(model_name, subsystem_name + "/Mux"), ...
        "Inputs", "12", "Position", [250 80 270 350]);
end

add_block("simulink/User-Defined Functions/MATLAB Fcn", block(model_name, subsystem_name + "/ControllerFcn"), ...
    "MATLABFcn", controller_expr, "Position", [320 120 420 170]);
add_block("simulink/Signal Routing/Demux", block(model_name, subsystem_name + "/Demux"), ...
    "Outputs", "4", "Position", [450 110 470 200]);

add_line(block(model_name, subsystem_name), "TempSetpoint/1", "Error/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "Temperature/1", "Error/2", "autorouting", "on");
add_line(block(model_name, subsystem_name), "Error/1", "Mux/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "SampleTime/1", "Mux/2", "autorouting", "on");
add_line(block(model_name, subsystem_name), "IntegralState/1", "Mux/3", "autorouting", "on");
add_line(block(model_name, subsystem_name), "PrevErrorState/1", "Mux/4", "autorouting", "on");
add_line(block(model_name, subsystem_name), "HasPrevState/1", "Mux/5", "autorouting", "on");

if is_pid
    add_line(block(model_name, subsystem_name), "Kp/1", "Mux/6", "autorouting", "on");
    add_line(block(model_name, subsystem_name), "Ki/1", "Mux/7", "autorouting", "on");
    add_line(block(model_name, subsystem_name), "Kd/1", "Mux/8", "autorouting", "on");
    add_line(block(model_name, subsystem_name), "OutputLimit/1", "Mux/9", "autorouting", "on");
    add_line(block(model_name, subsystem_name), "IntegralLimit/1", "Mux/10", "autorouting", "on");
else
    add_line(block(model_name, subsystem_name), "BaseKp/1", "Mux/6", "autorouting", "on");
    add_line(block(model_name, subsystem_name), "BaseKi/1", "Mux/7", "autorouting", "on");
    add_line(block(model_name, subsystem_name), "BaseKd/1", "Mux/8", "autorouting", "on");
    add_line(block(model_name, subsystem_name), "OutputLimit/1", "Mux/9", "autorouting", "on");
    add_line(block(model_name, subsystem_name), "IntegralLimit/1", "Mux/10", "autorouting", "on");
    add_line(block(model_name, subsystem_name), "ErrorScale/1", "Mux/11", "autorouting", "on");
    add_line(block(model_name, subsystem_name), "DeltaScale/1", "Mux/12", "autorouting", "on");
end

add_line(block(model_name, subsystem_name), "Mux/1", "ControllerFcn/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "ControllerFcn/1", "Demux/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "Demux/1", "TempEffort/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "Demux/2", "IntegralState/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "Demux/3", "PrevErrorState/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "Demux/4", "HasPrevState/1", "autorouting", "on");
end

function build_climate_logic_subsystem(model_name, subsystem_name)
open_system(block(model_name, subsystem_name));
delete_contents(block(model_name, subsystem_name));

for i = 1:5
    add_block("simulink/Sources/In1", block(model_name, subsystem_name + "/In" + num2str(i)), ...
        "Position", [30 20 + 40*(i-1) 60 40 + 40*(i-1)]);
end
add_block("simulink/Sinks/Out1", block(model_name, subsystem_name + "/HeaterLevel"), "Position", [520 40 550 60]);
add_block("simulink/Sinks/Out1", block(model_name, subsystem_name + "/FanLevel"), "Position", [520 90 550 110]);
add_block("simulink/Discrete/Unit Delay", block(model_name, subsystem_name + "/TempCoolingState"), ...
    "InitialCondition", "0", "SampleTime", "params.sample_time", "Position", [160 160 190 190]);
add_block("simulink/Discrete/Unit Delay", block(model_name, subsystem_name + "/VentilationState"), ...
    "InitialCondition", "0", "SampleTime", "params.sample_time", "Position", [160 210 190 240]);
add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/CoolingOnAbove"), ...
    "Value", "params.logic.cooling_on_above", "Position", [80 260 130 290]);
add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/CoolingOffAbove"), ...
    "Value", "params.logic.cooling_off_above", "Position", [80 300 130 330]);
add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/HumidityHysteresis"), ...
    "Value", "params.logic.humidity_hysteresis", "Position", [80 340 130 370]);
add_block("simulink/Signal Routing/Mux", block(model_name, subsystem_name + "/Mux"), ...
    "Inputs", "10", "Position", [250 40 270 280]);
add_block("simulink/User-Defined Functions/MATLAB Fcn", block(model_name, subsystem_name + "/LogicFcn"), ...
    "MATLABFcn", "env_control_climate_logic(u)", "Position", [320 80 420 130]);
add_block("simulink/Signal Routing/Demux", block(model_name, subsystem_name + "/Demux"), ...
    "Outputs", "4", "Position", [460 70 480 170]);

for i = 1:5
    add_line(block(model_name, subsystem_name), "In" + num2str(i) + "/1", "Mux/" + num2str(i), "autorouting", "on");
end
add_line(block(model_name, subsystem_name), "CoolingOnAbove/1", "Mux/6", "autorouting", "on");
add_line(block(model_name, subsystem_name), "CoolingOffAbove/1", "Mux/7", "autorouting", "on");
add_line(block(model_name, subsystem_name), "HumidityHysteresis/1", "Mux/8", "autorouting", "on");
add_line(block(model_name, subsystem_name), "TempCoolingState/1", "Mux/9", "autorouting", "on");
add_line(block(model_name, subsystem_name), "VentilationState/1", "Mux/10", "autorouting", "on");
add_line(block(model_name, subsystem_name), "Mux/1", "LogicFcn/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "LogicFcn/1", "Demux/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "Demux/1", "HeaterLevel/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "Demux/2", "FanLevel/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "Demux/3", "VentilationState/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "Demux/4", "TempCoolingState/1", "autorouting", "on");
end

function build_chamber_subsystem(model_name, subsystem_name)
open_system(block(model_name, subsystem_name));
delete_contents(block(model_name, subsystem_name));

for i = 1:4
    add_block("simulink/Sources/In1", block(model_name, subsystem_name + "/In" + num2str(i)), ...
        "Position", [30 20 + 40*(i-1) 60 40 + 40*(i-1)]);
end
add_block("simulink/Sinks/Out1", block(model_name, subsystem_name + "/Temperature"), "Position", [600 40 630 60]);
add_block("simulink/Sinks/Out1", block(model_name, subsystem_name + "/Humidity"), "Position", [600 90 630 110]);
add_block("simulink/Discrete/Unit Delay", block(model_name, subsystem_name + "/TempState"), ...
    "InitialCondition", "params.plant.initial_temp_c", "SampleTime", "params.sample_time", "Position", [170 180 200 210]);
add_block("simulink/Discrete/Unit Delay", block(model_name, subsystem_name + "/RHState"), ...
    "InitialCondition", "params.plant.initial_rh_pct", "SampleTime", "params.sample_time", "Position", [170 230 200 260]);

consts = { ...
    "SampleTime","params.sample_time"; ...
    "AmbientTemp","params.plant.ambient_temp_c"; ...
    "AmbientRH","params.plant.ambient_rh_pct"; ...
    "TauTemp","params.plant.tau_temp_s"; ...
    "TauRH","params.plant.tau_rh_s"; ...
    "KHeater","params.plant.k_heater"; ...
    "KFanCooling","params.plant.k_fan_cooling"; ...
    "KHumCooling","params.plant.k_humidifier_cooling"; ...
    "KIceCooling","params.plant.k_ice_cooling"; ...
    "KHumRH","params.plant.k_humidifier_rh"; ...
    "KVentRH","params.plant.k_vent_rh" ...
    };
for i = 1:size(consts,1)
    add_block("simulink/Sources/Constant", block(model_name, subsystem_name + "/" + consts{i,1}), ...
        "Value", consts{i,2}, "Position", [80 180 + 35*(i-1) 130 205 + 35*(i-1)]);
end

add_block("simulink/Signal Routing/Mux", block(model_name, subsystem_name + "/Mux"), ...
    "Inputs", "17", "Position", [270 30 290 430]);
add_block("simulink/User-Defined Functions/MATLAB Fcn", block(model_name, subsystem_name + "/PlantFcn"), ...
    "MATLABFcn", "env_control_chamber_step(u)", "Position", [360 120 460 170]);
add_block("simulink/Signal Routing/Demux", block(model_name, subsystem_name + "/Demux"), ...
    "Outputs", "2", "Position", [520 110 540 170]);

for i = 1:4
    add_line(block(model_name, subsystem_name), "In" + num2str(i) + "/1", "Mux/" + num2str(i), "autorouting", "on");
end
add_line(block(model_name, subsystem_name), "TempState/1", "Mux/5", "autorouting", "on");
add_line(block(model_name, subsystem_name), "RHState/1", "Mux/6", "autorouting", "on");
for i = 1:size(consts,1)
    add_line(block(model_name, subsystem_name), consts{i,1} + "/1", "Mux/" + num2str(6+i), "autorouting", "on");
end
add_line(block(model_name, subsystem_name), "Mux/1", "PlantFcn/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "PlantFcn/1", "Demux/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "Demux/1", "TempState/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "Demux/2", "RHState/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "TempState/1", "Temperature/1", "autorouting", "on");
add_line(block(model_name, subsystem_name), "RHState/1", "Humidity/1", "autorouting", "on");
end

function delete_contents(system_path)
blocks = find_system(system_path, "SearchDepth", 1, "Type", "Block");
for i = 1:numel(blocks)
    if strcmp(blocks{i}, system_path)
        continue
    end
    delete_block(blocks{i});
end
lines = find_system(system_path, "FindAll", "on", "SearchDepth", 1, "Type", "line");
for i = 1:numel(lines)
    delete_line(lines(i));
end
end

function path_value = block(model_name, block_name)
path_value = char(model_name + "/" + block_name);
end
