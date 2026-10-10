clear;
clc;
close all;

t = 0:0.01:10;
y = 1-exp(-t);

figure;
plot(t, y, 'LineWidth', 2);
grid on;
xlabel('Time (seconds)');
ylabel('System Output');
title('First-Order Step Response');