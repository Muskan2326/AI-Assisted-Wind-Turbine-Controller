
%% 7. Automated performance metrics

signals = {y_open, y_pid};
names = {'Open-loop', 'PID'};

fprintf('\n===== PERFORMANCE REPORT =====\n');

for j = 1:2

    y = signals{j};

    % Rise time: time to go from 10% to 90%
    idx10 = find(y >= 0.1 * reference, 1, 'first');
    idx90 = find(y >= 0.9 * reference, 1, 'first');

    if isempty(idx10) || isempty(idx90)
        rise_time = NaN;
    else
        rise_time = t(idx90) - t(idx10);
    end

    % Settling time: final entry into the 2% error band
    tolerance = 0.02 * abs(reference);
    outside = find(abs(y - reference) > tolerance);

    if isempty(outside)
        settling_time = 0;
    elseif outside(end) == N
        settling_time = NaN;
    else
        settling_time = t(outside(end) + 1);
    end

    % Maximum overshoot, as a percentage
    overshoot = max(0, ...
        (max(y) - reference) / abs(reference) * 100);

    % Final steady-state error, as a percentage
    steady_state_error = ...
        abs(reference - y(end)) / abs(reference) * 100;

    % Root mean squared tracking error
    rmse = sqrt(mean((reference - y).^2));

    fprintf('\n%s\n', names{j});
    fprintf('Rise time: %.3f s\n', rise_time);
    fprintf('Settling time: %.3f s\n', settling_time);
    fprintf('Overshoot: %.3f %%\n', overshoot);
    fprintf('Steady-state error: %.3f %%\n', ...
        steady_state_error);
    fprintf('RMSE: %.4f\n', rmse);
end


%% 8. Export performance metrics to CSV

controller = ["Open-loop"; "PID"];

rise_times = zeros(2,1);
settling_times = zeros(2,1);
overshoots = zeros(2,1);
steady_errors = zeros(2,1);
rmses = zeros(2,1);

for j = 1:2
    y = signals{j};

    idx10 = find(y >= 0.1 * reference, 1, 'first');
    idx90 = find(y >= 0.9 * reference, 1, 'first');

    if isempty(idx10) || isempty(idx90)
        rise_times(j) = NaN;
    else
        rise_times(j) = t(idx90) - t(idx10);
    end

    outside = find(abs(y-reference) > ...
        0.02*abs(reference));

    if isempty(outside)
        settling_times(j) = 0;
    elseif outside(end) == N
        settling_times(j) = NaN;
    else
        settling_times(j) = t(outside(end)+1);
    end

    overshoots(j) = max(0, ...
        (max(y)-reference)/abs(reference)*100);

    steady_errors(j) = ...
        abs(reference-y(end))/abs(reference)*100;

    rmses(j) = sqrt(mean((reference-y).^2));
end

results = table(controller, rise_times, ...
    settling_times, overshoots, steady_errors, rmses, ...
    'VariableNames', {'Controller','RiseTime_s', ...
    'SettlingTime_s','Overshoot_pct', ...
    'SteadyStateError_pct','RMSE'});

writetable(results, 'controller_results.csv');

disp(results);
fprintf('CSV exported: %s\n', ...
    fullfile(pwd, 'controller_results.csv'));


%% 9. Disturbance rejection experiment

% A temporary disturbance enters the plant at t = 4 s
disturbance = zeros(1, N);
disturbance(t >= 4 & t < 5) = 0.3;

y_disturbed = zeros(1, N);
integral_dist = 0;
previous_error_dist = reference;

for k = 2:N

    error_dist = reference - y_disturbed(k-1);

    integral_dist = integral_dist + error_dist * dt;

    derivative_dist = ...
        (error_dist - previous_error_dist) / dt;

    control = Kp * error_dist ...
        + Ki * integral_dist ...
        + Kd * derivative_dist;

    % Disturbance affects the plant input
    plant_input = control + disturbance(k);

    y_disturbed(k) = y_disturbed(k-1) + ...
        dt * (-y_disturbed(k-1) + plant_input);

    previous_error_dist = error_dist;
end

figure;
plot(t, reference * ones(1,N), '--', 'LineWidth', 1.5);
hold on;
plot(t, y_disturbed, 'LineWidth', 2);
xline(4, ':', 'Disturbance starts');
xline(5, ':', 'Disturbance ends');
xlabel('Time (seconds)');
ylabel('System Output');
title('PID Response to an Input Disturbance');
legend('Reference', 'Disturbed response', 'Location', 'best');
grid on;
hold off;


%% 10. Corrected disturbance metrics

disturbance_start = 4;
disturbance_end = 5;
tolerance = 0.02 * abs(reference);

% Compare disturbed response with the original PID response.
% This isolates the disturbance effect from startup error.
during_disturbance = ...
    t >= disturbance_start & t < disturbance_end;

disturbance_effect = y_disturbed - y_pid;

max_disturbance_deviation = ...
    max(abs(disturbance_effect(during_disturbance)));

% Recovery: return within 2% of the baseline PID response
% and remain there for the rest of the simulation.
post_disturbance = find(t >= disturbance_end);
recovery_time = NaN;

for idx = post_disturbance
    if all(abs(disturbance_effect(idx:end)) <= tolerance)
        recovery_time = t(idx) - disturbance_end;
        break;
    end
end

fprintf('\n===== CORRECTED DISTURBANCE REPORT =====\n');
fprintf('Maximum disturbance effect: %.4f\n', ...
    max_disturbance_deviation);

if isnan(recovery_time)
    fprintf('Recovery: Not achieved within simulation\n');
else
    fprintf('Recovery time: %.3f seconds\n', recovery_time);
end

% Visualize baseline versus disturbed response
figure;
plot(t, y_pid, 'LineWidth', 2);
hold on;
plot(t, y_disturbed, '--', 'LineWidth', 2);
xline(disturbance_start, ':', 'Disturbance starts');
xline(disturbance_end, ':', 'Disturbance ends');
xlabel('Time (seconds)');
ylabel('System Output');
title('Baseline PID vs Disturbed PID');
legend('Baseline PID', 'Disturbed PID', ...
    'Location', 'best');
grid on;
hold off;

%% 11. Export disturbance results

scenario = "InputDisturbance";
controller_name = "PID";

disturbance_results = table( ...
    scenario, ...
    controller_name, ...
    max_disturbance_deviation, ...
    recovery_time, ...
    'VariableNames', { ...
    'Scenario', ...
    'Controller', ...
    'MaxDisturbanceEffect', ...
    'RecoveryTime_s' ...
    });

output_dir = ...
    'D:\Simulation\AI-Assisted Wind Turbine Controller\results';

if ~isfolder(output_dir)
    mkdir(output_dir);
end

output_file = fullfile(output_dir, 'disturbance_results.csv');

writetable(disturbance_results, output_file);

disp(disturbance_results);
fprintf('Disturbance CSV saved to: %s\n', output_file);
