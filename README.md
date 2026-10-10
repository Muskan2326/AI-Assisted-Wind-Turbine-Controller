# AeroGrid — AI-Assisted Wind Turbine Controller

**A MATLAB-based wind turbine control simulation and Python-powered validation test bench.**

AeroGrid is a prototype for simulating wind turbine controller behavior under different operating conditions. It combines PID-based control, multi-scenario simulation, automated performance evaluation, and an interactive dashboard to help analyze rotor-speed tracking and disturbance response.

## Project Overview

Wind turbines operate under continuously changing wind conditions. Evaluating controller behavior across different scenarios helps identify tracking errors, overshoot, and recovery performance.

AeroGrid provides a simulation-oriented environment for testing controller configurations, visualizing results, and evaluating performance against configurable criteria.

## Key Features

- **PID Controller Simulation:** Evaluate rotor-speed tracking using configurable controller parameters.
- **Multi-Scenario Testing:** Simulate normal operation, wind gusts, wind-speed drops, and turbulent conditions.
- **Automated Validation:** Calculate performance metrics and evaluate test outcomes against defined pass/fail criteria.
- **Interactive Test Bench:** Configure test parameters and explore simulation results through a dashboard.
- **Performance Visualization:** Analyze rotor-speed response, tracking error, and other simulation metrics.
- **3D Digital Twin Prototype:** Explore a 3D wind turbine model through the browser-based viewer.

## Technology Stack

- **MATLAB:** Controller modeling and simulation
- **Python:** Scenario execution, validation, and data processing
- **Streamlit:** Interactive dashboard
- **NumPy, Pandas, Matplotlib:** Numerical analysis and visualization
- **HTML / JavaScript:** Browser-based 3D turbine viewer

*The exact dependencies and feature availability depend on the included scripts and project configuration.*

## Project Structure

```text
AI-Assisted-Wind-Turbine-Controller/
├── config/
├── docs/
├── matlab/
├── python/
│   ├── live_dashboard.py
│   ├── live_dashboard_integrated.py
│   ├── scenario_runner.py
│   ├── validator.py
│   ├── disturbance_validator.py
│   └── wind_turbine_validator.py
├── results/
├── tests/
├── turbine_3d.html
├── wind_turbine.blend
├── wind_turbine.glb
├── .gitignore
└── README.md
```

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Muskan2326/AI-Assisted-Wind-Turbine-Controller.git
cd AI-Assisted-Wind-Turbine-Controller
```

### 2. Install Dependencies

Create and activate a Python virtual environment if desired, then install the packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not present, create it with the dependencies required by the selected dashboard and validation scripts before running this command.

### 3. Launch the Dashboard

From the project root, run:

```bash
streamlit run python/live_dashboard.py
```

If your primary dashboard is a different script, replace the filename with the correct entry point.

### 4. Explore the 3D Turbine

Open `turbine_3d.html` in a modern browser to explore the 3D turbine viewer. Viewer behavior may depend on its JavaScript libraries and asset paths.

## Validation Metrics

Depending on the selected test and implementation, the validation workflow can evaluate:

- Maximum rotor-speed tracking error
- Peak rotor speed and overshoot
- Final tracking error
- Response to wind disturbances
- Pass/fail status against configured thresholds

**Note:** This project is a simulation prototype. Its results are not a substitute for physical turbine testing, hardware-in-the-loop validation, or certification.

## Future Improvements

- Expand automated regression testing across controller configurations.
- Compare PID and state-space control strategies.
- Improve robustness testing under varying wind profiles and sensor noise.
- Add repeatable experiment reports and performance summaries.
- Extend the digital twin visualization and dashboard integration.

## Author

**Muskan2326**

GitHub: [@Muskan2326](https://github.com/Muskan2326)

---

* A simulation-focused prototype for wind turbine controller evaluation and performance analysis.*
