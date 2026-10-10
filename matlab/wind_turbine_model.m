clear;
clc;
close all;

%% 1. Model parameters
J = 0.05;       % Equivalent inertia (kg*m^2)
B = 0.02;       % Damping (N*m*s/rad)

% Operating point
omega_ref = 10; % Reference speed (rad/s)
T_drive_0 = B * omega_ref;

%% 2. Simulation settings
dt = 0.01;
T_end = 10;
t = 0:dt:T_end;
N = numel(t);

%% 3. Driving torque disturbance
T_drive = T_drive_0 * ones(1, N);

% A 20% increase in driving torque from 4 to 5 s
T_drive(t >= 4 & t < 5) = 1.20 * T_drive_0;

%% 4. Simulate generator speed without active control
omega = zeros(1, N);
omega(1) = omega_ref;

for k = 2:N
    domega = (T_drive(k-1) - B*omega(k-1)) / J;

    omega(k) = omega(k-1) + dt*domega;
end

%% 5. Plot results
figure;

plot(t, omega, 'LineWidth', 2);
hold on;
yline(omega_ref, '--', 'Reference speed');
xline(4, ':', 'Disturbance starts');
xline(5, ':', 'Disturbance ends');

xlabel('Time (seconds)');
ylabel('Angular speed (rad/s)');
title('Simplified Wind Turbine Generator Model');
legend('Generator speed', 'Reference', 'Location', 'best');
grid on;
hold off;

%% 6. Display model information
fprintf('Inertia J: %.3f kg*m^2\n', J);
fprintf('Damping B: %.3f N*m*s/rad\n', B);
fprintf('Reference speed: %.2f rad/s\n', omega_ref);
fprintf('Final speed: %.4f rad/s\n', omega(end));
fprintf('Maximum speed: %.4f rad/s\n', max(omega));