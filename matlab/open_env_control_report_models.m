function model_names = open_env_control_report_models()
%OPEN_ENV_CONTROL_REPORT_MODELS Build and open conceptual report models.

addpath(fileparts(mfilename("fullpath")));
model_names = build_env_control_report_models();
for i = 1:numel(model_names)
    open_system(model_names(i));
end
end
