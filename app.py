import streamlit as st
import pandas as pd
import tempfile
import os

# Import our specific client layouts
from mp_layout import generate_picklists as format_mamas_papas
from th_layout import generate_th_picklists as format_tim_hortons
# Import our new universal custom layout
from custom_layout import generate_custom_picklist

# --- PAGE SETUP & KEP BRANDING ---
st.set_page_config(page_title="KEP Print Group | Pick Lists", page_icon="🖨️", layout="wide")

st.markdown("""
    <style>
    /* KEP Branding - Black buttons, bold text */
    .stButton>button {
        background-color: #000000;
        color: white;
        border-radius: 4px;
        font-weight: bold;
        border: none;
        width: 100%;
        padding: 10px;
    }
    .stButton>button:hover {
        background-color: #333333;
        color: white;
        border: none;
    }
    h1, h2, h3 { font-family: 'Arial', sans-serif; }
    /* Subtle background for the control panel */
    [data-testid="stColumn"]:nth-child(1) {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("🖨️ KEP Print Group - Pick List Generator")
st.write("Convert raw client spreadsheets into formatted dispatch documents.")
st.divider()

# --- MAIN DASHBOARD LAYOUT ---
left_col, right_col = st.columns([1, 2], gap="large")

with left_col:
    st.subheader("1. Configuration")
    
    client_option = st.selectbox(
        "Select Layout",
        ("Tim Hortons", "Mamas & Papas", "Custom Setup (Dynamic)")
    )
    
    # --- DYNAMIC CUSTOM SETTINGS ---
    custom_settings = {}
    if client_option == "Custom Setup (Dynamic)":
        st.caption("Define the exact locations for this specific spreadsheet.")
        
        c1, c2 = st.columns(2)
        with c1:
            custom_settings['store_row'] = st.number_input("Store Data Starts (Row)", min_value=1, value=7) - 1 # Subtract 1 for zero-indexing
            custom_settings['store_col'] = st.number_input("Store Name (Col A=1)", min_value=1, value=1) - 1
        with c2:
            custom_settings['address_col'] = st.number_input("Address (Col A=1)", min_value=1, value=2) - 1
            custom_settings['pick_col'] = st.number_input("Picks Start (Col A=1)", min_value=1, value=5) - 1

    st.subheader("2. Data Upload")
    uploaded_file = st.file_uploader("Upload raw Excel file (.xlsx)", type=["xlsx"])
    
    generate_btn = st.button("Generate PDF Pick List")

# --- LIVE PREVIEW & GENERATION LOGIC ---
with right_col:
    st.subheader("Data Preview")
    
    if uploaded_file is not None:
        # Show a preview to the team before they commit
        preview_df = pd.read_excel(uploaded_file, header=None, nrows=15)
        st.dataframe(preview_df, use_container_width=True, height=300)
        
        if generate_btn:
            with st.spinner(f'Applying {client_option} logic...'):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_in:
                    tmp_in.write(uploaded_file.getvalue())
                    input_path = tmp_in.name
                    
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_out:
                    output_path = tmp_out.name

                try:
                    # ROUTE TO THE CORRECT SCRIPT
                    if client_option == "Tim Hortons":
                        format_tim_hortons(input_path, output_path)
                    elif client_option == "Mamas & Papas":
                        format_mamas_papas(input_path, output_path)
                    elif client_option == "Custom Setup (Dynamic)":
                        generate_custom_picklist(input_path, output_path, **custom_settings)
                    
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        st.success("✅ Pick list generated successfully!")
                        with open(output_path, "rb") as pdf_file:
                            st.download_button(
                                label="⬇️ Download PDF Pick List",
                                data=pdf_file.read(),
                                file_name=f"KEP_{client_option.replace(' ', '')}_PickList.pdf",
                                mime="application/pdf",
                                key="download_btn" # Unique key for Streamlit
                            )
                    else:
                        st.error("Failed to generate PDF. Please check the spreadsheet layout.")

                except Exception as e:
                    st.error(f"Processing Error: {e}")
                finally:
                    if os.path.exists(input_path): os.remove(input_path)
                    if os.path.exists(output_path): os.remove(output_path)
    else:
        st.info("Upload a spreadsheet on the left to preview the raw data layout here.")
