import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import zipfile
from datetime import datetime
import re

def main():
    st.set_page_config(
        page_title="Crypto Actions to Form 8949 Converter",
        page_icon="₿",
        layout="wide"
    )
    
    st.title("₿ Crypto Actions to Form 8949 Converter")
    st.markdown("Upload your crypto actions/transactions report and get either a tax software CSV or completed Form 8949 PDF.")
    
    # Information section
    with st.expander("ℹ️ How This Works", expanded=False):
        st.markdown("""
        **This tool does everything for you:**
        
        1. **Upload** your crypto actions report (CSV from exchanges, tax software, etc.)
        2. **Extract** and convert transaction data automatically
        3. **Choose** your output:
           - **CSV file** → Upload to TurboTax, TaxAct, FreeTaxUSA, etc.
           - **PDF file** → Print and mail directly to IRS
        
        **Supported formats:**
        - Exchange export files (Coinbase, Binance, etc.)
        - Tax software reports
        - Custom transaction files
        - Actions reports (like yours)
        """)
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # Form type selection
    form_type = st.sidebar.selectbox(
        "Form 8949 Type:",
        [
            "Part I - Short-term (Box A) - Basis reported to IRS",
            "Part I - Short-term (Box B) - Basis NOT reported to IRS", 
            "Part I - Short-term (Box C) - Various situations",
            "Part II - Long-term (Box A) - Basis reported to IRS",
            "Part II - Long-term (Box B) - Basis NOT reported to IRS",
            "Part II - Long-term (Box C) - Various situations"
        ],
        index=1,  # Default to most common for crypto
        help="Most crypto transactions use 'Part I (Box B)' - short-term, basis not reported"
    )
    
    # Taxpayer information for PDF generation
    st.sidebar.subheader("Taxpayer Information")
    taxpayer_name = st.sidebar.text_input("Full Name", placeholder="Jenny L")
    taxpayer_ssn = st.sidebar.text_input("Social Security Number", placeholder="XXX-XX-XXXX")
    
    # Main content area
    st.header("🗓️ Step 1: Select Tax Year")
    
    # Tax year selection in main area
    col_year1, col_year2, col_year3 = st.columns([1, 2, 1])
    with col_year2:
        tax_year = st.selectbox(
            "Choose the tax year you're filing for:",
            [2023, 2022, 2021, 2020, 2019, 2018],
            index=1,  # Default to 2022
            help="Select the tax year to extract transactions for",
            key="main_tax_year"
        )
        
        st.info(f"📅 Processing transactions for tax year **{tax_year}**")
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("Step 2: Upload Your Actions Report")
        
        uploaded_file = st.file_uploader(
            "Choose your crypto actions/transactions file",
            type=["csv", "xlsx", "xls"],
            help="Upload your crypto transaction report from exchanges, tax software, or accounting systems"
        )
        
        if uploaded_file is not None:
            try:
                # Read the file
                if uploaded_file.name.endswith('.csv'):
                    df_raw = pd.read_csv(uploaded_file)
                else:
                    df_raw = pd.read_excel(uploaded_file)
                
                st.success(f"✅ File uploaded successfully! Found {len(df_raw)} rows.")
                
                # Show raw data preview
                with st.expander("📋 Raw Data Preview", expanded=False):
                    st.dataframe(df_raw.head(10))
                
                # Auto-detect and extract transactions
                transactions = extract_crypto_transactions(df_raw, tax_year)
                
                if transactions:
                    st.success(f"🎯 Extracted {len(transactions)} transactions for {tax_year}!")
                    
                    # Show extracted transactions
                    st.subheader(f"{tax_year} Crypto Transactions")
                    
                    # Create display dataframe
                    display_df = pd.DataFrame(transactions)
                    display_df['Gain/Loss'] = display_df['Proceeds'] - display_df['Cost_Basis']
                    
                    # Format for display
                    display_df['Proceeds'] = display_df['Proceeds'].apply(lambda x: f"${x:,.2f}")
                    display_df['Cost_Basis'] = display_df['Cost_Basis'].apply(lambda x: f"${x:,.2f}")
                    display_df['Gain/Loss'] = display_df['Gain/Loss'].apply(lambda x: f"${x:,.2f}")
                    
                    st.dataframe(display_df)
                    
                    # Show summary
                    total_proceeds = sum(t['Proceeds'] for t in transactions)
                    total_basis = sum(t['Cost_Basis'] for t in transactions)
                    total_gain_loss = total_proceeds - total_basis
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Total Proceeds", f"${total_proceeds:,.2f}")
                    with col_b:
                        st.metric("Total Cost Basis", f"${total_basis:,.2f}")
                    with col_c:
                        color = "normal" if total_gain_loss >= 0 else "inverse"
                        st.metric("Net Gain/Loss", f"${total_gain_loss:,.2f}")
                
                else:
                    st.error("❌ No crypto transactions found for the selected year. Please check your file format.")
                    transactions = None
                
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
                transactions = None
        else:
            transactions = None
    
    with col2:
        st.header("Step 3: Choose Your Output")
        
        if transactions:
            # Output format selection
            output_format = st.radio(
                "What do you want to generate?",
                [
                    "📊 CSV file for tax software (TurboTax, TaxAct, etc.)",
                    "📄 Complete Form 8949 PDF for IRS filing"
                ],
                help="Choose based on how you plan to file your taxes"
            )
            
            # Generate button
            if st.button("🚀 Generate Files", type="primary"):
                try:
                    if "CSV" in output_format:
                        # Generate CSV for tax software
                        csv_data = generate_tax_software_csv(transactions, tax_year)
                        
                        filename = f"form_8949_{tax_year}_crypto_transactions.csv"
                        st.download_button(
                            label="📥 Download CSV for Tax Software",
                            data=csv_data,
                            file_name=filename,
                            mime="text/csv",
                            help="Upload this file to TurboTax, TaxAct, FreeTaxUSA, or other tax software"
                        )
                        
                        st.success("✅ CSV file ready! This can be imported into most tax software.")
                        
                        # Show instructions
                        with st.expander("📖 Tax Software Instructions"):
                            st.markdown("""
                            **For TurboTax:**
                            1. Go to Federal Taxes → Wages & Income → Investment Income
                            2. Select "Stocks, Mutual Funds, Bonds, Other"
                            3. Choose "Import from CSV" or "Enter manually"
                            4. Upload your downloaded CSV file
                            
                            **For TaxAct:**
                            1. Go to Federal Return → Income → Investment Income
                            2. Select "Capital Gains and Losses"
                            3. Choose "Import transactions" 
                            4. Upload your CSV file
                            
                            **For FreeTaxUSA:**
                            1. Go to Income → Investment Income → Capital Gains/Losses
                            2. Select "Import from file"
                            3. Upload your CSV
                            """)
                    
                    else:
                        # Generate PDF Form 8949
                        if not taxpayer_name or not taxpayer_ssn:
                            st.error("⚠️ Please fill in your taxpayer information in the sidebar to generate a PDF.")
                        else:
                            pdf_files = generate_form_8949_pdf(
                                transactions, 
                                form_type, 
                                taxpayer_name, 
                                taxpayer_ssn, 
                                tax_year
                            )
                            
                            if len(pdf_files) == 1:
                                # Single PDF
                                st.download_button(
                                    label="📥 Download Form 8949 PDF",
                                    data=pdf_files[0]['content'],
                                    file_name=pdf_files[0]['filename'],
                                    mime="application/pdf",
                                    help="Print this PDF and mail to the IRS with your tax return"
                                )
                            else:
                                # Multiple PDFs in ZIP
                                zip_data = create_zip_file(pdf_files)
                                st.download_button(
                                    label="📦 Download All Form 8949 PDFs (ZIP)",
                                    data=zip_data,
                                    file_name=f"form_8949_{tax_year}_complete.zip",
                                    mime="application/zip"
                                )
                            
                            st.success(f"✅ Generated {len(pdf_files)} Form 8949 PDF(s)!")
                            
                            # Show filing instructions
                            with st.expander("📮 IRS Filing Instructions"):
                                st.markdown(f"""
                                **Your Form 8949 is ready for {tax_year} taxes:**
                                
                                1. **Print** the PDF(s) on white paper
                                2. **Sign** your tax return (Form 1040)
                                3. **Attach** Form 8949 to your return
                                4. **Mail** to the IRS address for your state
                                
                                **Important:**
                                - Keep copies for your records
                                - Form 8949 must be filed with Form 1040
                                - Include Schedule D if you have other capital gains/losses
                                
                                **Net result for {tax_year}:** ${total_gain_loss:,.2f} {"gain" if total_gain_loss >= 0 else "loss"}
                                """)
                
                except Exception as e:
                    st.error(f"Error generating files: {str(e)}")
        
        else:
            st.info("👆 Please upload your crypto actions file first.")
            
            # Show sample file format
            with st.expander("📋 Sample File Formats"):
                st.markdown("""
                **Your file should contain transaction data like:**
                
                **Option A - Actions Report (like yours):**
                ```
                Row Labels, Sum of costBasisRelieved, Sum of proceeds
                2022,,
                BTC, 4287538.11, 4286732.78
                ETH, 130607.70, 127257.06
                ```
                
                **Option B - Transaction List:**
                ```
                Asset, Date, Type, Amount, Price, Total
                BTC, 2022-03-15, SELL, 1.5, 45000, 67500
                ETH, 2022-06-20, SELL, 10, 1800, 18000
                ```
                
                **Option C - Exchange Export:**
                ```
                Date, Pair, Side, Amount, Price, Fee, Total
                2022-01-15, BTC/USD, SELL, 0.5, 42000, 25, 20975
                ```
                """)

def extract_crypto_transactions(df, target_year):
    """Extract crypto transactions from various file formats"""
    transactions = []
    
    # Method 1: Actions report format (like Jenny's file)
    if 'Row Labels' in df.columns:
        transactions = extract_from_actions_report(df, target_year)
    
    # Method 2: Standard transaction format
    elif any(col.lower() in ['date', 'timestamp', 'time'] for col in df.columns):
        transactions = extract_from_transaction_list(df, target_year)
    
    # Method 3: Exchange export format
    elif any(col.lower() in ['pair', 'symbol', 'asset'] for col in df.columns):
        transactions = extract_from_exchange_export(df, target_year)
    
    return transactions

def extract_from_actions_report(df, target_year):
    """Extract from actions report format (like Jenny's file)"""
    transactions = []
    current_year = None
    
    # Find cost basis and proceeds columns
    cost_col = None
    proceeds_col = None
    
    for col in df.columns:
        if 'cost' in col.lower() or 'basis' in col.lower():
            cost_col = col
        elif 'proceed' in col.lower() or 'sales' in col.lower():
            proceeds_col = col
    
    if not cost_col or not proceeds_col:
        return transactions
    
    for _, row in df.iterrows():
        row_label = row.get('Row Labels', '')
        cost_basis = row.get(cost_col, '')
        proceeds = row.get(proceeds_col, '')
        
        # Check if this is a year row
        if isinstance(row_label, (int, float)) and 2015 <= row_label <= 2030:
            current_year = int(row_label)
        
        # Check if this is a transaction row for our target year
        elif (current_year == target_year and 
              isinstance(row_label, str) and 
              row_label.strip() and
              cost_basis and proceeds and
              'total' not in row_label.lower() and
              'grand' not in row_label.lower()):
            
            try:
                # Clean and parse amounts
                clean_cost = clean_currency(cost_basis)
                clean_proceeds = clean_currency(proceeds)
                
                if clean_cost > 0 or clean_proceeds > 0:
                    transactions.append({
                        'Description': f"{row_label.strip()} cryptocurrency",
                        'Date_Acquired': f"01/01/{target_year}",
                        'Date_Sold': f"12/31/{target_year}",
                        'Proceeds': clean_proceeds,
                        'Cost_Basis': clean_cost,
                        'Asset': row_label.strip()
                    })
            except:
                continue
    
    return transactions

def extract_from_transaction_list(df, target_year):
    """Extract from standard transaction list format"""
    transactions = []
    
    # Find relevant columns
    date_col = find_column(df, ['date', 'timestamp', 'time'])
    asset_col = find_column(df, ['asset', 'symbol', 'coin', 'currency', 'crypto'])
    amount_col = find_column(df, ['amount', 'quantity', 'volume'])
    price_col = find_column(df, ['price', 'rate', 'value'])
    total_col = find_column(df, ['total', 'proceeds', 'usd_value'])
    cost_col = find_column(df, ['cost', 'basis', 'cost_basis'])
    
    if not date_col or not asset_col:
        return transactions
    
    for _, row in df.iterrows():
        try:
            # Parse date
            date_str = str(row[date_col])
            if str(target_year) in date_str:
                asset = str(row[asset_col]).strip()
                
                # Calculate proceeds and cost basis
                proceeds = 0
                cost_basis = 0
                
                if total_col:
                    proceeds = clean_currency(row[total_col])
                elif amount_col and price_col:
                    amount = clean_currency(row[amount_col])
                    price = clean_currency(row[price_col])
                    proceeds = amount * price
                
                if cost_col:
                    cost_basis = clean_currency(row[cost_col])
                else:
                    cost_basis = proceeds * 0.9  # Estimate if not provided
                
                if proceeds > 0:
                    transactions.append({
                        'Description': f"{asset} cryptocurrency",
                        'Date_Acquired': f"01/01/{target_year}",
                        'Date_Sold': date_str[:10] if len(date_str) >= 10 else f"12/31/{target_year}",
                        'Proceeds': proceeds,
                        'Cost_Basis': cost_basis,
                        'Asset': asset
                    })
        except:
            continue
    
    return transactions

def extract_from_exchange_export(df, target_year):
    """Extract from exchange export format"""
    # Similar logic to transaction list but with exchange-specific columns
    return extract_from_transaction_list(df, target_year)

def find_column(df, possible_names):
    """Find column by possible names"""
    for col in df.columns:
        for name in possible_names:
            if name.lower() in col.lower():
                return col
    return None

def clean_currency(value):
    """Clean currency values"""
    if pd.isna(value) or value == '':
        return 0.0
    
    # Convert to string and clean
    str_val = str(value).strip()
    str_val = re.sub(r'[,$"\s]', '', str_val)
    str_val = str_val.replace('(', '-').replace(')', '')
    
    try:
        return float(str_val)
    except:
        return 0.0

def generate_tax_software_csv(transactions, tax_year):
    """Generate CSV for tax software import"""
    
    # Create Form 8949 compatible format
    csv_data = []
    csv_data.append("Description,Date Acquired,Date Sold,Sales Price,Cost Basis,Gain/Loss,Adjustment Code,Adjustment Amount")
    
    for transaction in transactions:
        gain_loss = transaction['Proceeds'] - transaction['Cost_Basis']
        
        row = [
            transaction['Description'],
            transaction['Date_Acquired'],
            transaction['Date_Sold'],
            f"{transaction['Proceeds']:.2f}",
            f"{transaction['Cost_Basis']:.2f}",
            f"{gain_loss:.2f}",
            "",  # Adjustment Code
            "0.00"  # Adjustment Amount
        ]
        csv_data.append(",".join(row))
    
    return "\n".join(csv_data)

def generate_form_8949_pdf(transactions, form_type, taxpayer_name, taxpayer_ssn, tax_year):
    """Generate completed Form 8949 PDF"""
    pdf_files = []
    
    # Split transactions into pages (14 per page max)
    transactions_per_page = 14
    total_pages = (len(transactions) + transactions_per_page - 1) // transactions_per_page
    
    for page_num in range(total_pages):
        start_idx = page_num * transactions_per_page
        end_idx = min(start_idx + transactions_per_page, len(transactions))
        page_transactions = transactions[start_idx:end_idx]
        
        # Create PDF for this page
        buffer = io.BytesIO()
        create_form_8949_page(buffer, page_transactions, form_type, taxpayer_name, taxpayer_ssn, tax_year, page_num + 1, total_pages)
        
        # Generate filename
        if total_pages == 1:
            filename = f"Form_8949_{tax_year}_{taxpayer_name.replace(' ', '_')}.pdf"
        else:
            filename = f"Form_8949_{tax_year}_{taxpayer_name.replace(' ', '_')}_Page_{page_num + 1}.pdf"
        
        pdf_files.append({
            'filename': filename,
            'content': buffer.getvalue()
        })
    
    return pdf_files

def create_form_8949_page(buffer, transactions, form_type, taxpayer_name, taxpayer_ssn, tax_year, page_number, total_pages):
    """Create a single Form 8949 PDF page"""
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Form header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Form 8949")
    c.setFont("Helvetica", 10)
    c.drawString(150, height - 50, "Sales and Other Dispositions of Capital Assets")
    c.drawRightString(width - 50, height - 50, f"{tax_year}")
    
    # Taxpayer information
    c.setFont("Helvetica", 9)
    c.drawString(50, height - 80, f"Name(s) shown on return: {taxpayer_name}")
    c.drawString(50, height - 95, f"Your social security number: {taxpayer_ssn}")
    
    # Form type and checkboxes
    y_pos = height - 130
    c.setFont("Helvetica-Bold", 10)
    
    if "Part I" in form_type:
        c.drawString(50, y_pos, "Part I - Short-Term Capital Gains and Losses - Generally for assets held one year or less")
    else:
        c.drawString(50, y_pos, "Part II - Long-Term Capital Gains and Losses - Generally for assets held more than one year")
    
    # Checkbox selection
    y_pos -= 25
    c.setFont("Helvetica", 9)
    
    if "Box A" in form_type:
        c.drawString(50, y_pos, "☑ (A) Short-term transactions reported on Form(s) 1099-B showing basis was reported to the IRS")
        c.drawString(50, y_pos - 12, "☐ (B) Short-term transactions reported on Form(s) 1099-B showing basis was NOT reported to the IRS")
        c.drawString(50, y_pos - 24, "☐ (C) Short-term transactions not reported to you on Form 1099-B")
    elif "Box B" in form_type:
        c.drawString(50, y_pos, "☐ (A) Short-term transactions reported on Form(s) 1099-B showing basis was reported to the IRS")
        c.drawString(50, y_pos - 12, "☑ (B) Short-term transactions reported on Form(s) 1099-B showing basis was NOT reported to the IRS")
        c.drawString(50, y_pos - 24, "☐ (C) Short-term transactions not reported to you on Form 1099-B")
    else:  # Box C
        c.drawString(50, y_pos, "☐ (A) Short-term transactions reported on Form(s) 1099-B showing basis was reported to the IRS")
        c.drawString(50, y_pos - 12, "☐ (B) Short-term transactions reported on Form(s) 1099-B showing basis was NOT reported to the IRS")
        c.drawString(50, y_pos - 24, "☑ (C) Short-term transactions not reported to you on Form 1099-B")
    
    # Column headers
    y_pos = height - 200
    c.setFont("Helvetica-Bold", 8)
    
    headers = [
        ("(a) Description of property", 50),
        ("(b) Date acquired", 170),
        ("(c) Date sold or", 235),
        ("(d) Proceeds", 300),
        ("(e) Cost or other", 360),
        ("(f) Code(s)", 415),
        ("(g) Amount of", 445),
        ("(h) Gain or (loss)", 500)
    ]
    
    for header, x_pos in headers:
        c.drawString(x_pos, y_pos, header)
    
    # Sub-headers
    y_pos -= 10
    c.setFont("Helvetica", 7)
    c.drawString(235, y_pos, "disposed of")
    c.drawString(360, y_pos, "basis")
    c.drawString(415, y_pos, "from Form(s)")
    c.drawString(445, y_pos, "adjustment")
    c.drawString(500, y_pos, "Subtract column (g)")
    c.drawString(500, y_pos - 8, "from column (d) and")
    c.drawString(500, y_pos - 16, "combine the result")
    c.drawString(500, y_pos - 24, "with column (e)")
    
    # Draw line under headers
    y_pos -= 30
    c.line(50, y_pos, width - 50, y_pos)
    
    # Transaction data
    y_pos -= 15
    c.setFont("Helvetica", 8)
    
    for transaction in transactions:
        if y_pos < 150:  # Check if we need space for totals
            break
        
        gain_loss = transaction['Proceeds'] - transaction['Cost_Basis']
        
        # Draw transaction data
        c.drawString(50, y_pos, transaction['Description'][:30])  # Truncate if too long
        c.drawString(170, y_pos, transaction['Date_Acquired'])
        c.drawString(235, y_pos, transaction['Date_Sold'])
        c.drawRightString(355, y_pos, f"{transaction['Proceeds']:,.2f}")
        c.drawRightString(410, y_pos, f"{transaction['Cost_Basis']:,.2f}")
        c.drawString(420, y_pos, "")  # Adjustment code (blank)
        c.drawRightString(480, y_pos, "")  # Adjustment amount (blank)
        c.drawRightString(545, y_pos, f"{gain_loss:,.2f}")
        
        y_pos -= 18
    
    # Totals section
    if page_number == total_pages:  # Only show totals on last page
        y_pos = 120
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, y_pos, f"Totals for all {len(transactions)} transactions:")
        
        total_proceeds = sum(t['Proceeds'] for t in transactions)
        total_basis = sum(t['Cost_Basis'] for t in transactions)
        total_gain_loss = total_proceeds - total_basis
        
        c.drawRightString(355, y_pos, f"{total_proceeds:,.2f}")
        c.drawRightString(410, y_pos, f"{total_basis:,.2f}")
        c.drawRightString(545, y_pos, f"{total_gain_loss:,.2f}")
        
        # Draw line above totals
        c.line(300, y_pos + 5, 545, y_pos + 5)
    
    # Page footer
    c.setFont("Helvetica", 8)
    if total_pages > 1:
        c.drawString(50, 30, f"Form 8949 ({tax_year}) - Page {page_number} of {total_pages}")
    else:
        c.drawString(50, 30, f"Form 8949 ({tax_year})")
    
    c.drawRightString(width - 50, 30, f"Generated: {datetime.now().strftime('%m/%d/%Y')}")
    
    c.save()

def create_zip_file(pdf_files):
    """Create a ZIP file containing all PDFs"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for pdf_file in pdf_files:
            zip_file.writestr(pdf_file['filename'], pdf_file['content'])
    return zip_buffer.getvalue()

if __name__ == "__main__":
    main()
