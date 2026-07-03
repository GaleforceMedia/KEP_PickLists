import streamlit as st
import tempfile
import os

# Import your existing scripts
# We are importing the main functions from the files you provided
from mp_layout import generate_picklists as format_mamas_papas
from th_layout import generate_th_picklists as format_tim_hortons

# --- KEP BRANDING & PAGE SETUP ---
st.set_page_config(page_title="KEP Print Group - Pick Lists", page_icon="🖨️", layout="centered")

# Optional: Add a simple CSS block to make it feel more like an internal tool
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #005A9C; /* Replace with exact KEP Blue if you have the hex code */
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🖨️ KEP Print Group")
st.subheader("Automated Pick List Generator")
st.write("Upload a raw client spreadsheet to generate a formatted PDF pick list for dispatch.")
st.divider()

# --- APP INTERFACE ---

# 1. Client Layout Selector
client_option = st.selectbox(
    "1. Select the Client Layout",
    ("Tim Hortons", "Mamas & Papas") # We can add Craft Union here later
)

# Show a little preview of what the layout does based on your scripts
if client_option == "Tim Hortons":
    st.caption("Layout: High-density single-column format, up to 20 items per page.")
elif client_option == "Mamas & Papas":
    st.caption("Layout: Standard grid format with 'Required' and 'Received' check boxes.")

# 2. File Uploader
uploaded_file = st.file_uploader("2. Upload Raw Spreadsheet (.xlsx)", type=["xlsx"])

# 3. Generate Process
if uploaded_file is not None:
    if st.button("Generate PDF Pick List"):
        
        # We use a spinner to show the user something is happening
        with st.spinner(f'Applying {client_option} layout rules...'):
            
            # Create temporary files for the input (Excel) and output (PDF)
            # This is necessary because your fpdf scripts require file paths
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_in:
                tmp_in.write(uploaded_file.getvalue())
                input_path = tmp_in.name
                
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_out:
                output_path = tmp_out.name

            try:
                # Route to the correct formatting function we imported
                if client_option == "Tim Hortons":
                    format_tim_hortons(input_path, output_path)
                elif client_option == "Mamas & Papas":
                    format_mamas_papas(input_path, output_path)
                
                # Check if the PDF was actually created
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    st.success("✅ Pick list generated successfully!")
                    
                    # Serve the PDF back to the user
                    with open(output_path, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()
                        
                    st.download_button(
                        label="⬇️ Download PDF Pick List",
                        data=pdf_bytes,
                        file_name=f"KEP_{client_option.replace(' ', '')}_PickList.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("The PDF was not generated. Please check that the spreadsheet matches the expected layout format.")

            except Exception as e:
                st.error(f"An error occurred while processing: {e}")
            
            finally:
                # Clean up the temporary files so we don't clog up the server
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(output_path):
                    os.remove(output_path)