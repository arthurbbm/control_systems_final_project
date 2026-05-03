function model_names = build_env_control_report_models()
%BUILD_ENV_CONTROL_REPORT_MODELS Build conceptual report-only Simulink diagrams.

addpath(fileparts(mfilename("fullpath")));
load_system("simulink");

model_names = ["env_control_report_pid", "env_control_report_fuzzy"];
controller_labels = ["PID Controller", "Fuzzy-PID Controller"];

for i = 1:numel(model_names)
    model_name = model_names(i);
    model_path = fullfile(fileparts(mfilename("fullpath")), model_name + ".slx");

    if bdIsLoaded(model_name)
        close_system(model_name, 0);
    end

    if exist(model_path, "file")
        delete(model_path);
    end

    new_system(model_name);
    set_param(model_name, "StopTime", "100");

    build_report_model(model_name, controller_labels(i));

    save_system(model_name, model_path);
    open_system(model_name);
end
end

function build_report_model(model_name, controller_label)
add_block("simulink/Sources/Constant", block(model_name, "Temperature Setpoint"), ...
    "Value", "23", ...
    "Position", [40 110 110 140]);
add_block("simulink/Math Operations/Sum", block(model_name, "Error"), ...
    "Inputs", "+-", ...
    "Position", [160 112 190 138]);
add_block("simulink/Ports & Subsystems/Subsystem", block(model_name, controller_label), ...
    "Position", [250 85 400 165]);
add_block("simulink/Ports & Subsystems/Subsystem", block(model_name, "Climate Logic"), ...
    "Position", [470 75 620 175]);
add_block("simulink/Ports & Subsystems/Subsystem", block(model_name, "Chamber Plant"), ...
    "Position", [720 75 900 205]);

add_block("simulink/Sources/Constant", block(model_name, "Humidity Threshold"), ...
    "Value", "65", ...
    "Position", [250 250 320 280]);
add_block("simulink/Sources/Constant", block(model_name, "Humidifier Disturbance"), ...
    "Value", "1", ...
    "Position", [520 250 610 280]);
add_block("simulink/Sources/Step", block(model_name, "Ice Disturbance"), ...
    "Time", "60", ...
    "Before", "0", ...
    "After", "1", ...
    "Position", [520 305 610 335]);

add_block("simulink/Sinks/Scope", block(model_name, "Outputs"), ...
    "NumInputPorts", "4", ...
    "Position", [980 90 1030 210]);

build_conceptual_subsystem(block(model_name, controller_label), ...
    1, ...
    1, ...
    "Inputs: error, sample time, internal memory", ...
    "Output: signed temperature control effort");
build_conceptual_subsystem(block(model_name, "Climate Logic"), ...
    5, ...
    2, ...
    "Inputs: temperature effort, measured temperature, measured humidity, temperature setpoint, humidity threshold" + newline + ...
    "Behavior: heater/fan selection with hysteresis", ...
    "Outputs: heater command, fan command");
build_conceptual_subsystem(block(model_name, "Chamber Plant"), ...
    4, ...
    2, ...
    "Inputs: heater command, fan command, humidifier disturbance, ice disturbance" + newline + ...
    "Behavior: first-order chamber temperature and humidity response", ...
    "Outputs: temperature, humidity");

add_line(model_name, "Temperature Setpoint/1", "Error/1", "autorouting", "on");
add_line(model_name, "Chamber Plant/1", "Error/2", "autorouting", "on");
add_line(model_name, "Error/1", controller_label + "/1", "autorouting", "on");
add_line(model_name, controller_label + "/1", "Climate Logic/1", "autorouting", "on");
add_line(model_name, "Chamber Plant/1", "Climate Logic/2", "autorouting", "on");
add_line(model_name, "Temperature Setpoint/1", "Climate Logic/3", "autorouting", "on");
add_line(model_name, "Chamber Plant/2", "Climate Logic/4", "autorouting", "on");
add_line(model_name, "Humidity Threshold/1", "Climate Logic/5", "autorouting", "on");
add_line(model_name, "Climate Logic/1", "Chamber Plant/1", "autorouting", "on");
add_line(model_name, "Climate Logic/2", "Chamber Plant/2", "autorouting", "on");
add_line(model_name, "Humidifier Disturbance/1", "Chamber Plant/3", "autorouting", "on");
add_line(model_name, "Ice Disturbance/1", "Chamber Plant/4", "autorouting", "on");

add_line(model_name, "Chamber Plant/1", "Outputs/1", "autorouting", "on");
add_line(model_name, "Chamber Plant/2", "Outputs/2", "autorouting", "on");
add_line(model_name, "Climate Logic/1", "Outputs/3", "autorouting", "on");
add_line(model_name, "Climate Logic/2", "Outputs/4", "autorouting", "on");
end

function build_conceptual_subsystem(subsystem_path, num_inputs, num_outputs, note_1, note_2)
disp("Building conceptual subsystem: " + string(subsystem_path));
open_system(subsystem_path);
delete_contents(subsystem_path);

set_param(subsystem_path, "AttributesFormatString", sprintf("%s\n%s", note_1, note_2));

for i = 1:num_inputs
    in_block = subblock(subsystem_path, "In" + num2str(i));
    disp("  adding block: " + string(in_block));
    add_block("simulink/Sources/In1", in_block, ...
        "Position", [30 30 + 35 * (i - 1) 60 50 + 35 * (i - 1)]);
end

for i = 1:num_outputs
    out_block = subblock(subsystem_path, "Out" + num2str(i));
    disp("  adding block: " + string(out_block));
    add_block("simulink/Sinks/Out1", out_block, ...
        "Position", [290 30 + 35 * (i - 1) 320 50 + 35 * (i - 1)]);
end

for i = 1:min(num_inputs, num_outputs)
    add_line(subsystem_path, "In" + num2str(i) + "/1", "Out" + num2str(i) + "/1", "autorouting", "on");
end
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
path_value = sprintf("%s/%s", char(model_name), char(block_name));
end

function path_value = subblock(system_path, block_name)
path_value = sprintf("%s/%s", char(system_path), char(block_name));
end
