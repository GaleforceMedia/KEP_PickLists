import streamlit as st
import pandas as pd
import tempfile
import os

# Import our client layouts
from mp_layout import generate_picklists as format_mamas_papas
from th_layout import generate_th_picklists as format_tim_hortons
from custom_layout import generate_custom_picklist

# --- PAGE SETUP & BRANDING ---
st.set_page_config(page_title="KEP Print Group | Pick Lists", page_icon="🖨️", layout="wide")

st.markdown("""
    <style>
    .stButton>button {
        background-color: #000000;
        color: white;
        border-radius: 4px;
        font-weight: bold;
        border: none;
        width: 100%;
        padding: 10px;
    }
    .stButton>button:hover { background-color: #333333; color: white; }
    h1, h2, h3 { font-family: 'Arial', sans-serif; }
    [data-testid="stColumn"]:nth-child(1) {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🖨️ KEP Print Group - Pick List Generator")
st.write("Convert raw client spreadsheets into formatted dispatch documents.")
st.divider()

left_col, right_col = st.columns([1, 2], gap="large")

with left_col:
    st.subheader("1. Setup & Upload")
    client_option = st.selectbox("Select Layout Mode", ("Tim Hortons", "Mamas & Papas", "Custom Visual Mapping"))
    uploaded_file = st.file_uploader("Upload raw Excel file (.xlsx)", type=["xlsx"])

# --- LIVE PREVIEW & VISUAL MAPPING ---
with right_col:
    st.subheader("Data Preview & Mapping")
    
    if uploaded_file is not None:
        try:
            # We load the data immediately to show the preview and grab the column headers
            raw_df = pd.read_excel(uploaded_file)
            st.dataframe(raw_df.head(10), use_container_width=True, height=250)
            
            # --- CUSTOM MAPPING LOGIC ---
            if client_option == "Custom Visual Mapping":
                st.info("👆 Review your data above. Use the dropdowns below to map the columns.")
                
                # Get the actual column names from the uploaded sheet
                columns = [str(c) for c in raw_df.columns]
                
                c1, c2 = st.columns(2)
                with c1:
                    store_col_name = st.selectbox("Which column is the Store Name?", columns)
                    address_col_name = st.selectbox("Which column is the Address/Postcode?", columns)
                with c2:
                    pick_start_name = st.selectbox("Where do the product quantities start?", columns)
                
                generate_custom_btn = st.button("Generate Custom PDF")
                
                if generate_custom_btn:
                    with st.spinner('Building custom visual layout...'):
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_in, \
                             tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_out:
                            
                            tmp_in.write(uploaded_file.getvalue())
                            input_path = tmp_in.name
                            output_path = tmp_out.name
                            
                        try:
                            # Pass the string names directly to the script
                            generate_custom_picklist(input_path, output_path, store_col_name, address_col_name, pick_start_name)
                            
                            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                                st.success("✅ Custom Pick List generated successfully!")
                                with open(output_path, "rb") as pdf_file:
                                    st.download_button("⬇️ Download PDF Pick List", pdf_file.read(), file_name="KEP_Custom_PickList.pdf", mime="application/pdf")
                            else:
                                st.error("Failed to generate PDF. Check if the selected columns contain valid data.")
                        except Exception as e:
                            st.error(f"Processing Error: {e}")

            # --- STANDARD HARDCODED LOGIC ---
            else:
                generate_standard_btn = st.button(f"Generate {client_option} PDF")
                
                if generate_standard_btn:
                    with st.spinner(f'Applying {client_option} layout...'):
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_in, \
                             tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_out:
                            
                            tmp_in.write(uploaded_file.getvalue())
                            input_path = tmp_in.name
                            output_path = tmp_out.name
                        
                        try:
                            if client_option == "Tim Hortons":
                                format_tim_hortons(input_path, output_path)
                            elif client_option == "Mamas & Papas":
                                format_mamas_papas(input_path, output_path)
                                
                            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                                st.success("✅ Pick List generated successfully!")
                                with open(output_path, "rb") as pdf_file:
                                    st.download_button("⬇️ Download PDF Pick List", pdf_file.read(), file_name=f"KEP_{client_option.replace(' ', '')}_PickList.pdf", mime="application/pdf")
                        except Exception as e:
                            st.error(f"Processing Error: {e}")

        except Exception as e:
            st.error(f"Could not read the Excel file: {e}")
    else:
        st.info("Upload a spreadsheet on the left to activate the preview and mapping tools.")
