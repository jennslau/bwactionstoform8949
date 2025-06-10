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
    /* Bitwave design system colors */
    :root {
        --bitwave-blue: #1B9CFC;
        --bitwave-green: #00D2B8;
        --bitwave-dark: #1a1a1a;
        --bitwave-gray: #6b7280;
        --bitwave-light-gray: #f8fafc;
        --bitwave-border: #e5e7eb;
    }
    
    /* Global font improvements */
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Header styling - more subtle like Bitwave */
    .main-header {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d3748 100%);
        color: white;
        border-radius: 12px;
        padding: 2.5rem 2rem;
        margin-bottom: 3rem;
        text-align: center;
    }
    
    .main-header h1 {
        color: white !important;
        font-size: 2.25rem;
        font-weight: 600;
        margin: 0;
        letter-spacing: -0.
