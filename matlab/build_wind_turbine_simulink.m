
%% Build Wind Turbine Simulink Model
clear; clc;

mdl = 'wind_turbine_realtime';
if bdIsLoaded(mdl)
    close_system(mdl, 0);
end
new_system(mdl);
open_system(mdl);

set_param(mdl, ...
    'Solver', 'FixedStepDiscrete', ...
    'FixedStep', '0.01', ...
    'StopTime', '20');

% Sources
add_block('simulink/Sources/Clock', [mdl '/Clock'], ...
    'Position', [40 70 70 90]);

add_block('simulink/Sources/Constant', [mdl '/ScenarioCode'], ...
    'Value', 'scenario_code', ...
    'Position', [40 140 100 170]);

add_block('simulink/Sources/Random Number', [mdl '/Noise'], ...
    'Mean', '0', 'Variance', '1', ...
    'SampleTime', '0.01', ...
    'Position', [40 210 100 240]);

add_block('simulink/Math Operations/Gain', [mdl '/NoiseScale'], ...
    'Gain', '0.01', ...
    'Position', [135 210 185 240]);

% MATLAB Function block
add_block('simulink/User-Defined Functions/MATLAB Function', ...
    [mdl '/ControllerPlant'], ...
    'Position', [240 70 420 240]);

% Set MATLAB Function block code
rt = sfroot;
chart = rt.find('-isa', 'Stateflow.EMChart', ...
    'Path', [mdl '/ControllerPlant']);

code = [
"function [omega_open, omega_pid, torque_cmd, error_out] = controller_step(t, scenario, noise)"
"%#codegen"
"persistent wo wp integral previous_error"
"J = 0.05; B = 0.02; ref = 10; dt = 0.01;"
"Kp = 0.5; Ki = 0.5; Kd = 0.01; torque_limit = 0.10;"
"if isempty(wo) || t < dt/2"
"    wo = ref; wp = ref; integral = 0; previous_error = 0;"
"end"
"factor = 1;"
"if scenario == 1 && t >= 4 && t < 5"
"    factor = 1.20;"
"elseif scenario == 2 && t >= 4 && t < 7"
"    factor = 1.20;"
"elseif scenario == 3 && t >= 4 && t < 7"
"    factor = 0.80;"
"end"
"Tdrive = B * ref * factor;"
"% Open-loop plant"
"wo = wo + dt * (Tdrive - B*wo) / J;"
"% PID measurement"
"measured = wp;"
"if scenario == 4"
"    measured = wp + noise;"
"end"
"error_out = ref - measured;"
"% Positive generator torque opposes overspeed"
"control_error = measured - ref;"
"integral = max(-1, min(1, integral + control_error*dt));"
"derivative = (control_error - previous_error)/dt;"
"torque_cmd = Kp*control_error + Ki*integral + Kd*derivative;"
"torque_cmd = max(-torque_limit, min(torque_limit, torque_cmd));"
"wp = wp + dt*(Tdrive - B*wp - torque_cmd)/J;"
"previous_error = control_error;"
"omega_open = wo;"
"omega_pid = wp;"
];

chart.Script = strjoin(cellstr(code), newline);

% Outputs
names = {'OpenLoopSpeed', 'PIDSpeed', 'GeneratorTorque', 'TrackingError'};
for k = 1:numel(names)
    y = 300 + (k-1)*90;
    add_block('simulink/Sinks/To Workspace', ...
        [mdl '/' names{k}], ...
        'VariableName', lower(names{k}), ...
        'SaveFormat', 'Timeseries', ...
        'Position', [510 y 620 y+30]);
    add_line(mdl, ...
        ['ControllerPlant/' num2str(k)], ...
        [names{k} '/1']);
end

% Connect inputs
add_line(mdl, 'Clock/1', 'ControllerPlant/1');
add_line(mdl, 'ScenarioCode/1', 'ControllerPlant/2');
add_line(mdl, 'NoiseScale/1', 'ControllerPlant/3');
add_line(mdl, 'Noise/1', 'NoiseScale/1');

% Scope: compare open-loop and PID speed
add_block('simulink/Signal Routing/Mux', [mdl '/SpeedMux'], ...
    'Inputs', '2', 'Position', [480 70 485 130]);
add_block('simulink/Sinks/Scope', [mdl '/SpeedScope'], ...
    'Position', [540 65 610 130]);
add_line(mdl, 'ControllerPlant/1', 'SpeedMux/1');
add_line(mdl, 'ControllerPlant/2', 'SpeedMux/2');
add_line(mdl, 'SpeedMux/1', 'SpeedScope/1');

% Choose scenario: 0 normal, 1 short gust, 2 long gust,
% 3 wind-speed drop, 4 sensor noise
scenario_code = 1;  % Short wind gust
set_param('wind_turbine_realtime', 'SimulationCommand', 'start')

disp('Simulink model created: wind_turbine_realtime.slx');
disp('Set scenario_code = 0, 1, 2, 3, or 4 before simulation.');
