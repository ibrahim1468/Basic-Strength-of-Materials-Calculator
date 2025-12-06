import streamlit as st
import math

# --- PAGE CONFIG ---
st.set_page_config(page_title="MechToolbox", page_icon="⚙️")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; }
    .stAlert { margin-top: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def area(dia_mm):
    # Convert mm to m for calculation
    return math.pi * ((dia_mm/1000) / 2) ** 2

# --- SIDEBAR ---
st.sidebar.title("⚙️ Mechanics Toolbox")
mode = st.sidebar.radio("Select Module:", 
    ["Stress Calculator", "Strain Calculator", "Factor of Safety (FOS)"])

st.sidebar.markdown("---")
st.sidebar.info("v2.0 - Interactive Engineering Suite")

# --- MAIN CONTENT ---

if mode == "Stress Calculator":
    st.title("🔩 Stress Analysis")
    st.markdown("Calculate normal stress ($\sigma$) based on applied force and geometry.")

    col1, col2 = st.columns(2)
    with col1:
        force = st.number_input("Applied Force (N)", value=1000.0, step=100.0)
    with col2:
        dia = st.number_input("Diameter (mm)", value=10.0, step=1.0)

    if dia > 0:
        A = area(dia)
        stress_pa = force / A
        stress_mpa = stress_pa / 1e6

        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Area", f"{A:.4e} m²")
        c2.metric("Stress", f"{stress_mpa:.2f} MPa")
        
        # Visual representation
        st.progress(min(stress_mpa/500, 1.0)) # Assuming max 500 for visual bar
        st.caption("Visual Stress indicator (normalized to 500 MPa)")
    else:
        st.error("Diameter must be greater than 0.")

elif mode == "Strain Calculator":
    st.title("📏 Strain Calculator")
    
    tab1, tab2 = st.tabs(["By Deformation", "By Stress (Hooke's Law)"])

    with tab1:
        st.subheader("Geometric Strain ($\epsilon = \Delta L / L_0$)")
        l0 = st.number_input("Original Length (mm)", value=100.0)
        ln = st.number_input("New Length (mm)", value=100.5)
        
        if l0 > 0:
            strain = (ln - l0) / l0
            st.success(f"Strain: **{strain:.6f}** (unitless)")
            st.info(f"Elongation: {strain*100:.3f}%")

    with tab2:
        st.subheader("Material Strain ($\epsilon = \sigma / E$)")
        f_in = st.number_input("Force (N)", value=5000.0)
        d_in = st.number_input("Diameter (mm)", value=12.0, key="d_strain")
        E_in = st.number_input("Young's Modulus (GPa)", value=200.0) # Steel default

        if d_in > 0 and E_in > 0:
            s_pa = f_in / area(d_in)
            E_pa = E_in * 1e9
            eps = s_pa / E_pa
            
            st.metric("Resulting Stress", f"{s_pa/1e6:.2f} MPa")
            st.metric("Resulting Strain", f"{eps:.6e}")

elif mode == "Factor of Safety (FOS)":
    st.title("🛡️ Safety Check")
    st.markdown("Compare actual stress against material limits.")

    with st.expander("Material Properties", expanded=True):
        limit_mpa = st.number_input("Yield Strength (MPa)", value=250.0, help="The stress at which the material fails.")
    
    with st.expander("Load Conditions", expanded=True):
        col1, col2 = st.columns(2)
        load_n = col1.number_input("Load (N)", value=15000.0)
        dia_mm = col2.number_input("Diameter (mm)", value=10.0)

    if dia_mm > 0:
        actual_stress_pa = load_n / area(dia_mm)
        actual_stress_mpa = actual_stress_pa / 1e6
        
        fos = limit_mpa / actual_stress_mpa

        st.divider()
        st.write(f"Actual Stress: **{actual_stress_mpa:.2f} MPa**")
        
        st.markdown(f"### Factor of Safety: {fos:.2f}")

        if fos >= 1.0:
            st.success("✅ DESIGN IS SAFE")
            st.balloons()
        else:
            st.error("❌ DESIGN FAILURE DETECTED")
            st.warning("The applied stress exceeds the material strength.")