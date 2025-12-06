import streamlit as st
import math as m
import matplotlib.pyplot as plt
import numpy as np

# =================================== CONFIG & STYLING ===================================
st.set_page_config(
    page_title="Structural Mechanics Compute Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a professional, "Engineering Software" look (No Emojis)
st.markdown("""
    <style>
    .block-container {padding-top: 2rem;}
    h1 {font-family: 'Roboto', sans-serif; font-weight: 700; color: #1e3d59;}
    h2, h3 {font-family: 'Roboto', sans-serif; color: #1e3d59;}
    .stMetric {background-color: #f0f2f6; padding: 10px; border-radius: 5px; border-left: 5px solid #1e3d59;}
    .stSelectbox label, .stNumberInput label {font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# =================================== LOGIC & CONVERSION ENGINE ===================================

# Material Database (The "Unique" Feature)
MATERIALS = {
    "Custom": {"E": 200e9, "alpha": 12e-6, "yield": 250e6},
    "Structural Steel (A36)": {"E": 200e9, "alpha": 11.7e-6, "yield": 250e6},
    "Aluminum 6061-T6": {"E": 68.9e9, "alpha": 23.6e-6, "yield": 276e6},
    "Titanium (Ti-6Al-4V)": {"E": 113.8e9, "alpha": 8.6e-6, "yield": 880e6},
    "Copper": {"E": 110e9, "alpha": 17e-6, "yield": 70e6},
    "Brass": {"E": 105e9, "alpha": 19e-6, "yield": 200e6},
}

# Unit Multipliers (Converts TO SI Units)
UNIT_LENGTH = {"m": 1.0, "mm": 1e-3, "cm": 1e-2, "in": 0.0254, "ft": 0.3048}
UNIT_FORCE = {"N": 1.0, "kN": 1e3, "MN": 1e6, "lbf": 4.44822}
UNIT_PRESSURE = {"Pa": 1.0, "kPa": 1e3, "MPa": 1e6, "GPa": 1e9, "psi": 6894.76}
UNIT_TEMP = {"K": 1.0, "C": 1.0, "F": 0.5556} # Delta T conversion

def to_si(value, unit, conversion_dict):
    return value * conversion_dict[unit]

def from_si(value, unit, conversion_dict):
    return value / conversion_dict[unit]

# Physics Core (Unchanged logic, just wrapped)
def calc_area(diameter):
    return m.pi * (diameter / 2) ** 2

def calc_stress(force, area):
    return force / area if area > 0 else 0

def calc_thermal_stress(E, alpha, dT):
    return E * alpha * dT

# =================================== UI LAYOUT ===================================

st.title("STRUCTURAL MECHANICS COMPUTE ENGINE")
st.markdown("---")

# Sidebar for Mode Selection
st.sidebar.header("SYSTEM CONTROLS")
app_mode = st.sidebar.radio("Select Operation Mode", ["Calculator Dashboard", "Parametric Plotter"])

st.sidebar.markdown("---")
st.sidebar.markdown("**Material Presets**")
selected_material = st.sidebar.selectbox("Load Material Properties", list(MATERIALS.keys()))
mat_props = MATERIALS[selected_material]

# =================================== DASHBOARD MODE ===================================
if app_mode == "Calculator Dashboard":
    
    col_input, col_result = st.columns([1, 1])

    with col_input:
        st.subheader("Input Parameters")
        
        # 1. Geometry
        with st.container():
            st.markdown("#### Geometry")
            c1, c2 = st.columns([2, 1])
            d_val = c1.number_input("Diameter", value=20.0, step=1.0)
            d_unit = c2.selectbox("Unit", list(UNIT_LENGTH.keys()), index=1, key="u_d")
            
            diameter_si = to_si(d_val, d_unit, UNIT_LENGTH)
            area_si = calc_area(diameter_si)
            st.caption(f"Calculated Area: {area_si:.4e} m²")

        # 2. Loading
        with st.container():
            st.markdown("#### Mechanical Load")
            c1, c2 = st.columns([2, 1])
            f_val = c1.number_input("Applied Force", value=50.0, step=1.0)
            f_unit = c2.selectbox("Unit", list(UNIT_FORCE.keys()), index=1, key="u_f")
            
            force_si = to_si(f_val, f_unit, UNIT_FORCE)

        # 3. Thermal
        with st.container():
            st.markdown("#### Thermal Conditions")
            c1, c2 = st.columns([2, 1])
            dt_val = c1.number_input("Change in Temp (ΔT)", value=0.0, step=5.0)
            dt_unit = c2.selectbox("Unit", list(UNIT_TEMP.keys()), index=1, key="u_t") # Default C
            
            dt_si = to_si(dt_val, dt_unit, UNIT_TEMP)

        # 4. Material (Auto-filled but editable)
        with st.container():
            st.markdown("#### Material Properties")
            c1, c2 = st.columns([2, 1])
            E_display = from_si(mat_props["E"], "GPa", UNIT_PRESSURE)
            E_val = c1.number_input("Young's Modulus", value=E_display, format="%.2f")
            c2.text("\n\nGPa") # Fixed unit for simplicity in input, calculated in SI
            E_si = to_si(E_val, "GPa", UNIT_PRESSURE)

            c3, c4 = st.columns([2, 1])
            alpha_display = mat_props["alpha"] * 1e6
            alpha_val = c3.number_input("Thermal Expansion (α)", value=alpha_display, format="%.2f")
            c4.text("\n\nµm/m·K")
            alpha_si = alpha_val * 1e-6

            c5, c6 = st.columns([2, 1])
            yield_display = from_si(mat_props["yield"], "MPa", UNIT_PRESSURE)
            yield_val = c5.number_input("Allowable Stress (Yield)", value=yield_display, format="%.2f")
            c6.text("\n\nMPa")
            yield_si = to_si(yield_val, "MPa", UNIT_PRESSURE)

    with col_result:
        st.subheader("Computed Results")
        
        # Calculations
        mech_stress = calc_stress(force_si, area_si)
        therm_stress = calc_thermal_stress(E_si, alpha_si, dt_si)
        total_stress_val = mech_stress + therm_stress
        
        strain_val = total_stress_val / E_si if E_si > 0 else 0
        fos_val = yield_si / total_stress_val if total_stress_val > 0 else float('inf')

        # Formatting Output
        display_unit = st.radio("Display Results In:", ["Pa", "MPa", "psi", "kPa"], horizontal=True, index=1)
        
        s_mech_disp = from_si(mech_stress, display_unit, UNIT_PRESSURE)
        s_therm_disp = from_si(therm_stress, display_unit, UNIT_PRESSURE)
        s_total_disp = from_si(total_stress_val, display_unit, UNIT_PRESSURE)

        # Metrics
        m1, m2 = st.columns(2)
        m1.metric("Mechanical Stress", f"{s_mech_disp:.2f} {display_unit}")
        m2.metric("Thermal Stress", f"{s_therm_disp:.2f} {display_unit}")
        
        st.metric("TOTAL STRESS", f"{s_total_disp:.2f} {display_unit}", 
                  delta="Tensile" if total_stress_val > 0 else "Compressive")

        m3, m4 = st.columns(2)
        m3.metric("Total Strain (ε)", f"{strain_val:.6e}")
        m4.metric("Factor of Safety (FOS)", f"{fos_val:.2f}")

        # Visual FOS Gauge
        st.markdown("#### Safety Analysis")
        if fos_val < 1.0:
            st.error(f"CRITICAL FAILURE PREDICTED (FOS < 1.0)")
            bar_color = "red"
            progress = 1.0
        elif fos_val < 1.5:
            st.warning(f"MARGINAL DESIGN (FOS = {fos_val:.2f})")
            bar_color = "orange"
            progress = 0.7
        else:
            st.success(f"DESIGN SAFE (FOS = {fos_val:.2f})")
            bar_color = "green"
            progress = min(1.0, 1.0/fos_val + 0.2) # Visual representation
        
        # HTML Bar for visual impact without emojis
        st.markdown(f"""
            <div style="width:100%; background-color:#ddd; height:20px; border-radius:10px;">
                <div style="width:{min(fos_val*20, 100)}%; background-color:{'#28a745' if fos_val>=1.5 else '#dc3545'}; height:20px; border-radius:10px; transition: width 0.5s;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:0.8rem;">
                <span>0</span><span>1.0 (Limit)</span><span>5.0+</span>
            </div>
        """, unsafe_allow_html=True)

# =================================== PLOTTING MODE ===================================
elif app_mode == "Parametric Plotter":
    st.subheader("Parametric Analysis Plotter")
    st.info("Visualize how one variable affects the total stress, strain, or safety factor.")

    # 1. Configuration
    col_setup, col_plot = st.columns([1, 2])
    
    with col_setup:
        st.markdown("### X-Axis Configuration")
        x_axis_choice = st.selectbox("Select Independent Variable (X-Axis)", 
                                     ["Diameter", "Force", "Delta T", "Young's Modulus"])
        
        # Dynamic Sliders based on choice
        start, end = 0.0, 0.0
        
        if x_axis_choice == "Diameter":
            start = st.number_input("Start Diameter (mm)", value=5.0)
            end = st.number_input("End Diameter (mm)", value=50.0)
            x_label = "Diameter (m)"
            
        elif x_axis_choice == "Force":
            start = st.number_input("Start Force (kN)", value=0.0)
            end = st.number_input("End Force (kN)", value=100.0)
            x_label = "Force (N)"
            
        elif x_axis_choice == "Delta T":
            start = st.number_input("Start ΔT (C)", value=0.0)
            end = st.number_input("End ΔT (C)", value=200.0)
            x_label = "Temperature Change (K)"
            
        elif x_axis_choice == "Young's Modulus":
            start = st.number_input("Start E (GPa)", value=50.0)
            end = st.number_input("End E (GPa)", value=250.0)
            x_label = "Young's Modulus (Pa)"

        st.markdown("### Fixed Parameters")
        # Defaults
        def_force = 10000.0
        def_dia = 20.0
        def_dt = 0.0
        
        if x_axis_choice != "Force":
            def_force = st.number_input("Fixed Force (N)", value=10000.0)
        if x_axis_choice != "Diameter":
            def_dia = st.number_input("Fixed Diameter (mm)", value=20.0)
        if x_axis_choice != "Delta T":
            def_dt = st.number_input("Fixed ΔT (C)", value=0.0)

        # Y-Axis Choice
        y_choice = st.selectbox("Select Dependent Variable (Y-Axis)", 
                                ["Total Stress", "Strain", "Factor of Safety"])

    # 2. Computation Engine for Plot
    points = 100
    x_vals_plot = np.linspace(start, end, points)
    y_vals_plot = []

    # Get Material Constants from sidebar
    E_curr = mat_props["E"]
    alpha_curr = mat_props["alpha"]
    yield_curr = mat_props["yield"]

    for val in x_vals_plot:
        # Reset iteration variables to defaults
        d_i = def_dia * 1e-3
        f_i = def_force
        dt_i = def_dt
        E_i = E_curr

        # Update based on X-axis choice
        if x_axis_choice == "Diameter": d_i = val * 1e-3
        elif x_axis_choice == "Force": f_i = val * 1e3
        elif x_axis_choice == "Delta T": dt_i = val
        elif x_axis_choice == "Young's Modulus": E_i = val * 1e9
        
        # Physics
        A_i = calc_area(d_i)
        mech = calc_stress(f_i, A_i)
        therm = calc_thermal_stress(E_i, alpha_curr, dt_i)
        tot = mech + therm
        
        if y_choice == "Total Stress":
            y_vals_plot.append(tot / 1e6) # Convert to MPa
            y_label = "Stress (MPa)"
        elif y_choice == "Strain":
            y_vals_plot.append(tot / E_i if E_i > 0 else 0)
            y_label = "Strain (unitless)"
        elif y_choice == "Factor of Safety":
            y_vals_plot.append(yield_curr / tot if tot > 0 else 100) # Cap infinity
            y_label = "Factor of Safety"

    # 3. Plotting
    with col_plot:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(x_vals_plot, y_vals_plot, color="#1e3d59", linewidth=2.5)
        
        ax.set_title(f"{y_choice} vs {x_axis_choice}", fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel(f"{x_axis_choice}", fontsize=10)
        ax.set_ylabel(y_label, fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Special line for FOS
        if y_choice == "Factor of Safety":
            ax.axhline(1.0, color='#dc3545', linestyle='--', linewidth=2, label="Failure Limit")
            ax.legend()
            ax.set_ylim(0, max(5, max(y_vals_plot)))

        st.pyplot(fig)
