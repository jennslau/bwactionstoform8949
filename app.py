import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import zipfile
from datetime import datetime
import PyPDF2
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def main():
    st.set_page_config(
        page_title="CSV to Form 8949 PDF Filler",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 CSV to Form 8949 PDF Filler")
    st.markdown("Upload a CSV file with your capital gains/losses data and generate filled Form 8949 PDFs.")
    
    # Information section
    with st.expander("ℹ️ About Form 8949", expanded=False):
        st.markdown("""
        **Form 8949** is used to report sales and other dispositions of capital assets.
        
        **Required CSV Columns:**
        - **Description**: Description of property (e.g., "100 shares of XYZ Corp")
        - **Date_Acquired**: Date you acquired the property (MM/DD/YYYY)
        - **Date_Sold**: Date you sold the property (MM/DD/YYYY)
        - **Sales_Price**: Gross sales price
        - **Cost_Basis**: Your cost or other basis
        - **Gain_Loss**: Gain or loss (Sales_Price - Cost_Basis)
        
        **Optional Columns:**
        - **Adjustment_Code**: Code for adjustments (if any)
        - **Adjustment_Amount**: Amount of adjustment
        """)
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # Form type selection
    form_type = st.sidebar.selectbox(
        "Form 8949 Type:",
        [
            "Part I - Short-term (Box A checked)",
            "Part I - Short-term (Box B checked)", 
            "Part I - Short-term (Box C checked)",
            "Part II - Long-term (Box A checked)",
            "Part II - Long-term (Box B checked)",
            "Part II - Long-term (Box C checked)"
        ],
        help="Choose based on your holding period and whether basis was reported to IRS"
    )
    
    # Taxpayer information
    st.sidebar.subheader("Taxpayer Information")
    taxpayer_name = st.sidebar.text_input("Name", placeholder="Your Name")
    taxpayer_ssn = st.sidebar.text_input("Social Security Number", placeholder="XXX-XX-XXXX")
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("Step 1: Upload CSV File")
        
        # Sample CSV download
        sample_csv = create_sample_csv()
        st.download_button(
            label="📥 Download Sample CSV Template",
            data=sample_csv,
            file_name="form_8949_template.csv",
            mime="text/csv",
            help="Download this template to see the required format"
        )
        
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type="csv",
            help="Upload a CSV file with your capital gains/losses data"
        )
        
        if uploaded_file is not None:
            try:
                # Read the CSV file
                df = pd.read_csv(uploaded_file)
                st.success(f"✅ CSV loaded successfully! Found {len(df)} rows of transactions.")
                
                # Validate required columns
                required_columns = ['Description', 'Date_Acquired', 'Date_Sold', 'Sales_Price', 'Cost_Basis']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                    st.info("Please ensure your CSV has these columns: " + ", ".join(required_columns))
                    df = None
                else:
                    # Calculate Gain_Loss if not provided
                    if 'Gain_Loss' not in df.columns:
                        df['Gain_Loss'] = pd.to_numeric(df['Sales_Price'], errors='coerce') - pd.to_numeric(df['Cost_Basis'], errors='coerce')
                        st.info("✅ Calculated Gain/Loss column automatically")
                    
                    # Display preview
                    st.subheader("Data Preview")
                    st.dataframe(df.head())
                    
                    # Show summary
                    total_sales = pd.to_numeric(df['Sales_Price'], errors='coerce').sum()
                    total_basis = pd.to_numeric(df['Cost_Basis'], errors='coerce').sum()
                    total_gain_loss = pd.to_numeric(df['Gain_Loss'], errors='coerce').sum()
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Total Sales Price", f"${total_sales:,.2f}")
                    with col_b:
                        st.metric("Total Cost Basis", f"${total_basis:,.2f}")
                    with col_c:
                        st.metric("Net Gain/Loss", f"${total_gain_loss:,.2f}")
                
            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")
                df = None
        else:
            df = None
    
    with col2:
        st.header("Step 2: Generate Form 8949")
        
        if df is not None and taxpayer_name and taxpayer_ssn:
            # Processing options
            st.subheader("Processing Options")
            
            transactions_per_page = st.selectbox(
                "Transactions per page:",
                [14, 10, 7],
                index=0,
                help="Form 8949 can fit up to 14 transactions per page"
            )
            
            # Generate Forms button
            if st.button("🚀 Generate Form 8949 PDFs", type="primary"):
                try:
                    # Generate PDFs
                    pdf_files = generate_form_8949_pdfs(
                        df, 
                        form_type, 
                        taxpayer_name, 
                        taxpayer_ssn, 
                        transactions_per_page
                    )
                    
                    if len(pdf_files) == 1:
                        # Single PDF download
                        st.download_button(
                            label="📥 Download Form 8949 PDF",
                            data=pdf_files[0]['content'],
                            file_name=pdf_files[0]['filename'],
                            mime="application/pdf"
                        )
                    else:
                        # Multiple PDFs - create zip
                        zip_data = create_zip_file(pdf_files)
                        st.download_button(
                            label="📦 Download All Form 8949 PDFs (ZIP)",
                            data=zip_data,
                            file_name=f"form_8949_filled_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                            mime="application/zip"
                        )
                    
                    st.success(f"✅ Generated {len(pdf_files)} Form 8949 PDF(s) successfully!")
                    
                    # Show summary of what was generated
                    total_pages = len(pdf_files)
                    total_transactions = len(df)
                    st.info(f"📄 Generated {total_pages} page(s) for {total_transactions} transactions")
                    
                except Exception as e:
                    st.error(f"Error generating PDFs: {str(e)}")
                    st.error("Please check your data format and try again.")
        
        elif df is not None:
            st.warning("⚠️ Please fill in your taxpayer information in the sidebar.")
        else:
            st.info("👆 Please upload a CSV file first.")

def create_sample_csv():
    """Create a sample CSV template for Form 8949"""
    sample_data = {
        'Description': [
            '100 shares ABC Corp',
            '50 shares XYZ Inc',
            '200 shares DEF Ltd'
        ],
        'Date_Acquired': [
            '01/15/2023',
            '03/10/2023',
            '06/20/2023'
        ],
        'Date_Sold': [
            '12/15/2023',
            '11/05/2023',
            '12/30/2023'
        ],
        'Sales_Price': [
            5000.00,
            2500.00,
            8000.00
        ],
        'Cost_Basis': [
            4500.00,
            3000.00,
            7500.00
        ],
        'Gain_Loss': [
            500.00,
            -500.00,
            500.00
        ],
        'Adjustment_Code': [
            '',
            '',
            ''
        ],
        'Adjustment_Amount': [
            0.00,
            0.00,
            0.00
        ]
    }
    
    df = pd.DataFrame(sample_data)
    return df.to_csv(index=False)

def generate_form_8949_pdfs(df, form_type, taxpayer_name, taxpayer_ssn, transactions_per_page):
    """Generate Form 8949 PDF files"""
    pdf_files = []
    
    # Split data into pages
    total_transactions = len(df)
    pages_needed = (total_transactions + transactions_per_page - 1) // transactions_per_page
    
    for page_num in range(pages_needed):
        start_idx = page_num * transactions_per_page
        end_idx = min(start_idx + transactions_per_page, total_transactions)
        page_data = df.iloc[start_idx:end_idx]
        
        # Create PDF for this page
        buffer = io.BytesIO()
        create_form_8949_pdf(buffer, page_data, form_type, taxpayer_name, taxpayer_ssn, page_num + 1)
        
        # Generate filename
        if pages_needed == 1:
            filename = f"Form_8949_{taxpayer_name.replace(' ', '_')}.pdf"
        else:
            filename = f"Form_8949_{taxpayer_name.replace(' ', '_')}_Page_{page_num + 1}.pdf"
        
        pdf_files.append({
            'filename': filename,
            'content': buffer.getvalue()
        })
    
    return pdf_files

def create_form_8949_pdf(buffer, df, form_type, taxpayer_name, taxpayer_ssn, page_number):
    """Create a Form 8949 PDF that matches the IRS layout"""
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Form header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Form 8949")
    c.setFont("Helvetica", 10)
    c.drawString(150, height - 50, "Sales and Other Dispositions of Capital Assets")
    
    # Tax year
    c.drawString(width - 150, height - 50, "2023")  # Update year as needed
    
    # Taxpayer information
    c.setFont("Helvetica", 9)
    c.drawString(50, height - 80, f"Name: {taxpayer_name}")
    c.drawString(50, height - 95, f"Social Security Number: {taxpayer_ssn}")
    
    # Form type and checkboxes
    y_pos = height - 130
    c.setFont("Helvetica-Bold", 10)
    
    # Determine which part and box
    if "Part I" in form_type:
        c.drawString(50, y_pos, "Part I - Short-Term Capital Gains and Losses")
        part_text = "Short-Term"
    else:
        c.drawString(50, y_pos, "Part II - Long-Term Capital Gains and Losses")
        part_text = "Long-Term"
    
    # Checkbox indicators
    y_pos -= 25
    c.setFont("Helvetica", 9)
    
    if "Box A" in form_type:
        c.drawString(50, y_pos, "☑ (A) Basis reported to IRS")
        c.drawString(250, y_pos, "☐ (B) Basis not reported to IRS")
        c.drawString(450, y_pos, "☐ (C) Various")
    elif "Box B" in form_type:
        c.drawString(50, y_pos, "☐ (A) Basis reported to IRS")
        c.drawString(250, y_pos, "☑ (B) Basis not reported to IRS")
        c.drawString(450, y_pos, "☐ (C) Various")
    else:  # Box C
        c.drawString(50, y_pos, "☐ (A) Basis reported to IRS")
        c.drawString(250, y_pos, "☐ (B) Basis not reported to IRS")
        c.drawString(450, y_pos, "☑ (C) Various")
    
    # Column headers
    y_pos = height - 180
    c.setFont("Helvetica-Bold", 8)
    
    headers = [
        ("(a) Description of property", 50, 120),
        ("(b) Date acquired", 170, 60),
        ("(c) Date sold", 235, 60),
        ("(d) Proceeds", 300, 50),
        ("(e) Cost basis", 355, 50),
        ("(f) Adjustment", 410, 35),
        ("(g) Gain/(loss)", 450, 50),
        ("(h) Gain/(loss)", 505, 50)
    ]
    
    for header, x_pos, width_col in headers:
        c.drawString(x_pos, y_pos, header)
    
    # Draw header underlines
    y_pos -= 5
    c.line(50, y_pos, width - 50, y_pos)
    
    # Column subheaders for adjustments
    y_pos -= 15
    c.setFont("Helvetica", 7)
    c.drawString(410, y_pos, "Code")
    c.drawString(430, y_pos, "Amount")
    c.drawString(470, y_pos, "Column (e)")
    c.drawString(505, y_pos, "Subtract (f)")
    c.drawString(470, y_pos - 8, "plus (f)")
    c.drawString(505, y_pos - 8, "from (d)")
    
    # Data rows
    y_pos -= 25
    c.setFont("Helvetica", 8)
    
    for idx, row in df.iterrows():
        if y_pos < 100:  # Check if we need a new page
            break
            
        # Format dates
        date_acquired = format_date(row.get('Date_Acquired', ''))
        date_sold = format_date(row.get('Date_Sold', ''))
        
        # Format currency
        sales_price = format_currency(row.get('Sales_Price', 0))
        cost_basis = format_currency(row.get('Cost_Basis', 0))
        gain_loss = format_currency(row.get('Gain_Loss', 0))
        
        # Adjustment fields
        adj_code = str(row.get('Adjustment_Code', ''))
        adj_amount = format_currency(row.get('Adjustment_Amount', 0)) if row.get('Adjustment_Amount', 0) != 0 else ''
        
        # Draw row data
        c.drawString(50, y_pos, str(row.get('Description', ''))[:25])  # Truncate if too long
        c.drawString(170, y_pos, date_acquired)
        c.drawString(235, y_pos, date_sold)
        c.drawRightString(345, y_pos, sales_price)
        c.drawRightString(400, y_pos, cost_basis)
        c.drawString(415, y_pos, adj_code)
        c.drawRightString(445, y_pos, adj_amount)
        c.drawRightString(495, y_pos, cost_basis)  # Adjusted basis
        c.drawRightString(545, y_pos, gain_loss)
        
        y_pos -= 20
    
    # Page footer
    c.setFont("Helvetica", 8)
    c.drawString(50, 50, f"Form 8949 (2023) - Page {page_number}")
    c.drawRightString(width - 50, 50, f"Generated: {datetime.now().strftime('%m/%d/%Y')}")
    
    # Totals section at bottom (if this is the last page)
    if len(df) <= 14:  # Single page or last page
        y_pos = 120
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, y_pos, "Totals:")
        
        total_proceeds = pd.to_numeric(df['Sales_Price'], errors='coerce').sum()
        total_basis = pd.to_numeric(df['Cost_Basis'], errors='coerce').sum()
        total_gain_loss = pd.to_numeric(df['Gain_Loss'], errors='coerce').sum()
        
        c.drawRightString(345, y_pos, format_currency(total_proceeds))
        c.drawRightString(400, y_pos, format_currency(total_basis))
        c.drawRightString(545, y_pos, format_currency(total_gain_loss))
        
        # Draw line above totals
        c.line(300, y_pos + 5, 545, y_pos + 5)
    
    c.save()

def format_date(date_str):
    """Format date string for Form 8949"""
    if pd.isna(date_str) or date_str == '':
        return ''
    
    try:
        # Try to parse various date formats
        if '/' in str(date_str):
            return str(date_str)
        elif '-' in str(date_str):
            # Convert from YYYY-MM-DD to MM/DD/YYYY
            date_obj = pd.to_datetime(date_str)
            return date_obj.strftime('%m/%d/%Y')
        else:
            return str(date_str)
    except:
        return str(date_str)

def format_currency(amount):
    """Format currency for Form 8949"""
    try:
        if pd.isna(amount) or amount == 0:
            return ''
        return f"{float(amount):,.2f}"
    except:
        return str(amount)

def create_zip_file(pdf_files):
    """Create a ZIP file containing all PDFs"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for pdf_file in pdf_files:
            zip_file.writestr(pdf_file['filename'], pdf_file['content'])
    return zip_buffer.getvalue()

if __name__ == "__main__":
    main()