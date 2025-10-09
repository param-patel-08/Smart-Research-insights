"""
Babcock Research Trends - Enhanced Streamlit Dashboard
Implements all mega prompt features: global filters, adjacent themes, trend alerts, strength rankings, exports
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime
import sys
import os
from io import BytesIO

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.themes import BABCOCK_THEMES
from config.settings import (
    PROCESSED_PAPERS_CSV,
    TREND_ANALYSIS_PATH,
    TOPIC_MAPPING_PATH,
)

# ==================== PAGE CONFIG ====================

st.set_page_config(
    page_title="Babcock Research Trends",
    page_icon=" ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================

st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4788;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c5aa0;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #e6e9f0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f4788;
        color: #0f172a;
    }
    .priority-high { background-color: #ef9a9a; border-left-color: #c62828; }
    .priority-medium { background-color: #ffcc80; border-left-color: #ef6c00; }
    .priority-low { background-color: #c8e6c9; border-left-color: #2e7d32; }
    .stTabs [data-baseweb="tab-list"] { gap: 2rem; }
    .stTabs [data-baseweb="tab"] { padding: 1rem 2rem; }
    </style>
""", unsafe_allow_html=True)

# ==================== LOAD DATA ====================

@st.cache_data
def load_data():
    """Load analysis data with confidence and relevance scoring"""
    # Papers with topics
    if not os.path.exists(PROCESSED_PAPERS_CSV):
        raise FileNotFoundError(PROCESSED_PAPERS_CSV)
    df = pd.read_csv(PROCESSED_PAPERS_CSV)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    # Helper to load JSON
    def load_json_file(path):
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            with open(path, 'r', encoding='utf-8') as f:
                return json.loads(f.read())

    trends_obj = load_json_file(TREND_ANALYSIS_PATH)
    mapping_obj = load_json_file(TOPIC_MAPPING_PATH)

    # Append theme from mapping
    df['theme'] = df['topic_id'].astype(str).map(lambda tid: mapping_obj.get(str(tid), {}).get('theme', 'Other'))

    # Append confidence from mapping (0-100 scale)
    df['confidence'] = df['topic_id'].astype(str).map(lambda tid: mapping_obj.get(str(tid), {}).get('confidence', 0))
    # If confidence is [0,1], scale up
    if df['confidence'].max() <= 1.0:
        df['confidence'] = (df['confidence'] * 100).round(0)

    # Calculate relevance score
    def calculate_relevance(df_in):
        out = df_in.copy()
        # Citation score normalized
        if 'citations' in out.columns and pd.api.types.is_numeric_dtype(out['citations']):
            max_cit = max(1, out['citations'].max())
            out['citation_score'] = (out['citations'] / max_cit) * 100
        else:
            out['citation_score'] = 0
        # Recency score over ~2 years
        if 'date' in out.columns:
            days_old = (pd.Timestamp.now() - pd.to_datetime(out['date'])).dt.days.clip(lower=0)
            out['recency_score'] = (100 - (days_old / 730.0) * 100).clip(lower=0, upper=100)
        else:
            out['recency_score'] = 50
        # Combine
        out['relevance_score'] = (
            out['confidence'].fillna(0) * 0.40 +
            out['citation_score'].fillna(0) * 0.30 +
            out['recency_score'].fillna(0) * 0.30
        ).clip(lower=0, upper=100)
        return out

    df = calculate_relevance(df)
    return df, trends_obj, mapping_obj

# ==================== EXPORT HELPER ====================

def add_export_section(filtered_data, page_name):
    """Add CSV export capabilities"""
    st.markdown("---")
    st.markdown("##   Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv_data = filtered_data.to_csv(index=False)
        st.download_button(
            label="  Download CSV",
            data=csv_data,
            file_name=f"babcock_{page_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        try:
            # Excel export with openpyxl
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                filtered_data.to_excel(writer, sheet_name='Data', index=False)
                
                # Summary sheet
                summary = pd.DataFrame({
                    'Metric': ['Total Papers', 'Universities', 'Avg Confidence', 'Date Range'],
                    'Value': [
                        len(filtered_data),
                        filtered_data['university'].nunique() if 'university' in filtered_data.columns else 'N/A',
                        f"{filtered_data['confidence'].mean():.0f}%" if 'confidence' in filtered_data.columns else 'N/A',
                        f"{filtered_data['date'].min()} to {filtered_data['date'].max()}" if 'date' in filtered_data.columns else 'N/A'
                    ]
                })
                summary.to_excel(writer, sheet_name='Summary', index=False)
            
            excel_data = output.getvalue()
            st.download_button(
                label="  Download Excel",
                data=excel_data,
                file_name=f"babcock_{page_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except ImportError:
            st.info("Install openpyxl for Excel export: pip install openpyxl")

try:
    papers_df, trends, mapping = load_data()
except FileNotFoundError as e:
    st.error(f"   Data files not found! Please run: `python run_full_analysis.py`\nMissing: {e}")
    st.stop()

# Derive helper columns
papers_df['quarter'] = papers_df['date'].dt.to_period('Q')
