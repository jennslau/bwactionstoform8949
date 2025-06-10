# CSV to Form 8949 PDF Filler

A specialized web application that converts CSV data with capital gains/losses into properly filled IRS Form 8949 PDFs. Perfect for tax preparation and filing.

## 🎯 What This Tool Does

- 📊 Converts your capital gains/losses CSV data into official Form 8949 PDFs
- 📄 Generates properly formatted IRS forms that match the official layout
- 💼 Handles both short-term and long-term capital gains/losses
- 📦 Creates multiple pages automatically if you have many transactions
- 🧮 Calculates totals and gain/loss amounts automatically

## 📋 Required CSV Format

Your CSV file must have these columns (exact names):

| Column Name | Description | Example |
|-------------|-------------|---------|
| **Description** | Description of the property sold | "100 shares ABC Corp" |
| **Date_Acquired** | Date you bought the asset | "01/15/2023" |
| **Date_Sold** | Date you sold the asset | "12/15/2023" |
| **Sales_Price** | Gross sales price (numbers only) | 5000.00 |
| **Cost_Basis** | Your cost basis (numbers only) | 4500.00 |

**Optional Columns:**
- **Gain_Loss** - Will be calculated automatically if not provided
- **Adjustment_Code** - For special adjustments (usually blank)
- **Adjustment_Amount** - Amount of adjustments (usually 0)

## 🚀 Step-by-Step Setup Guide

### Step 1: Create a GitHub Account
1. Go to [GitHub.com](https://github.com)
2. Click "Sign up" and create your free account

### Step 2: Create Your Repository
1. Click the green "New" button in GitHub
2. Name it something like "form-8949-filler"
3. Make it **Public**
4. Check "Add a README file"
5. Click "Create repository"

### Step 3: Upload the Files
Upload these 3 files to your GitHub repository:

1. **app.py** - The main application (copy from the first code box above)
2. **requirements.txt** - The dependencies (copy from the second code box above)
3. **README.md** - This instruction file (copy from the third code box above)

**Important:** Make sure the main file is named exactly `app.py`

### Step 4: Deploy to Streamlit
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository
5. Confirm the main file is `app.py`
6. Click "Deploy!"

### Step 5: Wait for Build
- Takes 2-3 minutes to install everything
- You'll get a URL like: `https://yourname-form-8949-filler-app-streamlit.app`

## 📊 How to Use the Application

### 1. Prepare Your Data
- Download the sample CSV template from the app
- Fill in your capital gains/losses data
- Save as CSV format

### 2. Configure the Form
- **Name**: Enter your full name as it appears on your tax return
- **SSN**: Enter your Social Security Number
- **Form Type**: Choose the appropriate option:
  - **Part I** = Short-term (held 1 year or less)
  - **Part II** = Long-term (held more than 1 year)
  - **Box A** = Basis reported to IRS (most common)
  - **Box B** = Basis not reported to IRS
  - **Box C** = Various situations

### 3. Upload Your CSV
- Click "Choose a CSV file"
- Upload your prepared data file
- The app will validate your columns and show a preview

### 4. Generate Forms
- Click "Generate Form 8949 PDFs"
- Download your completed forms
- Multiple pages are created automatically if needed

## 📋 Form 8949 Box Selection Guide

**Choose Box A if:**
- Your broker sent you Form 1099-B showing the cost basis
- Most stock/ETF sales through major brokers

**Choose Box B if:**
- No Form 1099-B was sent, OR
- Form 1099-B doesn't show cost basis
- Crypto transactions, private sales

**Choose Box C if:**
- Mix of transactions with different reporting
- Special situations requiring adjustments

## 💡 Pro Tips

### Data Preparation
- Use MM/DD/YYYY format for dates
- Don't include $ signs or commas in amounts
- Keep descriptions under 25 characters for best formatting
- Double-check your math before uploading

### Common Issues
- **"Missing columns" error**: Check your CSV headers match exactly
- **Date format problems**: Use MM/DD/YYYY format
- **Number errors**: Remove $ signs and commas from amounts

### For Multiple Assets
- List each sale as a separate row
- Group similar transactions together
- The app will automatically paginate if you have many transactions

## 🏗️ File Structure
```
your-repository/
├── app.py              # Main application
├── requirements.txt    # Python dependencies  
└── README.md          # Instructions
```

## 🔧 Customization Options

You can modify `app.py` to:
- Change the tax year (currently set to 2023)
- Adjust the number of transactions per page
- Modify the PDF layout and formatting
- Add additional validation rules

## ⚠️ Important Tax Notes

- This tool creates Form 8949 PDFs but **does not provide tax advice**
- Always consult a tax professional for complex situations
- Verify all amounts and dates before filing
- Keep your original transaction records
- The generated forms are for tax filing purposes

## 🆘 Troubleshooting

**App won't start?**
- Verify `app.py` is the exact filename
- Check that all 3 files are uploaded to GitHub
- Make sure repository is public

**CSV upload fails?**
- Download and use the sample template
- Check column names match exactly
- Ensure dates are in MM/DD/YYYY format
- Remove formatting from number columns

**PDF generation errors?**
- Fill in your name and SSN
- Verify at least one row of data exists
- Check for special characters in descriptions

## 📞 Support

If you need help:
1. Download the sample CSV template first
2. Follow the exact column naming requirements
3. Check the troubleshooting section above
4. Verify your data format matches the examples

## 🎯 Next Steps

Once your app is running:
1. Bookmark the Streamlit URL for easy access
2. Share with your tax preparer if needed
3. Generate forms early in tax season
4. Keep digital copies of your generated forms

**Your Form 8949 filler will be live at:** `https://[your-username]-form-8949-filler-app-streamlit.app`

Happy tax filing! 📊✨

---

*Disclaimer: This tool is for educational and convenience purposes. Always consult with a qualified tax professional for tax advice.*