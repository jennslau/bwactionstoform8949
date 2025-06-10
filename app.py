try:
                        if "CSV" in output_format:
                            # Generate CSV for tax software
                            csv_data = generate_tax_software_csv(transactions, tax_year)
                            
                            filename = f"form_8949_{tax_year}_bitwave_transactions.csv"
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
                                # Split by term type if needed
                                short_term_txns = [t for t in transactions if t['is_short_term']]
                                long_term_txns = [t for t in transactions if not t['is_short_term']]
                                
                                pdf_files = []
                                
                                # Generate short-term PDF if applicable
                                if short_term_txns:
                                    short_form_type = form_type.replace("Part II", "Part I").replace("Long-term", "Short-term")
                                    short_pdfs = generate_form_8949_pdf(
                                        short_term_txns, 
                                        short_form_type, 
                                        taxpayer_name, 
                                        taxpayer_ssn, 
                                        tax_year,
                                        "Short-term"
                                    )
                                    pdf_files.extend(short_pdfs)
                                
                                # Generate long-term PDF if applicable
                                if long_term_txns:
                                    long_form_type = form_type.replace("Part I", "Part II").replace("Short-term", "Long-term")
                                    long_pdfs = generate_form_8949_pdf(
                                        long_term_txns, 
                                        long_form_type, 
                                        taxpayer_name, 
                                        taxpayer_ssn, 
                                        tax_year,
                                        "Long-term"
                                    )
                                    pdf_files.extend(long_pdfs)
                                
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
                                
                                # Show PDF generation status
                                with st.expander("📋 PDF Generation Details", expanded=False):
                                    st.markdown(f"""
                                    **Form Details:**
                                    - **Tax Year:** {tax_year}
                                    - **Form Type:** {form_type}
                                    - **Template:** Official IRS Form 8949 ({tax_year})
                                    - **Transactions:** {len(transactions)}
                                    - **Pages Generated:** {len(pdf_files)}
                                    
                                    **Transaction Breakdown:**
                                    - Short-term: {short_term_count}
                                    - Long-term: {long_term_count}
                                    
                                    **Using official IRS Form 8949 template for {tax_year} as the base.**
                                    """)
                                
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
            st.info("👆 Please upload your Bitwave actions file first.")
            
            # Show sample file format
            with st.expander("📋 Bitwave Actions Report Format"):
                st.markdown("""
                **Your Bitwave actions CSV should contain these columns:**
                
                ```
                action, asset, timestamp, lotId, proceeds, costBasisRelieved, 
                shortTermGainLoss, longTermGainLoss, costBasisAcquired, ...
                ```
                
                **Key fields used:**
                - **action:** "buy" or "sell"
                - **asset:** "BTC", "ETH", "ADA", etc.
                - **timestamp:** Transaction date/time
                - **lotId:** Unique identifier linking buy/sell transactions
                - **proceeds:** Sales proceeds (column R)
                - **costBasisRelieved:** Cost basis for this sale (column W)
                - **shortTermGainLoss/longTermGainLoss:** For validation
                
                **To export from Bitwave:**
                1. Go to your Actions report
                2. Set date range for desired tax year
                3. Export as CSV
                4. Upload the CSV file here
                
                **Note:** This tool uses the official IRS Form 8949 template for the selected tax year, 
                ensuring your forms meet current IRS formatting requirements.
                """)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import zipfile
from datetime import datetime
import re
import requests
import PyPDF2
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def main():
    st.set_page_config(
        page_title="Bitwave Actions to Form 8949 Converter",
        page_icon="₿",
        layout="wide"
    )
    
    # Custom CSS for Bitwave styling and centering
    st.markdown("""
    <style>
    /* Bitwave color scheme */
    :root {
        --bitwave-blue: #1B9CFC;
        --bitwave-green: #00D2B8;
        --bitwave-dark: #2C3E50;
    }
    
    /* Header styling */
    .main-header {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1rem 0;
        background: linear-gradient(135deg, var(--bitwave-blue) 0%, var(--bitwave-green) 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        color: white !important;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
        text-align: center;
    }
    
    .bitwave-logo {
        font-size: 3rem;
        font-weight: bold;
        margin-right: 1rem;
        background: linear-gradient(45deg, var(--bitwave-blue), var(--bitwave-green));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Center all step containers */
    .step-container {
        display: flex;
        justify-content: center;
        margin: 2rem 0;
    }
    
    .step-content {
        max-width: 800px;
        width: 100%;
        text-align: center;
    }
    
    /* Center step headers */
    .step-header {
        text-align: center;
        color: var(--bitwave-dark);
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid var(--bitwave-green);
        display: inline-block;
    }
    
    /* Style buttons with Bitwave colors */
    .stButton > button {
        background: linear-gradient(135deg, var(--bitwave-blue) 0%, var(--bitwave-green) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* Style info boxes */
    .stInfo {
        background: linear-gradient(135deg, rgba(27, 156, 252, 0.1) 0%, rgba(0, 210, 184, 0.1) 100%);
        border-left: 4px solid var(--bitwave-green);
    }
    
    /* Style success boxes */
    .stSuccess {
        background: rgba(0, 210, 184, 0.1);
        border-left: 4px solid var(--bitwave-green);
    }
    
    /* Center selectbox */
    .stSelectbox {
        display: flex;
        justify-content: center;
    }
    
    /* Center file uploader */
    .stFileUploader {
        display: flex;
        justify-content: center;
    }
    
    /* Center metrics */
    [data-testid="metric-container"] {
        background: rgba(27, 156, 252, 0.05);
        border: 1px solid rgba(27, 156, 252, 0.2);
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Center radio buttons */
    .stRadio {
        display: flex;
        justify-content: center;
    }
    
    .stRadio > div {
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with Bitwave branding
    st.markdown("""
    <div class="main-header">
        <div class="bitwave-logo">BITWAVE</div>
        <h1>Actions to Form 8949 Converter</h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("Convert your Bitwave actions report into tax-ready formats with official IRS Form 8949 templates.")
    
    # Information section
    with st.expander("ℹ️ How This Works", expanded=False):
        st.markdown("""
        **This tool is specifically designed for Bitwave actions reports:**
        
        1. **Upload** your Bitwave actions CSV export
        2. **Automatically extracts** sell transactions with proper lot matching
        3. **Maps acquisition dates** using lot IDs from buy transactions
        4. **Validates calculations** against Bitwave's short/long-term gain/loss columns
        5. **Choose output:**
           - **CSV file** → Upload to TurboTax, TaxAct, FreeTaxUSA, etc.
           - **PDF file** → Official IRS Form 8949 ready for direct filing
        
        **Required Bitwave columns:**
        - `action` (buy/sell)
        - `asset` (BTC, ETH, etc.)
        - `timestamp` (transaction date)
        - `lotId` (for matching buy/sell pairs)
        - `proceeds` (column R)
        - `costBasisRelieved` (column W)
        - `shortTermGainLoss` and `longTermGainLoss` (for validation)
        """)
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # Form type selection
    form_type = st.sidebar.selectbox(
        "Form 8949 Type:",
        [
            "Part I - Short-term (Box B) - Basis NOT reported to IRS", 
            "Part I - Short-term (Box A) - Basis reported to IRS",
            "Part I - Short-term (Box C) - Various situations",
            "Part II - Long-term (Box B) - Basis NOT reported to IRS",
            "Part II - Long-term (Box A) - Basis reported to IRS",
            "Part II - Long-term (Box C) - Various situations"
        ],
        index=0,  # Default to most common for crypto
        help="Most crypto transactions use 'Part I (Box B)' - short-term, basis not reported"
    )
    
    # Taxpayer information for PDF generation
    st.sidebar.subheader("Taxpayer Information")
    taxpayer_name = st.sidebar.text_input("Full Name", placeholder="Jenny L")
    taxpayer_ssn = st.sidebar.text_input("Social Security Number", placeholder="XXX-XX-XXXX")
    
    # Step 1: Tax Year Selection (Centered)
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    st.markdown('<div class="step-content">', unsafe_allow_html=True)
    st.markdown('<h2 class="step-header">🗓️ Step 1: Select Tax Year</h2>', unsafe_allow_html=True)
    
    # Centered tax year selection
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        tax_year = st.selectbox(
            "Choose the tax year you're filing for:",
            [2023, 2022, 2021, 2020, 2019, 2018],
            index=1,  # Default to 2022
            help="Select the tax year to extract transactions for",
            key="main_tax_year"
        )
        
        st.info(f"📅 Processing transactions for tax year **{tax_year}**")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Step 2: Upload File (Centered)
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    st.markdown('<div class="step-content">', unsafe_allow_html=True)
    st.markdown('<h2 class="step-header">📂 Step 2: Upload Bitwave Actions Report</h2>', unsafe_allow_html=True)
    
    # Centered file uploader
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        uploaded_file = st.file_uploader(
            "Choose your Bitwave actions CSV file",
            type=["csv"],
            help="Upload the CSV export from your Bitwave actions report"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
        
        
        if uploaded_file is not None:
            # Centered processing section
            st.markdown('<div class="step-container">', unsafe_allow_html=True)
            st.markdown('<div class="step-content">', unsafe_allow_html=True)
            
            try:
                # Read the Bitwave actions file
                df_raw = pd.read_csv(uploaded_file)
                
                st.success(f"✅ Bitwave actions file uploaded! Found {len(df_raw)} total actions.")
                
                # Validate it's a Bitwave file
                required_columns = ['action', 'asset', 'timestamp', 'lotId', ' proceeds ', ' costBasisRelieved ']
                missing_columns = [col for col in required_columns if col not in df_raw.columns]
                
                if missing_columns:
                    st.error(f"❌ This doesn't appear to be a valid Bitwave actions report.")
                    st.error(f"Missing columns: {', '.join(missing_columns)}")
                    st.info("Please ensure you've uploaded the correct Bitwave actions CSV export.")
                    transactions = None
                else:
                    # Extract transactions using Bitwave-specific logic
                    transactions = extract_bitwave_transactions(df_raw, tax_year)
                    
                    if transactions:
                        st.success(f"🎯 Extracted {len(transactions)} sell transactions for {tax_year}!")
                        
                        # Show extracted transactions summary
                        st.markdown(f'<h3 style="text-align: center; color: var(--bitwave-dark);">{tax_year} Crypto Sales Summary</h3>', unsafe_allow_html=True)
                        
                        # Create summary by asset
                        asset_summary = {}
                        for txn in transactions:
                            asset = txn['asset']
                            if asset not in asset_summary:
                                asset_summary[asset] = {
                                    'count': 0,
                                    'proceeds': 0,
                                    'cost_basis': 0,
                                    'gain_loss': 0
                                }
                            asset_summary[asset]['count'] += 1
                            asset_summary[asset]['proceeds'] += txn['proceeds']
                            asset_summary[asset]['cost_basis'] += txn['cost_basis']
                            asset_summary[asset]['gain_loss'] += txn['gain_loss']
                        
                        # Display asset summary
                        summary_data = []
                        for asset, data in asset_summary.items():
                            summary_data.append({
                                'Asset': asset,
                                'Transactions': data['count'],
                                'Total Proceeds': f"${data['proceeds']:,.2f}",
                                'Total Cost Basis': f"${data['cost_basis']:,.2f}",
                                'Net Gain/Loss': f"${data['gain_loss']:,.2f}"
                            })
                        
                        summary_df = pd.DataFrame(summary_data)
                        st.dataframe(summary_df, use_container_width=True)
                        
                        # Show overall totals in centered metrics
                        total_proceeds = sum(t['proceeds'] for t in transactions)
                        total_basis = sum(t['cost_basis'] for t in transactions)
                        total_gain_loss = sum(t['gain_loss'] for t in transactions)
                        
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Total Proceeds", f"${total_proceeds:,.2f}")
                        with col_b:
                            st.metric("Total Cost Basis", f"${total_basis:,.2f}")
                        with col_c:
                            st.metric("Net Gain/Loss", f"${total_gain_loss:,.2f}")
                        
                        # Show detailed transactions in expander
                        with st.expander(f"📋 View All {len(transactions)} Transactions", expanded=False):
                            display_transactions = []
                            for i, txn in enumerate(transactions[:100]):  # Limit display to first 100
                                display_transactions.append({
                                    '#': i + 1,
                                    'Asset': txn['asset'],
                                    'Sell Date': txn['date_sold'].strftime('%m/%d/%Y'),
                                    'Buy Date': txn['date_acquired'].strftime('%m/%d/%Y') if txn['date_acquired'] else 'Unknown',
                                    'Proceeds': f"${txn['proceeds']:.2f}",
                                    'Cost Basis': f"${txn['cost_basis']:.2f}",
                                    'Gain/Loss': f"${txn['gain_loss']:.2f}",
                                    'Term': 'Short' if txn['is_short_term'] else 'Long'
                                })
                            
                            txn_df = pd.DataFrame(display_transactions)
                            st.dataframe(txn_df, use_container_width=True)
                            
                            if len(transactions) > 100:
                                st.info(f"Showing first 100 transactions. Total: {len(transactions)}")
                    
                    else:
                        st.error(f"❌ No sell transactions found for {tax_year}. Please check your selected year.")
                        transactions = None
                
            except Exception as e:
                st.error(f"Error reading Bitwave file: {str(e)}")
                transactions = None
                
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            transactions = None
    
    # Step 3: Choose Output (Centered)
    if uploaded_file is not None:
        st.markdown("---")
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        st.markdown('<div class="step-content">', unsafe_allow_html=True)
        st.markdown('<h2 class="step-header">🎯 Step 3: Choose Your Output</h2>', unsafe_allow_html=True)
        
        if transactions:
            # Centered output format selection
            col_left, col_center, col_right = st.columns([1, 2, 1])
            with col_center:
                output_format = st.radio(
                    "What do you want to generate?",
                    [
                        "📊 CSV file for tax software (TurboTax, TaxAct, etc.)",
                        "📄 Complete Form 8949 PDF for IRS filing"
                    ],
                    help="Choose based on how you plan to file your taxes"
                )
                
                # Show term breakdown
                short_term_count = sum(1 for t in transactions if t['is_short_term'])
                long_term_count = len(transactions) - short_term_count
                
                if short_term_count > 0 and long_term_count > 0:
                    st.warning(f"⚠️ You have both short-term ({short_term_count}) and long-term ({long_term_count}) transactions. You may need separate Form 8949s for each.")
                
                # Centered generate button
                if st.button("🚀 Generate Files", type="primary"):
                try:
                    if "CSV" in output_format:
                        # Generate CSV for tax software
                        csv_data = generate_tax_software_csv(transactions, tax_year)
                        
                        filename = f"form_8949_{tax_year}_bitwave_transactions.csv"
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
                            # Split by term type if needed
                            short_term_txns = [t for t in transactions if t['is_short_term']]
                            long_term_txns = [t for t in transactions if not t['is_short_term']]
                            
                            pdf_files = []
                            
                            # Generate short-term PDF if applicable
                            if short_term_txns:
                                short_form_type = form_type.replace("Part II", "Part I").replace("Long-term", "Short-term")
                                short_pdfs = generate_form_8949_pdf(
                                    short_term_txns, 
                                    short_form_type, 
                                    taxpayer_name, 
                                    taxpayer_ssn, 
                                    tax_year,
                                    "Short-term"
                                )
                                pdf_files.extend(short_pdfs)
                            
                            # Generate long-term PDF if applicable
                            if long_term_txns:
                                long_form_type = form_type.replace("Part I", "Part II").replace("Short-term", "Long-term")
                                long_pdfs = generate_form_8949_pdf(
                                    long_term_txns, 
                                    long_form_type, 
                                    taxpayer_name, 
                                    taxpayer_ssn, 
                                    tax_year,
                                    "Long-term"
                                )
                                pdf_files.extend(long_pdfs)
                            
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
                            
                            # Show PDF generation status
                            with st.expander("📋 PDF Generation Details", expanded=False):
                                st.markdown(f"""
                                **Form Details:**
                                - **Tax Year:** {tax_year}
                                - **Form Type:** {form_type}
                                - **Template:** Official IRS Form 8949 ({tax_year})
                                - **Transactions:** {len(transactions)}
                                - **Pages Generated:** {len(pdf_files)}
                                
                                **Transaction Breakdown:**
                                - Short-term: {short_term_count}
                                - Long-term: {long_term_count}
                                
                                **Using official IRS Form 8949 template for {tax_year} as the base.**
                                """)
                            
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
            st.info("👆 Please upload your Bitwave actions file first.")
            
            # Show sample file format
            with st.expander("📋 Bitwave Actions Report Format"):
                st.markdown("""
                **Your Bitwave actions CSV should contain these columns:**
                
                ```
                action, asset, timestamp, lotId, proceeds, costBasisRelieved, 
                shortTermGainLoss, longTermGainLoss, costBasisAcquired, ...
                ```
                
                **Key fields used:**
                - **action:** "buy" or "sell"
                - **asset:** "BTC", "ETH", "ADA", etc.
                - **timestamp:** Transaction date/time
                - **lotId:** Unique identifier linking buy/sell transactions
                - **proceeds:** Sales proceeds (column R)
                - **costBasisRelieved:** Cost basis for this sale (column W)
                - **shortTermGainLoss/longTermGainLoss:** For validation
                
                **To export from Bitwave:**
                1. Go to your Actions report
                2. Set date range for desired tax year
                3. Export as CSV
                4. Upload the CSV file here
                """)

def extract_bitwave_transactions(df, target_year):
    """Extract and process transactions from Bitwave actions report"""
    
    # Create lot mapping from buy transactions
    lot_map = {}
    buy_transactions = df[df['action'] == 'buy'].copy()
    
    for _, row in buy_transactions.iterrows():
        if pd.notna(row['lotId']):
            lot_map[row['lotId']] = {
                'buy_date': pd.to_datetime(row['timestamp']),
                'asset': row['asset'],
                'cost_basis_acquired': clean_currency_value(row.get(' costBasisAcquired ', 0))
            }
    
    # Process sell transactions
    sell_transactions = df[df['action'] == 'sell'].copy()
    form8949_transactions = []
    
    for _, row in sell_transactions.iterrows():
        try:
            # Parse sell date
            sell_date = pd.to_datetime(row['timestamp'])
            
            # Filter by target year
            if sell_date.year != target_year:
                continue
            
            # Get lot information
            lot_id = row['lotId']
            lot_info = lot_map.get(lot_id, {})
            buy_date = lot_info.get('buy_date')
            
            # Extract monetary values
            proceeds = clean_currency_value(row.get(' proceeds ', 0))
            cost_basis = clean_currency_value(row.get(' costBasisRelieved ', 0))
            
            # Skip if no meaningful transaction
            if proceeds <= 0 and cost_basis <= 0:
                continue
            
            # Parse gain/loss values for validation
            short_term_gl = clean_currency_value(row.get(' shortTermGainLoss ', 0))
            long_term_gl = clean_currency_value(row.get(' longTermGainLoss ', 0))
            
            # Calculate gain/loss
            calculated_gain_loss = proceeds - cost_basis
            reported_gain_loss = short_term_gl + long_term_gl
            
            # Determine if short-term or long-term
            is_short_term = abs(short_term_gl) > 0.01
            is_long_term = abs(long_term_gl) > 0.01
            
            # If buy date is available, calculate holding period
            if buy_date and sell_date:
                holding_days = (sell_date - buy_date).days
                # Override with actual holding period if available
                if holding_days <= 365:
                    is_short_term = True
                    is_long_term = False
                else:
                    is_short_term = False
                    is_long_term = True
            
            # Create transaction record
            transaction = {
                'asset': row['asset'],
                'description': f"{row['asset']} cryptocurrency",
                'date_acquired': buy_date or sell_date,  # Fallback to sell date if buy not found
                'date_sold': sell_date,
                'proceeds': proceeds,
                'cost_basis': cost_basis,
                'gain_loss': calculated_gain_loss,
                'reported_gain_loss': reported_gain_loss,
                'short_term_gain_loss': short_term_gl,
                'long_term_gain_loss': long_term_gl,
                'is_short_term': is_short_term,
                'is_long_term': is_long_term,
                'lot_id': lot_id
            }
            
            form8949_transactions.append(transaction)
            
        except Exception as e:
            # Skip problematic rows
            continue
    
    return form8949_transactions

def clean_currency_value(value):
    """Clean and parse currency values from Bitwave format"""
    if pd.isna(value) or value == '' or value == '-':
        return 0.0
    
    # Convert to string and clean
    str_val = str(value).strip()
    
    # Handle parentheses for negative values
    is_negative = False
    if '(' in str_val and ')' in str_val:
        is_negative = True
        str_val = str_val.replace('(', '').replace(')', '')
    
    # Remove currency symbols, commas, and spaces
    str_val = re.sub(r'[,$\s]', '', str_val)
    
    try:
        result = float(str_val)
        return -result if is_negative else result
    except:
        return 0.0

def generate_tax_software_csv(transactions, tax_year):
    """Generate CSV for tax software import"""
    
    csv_lines = []
    csv_lines.append("Description,Date Acquired,Date Sold,Sales Price,Cost Basis,Gain/Loss,Adjustment Code,Adjustment Amount")
    
    for transaction in transactions:
        # Format dates
        date_acquired = transaction['date_acquired'].strftime('%m/%d/%Y') if transaction['date_acquired'] else '01/01/2020'
        date_sold = transaction['date_sold'].strftime('%m/%d/%Y')
        
        row = [
            transaction['description'],
            date_acquired,
            date_sold,
            f"{transaction['proceeds']:.2f}",
            f"{transaction['cost_basis']:.2f}",
            f"{transaction['gain_loss']:.2f}",
            "",  # Adjustment Code
            "0.00"  # Adjustment Amount
        ]
        csv_lines.append(",".join(row))
    
    return "\n".join(csv_lines)

def generate_form_8949_pdf(transactions, form_type, taxpayer_name, taxpayer_ssn, tax_year, term_type=""):
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
        create_form_8949_with_official_template(buffer, page_transactions, form_type, taxpayer_name, taxpayer_ssn, tax_year, page_num + 1, total_pages, transactions)
        
        # Generate filename
        term_suffix = f"_{term_type}" if term_type else ""
        if total_pages == 1:
            filename = f"Form_8949_{tax_year}{term_suffix}_{taxpayer_name.replace(' ', '_')}.pdf"
        else:
            filename = f"Form_8949_{tax_year}{term_suffix}_{taxpayer_name.replace(' ', '_')}_Page_{page_num + 1}.pdf"
        
        pdf_files.append({
            'filename': filename,
            'content': buffer.getvalue()
        })
    
    return pdf_files

def get_official_form_8949(tax_year):
    """Fetch the official IRS Form 8949 for the specified tax year"""
    
    # IRS Form 8949 URLs by year
    irs_urls = {
        2024: "https://www.irs.gov/pub/irs-pdf/f8949.pdf",
        2023: "https://www.irs.gov/pub/irs-prior/f8949--2023.pdf", 
        2022: "https://www.irs.gov/pub/irs-prior/f8949--2022.pdf",
        2021: "https://www.irs.gov/pub/irs-prior/f8949--2021.pdf",
        2020: "https://www.irs.gov/pub/irs-prior/f8949--2020.pdf",
        2019: "https://www.irs.gov/pub/irs-prior/f8949--2019.pdf",
        2018: "https://www.irs.gov/pub/irs-prior/f8949--2018.pdf"
    }
    
    # Try to fetch the official form
    url = irs_urls.get(tax_year, irs_urls[2024])  # Default to latest if year not found
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.content
        else:
            # Fallback: try the current year form
            response = requests.get(irs_urls[2024], timeout=10)
            if response.status_code == 200:
                return response.content
    except:
        pass
    
    return None

def create_form_8949_with_official_template(buffer, page_transactions, form_type, taxpayer_name, taxpayer_ssn, tax_year, page_number, total_pages, all_transactions):
    """Create Form 8949 using official IRS template as base"""
    
    # Try to get official form
    official_form_pdf = get_official_form_8949(tax_year)
    
    if official_form_pdf:
        try:
            # Use official form as base and overlay data
            return create_form_with_pdf_overlay(buffer, page_transactions, form_type, taxpayer_name, taxpayer_ssn, tax_year, page_number, total_pages, all_transactions, official_form_pdf)
        except:
            # Fallback to custom creation if overlay fails
            pass
    
    # Fallback: create custom form (original method)
    return create_form_8949_page_custom(buffer, page_transactions, form_type, taxpayer_name, taxpayer_ssn, tax_year, page_number, total_pages, all_transactions)

def create_form_with_pdf_overlay(buffer, page_transactions, form_type, taxpayer_name, taxpayer_ssn, tax_year, page_number, total_pages, all_transactions, official_form_pdf):
    """Overlay transaction data onto official IRS Form 8949 PDF"""
    
    # Read the official PDF
    official_pdf_stream = io.BytesIO(official_form_pdf)
    pdf_reader = PyPDF2.PdfReader(official_pdf_stream)
    
    # Determine which page to use (Part I or Part II)
    template_page_num = 0 if "Part I" in form_type else 1
    if template_page_num >= len(pdf_reader.pages):
        template_page_num = 0  # Fallback to first page
    
    template_page = pdf_reader.pages[template_page_num]
    
    # Create overlay with transaction data
    overlay_buffer = io.BytesIO()
    c = canvas.Canvas(overlay_buffer, pagesize=letter)
    width, height = letter
    
    # Set font
    c.setFont("Helvetica", 9)
    
    # Add taxpayer information (positioned to match form fields)
    c.drawString(60, height - 85, taxpayer_name)  # Name field
    c.drawString(400, height - 85, taxpayer_ssn)  # SSN field
    
    # Add tax year
    c.setFont("Helvetica-Bold", 12)
    c.drawString(530, height - 50, str(tax_year))
    
    # Check appropriate box based on form_type
    checkbox_y = height - 220  # Approximate position of checkboxes
    c.setFont("Helvetica", 12)
    
    if "Box A" in form_type:
        c.drawString(55, checkbox_y, "✓")
    elif "Box B" in form_type:
        c.drawString(55, checkbox_y - 15, "✓") 
    elif "Box C" in form_type:
        c.drawString(55, checkbox_y - 30, "✓")
    elif "Box D" in form_type:
        c.drawString(55, checkbox_y, "✓")
    elif "Box E" in form_type:
        c.drawString(55, checkbox_y - 15, "✓")
    elif "Box F" in form_type:
        c.drawString(55, checkbox_y - 30, "✓")
    
    # Add transaction data (positioned to match form fields)
    c.setFont("Helvetica", 8)
    start_y = height - 280  # Starting position for transaction rows
    row_height = 20  # Height between rows
    
    for i, transaction in enumerate(page_transactions[:14]):  # Max 14 transactions per page
        y_pos = start_y - (i * row_height)
        
        # Format dates
        date_acquired = transaction['date_acquired'].strftime('%m/%d/%Y') if transaction['date_acquired'] else 'VARIOUS'
        date_sold = transaction['date_sold'].strftime('%m/%d/%Y')
        
        # Position data in columns (adjusted to match official form layout)
        c.drawString(60, y_pos, transaction['description'][:30])  # Column (a) - Description
        c.drawString(175, y_pos, date_acquired)  # Column (b) - Date acquired  
        c.drawString(240, y_pos, date_sold)  # Column (c) - Date sold
        c.drawRightString(320, y_pos, f"{transaction['proceeds']:,.2f}")  # Column (d) - Proceeds
        c.drawRightString(380, y_pos, f"{transaction['cost_basis']:,.2f}")  # Column (e) - Cost basis
        # Column (f) - Code (leave blank)
        # Column (g) - Adjustment (leave blank) 
        c.drawRightString(520, y_pos, f"{transaction['gain_loss']:,.2f}")  # Column (h) - Gain/Loss
    
    # Add totals (only on last page)
    if page_number == total_pages and len(page_transactions) > 0:
        totals_y = start_y - (14 * row_height) - 10  # Position below transaction rows
        
        total_proceeds = sum(t['proceeds'] for t in all_transactions)
        total_basis = sum(t['cost_basis'] for t in all_transactions)
        total_gain_loss = sum(t['gain_loss'] for t in all_transactions)
        
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(320, totals_y, f"{total_proceeds:,.2f}")
        c.drawRightString(380, totals_y, f"{total_basis:,.2f}")
        c.drawRightString(520, totals_y, f"{total_gain_loss:,.2f}")
    
    # Add page footer
    c.setFont("Helvetica", 7)
    if total_pages > 1:
        c.drawString(50, 30, f"Page {page_number} of {total_pages}")
    c.drawRightString(width - 50, 30, f"Generated: {datetime.now().strftime('%m/%d/%Y')}")
    
    c.save()
    
    # Merge overlay with template
    overlay_buffer.seek(0)
    overlay_reader = PyPDF2.PdfReader(overlay_buffer)
    overlay_page = overlay_reader.pages[0]
    
    # Merge the pages
    template_page.merge_page(overlay_page)
    
    # Write to output buffer
    pdf_writer = PyPDF2.PdfWriter()
    pdf_writer.add_page(template_page)
    pdf_writer.write(buffer)
    
    return True

def create_form_8949_page_custom(buffer, page_transactions, form_type, taxpayer_name, taxpayer_ssn, tax_year, page_number, total_pages, all_transactions):
    """Create a single Form 8949 PDF page"""
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Form header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Form 8949")
    c.setFont("Helvetica", 10)
    c.drawString(150, height - 50, "Sales and Other Dispositions of Capital Assets")
    c.drawRightString(width - 50, height - 50, f"{tax_year}")
    
    # Department of Treasury - Internal Revenue Service
    c.setFont("Helvetica", 8)
    c.drawString(150, height - 62, "Department of the Treasury - Internal Revenue Service")
    
    # Taxpayer information
    c.setFont("Helvetica", 9)
    c.drawString(50, height - 85, f"Name(s) shown on return: {taxpayer_name}")
    c.drawString(50, height - 100, f"Your social security number: {taxpayer_ssn}")
    
    # Form type and checkboxes
    y_pos = height - 135
    c.setFont("Helvetica-Bold", 10)
    
    if "Part I" in form_type:
        c.drawString(50, y_pos, "Part I - Short-Term Capital Gains and Losses - Generally for assets held one year or less")
        part_text = "Short-Term"
    else:
        c.drawString(50, y_pos, "Part II - Long-Term Capital Gains and Losses - Generally for assets held more than one year")
        part_text = "Long-Term"
    
    # Checkbox selection
    y_pos -= 25
    c.setFont("Helvetica", 9)
    
    checkbox_text = [
        "(A) Short-term transactions reported on Form(s) 1099-B showing basis was reported to the IRS",
        "(B) Short-term transactions reported on Form(s) 1099-B showing basis was NOT reported to the IRS",  
        "(C) Short-term transactions not reported to you on Form 1099-B"
    ]
    
    if "Part II" in form_type:
        checkbox_text = [text.replace("Short-term", "Long-term") for text in checkbox_text]
    
    for i, text in enumerate(checkbox_text):
        checkbox = "☑" if (("Box A" in form_type and i == 0) or 
                           ("Box B" in form_type and i == 1) or 
                           ("Box C" in form_type and i == 2)) else "☐"
        c.drawString(50, y_pos - (i * 15), f"{checkbox} {text}")
    
    # Column headers
    y_pos = height - 220
    c.setFont("Helvetica-Bold", 8)
    
    headers = [
        ("(a) Description of property", 50),
        ("(b) Date acquired", 170),
        ("(c) Date sold or disposed of", 235),
        ("(d) Proceeds (sales price)", 315),
        ("(e) Cost or other basis", 380),
        ("(f) Code(s) from", 440),
        ("(g) Amount of", 470),
        ("(h) Gain or (loss)", 510)
    ]
    
    for header, x_pos in headers:
        c.drawString(x_pos, y_pos, header)
    
    # Sub-headers
    y_pos -= 10
    c.setFont("Helvetica", 7)
    c.drawString(440, y_pos, "Form(s) 8949")
    c.drawString(470, y_pos, "adjustment")
    c.drawString(510, y_pos, "Subtract column (g)")
    c.drawString(510, y_pos - 8, "from column (d) and")
    c.drawString(510, y_pos - 16, "combine the result")
    c.drawString(510, y_pos - 24, "with column (e)")
    
    # Draw line under headers
    y_pos -= 30
    c.line(50, y_pos, width - 50, y_pos)
    
    # Transaction data
    y_pos -= 15
    c.setFont("Helvetica", 8)
    
    for transaction in page_transactions:
        if y_pos < 150:  # Check if we need space for totals
            break
        
        # Format dates
        date_acquired = transaction['date_acquired'].strftime('%m/%d/%Y') if transaction['date_acquired'] else 'VARIOUS'
        date_sold = transaction['date_sold'].strftime('%m/%d/%Y')
        
        # Draw transaction data
        c.drawString(50, y_pos, transaction['description'][:35])  # Truncate if too long
        c.drawString(170, y_pos, date_acquired)
        c.drawString(235, y_pos, date_sold)
        c.drawRightString(375, y_pos, f"{transaction['proceeds']:,.2f}")
        c.drawRightString(435, y_pos, f"{transaction['cost_basis']:,.2f}")
        c.drawString(445, y_pos, "")  # Adjustment code (blank)
        c.drawRightString(505, y_pos, "")  # Adjustment amount (blank)
        c.drawRightString(555, y_pos, f"{transaction['gain_loss']:,.2f}")
        
        y_pos -= 18
    
    # Totals section (only on last page)
    if page_number == total_pages:
        y_pos = 130
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, y_pos, f"Totals for all transactions:")
        
        total_proceeds = sum(t['proceeds'] for t in all_transactions)
        total_basis = sum(t['cost_basis'] for t in all_transactions)
        total_gain_loss = sum(t['gain_loss'] for t in all_transactions)
        
        c.drawRightString(375, y_pos, f"{total_proceeds:,.2f}")
        c.drawRightString(435, y_pos, f"{total_basis:,.2f}")
        c.drawRightString(555, y_pos, f"{total_gain_loss:,.2f}")
        
        # Draw line above totals
        c.line(315, y_pos + 5, 555, y_pos + 5)
    
    # Page footer
    c.setFont("Helvetica", 8)
    if total_pages > 1:
        c.drawString(50, 40, f"Form 8949 ({tax_year}) - Page {page_number} of {total_pages}")
    else:
        c.drawString(50, 40, f"Form 8949 ({tax_year})")
    
    c.drawRightString(width - 50, 40, f"Generated from Bitwave: {datetime.now().strftime('%m/%d/%Y')}")
    
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
