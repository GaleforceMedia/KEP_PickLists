import streamlit as st
import pandas as pd
import tempfile
import os
import zipfile
import io

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
st.write("Convert raw client spreadsheets into formatted dispatch documents. Upload multiple files to batch process.")
st.divider()

left_col, right_col = st.columns([1, 2], gap="large")

with left_col:
    st.subheader("1. Setup & Upload")
    client_option = st.selectbox("Select Layout Mode", ("Tim Hortons", "Mamas & Papas", "Custom Visual Mapping"))
    
    # Upload multiple files enabled
    uploaded_files = st.file_uploader("Upload raw Excel files (.xlsx)", type=["xlsx"], accept_multiple_files=True)

# --- LIVE PREVIEW & VISUAL MAPPING ---
with right_col:
    st.subheader("Data Preview & Mapping")
    
    if uploaded_files:
        try:
            # We base the preview and column headers on the FIRST uploaded file in the batch
            first_file = uploaded_files[0]
            raw_df = pd.read_excel(first_file)
            
            # Expanded to 20 rows and increased window height
            st.write(f"**Previewing:** `{first_file.name}` (Showing top 20 rows)")
            st.dataframe(raw_df.head(20), use_container_width=True, height=450)
            
            # --- CUSTOM MAPPING LOGIC ---
            if client_option == "Custom Visual Mapping":
                st.info("👆 Review your data above. Map the columns below. This mapping will apply to ALL files in your batch.")
                
                columns = [str(c) for c in raw_df.columns]
                
                c1, c2 = st.columns(2)
                with c1:
                    store_col_name = st.selectbox("Which column is the Store Name?", columns)
                    address_col_name = st.selectbox("Which column is the Address/Postcode?", columns)
                with c2:
                    pick_start_name = st.selectbox("Where do the product quantities start?", columns)
                
                generate_custom_btn = st.button(f"Generate Custom PDFs ({len(uploaded_files)} files)")
                
                if generate_custom_btn:
                    with st.spinner(f'Batch processing {len(uploaded_files)} files...'):
                        zip_buffer = io.BytesIO()
                        
                        # Open a ZIP file in memory
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                            for file in uploaded_files:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_in, \
                                     tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_out:
                                    
                                    tmp_in.write(file.getvalue())
                                    input_path = tmp_in.name
                                    output_path = tmp_out.name
                                    
                                try:
                                    # Process the individual file
                                    generate_custom_picklist(input_path, output_path, store_col_name, address_col_name, pick_start_name)
                                    
                                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                                        # Name the PDF based on the original Excel file name
                                        pdf_filename = f"KEP_Custom_{file.name.replace('.xlsx', '')}.pdf"
                                        zip_file.write(output_path, arcname=pdf_filename)
                                except Exception as e:
                                    st.error(f"Error processing {file.name}: {e}")
                                finally:
                                    if os.path.exists(input_path): os.remove(input_path)
                                    if os.path.exists(output_path): os.remove(output_path)
                        
                        st.success(f"✅ Successfully zipped {len(uploaded_files)} files!")
                        st.download_button(
                            label="⬇️ Download All PDFs (ZIP)",
                            data=zip_buffer.getvalue(),
                            file_name="KEP_Custom_PickLists.zip",
                            mime="application/zip"
                        )

            # --- STANDARD HARDCODED LOGIC ---
            else:
                generate_standard_btn = st.button(f"Generate {client_option} PDFs ({len(uploaded_files)} files)")
                
                if generate_standard_btn:
                    with st.spinner(f'Batch processing {len(uploaded_files)} files using {client_option} layout...'):
                        zip_buffer = io.BytesIO()
                        
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                            for file in uploaded_files:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_in, \
                                     tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_out:
                                    
                                    tmp_in.write(file.getvalue())
                                    input_path = tmp_in.name
                                    output_path = tmp_out.name
                                
                                try:
                                    if client_option == "Tim Hortons":
                                        format_tim_hortons(input_path, output_path)
                                    elif client_option == "Mamas & Papas":
                                        format_mamas_papas(input_path, output_path)
                                        
                                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                                        clean_name = client_option.replace(' ', '')
                                        pdf_filename = f"KEP_{clean_name}_{file.name.replace('.xlsx', '')}.pdf"
                                        zip_file.write(output_path, arcname=pdf_filename)
                                except Exception as e:
                                    st.error(f"Error processing {file.name}: {e}")
                                finally:
                                    if os.path.exists(input_path): os.remove(input_path)
                                    if os.path.exists(output_path): os.remove(output_path)
                        
                        st.success(f"✅ Successfully zipped {len(uploaded_files)} files!")
                        clean_zip_name = client_option.replace(' ', '')
                        st.download_button(
                            label="⬇️ Download All PDFs (ZIP)",
                            data=zip_buffer.getvalue(),
                            file_name=f"KEP_{clean_zip_name}_PickLists.zip",
                            mime="application/zip"
                        )

        except Exception as e:
            st.error(f"Could not read the Excel file: {e}")
    else:
        st.info("Upload one or more spreadsheets on the left to activate the preview and mapping tools.")
