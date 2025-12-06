import streamlit as st
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# ========================= CONFIG & STYLE =========================
st.set_page_config(
    page_title="Rod Stress & Strain Analyzer",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .big-font {font-size: 48px !important; font-weight: bold; color: #2c3e50; text-align: center;}
    .stress-box {padding: 15px; border-radius: 12px; text-align: center; font-size: 20px; margin: 10px 0;}
    .safe {background-color: #d4edda; color: #155724; border: 2px solid #c3e6cb;}
    .warning {background-color: #fff3cd; color: #856404; border: 2px solid #ffeaa7;}
    .danger {background-color: #f8d7da; color: #721c24; border: 2px solid #f5c6cb;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">Rod Stress & Strain Analyzer</p>', unsafe_allow_html=True)
st.markdown("### Mechanical + Thermal Stress Calculator • Fully Interactive", unsafe_allow_html=True)

# ========================= SIDEBAR – MATERIAL LIBRARY =========================
st.sidebar.header("Material Library")

materials = {
    "Custom":              {"E": None,      "alpha": None,      "allowable": None},
    "Mild Steel":          {"E": 200e9,     "alpha": 12e-6,     "allowable": 250e6},
    "Stainless Steel":     {"E": 193e9,     "alpha": 17.3e-6,   "allowable": 215e6},
    "Aluminum 6061-T6":    {"E": 69e9,      "alpha": 23.6e-6,   "allowable": 276e6},
    "Titanium Ti-6Al-4V":  {"E": 114e9,     "alpha": 8.6e-6,    "allowable": 880e6},
    "Brass":               {"E": 100e9,     "alpha": 18.7e-6,   "allowable": 150e6},
}

mat_name = st.sidebar.selectbox("Choose Material Preset", options=list(materials.keys()))
mat = materials[mat_name]

E = st.sidebar.number_input(
    "Young's Modulus E (Pa)",
    value=mat["E"] or 200e9,
    step=1e9,
    format="%.3e"
)
alpha = st.sidebar.number_input(
    "Thermal Expansion Coefficient α (1/K)",
    value=mat["alpha"] or 12e-6,
    format="%.3e"
)
allowable = st.sidebar.number_input(
    "Allowable Stress (Pa)",
    value=mat["allowable"] or 250e6,
    step=1e6,
    format="%.3e"
)

st.sidebar.markdown("---")
st.sidebar.subheader("Geometry & Loading")
diameter_mm = st.sidebar.slider("Rod Diameter", 1.0, 100.0, 20.0, 0.5, help="mm")
force_N     = st.sidebar.slider("Axial Force", 0, 300000, 50000, 1000, help="N")
delta_T     = st.sidebar.slider("Temperature Change ΔT", -200, 400, 100, 5, help="°C")

diameter = diameter_mm / 1000  # meters

# ========================= CALCULATIONS =========================
A = np.pi * (diameter / 2)**2
mech_stress   = force_N / A if A > 0 else 0
therm_stress  = E * alpha * delta_T
total_stress  = mech_stress + therm_stress
total_strain  = total_stress / E if E > 0 else 0
fos = allowable / abs(total_stress) if total_stress != 0 else float('inf')

# ========================= TABS =========================
tab1, tab2, tab3 = st.tabs(["Results", "Graphs (Custom Range)", "Report"])

# -------------------------- RESULTS TAB --------------------------
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Input Summary")
        st.write(f"**Diameter:** {diameter_mm:.1f} mm  →  Area = {A*1e6:.2f} mm²")
        st.write(f"**Force:** {force_N/1000:.1f} kN")
        st.write(f"**ΔT:** {delta_T:+.0f} °C")
        st.write(f"**Material:** {mat_name}")

    with col2:
        st.markdown("### Stress & Safety")
        st.metric("Mechanical Stress", f"{mech_stress/1e6:.2f} MPa")
        st.metric("Thermal Stress", f"{therm_stress/1e6:+.2f} MPa",
                  delta="Compressive" if delta_T < 0 else "Tensile")
        st.metric("**Total Stress**", f"{total_stress/1e6:+.2f} MPa")
        st.metric("Total Strain", f"{total_strain*1e6:.1f} µε")

        # FOS visual box
        if fos >= 2.0:
            st.markdown(f'<div class="stress-box safe">FOS = {fos:.2f} → VERY SAFE</div>', unsafe_allow_html=True)
        elif fos >= 1.2:
            st.markdown(f'<div class="stress-box warning">FOS = {fos:.2f} → ACCEPTABLE</div>', unsafe_allow_html=True)
        elif fos >= 1.0:
            st.markdown(f'<div class="stress-box warning">FOS = {fos:.2f} → MARGINAL</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="stress-box danger">FOS = {fos:.2f} → FAILURE RISK!</div>', unsafe_allow_html=True)

# -------------------------- GRAPHS TAB --------------------------
with tab2:
    st.markdown("### Choose a graph and set your own range")

    graph = st.selectbox("Select Graph", [
        "Mechanical Stress vs Diameter",
        "Factor of Safety vs Force",
        "Total Strain vs Young’s Modulus",
        "Thermal Stress vs Temperature Change"
    ])

    # 1. Stress vs Diameter
    if graph == "Mechanical Stress vs Diameter":
        c1, c2 = st.columns(2)
        d_min = c1.number_input("Min Diameter (mm)", 1.0, 100.0, 5.0)
        d_max = c1.number_input("Max Diameter (mm)", d_min+1, 200.0, 60.0)
        points = c2.slider("Number of points", 20, 300, 100)

        d_range = np.linspace(d_min/1000, d_max/1000, points)
        stress_range = force_N / (np.pi * (d_range/2)**2) / 1e6

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=d_range*1000, y=stress_range, mode='lines', name='Stress (MPa)'))
        fig.add_vline(x=diameter_mm, line_dash="dash", line_color="red", annotation_text="Current")
        fig.update_layout(title="Mechanical Stress vs Diameter", xaxis_title="Diameter (mm)", yaxis_title="Stress (MPa)")
        st.plotly_chart(fig, use_container_width=True)

    # 2. FOS vs Force
    elif graph == "Factor of Safety vs Force":
        c1, c2 = st.columns(2)
        f_min = c1.number_input("Min Force (kN)", 0, 200, 1)
        f_max = c1.number_input("Max Force (kN)", f_min+10, 1000, 300)
        points = c2.slider("Points", 20, 300, 100, key="fos_points")

        F_range = np.linspace(f_min*1000, f_max*1000, points)
        total_stress_range = F_range / A + therm_stress
        fos_range = allowable / np.abs(total_stress_range + 1e-9)  # avoid divide-by-zero

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=F_range/1000, y=fos_range, mode='lines', name='FOS'))
        fig.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Failure")
        fig.add_vline(x=force_N/1000, line_dash="dot", line_color="green")
        fig.update_layout(title="Factor of Safety vs Force", xaxis_title="Force (kN)", yaxis_title="FOS")
        st.plotly_chart(fig, use_container_width=True)

    # 3. Strain vs E
    elif graph == "Total Strain vs Young’s Modulus":
        c1, c2 = st.columns(2)
        e_min = c1.number_input("Min E (GPa)", 1, 200, 20)
        e_max = c1.number_input("Max E (GPa)", e_min+10, 500, 300)
        points = c2.slider("Points", 20, 300, 100, key="strain_points")

        E_range = np.linspace(e_min*1e9, e_max*1e9, points)
        strain_range = (mech_stress + E_range * alpha * delta_T) / E_range * 1e6

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=E_range/1e9, y=strain_range, mode='lines', name='Strain (µε)'))
        fig.add_vline(x=E/1e9, line_dash="dash", line_color="purple")
        fig.update_layout(title="Total Strain vs Young’s Modulus", xaxis_title="E (GPa)", yaxis_title="Strain (microstrain)")
        st.plotly_chart(fig, use_container_width=True)

    # 4. Thermal Stress vs ΔT
    elif graph == "Thermal Stress vs Temperature Change":
        c1, c2 = st.columns(2)
        t_min = c1.number_input("Min ΔT (°C)", -300, 200, -100)
        t_max = c1.number_input("Max ΔT (°C)", t_min+20, 600, 300)
        points = c2.slider("Points", 20, 300, 100, key="temp_points")

        dt_range = np.linspace(t_min, t_max, points)
        therm_range = E * alpha * dt_range / 1e6

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dt_range, y=therm_range, mode='lines', name='Thermal Stress (MPa)'))
        fig.add_vline(x=delta_T, line_dash="dash", line_color="orange")
        fig.add_hline(y=0, line_color="gray")
        fig.update_layout(title="Thermal Stress vs Temperature Change", xaxis_title="ΔT (°C)", yaxis_title="Stress (MPa)")
        st.plotly_chart(fig, use_container_width=True)

# -------------------------- REPORT TAB --------------------------
with tab3:
    st.markdown("### Analysis Report")
    status = "SAFE" if fos >= 1 else "UNSAFE"
    color = "green" if fos >= 1 else "red"

    report = f"""
# Rod Stress & Strain Analysis Report
Generated on: {datetime.now().strftime("%B %d, %Y at %H:%M")}

Material          : {mat_name}
Diameter          : {diameter_mm:.1f} mm
Applied Force     : {force_N/1000:.1f} kN
Temperature Change: {delta_T:+.0f} °C

Cross-section Area   : {A*1e6:.2f} mm²
Mechanical Stress    : {mech_stress/1e6:.2f} MPa
Thermal Stress       : {therm_stress/1e6:+.2f} MPa
Total Stress         : {total_stress/1e6:+.2f} MPa
Factor of Safety     : {fos:.2f} → {status}
"""

    st.markdown(report)
    st.download_button(
        "Download Report as .txt",
        report,
        file_name=f"Rod_Analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain"
    )

# ========================= FOOTER =========================
st.markdown("---")
st.caption("Made with ❤️ for Mechanical Engineers • 100% interactive • No hardcoded ranges")
