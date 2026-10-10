clear;
clc;
close all;

%% 1. Simulation settings
dt = 0.01;              % Time step in seconds
T = 10;                 % Total simulation time
t = 0:dt:T;
N = length(t);

reference = 1;          % Desired output

%% 2. PID controller gains
Kp = 2.0;
Ki = 1.0;
Kd = 0.1;

%% 3. Initialize variables
y_open = zeros(1, N);
y_pid = zeros(1, N);

u_open = ones(1, N);
u_pid = zeros(1, N);

integral_error = 0;
previous_error = reference;

%% 4. Run simulation
for k = 2:N

    % Open-loop plant: dy/dt = -y + u
    y_open(k) = y_open(k-1) + ...
        dt * (-y_open(k-1) + u_open(k));

    % Calculate PID error
    error = reference - y_pid(k-1);

    integral_error = integral_error + error * dt;

    derivative_error = ...
        (error - previous_error) / dt;

    % PID control signal
    u_pid(k) = Kp * error ...
        + Ki * integral_error ...
        + Kd * derivative_error;

    % Apply control signal to the plant
    y_pid(k) = y_pid(k-1) + ...
        dt * (-y_pid(k-1) + u_pid(k));

    previous_error = error;
end

%% 5. Plot comparison
figure;

plot(t, reference * ones(1, N), '--', ...
    'LineWidth', 1.5);
hold on;

plot(t, y_open, 'LineWidth', 2);
plot(t, y_pid, 'LineWidth', 2);

xlabel('Time (seconds)');
ylabel('System Output');
title('Open-Loop vs PID Controller');

legend('Reference', 'Open-loop', 'PID-controlled', ...
    'Location', 'best');

grid on;
hold off;

%% 6. Display final values
fprintf('Open-loop final output: %.4f\n', y_open(end));
fprintf('PID final output: %.4f\n', y_pid(end));
fprintf('Reference output: %.4f\n', reference);