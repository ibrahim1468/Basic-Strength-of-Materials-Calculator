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

# Custom CSS for a professional, "Engineering Software" look
st.markdown("""
    <style>
    .block-container {padding-top: 2rem;}
    h1 {font-family: 'Roboto', sans-serif; font-weight: 700; color: #1e3d59;}
    h2, h3 {font-family: 'Roboto', sans-serif; color: #1e3d59;}
    
    /* Force text color in metrics to be dark since background is light */
    [data-testid="stMetricValue"] { color: #1e3d59 !important; }
    [data-testid="stMetricLabel"] { color: #1e3d59 !important; }
    
    .stMetric {
        background-color: #f0f2f6; 
        padding: 10px; 
        border-radius: 5px; 
        border-left: 5px solid #1e3d59;
    }
    
    .stSelectbox label, .stNumberInput label {font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# =================================== ENGINEERING DATA ENGINE ===================================

# COMPREHENSIVE MATERIAL DATABASE (SI UNITS: Pa, 1/K, Pa)
# Sources: MatWeb, ASTM Standards, Engineering Toolbox
MATERIALS = {
    "--- User Defined ---": {"E": 0.0, "alpha": 0.0, "yield": 0.0},
    
    # METALS - FERROUS
    "Steel, Structural (ASTM A36)":    {"E": 200e9,  "alpha": 11.7e-6, "yield": 250e6},
    "Steel, Stainless (304)":          {"E": 193e9,  "alpha": 17.2e-6, "yield": 205e6},
    "Steel, High Strength (ASTM A514)":{"E": 205e9,  "alpha": 11.7e-6, "yield": 690e6},
    "Cast Iron, Gray (ASTM 20)":       {"E": 100e9,  "alpha": 11.0e-6, "yield": 150e6}, # Ult Strength
    "Cast Iron, Ductile (60-40-18)":   {"E": 169e9,  "alpha": 11.0e-6, "yield": 276e6},

    # METALS - NON-FERROUS
    "Aluminum 6061-T6":               {"E": 68.9e9, "alpha": 23.6e-6, "yield": 276e6},
    "Aluminum 2024-T4":               {"E": 73.1e9, "alpha": 23.2e-6, "yield": 324e6},
    "Aluminum 7075-T6":               {"E": 71.7e9, "alpha": 23.6e-6, "yield": 503e6},
    "Titanium Alloy (Ti-6Al-4V)":     {"E": 113.8e9,"alpha": 8.6e-6,  "yield": 880e6},
    "Copper, Pure (Annealed)":        {"E": 110e9,  "alpha": 16.5e-6, "yield": 69e6},
    "Brass, Yellow (C26800)":         {"E": 105e9,  "alpha": 20.3e-6, "yield": 250e6},
    "Bronze, Phosphor (C51000)":      {"E": 110e9,  "alpha": 17.8e-6, "yield": 300e6},
    "Magnesium Alloy (AZ31B)":        {"E": 45e9,   "alpha": 26.0e-6, "yield": 220e6},

    # PLASTICS / POLYMERS
    "Plastic - ABS":                  {"E": 2.3e9,  "alpha": 74e-6,   "yield": 40e6},
    "Plastic - Nylon 6/6":            {"E": 2.8e9,  "alpha": 80e-6,   "yield": 80e6},
    "Plastic - Polycarbonate":        {"E": 2.4e9,  "alpha": 67e-6,   "yield": 65e6},
    "Plastic - HDPE":                 {"E": 0.8e9,  "alpha": 120e-6,  "yield": 25e6},
    "Plastic - PVC (Rigid)":          {"E": 3.0e9,  "alpha": 50e-6,   "yield": 50e6},
    "Plastic - Acrylic (PMMA)":       {"E": 3.0e9,  "alpha": 70e-6,   "yield": 65e6},

    # COMPOSITES (Approximate Longitudinal Values)
    "Composite - Carbon Fiber (UD)":  {"E": 135e9,  "alpha": 0.5e-6,  "yield": 1500e6},
    "Composite - Glass Fiber (UD)":   {"E": 40e9,   "alpha": 7.0e-6,  "yield": 1000e6},

    # CERAMICS & OTHERS
    "Glass, Soda-Lime":               {"E": 70e9,   "alpha": 9.0e-6,  "yield": 50e6}, # Fracture Strength
    "Concrete, High Strength":        {"E": 30e9,   "alpha": 10e-6,   "yield": 40e6}, # Compressive
    "Wood - Oak (White)":             {"E": 12e9,   "alpha": 5e-6,    "yield": 50e6}, # Parallel to grain
    "Wood - Pine (Southern)":         {"E": 11e9,   "alpha": 5e-6,    "yield": 40e6}, # Parallel to grain
}

# Unit Multipliers (Converts TO SI Units)
UNIT_LENGTH = {"m": 1.0, "mm": 1e-3, "cm": 1e-2, "in": 0.0254, "ft": 0.3048}
UNIT_FORCE = {"N": 1.0, "kN": 1e3, "MN": 1e6, "lbf": 4.44822, "kip": 4448.22}
UNIT_PRESSURE = {"Pa": 1.0, "kPa": 1e3, "MPa": 1e6, "GPa": 1e9, "psi": 6894.76, "ksi": 6894760.0}
UNIT_TEMP = {"K": 1.0, "C": 1.0, "F": 0.5556} # Delta T conversion

def to_si(value, unit, conversion_dict):
    return value * conversion_dict[unit]

def from_si(value, unit, conversion_dict):
    return value / conversion_dict[unit]

# Physics Core
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
st.sidebar.markdown("**Material Library**")
selected_material_name = st.sidebar.selectbox("Select Material", list(MATERIALS.keys()), index=1)
mat_props = MATERIALS[selected_material_name]

# Helper to check if custom mode
is_custom = selected_material_name == "--- User Defined ---"

if is_custom:
    st.sidebar.info("📝 You are in Custom Mode. Please enter material properties manually in the main window.")
else:
    st.sidebar.success(f"✅ Loaded: {selected_material_name}")
    with st.sidebar.expander("View Properties"):
        st.write(f"E: {mat_props['E']/1e9:.1f} GPa")
        st.write(f"α: {mat_props['alpha']*1e6:.1f} µε/K")
        st.write(f"Yield: {mat_props['yield']/1e6:.1f} MPa")

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
            dt_unit = c2.selectbox("Unit", list(UNIT_TEMP.keys()), index=1, key="u_t")
            
            dt_si = to_si(dt_val, dt_unit, UNIT_TEMP)

        # 4. Material (Auto-filled but editable)
        with st.container():
            st.markdown("#### Material Properties")
            if is_custom:
                st.caption("Enter your custom material properties below:")
            
            c1, c2 = st.columns([2, 1])
            # Default values: Use DB value if not custom, else default to 200 (Steel)
            def_E = from_si(mat_props["E"], "GPa", UNIT_PRESSURE) if not is_custom else 200.0
            E_val = c1.number_input("Young's Modulus", value=def_E, format="%.2f", key="E_in")
            c2.text("\n\nGPa") 
            E_si = to_si(E_val, "GPa", UNIT_PRESSURE)

            c3, c4 = st.columns([2, 1])
            def_alpha = mat_props["alpha"] * 1e6 if not is_custom else 11.7
            alpha_val = c3.number_input("Thermal Expansion (α)", value=def_alpha, format="%.2f", key="a_in")
            c4.text("\n\nµm/m·K")
            alpha_si = alpha_val * 1e-6

            c5, c6 = st.columns([2, 1])
            def_yield = from_si(mat_props["yield"], "MPa", UNIT_PRESSURE) if not is_custom else 250.0
            yield_val = c5.number_input("Limit Stress (Yield/UTS)", value=def_yield, format="%.2f", key="y_in")
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
        display_unit = st.radio("Display Results In:", ["Pa", "MPa", "psi", "ksi", "kPa"], horizontal=True, index=1)
        
        s_mech_disp = from_si(mech_stress, display_unit, UNIT_PRESSURE)
        s_therm_disp = from_si(therm_stress, display_unit, UNIT_PRESSURE)
        s_total_disp = from_si(total_stress_val, display_unit, UNIT_PRESSURE)

        # Metrics
        m1, m2 = st.columns(2)
        m1.metric("Mechanical Stress", f"{s_mech_disp:.2f} {display_unit}")
        m2.metric("Thermal Stress", f"{s_therm_disp:.2f} {display_unit}")
        
        # --- CUSTOM HTML FOR TOTAL STRESS COLORING ---
        if fos_val >= 1.0:
            res_color = "#28a745" # Green
            status_text = "SAFE"
        else:
            res_color = "#dc3545" # Red
            status_text = "UNSAFE"

        st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 5px; border-left: 8px solid {res_color}; margin-top: 10px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <label style="font-size: 16px; font-weight: bold; color: #1e3d59; display: block; margin-bottom: 5px;">TOTAL STRESS</label>
                <div style="font-size: 32px; font-weight: bold; color: {res_color}; font-family: sans-serif;">
                    {s_total_disp:.2f} {display_unit}
                </div>
                <div style="font-size: 14px; color: #555; margin-top: 5px;">
                    Type: <b>{'Tensile' if total_stress_val > 0 else 'Compressive'}</b> | Design Status: <b style="color:{res_color}">{status_text}</b>
                </div>
            </div>
        """, unsafe_allow_html=True)
        # ---------------------------------------------

        m3, m4 = st.columns(2)
        m3.metric("Total Strain (ε)", f"{strain_val:.6e}")
        m4.metric("Factor of Safety (FOS)", f"{fos_val:.2f}")

        # Visual FOS Gauge
        st.markdown("#### Safety Analysis")
        bar_color = "#28a745" if fos_val >= 1.0 else "#dc3545"
        
        # HTML Bar
        st.markdown(f"""
            <div style="width:100%; background-color:#ddd; height:20px; border-radius:10px;">
                <div style="width:{min(fos_val*20, 100)}%; background-color:{bar_color}; height:20px; border-radius:10px; transition: width 0.5s;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:0.8rem; color: #555;">
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
        
        # Dynamic Sliders
        start, end = 0.0, 0.0
        
        if x_axis_choice == "Diameter":
            start = st.number_input("Start Diameter (mm)", value=5.0)
            end = st.number_input("End Diameter (mm)", value=50.0)
            
        elif x_axis_choice == "Force":
            start = st.number_input("Start Force (kN)", value=0.0)
            end = st.number_input("End Force (kN)", value=100.0)
            
        elif x_axis_choice == "Delta T":
            start = st.number_input("Start ΔT (C)", value=0.0)
            end = st.number_input("End ΔT (C)", value=200.0)
            
        elif x_axis_choice == "Young's Modulus":
            start = st.number_input("Start E (GPa)", value=50.0)
            end = st.number_input("End E (GPa)", value=250.0)

        st.markdown("### Fixed Parameters")
        def_force = 10000.0
        def_dia = 20.0
        def_dt = 0.0
        
        if x_axis_choice != "Force":
            def_force = st.number_input("Fixed Force (N)", value=10000.0)
        if x_axis_choice != "Diameter":
            def_dia = st.number_input("Fixed Diameter (mm)", value=20.0)
        if x_axis_choice != "Delta T":
            def_dt = st.number_input("Fixed ΔT (C)", value=0.0)

        y_choice = st.selectbox("Select Dependent Variable (Y-Axis)", 
                                ["Total Stress", "Strain", "Factor of Safety"])

    # 2. Computation Engine for Plot
    points = 100
    x_vals_plot = np.linspace(start, end, points)
    y_vals_plot = []

    # Use material properties from selection (or inputs if custom not implemented in plot yet)
    # For simplicity in Plotter, we pull from the dictionary constants for now
    E_curr = mat_props["E"] if mat_props["E"] > 0 else 200e9
    alpha_curr = mat_props["alpha"] if mat_props["alpha"] > 0 else 11.7e-6
    yield_curr = mat_props["yield"] if mat_props["yield"] > 0 else 250e6

    for val in x_vals_plot:
        d_i = def_dia * 1e-3
        f_i = def_force
        dt_i = def_dt
        E_i = E_curr

        if x_axis_choice == "Diameter": d_i = val * 1e-3
        elif x_axis_choice == "Force": f_i = val * 1e3
        elif x_axis_choice == "Delta T": dt_i = val
        elif x_axis_choice == "Young's Modulus": E_i = val * 1e9
        
        A_i = calc_area(d_i)
        mech = calc_stress(f_i, A_i)
        therm = calc_thermal_stress(E_i, alpha_curr, dt_i)
        tot = mech + therm
        
        if y_choice == "Total Stress":
            y_vals_plot.append(tot / 1e6) 
            y_label = "Stress (MPa)"
        elif y_choice == "Strain":
            y_vals_plot.append(tot / E_i if E_i > 0 else 0)
            y_label = "Strain (unitless)"
        elif y_choice == "Factor of Safety":
            y_vals_plot.append(yield_curr / tot if tot > 0 else 100)
            y_label = "Factor of Safety"

    # 3. Plotting
    with col_plot:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(x_vals_plot, y_vals_plot, color="#1e3d59", linewidth=2.5)
        
        ax.set_title(f"{y_choice} vs {x_axis_choice}", fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel(f"{x_axis_choice}", fontsize=10)
        ax.set_ylabel(y_label, fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.6)
        
        if y_choice == "Factor of Safety":
            ax.axhline(1.0, color='#dc3545', linestyle='--', linewidth=2, label="Failure Limit")
            ax.legend()
            ax.set_ylim(0, max(5, max(y_vals_plot)))

        st.pyplot(fig)
