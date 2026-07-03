import pandas as pd
from fpdf import FPDF
import os

def generate_custom_picklist(excel_file, output_pdf, store_col_name, address_col_name, pick_start_name):
    try:
        # Load the excel file, assuming the very first row contains the headers
        df = pd.read_excel(excel_file)
    except Exception as e:
        print(f"Error loading Excel: {e}")
        return

    # Strip any accidental spaces from column names just to be safe
    df.columns = df.columns.str.strip()

    # Find exactly where the products begin based on the name selected in the app
    try:
        pick_start_idx = df.columns.get_loc(pick_start_name.strip())
    except KeyError:
        print(f"Error: Could not find the starting column '{pick_start_name}'")
        return

    # Extract all the product names from that starting point to the end of the sheet
    products = []
    for col_idx in range(pick_start_idx, len(df.columns)):
        prod_title = df.columns[col_idx]
        
        # Ignore blank columns or pandas "Unnamed" artifact columns
        if not pd.isna(prod_title) and not str(prod_title).startswith("Unnamed"):
            products.append({
                "title": str(prod_title).strip(),
                "col_name": prod_title
            })

    pdf = FPDF()
    pdf.set_auto_page_break(auto=False)

    # Loop through the data row by row
    for index, row in df.iterrows():
        store_name = row.get(store_col_name.strip())
        
        # Skip empty rows
        if pd.isna(store_name) or str(store_name).strip() == "":
            continue
            
        store_name = str(store_name).strip()
        address = row.get(address_col_name.strip())
        address_str = str(address).strip() if not pd.isna(address) else ""
        
        pdf.add_page()
        
        # --- HEADER ---
        pdf.set_font("Arial", size=18, style='B')
        pdf.cell(0, 10, txt=f"STORE: {store_name}", ln=True)
        
        if address_str and address_str != "nan":
            pdf.set_font("Arial", size=12, style='I')
            safe_addr = address_str.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, txt=f"Location: {safe_addr}")
        
        pdf.ln(5)
        y_pos = pdf.get_y()
        pdf.set_draw_color(0, 0, 0)
        pdf.line(10, y_pos, 200, y_pos)
        pdf.ln(5)

        # --- GRID HEADER ---
        pdf.set_font("Arial", size=10, style='B')
        pdf.cell(140, 8, "Product Description", border=1)
        pdf.cell(25, 8, "Req", border=1, align='C')
        pdf.cell(25, 8, "Picked", border=1, align='C')
        pdf.ln()

        # --- DRAW ITEMS ---
        for prod in products:
            val = row.get(prod["col_name"])
            
            qty = 0
            if not pd.isna(val):
                try:
                    qty = int(float(str(val).strip()))
                except ValueError:
                    qty = 0
            
            # Only print items where quantity is greater than 0
            if qty > 0:
                if pdf.get_y() > 260:
                    pdf.add_page()
                    pdf.cell(140, 8, "Product Description", border=1)
                    pdf.cell(25, 8, "Req", border=1, align='C')
                    pdf.cell(25, 8, "Picked", border=1, align='C')
                    pdf.ln()

                pdf.set_font("Arial", size=11)
                
                # Truncate extremely long item descriptions so they fit nicely
                desc = prod["title"][:70].encode('latin-1', 'replace').decode('latin-1')
                
                pdf.cell(140, 10, desc, border=1)
                pdf.set_font("Arial", size=12, style='B')
                pdf.cell(25, 10, str(qty), border=1, align='C')
                pdf.cell(25, 10, "", border=1) 
                pdf.ln()

    pdf.output(output_pdf)
