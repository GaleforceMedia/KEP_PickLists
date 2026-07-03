import pandas as pd
from fpdf import FPDF
import sys
import os

def get_column_letter(n):
    string = ""
    while n >= 0:
        string = chr(n % 26 + 65) + string
        n = n // 26 - 1
    return string

def generate_picklists(excel_file, output_pdf, campaign_title="Mama's and Papa's Campaign", image_dir=None):
    # --- CONFIGURATION MAP ---
    SHEET_NAME = 0 
    JOB_ROW_INDEX = 1       
    VERSIONS_ROW_INDEX = 6  
    SIZE_ROW_INDEX = 4      
    CODE_ROW_INDEX = 5      
    
    STORE_START_ROW = 7      
    STORE_NAME_COL = 2       
    ADDRESS_COL = 7          
    POSTCODE_COL = 8         
    PRODUCT_START_COL = 9    

    try:
        df = pd.read_excel(excel_file, sheet_name=SHEET_NAME, header=None)
    except FileNotFoundError:
        print(f"  [!] ERROR: Could not find '{excel_file}'.")
        return

    # 1. Extract the product profiles
    products = []
    for col_idx in range(PRODUCT_START_COL, len(df.columns)):
        job_num = df.iloc[JOB_ROW_INDEX, col_idx]
        versions = df.iloc[VERSIONS_ROW_INDEX, col_idx]
        size = df.iloc[SIZE_ROW_INDEX, col_idx]
        code = df.iloc[CODE_ROW_INDEX, col_idx]
        
        if pd.isna(code) or str(code).strip() == "":
            products.append(None)
        else:
            products.append({
                "job_num": str(job_num).strip() if not pd.isna(job_num) else "N/A",
                "versions": str(versions).strip() if not pd.isna(versions) else "N/A",
                "code": str(code).strip(),
                "size": str(size).strip() if not pd.isna(size) else "N/A",
                "col_letter": get_column_letter(col_idx)
            })

    # 2. Parse the Stores
    store_orders = {}
    for index, row in df.iloc[STORE_START_ROW:].iterrows():
        store_name = row[STORE_NAME_COL]
        if pd.isna(store_name) or str(store_name).strip() == "":
            continue
            
        store_name = str(store_name).strip()
        address = str(row[ADDRESS_COL]).strip() if not pd.isna(row[ADDRESS_COL]) else ""
        postcode = str(row[POSTCODE_COL]).strip() if not pd.isna(row[POSTCODE_COL]) else ""
        
        items_for_store = []
        
        for col_idx, product_info in enumerate(products):
            if product_info is None:
                continue 
                
            val = row[PRODUCT_START_COL + col_idx]
            qty = 0 
            
            if not pd.isna(val):
                try:
                    qty = int(float(val))
                except ValueError:
                    qty = 0 
                    
            items_for_store.append({
                "product": product_info,
                "qty": qty
            })
                
        if items_for_store:
            store_orders[store_name] = {
                "address": address, 
                "postcode": postcode, 
                "items": items_for_store
            }

    # 3. Generate the PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=False) 
    
    def draw_header(store, addr, pcode):
        pdf.add_page()
        pdf.set_font("Arial", size=16, style='B')
        
        safe_title = campaign_title.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(200, 8, txt=safe_title, ln=True, align='C')
        pdf.ln(3)
        
        pdf.set_font("Arial", size=18, style='B')
        pdf.cell(200, 8, txt=f"Store: {store}", ln=True)
        
        if addr and addr != "nan":
            pdf.set_font("Arial", size=11, style='I')
            safe_addr = addr.encode('latin-1', 'replace').decode('latin-1')
            safe_pcode = pcode.encode('latin-1', 'replace').decode('latin-1')
            full_address = f"{safe_addr}, {safe_pcode}" if pcode and pcode != "nan" else safe_addr
            pdf.multi_cell(0, 5, txt=f"Location: {full_address}")
        
        pdf.ln(4)
        y = pdf.get_y()
        pdf.set_draw_color(0, 0, 0)
        pdf.set_line_width(0.5)
        pdf.line(10, y, 200, y)
        pdf.ln(1.5)

        pdf.set_font("Arial", size=9, style='B')
        pdf.set_xy(10, y + 1.5)
        pdf.cell(25, 5, "Artwork", align='C')
        pdf.set_x(35)
        pdf.cell(125, 5, "Job Description", align='L')
        pdf.set_x(160)
        pdf.cell(20, 5, "Required", align='C')
        pdf.set_x(182)
        pdf.cell(18, 5, "Received", align='C')
        pdf.ln(6)

    for store_name, data in store_orders.items():
        draw_header(store_name, data["address"], data["postcode"])
        
        for idx, item in enumerate(data["items"], start=1):
            if pdf.get_y() > 245:
                draw_header(f"{store_name} (Continued)", data["address"], data["postcode"])

            mp_prefix = f"MP{idx:02d}"
            qty = item['qty']
            p = item['product']
            
            y_start = pdf.get_y()

            pdf.set_xy(160, y_start)
            if qty == 0:
                pdf.set_fill_color(235, 235, 235)
                pdf.rect(160, y_start, 20, 15, 'F')
                pdf.set_xy(160, y_start + 4.5)
                pdf.set_font("Arial", size=8, style='B')
                pdf.set_text_color(160, 160, 160)
                pdf.cell(20, 6, "SKIP", align='C')
                pdf.set_text_color(0, 0, 0)
            else:
                pdf.set_draw_color(0, 0, 0)
                pdf.set_line_width(0.3)
                pdf.rect(160, y_start, 20, 15, 'D')
                pdf.set_xy(160, y_start + 4.5)
                pdf.set_font("Arial", size=12, style='B')
                pdf.cell(20, 6, f"{qty}", align='C')

            pdf.set_draw_color(0, 0, 0)
            pdf.set_line_width(0.3)
            pdf.rect(182, y_start, 18, 15, 'D')

            text_x = 10 
            img_to_use = None
            if image_dir:
                col_letter = p['col_letter']
                prod_code = p['code']
                
                possible_names = [
                    f"{col_letter}.jpg", f"{col_letter}.png", f"{col_letter}.jpeg",
                    f"{col_letter.lower()}.jpg", f"{col_letter.lower()}.png",
                    f"{prod_code}.jpg", f"{prod_code}.png", f"{prod_code}.jpeg"
                ]

                for root, dirs, files in os.walk(image_dir):
                    for file in files:
                        if file in possible_names:
                            img_to_use = os.path.join(root, file)
                            break
                    if img_to_use:
                        break
            
            if img_to_use:
                try:
                    pdf.image(img_to_use, x=10, y=y_start, w=22, h=22)
                    text_x = 35 
                except Exception:
                    pass 

            pdf.set_xy(text_x, y_start)
            pdf.set_font("Arial", size=11, style='B' if qty > 0 else '')
            l1 = f"{mp_prefix}  |  Size: {p['size']}"
            pdf.cell(155 - text_x, 5, txt=l1.encode('latin-1', 'replace').decode('latin-1'), ln=True)
            
            pdf.set_x(text_x)
            pdf.set_font("Arial", size=10)
            l2 = f"Code: {p['code']}  |  Job: {p['job_num']}"
            pdf.cell(155 - text_x, 5, txt=l2.encode('latin-1', 'replace').decode('latin-1'), ln=True)
            
            pdf.set_x(text_x)
            l3 = f"Versions: {p['versions']}"
            pdf.multi_cell(155 - text_x, 4.5, txt=l3.encode('latin-1', 'replace').decode('latin-1'))

            lowest_y = max(pdf.get_y(), y_start + 22) + 3
            pdf.set_y(lowest_y)
            
            pdf.set_draw_color(225, 225, 225)
            pdf.set_line_width(0.2)
            pdf.line(10, lowest_y, 200, lowest_y)
            pdf.ln(2)

        pdf.set_text_color(0, 0, 0) 

    pdf.output(output_pdf)

# --- NEW: DHL DATA EXTRACTOR ---
def extract_dhl_data(excel_file, ref, weight, parcels, dispatch_date, account_no="F090406"):
    SHEET_NAME = 0 
    STORE_START_ROW = 7      
    STORE_NAME_COL = 2       
    ADDRESS_COL = 7          
    POSTCODE_COL = 8         
    PRODUCT_START_COL = 9    

    try:
        df = pd.read_excel(excel_file, sheet_name=SHEET_NAME, header=None)
    except Exception:
        return []

    dhl_rows = []
    
    for index, row in df.iloc[STORE_START_ROW:].iterrows():
        store_name = row[STORE_NAME_COL]
        if pd.isna(store_name) or str(store_name).strip() == "":
            continue
            
        store_name = str(store_name).strip()
        address = str(row[ADDRESS_COL]).strip() if not pd.isna(row[ADDRESS_COL]) else ""
        postcode = str(row[POSTCODE_COL]).strip() if not pd.isna(row[POSTCODE_COL]) else ""
        
        # Determine if this store is getting ANY items
        has_items = False
        for col_idx in range(PRODUCT_START_COL, len(df.columns)):
            val = row[col_idx]
            if not pd.isna(val):
                try:
                    qty = int(float(val))
                    if qty > 0:
                        has_items = True
                        break
                except ValueError:
                    pass
                    
        # Only add to DHL if they actually have an active pick
        if has_items:
            # Splitting the raw address string to fit into DHL's separated boxes
            addr_parts = [p.strip() for p in address.split(',') if p.strip()]
            addr2 = addr_parts[0] if len(addr_parts) > 0 else ""
            addr3 = addr_parts[1] if len(addr_parts) > 1 else ""
            addr4 = ", ".join(addr_parts[2:]) if len(addr_parts) > 2 else ""
            
            dhl_rows.append({
                'Account Number': account_no,
                'Full Name': store_name,
                'Address 1': 'Mamas & Papas',
                'Address 2': addr2,
                'Address 3': addr3,
                'Address 4': addr4,
                'Postcode': postcode,
                'Country': 'United Kingdom',
                'Email': '',
                'FAO': 'General Manager',
                'Tel No': '',
                'No of items': parcels,
                'Weight kg': weight,
                'Notes': '',
                'Delivery Email': '',
                'Job Ref': ref,
                'Service': '1',
                'Dispatch Date': dispatch_date
            })
            
    return dhl_rows
