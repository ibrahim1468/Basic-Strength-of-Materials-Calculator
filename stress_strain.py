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
    .header {color: #1e3799; font-size: 28px; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font"> Rod Stress & Strain Analyzer</p>', unsafe_allow_html=True)
st.markdown("### Analyze mechanical + Visualize + Learn Instantly", unsafe_allow_html=True)

# ========================= SIDEBAR INPUTS =========================
st.sidebar.header("Material Library")

materials = {
    "Custom": {"E": None, "alpha": None, "allowable": None},
    "Mild Steel": {"E": 200e9, "Pa", "alpha": 12e-6, "allowable": 250e6},
    "Stainless Steel": {"E": 193e9, "alpha": 17.3e-6, "allowable": 215e6},
    "Aluminum 6061-T6": {"E": 69e9, "alpha": 23.6e-6, "allowable": 276e6},
    "Titanium Ti-6Al-4V": {"E": 114e9, "alpha": 8.6e-6, "allowable": 880e6},
    "Brass": {"E": 100e9, "alpha": 18.7e-6, "allowable": 150e6},
}

mat_name = st.sidebar.selectbox("Choose Material Preset", options=list(materials.keys()))
mat = materials[mat_name]

E = st.sidebar.number_input("Young's Modulus E", value=mat["E"] or 200e9, step=1e9, format="%.3e", help="Pa")
alpha = st.sidebar.number_input("Thermal Expansion α", value=mat["alpha"] or 12e-6, format="%.3e", help="1/K")
allowable = st.sidebar.number_input("Allowable Stress", value=mat["allowable"] or 250e6, step=1e6, format="%.3e", help="Pa")

st.sidebar.markdown("---")
st.sidebar.subheader("Geometry & Load")
diameter_mm = st.sidebar.slider("Diameter", 1.0, 100.0, 20.0, 0.5, help="mm")
force_N = st.sidebar.slider("Applied Axial Force", 0, 200000, 50000, 1000, help="Newtons")
delta_T = st.sidebar.slider("Temperature Change ΔT", -200, 400, 100, 5, help="°C (positive = heating)")

diameter = diameter_mm / 1000  # convert to meters

# ========================= CALCULATIONS =========================
A = np.pi * (diameter / 2)**2
mech_stress = force_N / A if A > 0 else 0
therm_stress = E * alpha * delta_T
total_stress = mech_stress + therm_stress
total_strain = total_stress / E if E > 0 else 0
fos = allowable / abs(total_stress) if total_stress != 0 else float('inf')

# ========================= TABS =========================
tab1, tab2, tab3 = st.tabs(["Results Summary", "Interactive Graphs", "Download Report"])

with tab1:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Input Summary")
        st.write(f"**Diameter:** {diameter_mm:.1f} mm → Area = {A*1e6:.2f} mm²")
        st.write(f"**Force:** {force_N/1000:.1f} kN")
        st.write(f"**ΔT:** {delta_T:+.0f} °C")
        st.write(f"**Material:** {mat_name}")

    with c2:
        st.markdown("### Stress & Safety")
        st.metric("Mechanical Stress", f"{mech_stress/1e6:.2f} MPa")
        st.metric("Thermal Stress", f"{therm_stress/1e6:+.2f} MPa",
                  delta="Compressive" if delta_T < 0 else "Tensile")
        st.metric("Total Stress", f"{total_stress/1e6:+.2f} MPa")
        st.metric("Total Strain", f"{total_strain*1e6:.1f} µε")

        # FOS Visual
        if fos >= 2.0:
            st.markdown(f'<div class="stress-box safe">Factor of Safety = {fos:.2f} → VERY SAFE</div>', unsafe_allow_html=True)
        elif fos >= 1.2:
            st.markdown(f'<div class="stress-box warning">Factor of Safety = {fos:.2f} → ACCEPTABLE</div>', unsafe_allow_html=True)
        elif fos >= 1.0:
            st.markdown(f'<div class="stress-box warning">Factor of Safety = {fos:.2f} → MARGINAL (Review Design)</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="stress-box danger">Factor of Safety = {fos:.2f} → FAILURE RISK!</div>', unsafe_allow_html=True)

# ========================= GRAPHS TAB (USER-CONTROLLED RANGES) =========================
with tab2:
    st.markdown("### Interactive Graphs – You Control the Range!")

    graph = st.selectbox("Choose Graph", [
        "Mechanical Stress vs Diameter",
        "Factor of Safety vs Force",
        "Total Strain vs Young's Modulus",
        "Thermal Stress vs Temperature Change"
    ])

    if graph == "Mechanical Stress vs Diameter":
        col1, col2 = st.columns(2)
        with col1:
            d_min = st.number_input("Min Diameter (mm)", 1.0, 50.0, 5.0)
            d_max = st.number_input("Max Diameter (mm)", 10.0, 100.0, 50.0)
        with col2:
            steps = st.slider("Number of Points", 20, 200, 100)

        d_range = np.linspace(d_min/1000, d_max/1000, steps)
        stress_range = force_N / (np.pi * (d_range/2)**2) / 1e6

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=d_range*1000, y=stress_range, mode='lines', name='Stress'))
        fig.add_vline(x=diameter_mm, line=dict(color="red", dash="dash"), annotation_text="Current")
        fig.update_layout(title="Mechanical Stress vs Diameter", xaxis_title="Diameter (mm)", yaxis_title="Stress (MPa)", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    elif graph == "Factor of Safety vs Force":
        col1, col2 = st.columns(2)
        with col1:
            f_min = st.number_input("Min Force (kN)", 0, 100, 1)
            f_max = st.number_input("Max Force (kN)", 50, 500, 200)
        with col2:
            steps = st.slider("Points", 20, 200, 100, key="fos")

        F_range = np.linspace(f_min*1000, f_max*1000, steps)
        total_stress_range = (F_range / A) + therm_stress
        fos_range = allowable / np.abs(total_stress_range)
        fos_range[total_stress_range == 0] = 100  # avoid divide by zero

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=F_range/1000, y=fos_range, mode='lines', name='FOS'))
        fig.add_hline(y=1.0, line=dict(color="red", dash="dash"), annotation_text="Failure")
        fig.add_vline(x=force_N/1000, line=dict(color="green", dash="dot"))
        fig.update_layout(title="Factor of Safety vs Applied Force", xaxis_title="Force (kN)", yaxis_title="FOS")
        st.plotly_chart(fig, use_container_width=True)

    elif graph == "Total Strain vs Young's Modulus":
        col1, col2 = st.columns(2)
        with col1:
            e_min = st.number_input("Min E (GPa)", 1, 100, 20)
            e_max = st.number_input("Max E (GPa)", 50, 400, 300)
        with col2:
            steps = st.slider("Points", 20, 200, 100, key="strain")

        E_range = np.linspace(e_min*1e9, e_max*1e9, steps)
        therm_range = E_range * alpha * delta_T
        total_stress_E = mech_stress + therm_range
        strain_range = total_stress_E / E_range

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=E_range/1e9, y=strain_range*1e6, mode='lines', name='Strain'))
        fig.add_vline(x=E/1e9, line=dict(color="purple", dash="dash"))
        fig.update_layout(title="Total Strain vs Young's Modulus", xaxis_title="Young’s Modulus (GPa)", yaxis_title="Strain (microstrain)")
        st.plotly_chart(fig, use_container_width=True)

    elif graph == "Thermal Stress vs Temperature Change":
        col1, col2 = st.columns(2)
        with col1:
            t_min = st.number_input("Min ΔT (°C)", -300, 100, -100)
            t_max = st.number_input("Max ΔT (°C)", 0, 500, 300)
        with col2:
            steps = st.slider("Points", 20, 200, 100, key="temp")

        dt_range = np.linspace(t_min, t_max, steps)
        therm_stress_range = E * alpha * dt_range / 1e6

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dt_range, y=therm_stress_range, mode='lines', name='Thermal Stress'))
        fig.add_vline(x=delta_T, line=dict(color="orange", dash="dash"))
        fig.add_hline(y=0, line=dict(color="gray"))
        fig.update_layout(title="Thermal Stress vs Temperature Change", xaxis_title="ΔT (°C)", yaxis_title="Thermal Stress (MPa)")
        st.plotly_chart(fig, use_container_width=True)

# ========================= REPORT TAB =========================
with tab3:
    st.markdown("### Analysis Report")

    status = "SAFE" if fos >= 1 else "UNSAFE"
    color = "green" if fos >= 1 else "red"

    report_text = f"""
    # Rod Stress & Strain Analysis Report
    **Date:** {datetime.now().strftime("%B %d, %Y %H:%M")}
    **Material:** {mat_name}
    **Diameter:** {diameter_mm:.1f} mm
    **Applied Force:** {force_N/1000:.1f} kN
    **Temperature Change:** {delta_T:+.0f} °C

    ### Results
    - Cross-sectional Area: {A*1e6:.2f} mm²
    - Mechanical Stress: {mech_stress/1e6:.2f} MPa
    - Thermal Stress: {therm_stress/1e6:+.2f} MPa
    - **Total Stress: {total_stress/1e6:+.2f} MPa**
    - **Factor of Safety: {fos:.2f} → <span style="color:{color};font-weight:bold">{status}</span>**

    Generated with Rod Stress & Strain Analyzer
    """

    st.markdown(report_text, unsafe_allow_html=True)
    st.download_button(
        label="Download Report as Text File",
        data=report_text,
        file_name=f"rod_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain"
    )

# ========================= FOOTER =========================
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>Made with ❤️ for Mechanical Engineers | "
    "Fully interactive • No random data • Learn by exploring</p>",
    unsafe_allow_html=True
)