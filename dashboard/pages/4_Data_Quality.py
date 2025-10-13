import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from dashboard.common import load_data, load_css, build_filters, apply_fig_theme

st.set_page_config(page_title="Research Trend Analyzer - Data Quality", layout="wide")
load_css()

 

papers_df, trends, mapping = load_data()
filtered, ctx = build_filters(papers_df)

st.markdown('<p class="main-header">Data Quality</p>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
missing_abs = filtered['abstract'].isna().sum() if 'abstract' in filtered.columns else 0
c1.metric("Missing Abstracts", f"{missing_abs:,}")
c2.metric("Avg Confidence", f"{filtered['confidence'].mean():.0f}%" if 'confidence' in filtered.columns else 'N/A')
c3.metric("Has Citations", f"{filtered['citations'].notna().mean()*100:.0f}%" if 'citations' in filtered.columns else 'N/A')

st.markdown("---")
colA, colB = st.columns(2)
with colA:
    st.markdown('<p class="sub-header">Confidence Distribution</p>', unsafe_allow_html=True)
    if 'confidence' in filtered.columns:
        fig = px.histogram(filtered, x='confidence', nbins=20, title='Confidence (%)')
        fig = apply_fig_theme(fig, height=320)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No confidence field available")
with colB:
    st.markdown('<p class="sub-header">Citations Distribution</p>', unsafe_allow_html=True)
    if 'citations' in filtered.columns:
        fig = px.histogram(filtered, x='citations', nbins=20, title='Citations')
        fig = apply_fig_theme(fig, height=320)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No citations field available")
