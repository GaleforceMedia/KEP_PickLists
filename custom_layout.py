import pandas as pd
from fpdf import FPDF
import os

def generate_custom_picklist(excel_file, output_pdf, store_row, store_col, address_col, pick_col):
    try:
        # Load without headers so we can navigate by absolute coordinates
        df = pd.read_excel(excel_file, header=None)
    except Exception as e:
        print(f"Error loading Excel: {e}")
        return

    # Extract Product Headers (Assuming they are row 0 and row 1 for this generic layout)
    # This grabs whatever text is at the top of the columns
    products = []
    for col_idx in range(pick_col, len(df.columns)):
        prod_title = df.iloc[0, col_idx] if not pd.isna(df.iloc[0, col_idx]) else f"Item {col_idx}"
        products.append({
            "title": str(prod_title).strip(),
            "col_idx": col_idx
        })

    pdf = FPDF()
    pdf.set_auto_page_break(auto=False)

    # Iterate through the rows where the user said the store data starts
    for index, row in df.iloc[store_row:].iterrows():
        store_name = row[store_col]
        
        # Skip empty rows
        if pd.isna(store_name) or str(store_name).strip() == "":
            continue
            
        store_name = str(store_name).strip()
        address = str(row[address_col]).strip() if not pd.isna(row[address_col]) else ""
        
        pdf.add_page()
        
        # --- HEADER ---
        pdf.set_font("Arial", size=18, style='B')
        pdf.cell(0, 10, txt=f"STORE: {store_name}", ln=True)
        
        if address and address != "nan":
            pdf.set_font("Arial", size=12, style='I')
            # Handle weird characters
            safe_addr = address.encode('latin-1', 'replace').decode('latin-1')
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
            val = row[prod["col_idx"]]
            
            # Try to get a clean number
            qty = 0
            if not pd.isna(val):
                try:
                    qty = int(float(str(val).strip()))
                except ValueError:
                    qty = 0
            
            # Only print items where quantity is greater than 0
            if qty > 0:
                # Add new page if we are hitting the bottom
                if pdf.get_y() > 260:
                    pdf.add_page()
                    pdf.cell(140, 8, "Product Description", border=1)
                    pdf.cell(25, 8, "Req", border=1, align='C')
                    pdf.cell(25, 8, "Picked", border=1, align='C')
                    pdf.ln()

                pdf.set_font("Arial", size=11)
                
                # Truncate long descriptions to fit the cell
                desc = prod["title"][:70].encode('latin-1', 'replace').decode('latin-1')
                
                pdf.cell(140, 10, desc, border=1)
                
                # Bold the quantity
                pdf.set_font("Arial", size=12, style='B')
                pdf.cell(25, 10, str(qty), border=1, align='C')
                
                # Empty box for the dispatch team to tick
                pdf.cell(25, 10, "", border=1) 
                pdf.ln()

    pdf.output(output_pdf)
