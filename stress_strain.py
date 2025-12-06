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
    
    /* Force text color in metrics to be dark */
    [data-testid="stMetricValue"] { color: #1e3d59 !important; }
    [data-testid="stMetricLabel"] { color: #1e3d59 !important; }
    
    .stMetric {
        background-color: #f0f2f6; 
        padding: 10px; 
        border-radius: 5px; 
        border-left: 5px solid #1e3d59;
    }
    
    .stSelectbox label, .stNumberInput label {font-weight: bold;}
    
    /* Warning Box Style */
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ffeeba;
        margin-bottom: 10px;
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

# =================================== ENGINEERING DATA ENGINE ===================================

MATERIALS = {
    "--- User Defined ---": {"E": 0.0, "alpha": 0.0, "yield": 0.0},
    "Steel, Structural (ASTM A36)":    {"E": 200e9,  "alpha": 11.7e-6, "yield": 250e6},
    "Steel, Stainless (304)":          {"E": 193e9,  "alpha": 17.2e-6, "yield": 205e6},
    "Aluminum 6061-T6":               {"E": 68.9e9, "alpha": 23.6e-6, "yield": 276e6},
    "Titanium Alloy (Ti-6Al-4V)":     {"E": 113.8e9,"alpha": 8.6e-6,  "yield": 880e6},
    "Copper, Pure (Annealed)":        {"E": 110e9,  "alpha": 16.5e-6, "yield": 69e6},
    "Brass, Yellow (C26800)":         {"E": 105e9,  "alpha": 20.3e-6, "yield": 250e6},
    "Plastic - Nylon 6/6":            {"E": 2.8e9,  "alpha": 80e-6,   "yield": 80e6},
    "Plastic - Polycarbonate":        {"E": 2.4e9,  "alpha": 67e-6,   "yield": 65e6},
    "Concrete, High Strength":        {"E": 30e9,   "alpha": 10e-6,   "yield": 40e6}, 
    "Wood - Oak (White)":             {"E": 12e9,   "alpha": 5e-6,    "yield": 50e6}, 
}

UNIT_LENGTH = {"m": 1.0, "mm": 1e-3, "cm": 1e-2, "in": 0.0254, "ft": 0.3048}
UNIT_FORCE = {"N": 1.0, "kN": 1e3, "MN": 1e6, "lbf": 4.44822, "kip": 4448.22}
UNIT_PRESSURE = {"Pa": 1.0, "kPa": 1e3, "MPa": 1e6, "GPa": 1e9, "psi": 6894.76, "ksi": 6894760.0}
UNIT_TEMP = {"K": 1.0, "C": 1.0, "F": 0.5556}

def to_si(value, unit, conversion_dict):
    return value * conversion_dict[unit]

def from_si(value, unit, conversion_dict):
    return value / conversion_dict[unit]

# =================================== PHYSICS CORE & VALIDATION ===================================

def validate_inputs(d_si, E_si, yield_si):
    """Returns a list of error messages. Empty list means valid."""
    errors = []
    if d_si <= 0:
        errors.append("Diameter must be a positive number.")
    if E_si <= 0:
        errors.append("Young's Modulus must be greater than zero.")
    if yield_si < 0:
        errors.append("Yield strength cannot be negative.")
    return errors

def check_warnings(f_si, dt_si):
    """Returns a list of warning messages for extreme but valid values."""
    warnings = []
    # Force > 100 MN (unrealistic for simple rod)
    if abs(f_si) > 1e8: 
        warnings.append(f"High Force Detected ({abs(f_si)/1e6:.0f} MN). Ensure units are correct.")
    # Temp > 2000 C (Melting point of steel is ~1500C)
    if abs(dt_si) > 2000:
        warnings.append(f"Extreme Temperature Change ({dt_si:.0f} K). Material phase change/melting likely.")
    return warnings

def calc_area(diameter):
    if diameter <= 0: return 0.0
    return m.pi * (diameter / 2) ** 2

def calc_stress_safe(force, area):
    if area <= 1e-12: # Near zero area protection
        return None 
    return force / area

def calc_thermal_stress(E, alpha, dT):
    return E * alpha * dT

# =================================== UI LAYOUT ===================================

st.title("STRUCTURAL MECHANICS COMPUTE ENGINE")
st.markdown("---")

# Sidebar
st.sidebar.header("SYSTEM CONTROLS")
app_mode = st.sidebar.radio("Select Operation Mode", ["Calculator Dashboard", "Parametric Plotter"])
st.sidebar.markdown("---")
st.sidebar.markdown("**Material Library**")
selected_material_name = st.sidebar.selectbox("Select Material", list(MATERIALS.keys()), index=1)
mat_props = MATERIALS[selected_material_name]
is_custom = selected_material_name == "--- User Defined ---"

if is_custom:
    st.sidebar.info("📝 Custom Mode Active")
else:
    st.sidebar.success(f"✅ Loaded: {selected_material_name}")

# =================================== DASHBOARD MODE ===================================
if app_mode == "Calculator Dashboard":
    
    col_input, col_result = st.columns([1, 1])

    with col_input:
        st.subheader("Input Parameters")
        
        # 1. Geometry
        with st.container():
            st.markdown("#### Geometry")
            c1, c2 = st.columns([2, 1])
            # Enforce min_value to prevent 0 or negative inputs
            d_val = c1.number_input("Diameter", value=20.0, step=1.0, min_value=0.0001, format="%.4f")
            d_unit = c2.selectbox("Unit", list(UNIT_LENGTH.keys()), index=1, key="u_d")
            
            diameter_si = to_si(d_val, d_unit, UNIT_LENGTH)
            area_si = calc_area(diameter_si)
            st.caption(f"Calculated Area: {area_si:.4e} m²")

        # 2. Loading
        with st.container():
            st.markdown("#### Mechanical Load")
            c1, c2 = st.columns([2, 1])
            # Allow negative force (Compression), but handle 0
            f_val = c1.number_input("Applied Force", value=50.0, step=100.0, format="%.2f")
            f_unit = c2.selectbox("Unit", list(UNIT_FORCE.keys()), index=1, key="u_f")
            force_si = to_si(f_val, f_unit, UNIT_FORCE)

        # 3. Thermal
        with st.container():
            st.markdown("#### Thermal Conditions")
            c1, c2 = st.columns([2, 1])
            dt_val = c1.number_input("Change in Temp (ΔT)", value=0.0, step=5.0)
            dt_unit = c2.selectbox("Unit", list(UNIT_TEMP.keys()), index=1, key="u_t")
            dt_si = to_si(dt_val, dt_unit, UNIT_TEMP)

        # 4. Material
        with st.container():
            st.markdown("#### Material Properties")
            c1, c2 = st.columns([2, 1])
            def_E = from_si(mat_props["E"], "GPa", UNIT_PRESSURE) if not is_custom else 200.0
            # Enforce E > 0
            E_val = c1.number_input("Young's Modulus", value=def_E, min_value=0.01, format="%.2f", key="E_in")
            c2.text("\n\nGPa") 
            E_si = to_si(E_val, "GPa", UNIT_PRESSURE)

            c3, c4 = st.columns([2, 1])
            def_alpha = mat_props["alpha"] * 1e6 if not is_custom else 11.7
            alpha_val = c3.number_input("Thermal Expansion (α)", value=def_alpha, format="%.2f", key="a_in")
            c4.text("\n\nµm/m·K")
            alpha_si = alpha_val * 1e-6

            c5, c6 = st.columns([2, 1])
            def_yield = from_si(mat_props["yield"], "MPa", UNIT_PRESSURE) if not is_custom else 250.0
            # Yield must be positive
            yield_val = c5.number_input("Limit Stress (Yield)", value=def_yield, min_value=0.0, format="%.2f", key="y_in")
            c6.text("\n\nMPa")
            yield_si = to_si(yield_val, "MPa", UNIT_PRESSURE)

    with col_result:
        st.subheader("Computed Results")
        
        # --- VALIDATION LAYER ---
        input_errors = validate_inputs(diameter_si, E_si, yield_si)
        warnings = check_warnings(force_si, dt_si)

        # Display Warnings (Non-blocking)
        for w in warnings:
            st.markdown(f"<div class='warning-box'>⚠️ {w}</div>", unsafe_allow_html=True)

        # Stop if Critical Errors
        if input_errors:
            for e in input_errors:
                st.error(f"⛔ {e}")
        else:
            # Perform Calcs (Safe Mode)
            mech_stress = calc_stress_safe(force_si, area_si)
            
            if mech_stress is None:
                st.error("⛔ Mathematical Singularity: Area is effectively zero.")
            else:
                therm_stress = calc_thermal_stress(E_si, alpha_si, dt_si)
                total_stress_val = mech_stress + therm_stress
                
                # Strain Check (Div by Zero Protected by Input Validation)
                strain_val = total_stress_val / E_si 
                
                # FOS Check
                abs_stress = abs(total_stress_val)
                if abs_stress < 1e-3: # Near zero stress
                    fos_val = float('inf')
                else:
                    fos_val = yield_si / abs_stress

                # --- DISPLAY ---
                display_unit = st.radio("Display Results In:", ["Pa", "MPa", "psi", "ksi", "kPa"], horizontal=True, index=1)
                
                s_mech_disp = from_si(mech_stress, display_unit, UNIT_PRESSURE)
                s_therm_disp = from_si(therm_stress, display_unit, UNIT_PRESSURE)
                s_total_disp = from_si(total_stress_val, display_unit, UNIT_PRESSURE)

                m1, m2 = st.columns(2)
                m1.metric("Mechanical Stress", f"{s_mech_disp:.2f} {display_unit}")
                m2.metric("Thermal Stress", f"{s_therm_disp:.2f} {display_unit}")
                
                # Logic for Color/Status
                # FOS < 1 means fail. 
                # Note: We use absolute stress for FOS, but sign for Tensile/Comp
                if fos_val >= 1.0:
                    res_color = "#28a745" # Green
                    status_text = "SAFE"
                else:
                    res_color = "#dc3545" # Red
                    status_text = "UNSAFE"

                # Stress Type
                if abs(total_stress_val) < 1e-9:
                    stress_type = "Neutral"
                elif total_stress_val > 0:
                    stress_type = "Tensile (+)"
                else:
                    stress_type = "Compressive (-)"

                st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 5px; border-left: 8px solid {res_color}; margin-top: 10px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <label style="font-size: 16px; font-weight: bold; color: #1e3d59; display: block; margin-bottom: 5px;">TOTAL STRESS</label>
                        <div style="font-size: 32px; font-weight: bold; color: {res_color}; font-family: sans-serif;">
                            {s_total_disp:.2f} {display_unit}
                        </div>
                        <div style="font-size: 14px; color: #555; margin-top: 5px;">
                            Type: <b>{stress_type}</b> | Design Status: <b style="color:{res_color}">{status_text}</b>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                m3, m4 = st.columns(2)
                m3.metric("Total Strain (ε)", f"{strain_val:.6e}")
                
                fos_text = f"{fos_val:.2f}" if fos_val < 1000 else "> 1000"
                m4.metric("Factor of Safety (FOS)", fos_text)

                # Visual FOS Gauge
                st.markdown("#### Safety Analysis")
                bar_color = "#28a745" if fos_val >= 1.0 else "#dc3545"
                # Cap fill at 100% for visual sanity
                fill_pct = 0 if fos_val == 0 else min(fos_val*20, 100)
                
                st.markdown(f"""
                    <div style="width:100%; background-color:#ddd; height:20px; border-radius:10px;">
                        <div style="width:{fill_pct}%; background-color:{bar_color}; height:20px; border-radius:10px; transition: width 0.5s;"></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; color: #555;">
                        <span>0</span><span>1.0 (Limit)</span><span>5.0+</span>
                    </div>
                """, unsafe_allow_html=True)

# =================================== PLOTTING MODE ===================================
elif app_mode == "Parametric Plotter":
    st.subheader("Parametric Analysis Plotter")
    st.info("Visualize how one variable affects the total stress, strain, or safety factor.")

    col_setup, col_plot = st.columns([1, 2])
    
    with col_setup:
        st.markdown("### X-Axis Configuration")
        x_axis_choice = st.selectbox("Select Independent Variable (X-Axis)", 
                                     ["Diameter", "Force", "Delta T", "Young's Modulus"])
        
        # Protect Start/End inputs based on physics
        start, end = 0.0, 0.0
        
        if x_axis_choice == "Diameter":
            start = st.number_input("Start Diameter (mm)", value=5.0, min_value=0.1)
            end = st.number_input("End Diameter (mm)", value=50.0, min_value=0.1)
            
        elif x_axis_choice == "Force":
            start = st.number_input("Start Force (kN)", value=0.0)
            end = st.number_input("End Force (kN)", value=100.0)
            
        elif x_axis_choice == "Delta T":
            start = st.number_input("Start ΔT (C)", value=0.0)
            end = st.number_input("End ΔT (C)", value=200.0)
            
        elif x_axis_choice == "Young's Modulus":
            start = st.number_input("Start E (GPa)", value=50.0, min_value=0.1)
            end = st.number_input("End E (GPa)", value=250.0, min_value=0.1)

        st.markdown("### Fixed Parameters")
        def_force = 10000.0
        def_dia = 20.0
        def_dt = 0.0
        
        if x_axis_choice != "Force":
            def_force = st.number_input("Fixed Force (N)", value=10000.0)
        if x_axis_choice != "Diameter":
            def_dia = st.number_input("Fixed Diameter (mm)", value=20.0, min_value=0.1)
        if x_axis_choice != "Delta T":
            def_dt = st.number_input("Fixed ΔT (C)", value=0.0)

        y_choice = st.selectbox("Select Dependent Variable (Y-Axis)", 
                                ["Total Stress", "Strain", "Factor of Safety"])

    # Computation Engine
    points = 100
    if start == end:
        st.error("Start and End values cannot be the same.")
    else:
        x_vals_plot = np.linspace(start, end, points)
        y_vals_plot = []

        E_curr = mat_props["E"] if mat_props["E"] > 0 else 200e9
        alpha_curr = mat_props["alpha"] if mat_props["alpha"] > 0 else 11.7e-6
        yield_curr = mat_props["yield"] if mat_props["yield"] > 0 else 250e6

        for val in x_vals_plot:
            # Defaults
            d_i = def_dia * 1e-3
            f_i = def_force
            dt_i = def_dt
            E_i = E_curr

            # Override based on X-axis
            if x_axis_choice == "Diameter": d_i = val * 1e-3
            elif x_axis_choice == "Force": f_i = val * 1e3
            elif x_axis_choice == "Delta T": dt_i = val
            elif x_axis_choice == "Young's Modulus": E_i = val * 1e9
            
            # SAFE CALCULATION LOOP
            # 1. Geometry Check
            if d_i <= 1e-9:
                y_vals_plot.append(np.nan) # Append NaN to break line, don't crash
                continue

            A_i = calc_area(d_i)
            mech = f_i / A_i # Safe because d_i > 0 checked above
            therm = calc_thermal_stress(E_i, alpha_curr, dt_i)
            tot = mech + therm
            
            if y_choice == "Total Stress":
                y_vals_plot.append(tot / 1e6) 
                y_label = "Stress (MPa)"
            elif y_choice == "Strain":
                if E_i <= 0: y_vals_plot.append(np.nan)
                else: y_vals_plot.append(tot / E_i)
                y_label = "Strain (unitless)"
            elif y_choice == "Factor of Safety":
                if abs(tot) < 1e-5: y_vals_plot.append(100.0) # Cap infinity for plot
                else: y_vals_plot.append(yield_curr / abs(tot))
                y_label = "Factor of Safety"

        # Plotting
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
                # Dynamically set Y limit to keep graph readable
                valid_y = [y for y in y_vals_plot if not np.isnan(y)]
                if valid_y:
                    top_lim = min(max(valid_y)*1.1, 10) # Cap plot at FOS 10 for readability
                    ax.set_ylim(0, top_lim)

            st.pyplot(fig)
