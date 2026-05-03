function sim_out = run_env_control_simplified_simulation()
%RUN_ENV_CONTROL_SIMPLIFIED_SIMULATION Build the simplified model and run it.

addpath(fileparts(mfilename("fullpath")));
params = setup_env_control_params();
model_name = build_env_control_simplified_model();
sim_out = sim(model_name, "StopTime", num2str(params.stop_time));
open_system(model_name);
end
