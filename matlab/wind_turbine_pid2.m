%% AI-Assisted Wind Turbine Controller Validation
% Simplified educational generator model
% Open-loop vs PID controller
% Disturbance testing and automated performance metrics

clear;
clc;
close all;

%% 1. Model parameters
J = 0.05;                 % Equivalent rotational inertia
B = 0.02;                 % Damping coefficient
omega_ref = 10;           % Target generator speed (rad/s)

% Operating-point driving torque
T_drive_0 = B * omega_ref;

%% 2. Simulation settings
dt = 0.01;
T_end = 20;
t = 0:dt:T_end;
N = numel(t);

disturbance_start = 4;
disturbance_end = 5;
disturbance_factor = 1.20;

%% 3. Disturbance input
T_drive = T_drive_0 * ones(1,N);

disturbance_mask = ...
    (t >= disturbance_start) & ...
    (t < disturbance_end);

T_drive(disturbance_mask) = ...
    disturbance_factor * T_drive_0;

%% 4. Open-loop simulation
% No active speed feedback controller

omega_open = zeros(1,N);
omega_open(1) = omega_ref;

for k = 1:N-1
    domega = ...
        (T_drive(k) - B*omega_open(k))/J;

    omega_open(k+1) = ...
        omega_open(k) + dt*domega;
end

%% 5. PID controller simulation
% Controller parameters
Kp = 0.5;
Ki = 0.5;
Kd = 0.01;

% Torque adjustment limits
T_adjust_max = 0.10;
integral_limit = 1.0;

omega_pid = zeros(1,N);
omega_pid(1) = omega_ref;

T_gen = zeros(1,N);
error = zeros(1,N);
integral_error = 0;
previous_error = 0;

for k = 1:N-1

    % Speed tracking error
    error(k) = omega_pid(k) - omega_ref;

    % Integral term with bounded accumulation
    integral_error = integral_error ...
        + error(k)*dt;

    integral_error = max(-integral_limit, ...
        min(integral_limit, integral_error));

    % Derivative term
    derivative_error = ...
        (error(k)-previous_error)/dt;

    % PID torque command
    torque_command = ...
        Kp*error(k) ...
        + Ki*integral_error ...
        + Kd*derivative_error;

    % Saturation
    torque_command = max(-T_adjust_max, ...
        min(T_adjust_max, torque_command));

    T_gen(k) = torque_command;

    % Generator dynamics
    domega = ...
        (T_drive(k) - B*omega_pid(k) ...
        - T_gen(k))/J;

    omega_pid(k+1) = ...
        omega_pid(k) + dt*domega;

    previous_error = error(k);
end

error(N) = omega_ref - omega_pid(N);
T_gen(N) = T_gen(N-1);

%% 6. Plot controller comparison
figure('Name','Wind Turbine Controller Validation');

plot(t, omega_open, 'LineWidth', 1.8);
hold on;

plot(t, omega_pid, 'LineWidth', 1.8);

plot(t, omega_ref*ones(1,N), '--', ...
    'LineWidth', 1.2);

xline(disturbance_start, ':', ...
    'Disturbance starts');

xline(disturbance_end, ':', ...
    'Disturbance ends');

xlabel('Time (seconds)');
ylabel('Angular speed (rad/s)');

title('Wind Turbine Speed: Open-loop vs PID');

legend('Open-loop','PID-controlled','Reference', ...
    'Location','best');

grid on;
hold off;

%% 7. Automated performance metrics
% Rise time is not meaningful for this experiment
% because the system starts at the reference speed.

controller_names = ["Open-loop"; "PID"];

responses = {omega_open, omega_pid};

rise_time_s = NaN(2,1);
recovery_time_s = NaN(2,1);
max_deviation_rad_s = zeros(2,1);
overshoot_pct = zeros(2,1);
steady_state_error_pct = zeros(2,1);
rmse = zeros(2,1);
max_abs_torque = [0; max(abs(T_gen))];

tolerance = 0.02 * abs(omega_ref);

for j = 1:2

    y = responses{j};

    % Maximum absolute speed deviation during disturbance
    during_disturbance = ...
        t >= disturbance_start & ...
        t < disturbance_end;

    max_deviation_rad_s(j) = ...
        max(abs(y(during_disturbance)-omega_ref));

    % Positive overshoot relative to reference
    overshoot_pct(j) = ...
        max(0, max(y)-omega_ref) ...
        / abs(omega_ref)*100;

    % Final steady-state error
    steady_state_error_pct(j) = ...
        abs(y(end)-omega_ref) ...
        / abs(omega_ref)*100;

    % Overall root mean squared tracking error
    rmse(j) = ...
        sqrt(mean((y-omega_ref).^2));




    % Recovery calculation after disturbance ends
    tolerance = 0.02 * abs(omega_ref);
    responses = {omega_open, omega_pid};
    recovery_time_s = NaN(2, 1);

    post_disturbance = find(t > disturbance_end);

    for j = 1:2
        y = responses{j};
        recovery_idx = NaN;

        for n = 1:numel(post_disturbance)
            k = post_disturbance(n);

            if all(abs(y(k:end) - omega_ref) <= tolerance)
                recovery_idx = k;
                break;
            end
        end

        if ~isnan(recovery_idx)
            recovery_time_s(j) = ...
                t(recovery_idx) - disturbance_end;
        end
    end
end

%% 8. Results table
metrics = table( ...
    controller_names, ...
    rise_time_s, ...
    max_deviation_rad_s, ...
    recovery_time_s, ...
    overshoot_pct, ...
    steady_state_error_pct, ...
    rmse, ...
    max_abs_torque, ...
    'VariableNames', { ...
    'Controller', ...
    'RiseTime_s', ...
    'MaxDeviation_rad_s', ...
    'RecoveryTime_s', ...
    'Overshoot_pct', ...
    'SteadyStateError_pct', ...
    'RMSE', ...
    'MaxAbsTorque_Nm'});

disp(' ');
disp('===== WIND TURBINE VALIDATION REPORT =====');
disp(metrics);

%% 9. Export results to project folder
output_dir = ...
    'D:\Simulation\AI-Assisted Wind Turbine Controller\results';

if ~isfolder(output_dir)
    mkdir(output_dir);
end

output_file = fullfile(output_dir, ...
    'wind_turbine_pid_metrics.csv');

writetable(metrics, output_file);

fprintf('\nMetrics exported successfully:\n%s\n', ...
    output_file);

%% 10. Save simulation time-series data
time_series = table( ...
    t(:), ...
    T_drive(:), ...
    omega_open(:), ...
    omega_pid(:), ...
    T_gen(:), ...
    'VariableNames', { ...
    'Time_s', ...
    'DrivingTorque_Nm', ...
    'OpenLoopSpeed_rad_s', ...
    'PIDSpeed_rad_s', ...
    'GeneratorTorque_Nm'});

writetable(time_series, ...
    fullfile(output_dir, ...
    'wind_turbine_timeseries.csv'));

fprintf('Time-series data exported successfully.\n');
