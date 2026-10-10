"""
AeroGrid — Wind Turbine Digital Twin (visual simulation prototype)
Run:
    pip install streamlit plotly matplotlib numpy pandas
    streamlit run wind_turbine_digital_twin.py

This is a real-time *software simulation* of a simplified turbine/controller model,
not a connection to physical turbine hardware or MATLAB/Simulink.
"""

import time
import math
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Rectangle
from pathlib import Path
import streamlit.components.v1 as components

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def render_turbine_3d(
    rotor_speed=10.0,
    wind_speed=8.0,
    pitch_angle=0.0,
    generator_torque=0.0
):
    """Render the exported Blender GLB in a Three.js viewer; fall back if unavailable."""
    import base64
    model_path = PROJECT_ROOT / "wind_turbine.glb"
    html_path = PROJECT_ROOT / "turbine_3d.html"

    if not html_path.exists():
        st.warning(f"3D viewer HTML not found: {html_path}. Keep turbine_3d.html beside the dashboard project.")
        return
    if not model_path.exists():
        st.warning(f"Blender model not found: {model_path}. Copy wind_turbine.glb into the project root.")
        return

    html = html_path.read_text(encoding="utf-8")
    model_b64 = base64.b64encode(model_path.read_bytes()).decode("ascii")
    replacements = {
        "__GLB_BASE64__": model_b64,
        "__ROTOR_SPEED__": str(float(rotor_speed)),
        "__WIND_SPEED__": str(float(wind_speed)),
        "__PITCH_ANGLE__": str(float(pitch_angle)),
        "__GENERATOR_TORQUE__": str(float(generator_torque)),
    }
    for token, value in replacements.items():
        html = html.replace(token, value)
    components.html(html, height=650, scrolling=False)

st.set_page_config(
    page_title="AeroGrid | Wind Turbine Digital Twin",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Theme ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root { --bg:#07111f; --panel:#101e31; --panel2:#14263b; --line:#263c55;
        --text:#e8f1fb; --muted:#91a8c1; --cyan:#54e0d0; --blue:#60a5fa; --amber:#f6bd60; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background: radial-gradient(ellipse at 75% 0%, #15314b 0%, #091525 43%, #07111f 100%); color:var(--text); }
[data-testid="stSidebar"] { background:#0b1728; border-right:1px solid #22354b; }
.block-container { padding-top:1.2rem; padding-bottom:2rem; max-width:1600px; }
h1,h2,h3 { font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.03em; color:#f1f7ff; }
.hero { padding:25px 28px; border:1px solid #2a526b; border-radius:20px;
        background:linear-gradient(115deg,rgba(18,43,67,.98),rgba(15,62,72,.82));
        box-shadow:0 14px 45px rgba(0,0,0,.20); margin-bottom:18px; }
.eyebrow { color:#65e8d8; font-size:11px; letter-spacing:.22em; font-weight:700; text-transform:uppercase; }
.hero h1 { font-size:32px; margin:8px 0 5px 0; }
.hero p { color:#b7cbe0; margin:0; font-size:14px; }
.kpi { border:1px solid #263d56; background:linear-gradient(150deg,#12243a,#0e1b2c);
       padding:16px 18px; border-radius:15px; min-height:105px; }
.kpi-label { color:#9ab0c8; font-size:11px; text-transform:uppercase; letter-spacing:.08em; }
.kpi-value { font-family:'Space Grotesk',sans-serif; font-size:27px; font-weight:700; color:#f4f8ff; margin-top:5px; }
.kpi-foot { color:#69e2d3; font-size:11px; margin-top:2px; }
.panel { border:1px solid #253b54; background:rgba(15,29,47,.82); padding:15px 18px; border-radius:16px; }
.small-note { color:#91a8c1; font-size:12px; }
div.stButton > button { background:linear-gradient(90deg,#2dd4bf,#65e8d8); color:#06202a; border:0;
                         border-radius:10px; font-weight:700; min-height:44px; width:100%; }
div.stButton > button:hover { background:#9af5e9; color:#06202a; border:0; }
.stSlider label, .stSelectbox label, .stNumberInput label { color:#c9d8e8 !important; }
div[data-testid="stMetric"] { background:#102137; border:1px solid #263d56; border-radius:12px; padding:12px 14px; }
div[data-testid="stMetricLabel"] { color:#9ab0c8; }
hr { border-color:#263b52; }
</style>
""", unsafe_allow_html=True)

# ---------- Simulation model ----------
REF_DEFAULT = 10.0
J = 0.05
B = 0.02
DT = 0.02

SCENARIOS = {
    "Normal operation": {"gust": 0.00, "start": 0.0, "end": 0.0, "label": "Steady wind"},
    "Short wind gust": {"gust": 0.22, "start": 4.0, "end": 6.0, "label": "+22% wind gust"},
    "Long wind gust": {"gust": 0.22, "start": 4.0, "end": 9.0, "label": "+22% wind gust"},
    "Wind speed drop": {"gust": -0.18, "start": 4.0, "end": 7.0, "label": "−18% wind drop"},
    "Turbulent wind": {"gust": 0.15, "start": 3.0, "end": 12.0, "label": "Variable turbulence"},
    "Sensor noise": {"gust": 0.0, "start": 0.0, "end": 0.0, "label": "Noisy speed sensor"},
}

def simulate(scenario, kp, ki, kd, duration, ref=REF_DEFAULT, noise_level=0.0, test_config=None):
    n = int(duration / DT) + 1
    t = np.linspace(0, duration, n)
    wind = np.full(n, 12.0)
    cfg = dict(SCENARIOS[scenario])
    test_config = test_config or {}
    if scenario in ("Short wind gust", "Long wind gust", "Wind speed drop"):
        cfg["gust"] = float(test_config.get("gust_fraction", cfg["gust"]))
        cfg["start"] = float(test_config.get("disturbance_start", cfg["start"]))
        cfg["end"] = float(test_config.get("disturbance_end", cfg["end"]))
    gust_mask = (t >= cfg["start"]) & (t <= cfg["end"]) if cfg["end"] > cfg["start"] else np.zeros(n, dtype=bool)
    if scenario == "Turbulent wind":
        turb_amp = float(test_config.get("turbulence_amplitude", 0.45))
        wind += turb_amp*np.sin(2*np.pi*0.42*t) + 0.25*turb_amp*np.sin(2*np.pi*1.15*t)
    wind[gust_mask] *= (1.0 + cfg["gust"])
    # Wind power/torque proxy: normalized cubic wind relation, capped for stability.
    aero_base = 0.42
    aero = aero_base * (wind / 12.0)**3
    aero = np.clip(aero, 0.12, 0.95)
    if scenario == "Sensor noise":
        rng = np.random.default_rng(42)
        sensor_noise = rng.normal(0, noise_level, n)
    else:
        sensor_noise = np.zeros(n)

    open_speed = np.zeros(n); pid_speed = np.zeros(n)
    open_speed[0] = ref; pid_speed[0] = ref
    gen_torque = np.zeros(n); pitch = np.zeros(n); power = np.zeros(n)
    error_arr = np.zeros(n)
    integral = 0.0
    prev_speed = float(pid_speed[0])
    base_gen = 0.22  # balances nominal aero torque (0.42) and damping at 10 rad/s
    gen_torque[0] = base_gen
    pitch[0] = 2.0
    power[0] = base_gen * ref * 0.92
    torque_min, torque_max = 0.05, 0.90
    max_torque_step = 0.03
    for i in range(1, n):
        # Open-loop uses a fixed generator torque, so wind changes directly affect speed.
        open_acc = (aero[i-1] - base_gen - B*open_speed[i-1]) / J
        open_speed[i] = max(0.0, open_speed[i-1] + DT*open_acc)

        measured = pid_speed[i-1] + sensor_noise[i-1]
        err = ref - measured  # positive means rotor is slower than target
        # Derivative-on-measurement; deriv is negative when speed is rising.
        deriv = -(pid_speed[i-1] - prev_speed) / DT
        integral_candidate = float(np.clip(integral + err*DT, -3.0, 3.0))
        # IMPORTANT: generator torque is a braking load. If speed is too low,
        # reduce torque; if speed is too high, increase torque. This sign was
        # reversed in the previous implementation and caused runaway overspeed.
        # Wind-torque feed-forward: compensate part of the aerodynamic torque
        # change immediately, instead of waiting for rotor-speed error to grow.
        # This is a normalized simplified-model term, not a physical turbine estimate.
        feedforward_torque = base_gen + (aero[i-1] - aero_base)
        raw_command = feedforward_torque - kp*err - ki*integral_candidate - kd*deriv
        requested_torque = float(np.clip(raw_command, torque_min, torque_max))
        # Conditional integration anti-windup: don't integrate further into saturation.
        pushing_high = raw_command > torque_max and err < 0
        pushing_low = raw_command < torque_min and err > 0
        if not (pushing_high or pushing_low):
            integral = integral_candidate
        raw_command = feedforward_torque - kp*err - ki*integral - kd*deriv
        requested_torque = float(np.clip(raw_command, torque_min, torque_max))
        gen_torque[i] = float(np.clip(
            requested_torque,
            gen_torque[i-1] - max_torque_step,
            gen_torque[i-1] + max_torque_step
        ))

        # Supervisory pitch action feathers blades above rated speed.
        overspeed = max(0.0, pid_speed[i-1] - (ref + 0.35))
        pitch[i] = float(np.clip(2.0 + 9.0*overspeed, 0.0, 25.0))
        aero_pid = aero[i-1] * max(0.35, math.cos(math.radians(pitch[i])))
        pid_acc = (aero_pid - gen_torque[i] - B*pid_speed[i-1]) / J
        pid_speed[i] = max(0.0, pid_speed[i-1] + DT*pid_acc)
        error_arr[i] = err
        prev_speed = pid_speed[i-1]
        power[i] = max(0.0, gen_torque[i] * pid_speed[i] * 0.92)
    return pd.DataFrame({
        "time_s": t, "wind_speed_mps": wind, "open_loop_rad_s": open_speed,
        "pid_speed_rad_s": pid_speed, "reference_rad_s": ref,
        "generator_torque_pu": gen_torque, "blade_pitch_deg": pitch,
        "power_proxy_kw": power, "tracking_error_rad_s": ref-pid_speed,
    })

def turbine_figure(rotor_speed, wind_speed, pitch_deg, torque, scenario, time_s):
    """A live schematic: rotating blades and wind arrows update as simulation advances."""
    fig, ax = plt.subplots(figsize=(4.6, 4.2), dpi=115)
    fig.patch.set_facecolor("#0e1c2e")
    ax.set_facecolor("#0e1c2e")
    ax.set_xlim(-2.5, 3.4); ax.set_ylim(-0.35, 5.6); ax.axis("off")
    # Ground and tower
    ax.plot([-2.4, 3.3], [0, 0], color="#36516b", lw=2)
    ax.add_patch(Polygon([(-0.20,0.05),(0.18,0.05),(0.10,3.5),(-0.08,3.5)],
                         closed=True, facecolor="#a7bed1", edgecolor="#d9e8f5", lw=1.0))
    ax.add_patch(Rectangle((-0.30,3.45),0.72,0.22,facecolor="#6e8da7",edgecolor="#c4d7e8",lw=1))
    # Nacelle and hub
    ax.add_patch(Rectangle((0.12,3.48),0.85,0.32,facecolor="#d8e6f1",edgecolor="#f4f8ff",lw=1))
    ax.add_patch(Circle((0.10,3.64),0.14,facecolor="#54e0d0",edgecolor="#d9fffb",lw=1.2,zorder=5))
    # Wind direction lines, change with wind speed
    for j in range(5):
        y = 2.95 + j*0.23
        x0 = -2.25 + (j%2)*0.18
        ax.annotate("", xy=(-0.65,y), xytext=(x0,y),
                    arrowprops=dict(arrowstyle="->", color="#60a5fa", lw=1.4, alpha=.45+.08*(j%3)))
    # Rotor blades, angle advances with simulated rotor speed.
    angle = (time_s * max(rotor_speed,0.1) * 0.8) % (2*np.pi)
    hub_x, hub_y = -0.02, 3.64
    for b in range(3):
        a = angle + b*2*np.pi/3
        r1, r2 = 0.12, 1.72
        # tapered blade polygon around a radial line
        ux, uy = math.cos(a), math.sin(a)
        px, py = -uy, ux
        p1=(hub_x+ux*r1+px*.06, hub_y+uy*r1+py*.06)
        p2=(hub_x+ux*r2+px*.12, hub_y+uy*r2+py*.12)
        p3=(hub_x+ux*r2-px*.12, hub_y+uy*r2-py*.12)
        p4=(hub_x+ux*r1-px*.06, hub_y+uy*r1-py*.06)
        ax.add_patch(Polygon([p1,p2,p3,p4],closed=True,facecolor="#e7f1fa",edgecolor="#8caec7",lw=.8,zorder=4))
    ax.add_patch(Circle((hub_x,hub_y),0.16,facecolor="#54e0d0",edgecolor="#e1fffb",lw=1.2,zorder=6))
    ax.text(-2.25,5.18,"TURBINE LIVE VIEW",color="#54e0d0",fontsize=9,fontweight="bold")
    ax.text(-2.25,4.82,f"Wind  {wind_speed:4.1f} m/s",color="#eaf3fc",fontsize=10)
    ax.text(1.10,3.60,f"{pitch_deg:4.1f}° pitch",color="#f6bd60",fontsize=8.5)
    ax.text(1.10,3.32,f"{torque:4.2f} torque",color="#eaf3fc",fontsize=8.5)
    ax.text(-2.25,0.36,f"Scenario: {scenario}",color="#b4c8dd",fontsize=8.5)
    ax.text(-2.25,0.12,f"Simulated time: {time_s:5.2f} s",color="#8fa8c2",fontsize=8)
    plt.tight_layout(pad=0.25)
    return fig

def make_chart(df, end_index):
    d = df.iloc[:end_index+1]
    fig = make_subplots(rows=2, cols=2, vertical_spacing=0.18, horizontal_spacing=0.12,
                        subplot_titles=("Rotor speed & tracking", "Wind speed",
                                        "Generator torque", "Power output proxy"))
    fig.add_trace(go.Scatter(x=d.time_s,y=d.open_loop_rad_s,name="Open-loop",line=dict(color="#60a5fa",width=2,dash="dot")),row=1,col=1)
    fig.add_trace(go.Scatter(x=d.time_s,y=d.pid_speed_rad_s,name="PID controlled",line=dict(color="#54e0d0",width=2.8)),row=1,col=1)
    fig.add_trace(go.Scatter(x=d.time_s,y=d.reference_rad_s,name="Target",line=dict(color="#f6bd60",width=1.5,dash="dash")),row=1,col=1)
    fig.add_trace(go.Scatter(x=d.time_s,y=d.wind_speed_mps,name="Wind",line=dict(color="#60a5fa",width=2),fill="tozeroy",fillcolor="rgba(96,165,250,.08)"),row=1,col=2)
    fig.add_trace(go.Scatter(x=d.time_s,y=d.generator_torque_pu,name="Generator torque",line=dict(color="#f6bd60",width=2.2)),row=2,col=1)
    fig.add_trace(go.Scatter(x=d.time_s,y=d.power_proxy_kw,name="Power proxy",line=dict(color="#c4a7ff",width=2.2),fill="tozeroy",fillcolor="rgba(196,167,255,.08)"),row=2,col=2)
    fig.update_layout(height=520, margin=dict(l=12,r=12,t=52,b=12), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="#0c192a", font=dict(color="#c8d9eb",family="DM Sans",size=11),
                      legend=dict(orientation="h",yanchor="bottom",y=1.04,xanchor="left",x=0),
                      hovermode="x unified")
    fig.update_xaxes(title_text="Time (s)",gridcolor="#243950",zerolinecolor="#243950")
    fig.update_yaxes(gridcolor="#243950",zerolinecolor="#243950")
    fig.update_yaxes(title_text="rad/s",row=1,col=1)
    fig.update_yaxes(title_text="m/s",row=1,col=2)
    fig.update_yaxes(title_text="Torque (relative)",row=2,col=1)
    fig.update_yaxes(title_text="Relative power",row=2,col=2)
    return fig

# ---------- Interactive test bench ----------
with st.sidebar:
    st.markdown("## ⚙️ Control center")
    st.caption("Configure each test independently")
    test_mode = st.radio("Test mode", ["Single interactive test", "Run full test suite"], index=0)
    scenario = st.selectbox("Test / wind scenario", list(SCENARIOS.keys()), index=1)
    ref_speed = st.slider("Target rotor speed (rad/s)", 6.0, 14.0, 10.0, 0.5)
    kp = st.slider("Proportional gain · Kp", 0.0, 2.0, 0.20, 0.05)
    ki = st.slider("Integral gain · Ki", 0.0, 2.0, 0.08, 0.02)
    kd = st.slider("Derivative gain · Kd", 0.0, 0.10, 0.002, 0.001, format="%.3f")
    duration = st.slider("Simulation duration (s)", 8, 30, 20, 2)
    playback = st.select_slider("Playback speed", options=[0.5, 1, 2, 4], value=2,
                                format_func=lambda x: f"{x:g}×")
    st.markdown("#### Test-specific parameters")
    if scenario in ("Short wind gust", "Long wind gust", "Wind speed drop"):
        default_gust = SCENARIOS[scenario]["gust"] * 100
        gust_percent = st.slider("Wind disturbance (%)", -50, 60, int(default_gust), 1)
        disturbance_start = st.slider("Disturbance start (s)", 0.0, float(duration-1),
                                      min(float(SCENARIOS[scenario]["start"]), float(duration-1)), 0.5)
        min_end = min(float(duration), float(disturbance_start + 0.5))
        disturbance_end = st.slider("Disturbance end (s)", min_end, float(duration),
                                    max(min_end, min(float(SCENARIOS[scenario]["end"]), float(duration))), 0.5)
    else:
        gust_percent = int(SCENARIOS[scenario]["gust"] * 100)
        disturbance_start = float(SCENARIOS[scenario]["start"])
        disturbance_end = float(SCENARIOS[scenario]["end"])
    if scenario == "Turbulent wind":
        turbulence_amplitude = st.slider("Turbulence amplitude", 0.0, 1.5, 0.45, 0.05)
    else:
        turbulence_amplitude = 0.45
    noise = st.slider("Sensor noise (rad/s)", 0.0, 0.15, 0.03 if scenario=="Sensor noise" else 0.0, 0.01)
    max_error_limit = st.slider("PASS limit · max tracking error (rad/s)", 0.25, 5.0, 1.0, 0.25)
    max_overshoot_limit = st.slider("PASS limit · overshoot (%)", 0.0, 50.0, 15.0, 1.0)
    test_config = {
        "gust_fraction": gust_percent / 100.0,
        "disturbance_start": disturbance_start,
        "disturbance_end": disturbance_end,
        "turbulence_amplitude": turbulence_amplitude,
    }
    st.markdown("---")
    run_clicked = st.button("▶  Run selected test" if test_mode == "Single interactive test" else "▶  Run full test suite", use_container_width=True)
    reset_clicked = st.button("↺  Reset view", use_container_width=True)
    st.markdown("---")
    st.markdown("**Test status**")
    st.markdown("🟢 Within validation limits")
    st.markdown("🟠 Disturbance active")
    st.markdown("🔵 Open-loop benchmark")

if reset_clicked:
    st.session_state.pop("last_df", None)
    st.session_state.pop("finished", None)
    st.rerun()

# ---------- Header ----------
st.markdown("""
<div class="hero">
  <div class="eyebrow">AEROGRID · WIND TURBINE DIGITAL TWIN PROTOTYPE</div>
  <h1>Wind Turbine Interactive Test Bench</h1>
  <p>Watch the rotor turn, wind disturbances hit, controller torque respond, and operating metrics update live.</p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="panel" style="display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;margin-bottom:18px">
  <div><div class="kpi-label">ACTIVE SCENARIO</div><b>{scenario}</b><div class="small-note">{SCENARIOS[scenario]['label']}</div></div>
  <div><div class="kpi-label">CONTROL STRATEGY</div><b>PID + open-loop benchmark</b><div class="small-note">Kp {kp:.2f} · Ki {ki:.2f} · Kd {kd:.3f}</div></div>
  <div><div class="kpi-label">TARGET SPEED</div><b>{ref_speed:.1f} rad/s</b><div class="small-note">Nominal rotor-speed reference</div></div>
  <div><div class="kpi-label">SIMULATION MODE</div><b>Software digital twin</b><div class="small-note">Not connected to physical hardware</div></div>
</div>
""", unsafe_allow_html=True)

if run_clicked and test_mode == "Single interactive test":
    df = simulate(scenario, kp, ki, kd, duration, ref_speed, noise, test_config)
    chart_slot = st.empty()
    turbine_slot = st.empty()
    metric_slot = st.empty()
    status_slot = st.empty()
    progress_slot = st.progress(0, text="Initialising turbine model…")
    n = len(df)
    # Create the WebGL viewer once; repeatedly recreating an iframe resets its animation.
    first = df.iloc[0]
    with turbine_slot.container():
        st.markdown("#### Interactive 3D turbine")
        render_turbine_3d(
            rotor_speed=max(float(first.pid_speed_rad_s), 0.1),
            wind_speed=float(first.wind_speed_mps),
            pitch_angle=float(first.blade_pitch_deg),
            generator_torque=float(first.generator_torque_pu)
        )
    # Update chart/metrics in batches; keep the 3D iframe mounted for the full run.
    batch = max(1, int(0.40 / DT))
    for end in range(0, n, batch):
        stop = min(end + batch, n)
        current = df.iloc[stop-1]
        t_now = float(current.time_s)
        wind_now = float(current.wind_speed_mps)
        pid_now = float(current.pid_speed_rad_s)
        open_now = float(current.open_loop_rad_s)
        torque_now = float(current.generator_torque_pu)
        pitch_now = float(current.blade_pitch_deg)
        power_now = float(current.power_proxy_kw)
        start = float(test_config.get("disturbance_start", SCENARIOS[scenario]["start"]))
        finish = float(test_config.get("disturbance_end", SCENARIOS[scenario]["end"]))
        disturbance_active = finish > start and start <= t_now <= finish
        with chart_slot.container():
            st.plotly_chart(make_chart(df, stop-1), use_container_width=True, key=f"live_chart_{stop}")
        dev = abs(ref_speed-pid_now)
        status = "🟠 WIND DISTURBANCE ACTIVE" if disturbance_active else ("🟢 PID TRACKING" if dev < 0.25 else "🔵 CONTROLLER CORRECTING")
        with metric_slot.container():
            cols = st.columns(5)
            vals = [
                ("Rotor speed", f"{pid_now:.2f}", "rad/s"),
                ("Wind speed", f"{wind_now:.2f}", "m/s"),
                ("Generator torque", f"{torque_now:.3f}", "relative"),
                ("Blade pitch", f"{pitch_now:.1f}°", "pitch angle"),
                ("Power output", f"{power_now:.2f}", "relative kW proxy"),
            ]
            for col,(label,value,unit) in zip(cols,vals):
                with col:
                    st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-foot">{unit}</div></div>',unsafe_allow_html=True)
        status_slot.info(f"{status}  ·  simulated time {t_now:.2f}/{duration:.2f} s  ·  speed error {ref_speed-pid_now:+.3f} rad/s")
        progress_slot.progress(min(1.0, t_now/duration), text=f"Simulation time: {t_now:.2f} / {duration:.2f} s")
        time.sleep(max(0.01, (stop-end)*DT / playback))
    st.session_state["last_df"] = df
    st.session_state["finished"] = True
    st.success("Simulation finished. The rotor animation and all time-series are available in the completed view below.")
    st.download_button("⬇ Download simulation CSV", data=df.to_csv(index=False).encode("utf-8"),
                       file_name="wind_turbine_live_simulation.csv", mime="text/csv")
    # Completed summary
    max_dev = float(np.max(np.abs(df.pid_speed_rad_s-ref_speed)))
    peak = float(df.pid_speed_rad_s.max())
    overshoot = max(0.0,(peak-ref_speed)/ref_speed*100)
    st.subheader("Run summary")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Maximum tracking deviation",f"{max_dev:.3f} rad/s")
    c2.metric("Peak rotor speed",f"{peak:.3f} rad/s")
    c3.metric("Overshoot",f"{overshoot:.2f}%")
    c4.metric("Final speed error",f"{ref_speed-float(df.pid_speed_rad_s.iloc[-1]):+.3f} rad/s")
    low_sat_pct = float((df.generator_torque_pu <= 0.051).mean() * 100)
    high_sat_pct = float((df.generator_torque_pu >= 0.899).mean() * 100)
    st.caption(f"Actuator saturation: torque at minimum {low_sat_pct:.1f}% of run · at maximum {high_sat_pct:.1f}% of run")
    pass_flag = max_dev <= max_error_limit and overshoot <= max_overshoot_limit
    (st.success if pass_flag else st.error)(
        f"VALIDATION {'PASS' if pass_flag else 'FAIL'} · max error {max_dev:.3f}/{max_error_limit:.2f} rad/s · overshoot {overshoot:.2f}/{max_overshoot_limit:.1f}%"
    )
elif run_clicked and test_mode == "Run full test suite":
    suite_rows = []
    suite_data = {}
    suite_scenarios = list(SCENARIOS.keys())
    with st.spinner("Running all scenario tests…"):
        for test_name in suite_scenarios:
            cfg = dict(SCENARIOS[test_name])
            local_cfg = {"gust_fraction": cfg["gust"], "disturbance_start": cfg["start"],
                         "disturbance_end": cfg["end"], "turbulence_amplitude": 0.45}
            df_test = simulate(test_name, kp, ki, kd, duration, ref_speed,
                               noise if test_name == "Sensor noise" else 0.0, local_cfg)
            max_dev_test = float(np.max(np.abs(df_test.pid_speed_rad_s - ref_speed)))
            peak_test = float(df_test.pid_speed_rad_s.max())
            over_test = max(0.0, (peak_test-ref_speed)/ref_speed*100.0)
            final_error = float(ref_speed-df_test.pid_speed_rad_s.iloc[-1])
            passed = max_dev_test <= max_error_limit and over_test <= max_overshoot_limit
            suite_rows.append({"Test": test_name, "Max tracking error (rad/s)": round(max_dev_test, 3),
                               "Peak speed (rad/s)": round(peak_test, 3), "Overshoot (%)": round(over_test, 2),
                               "Final error (rad/s)": round(final_error, 3),
                               "Result": "PASS" if passed else "FAIL"})
            suite_data[test_name] = df_test
    suite_df = pd.DataFrame(suite_rows)
    st.subheader("Full test-suite results")
    st.caption("All six built-in scenarios use the current target speed and PID gains. This is a simplified software model; interpret PASS/FAIL against your project requirements.")
    st.dataframe(suite_df, use_container_width=True, hide_index=True)
    passed_count = int((suite_df["Result"] == "PASS").sum())
    m1, m2, m3 = st.columns(3)
    m1.metric("Tests passed", f"{passed_count}/{len(suite_df)}")
    m2.metric("Tests failed", f"{len(suite_df)-passed_count}")
    m3.metric("Scenarios executed", len(suite_df))
    st.download_button("⬇ Download test-suite report (CSV)", data=suite_df.to_csv(index=False).encode("utf-8"),
                       file_name="wind_turbine_test_suite.csv", mime="text/csv")
    selected_result = st.selectbox("Inspect test result", suite_scenarios, key="suite_inspect")
    detail = suite_data[selected_result]
    st.plotly_chart(make_chart(detail, len(detail)-1), use_container_width=True, key="suite_inspect_chart")
    st.subheader(f"{selected_result} · 3D snapshot")
    render_turbine_3d(rotor_speed=float(detail.pid_speed_rad_s.iloc[-1]),
                      wind_speed=float(detail.wind_speed_mps.iloc[-1]),
                      pitch_angle=float(detail.blade_pitch_deg.iloc[-1]),
                      generator_torque=float(detail.generator_torque_pu.iloc[-1]))
    st.session_state["last_df"] = detail
    st.session_state["finished"] = True
else:
    # Show a meaningful idle preview, not a blank/flat chart.
    preview = simulate(scenario, kp, ki, kd, duration, ref_speed, noise, test_config)
    preview_index = min(len(preview)-1, int(0.32*len(preview)))
    cur = preview.iloc[preview_index]
    left, right = st.columns([1, 2.2], gap="medium")
    with left:
        st.markdown("#### Interactive 3D turbine")
        render_turbine_3d(
            rotor_speed=float(cur.pid_speed_rad_s),
            wind_speed=float(cur.wind_speed_mps),
            pitch_angle=float(cur.blade_pitch_deg),
            generator_torque=float(cur.generator_torque_pu)
        )
    with right:
        st.plotly_chart(make_chart(preview, len(preview)-1), use_container_width=True, key="preview_chart")
    cols=st.columns(5)
    preview_vals=[
        ("Rotor speed",f"{cur.pid_speed_rad_s:.2f}","rad/s"),
        ("Wind speed",f"{cur.wind_speed_mps:.2f}","m/s"),
        ("Generator torque",f"{cur.generator_torque_pu:.3f}","relative"),
        ("Blade pitch",f"{cur.blade_pitch_deg:.1f}°","pitch angle"),
        ("Power output",f"{cur.power_proxy_kw:.2f}","relative kW proxy"),
    ]
    for col,(label,value,unit) in zip(cols,preview_vals):
        with col:
            st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-foot">{unit}</div></div>',unsafe_allow_html=True)
    st.info("Preview mode — select **Run selected test** to animate the rotor and update the charts in time. Short Wind Gust is selected by default so the disturbance is visible.")

st.markdown("---")
st.markdown("### How to read the digital twin")
guide1,guide2,guide3=st.columns(3)
with guide1:
    st.markdown('<div class="panel"><b style="color:#54e0d0">01 · Rotor & wind</b><p class="small-note">Blade rotation represents rotor motion. Wind speed changes when the selected gust/drop scenario becomes active.</p></div>',unsafe_allow_html=True)
with guide2:
    st.markdown('<div class="panel"><b style="color:#f6bd60">02 · Controller action</b><p class="small-note">PID changes generator torque to reduce speed error. Blade pitch is shown as a simplified overspeed-protection response.</p></div>',unsafe_allow_html=True)
with guide3:
    st.markdown('<div class="panel"><b style="color:#c4a7ff">03 · Validation view</b><p class="small-note">Compare PID with open-loop response. Export the run CSV for your existing Python validation workflow.</p></div>',unsafe_allow_html=True)
st.caption("Engineering note: this is an illustrative, simplified software model using normalized torque/power values. It is not a validated aeroelastic model, hardware telemetry, or a direct MATLAB/Simulink co-simulation.")
