"""
Smarter Research Insights - AI-Powered Research Intelligence Dashboard
Refactored modular architecture for maintainability and scalability.
"""
import os
import sys
import streamlit as st
import plotly.express as px

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import utilities and components
from dashboard.utils.data_loader import load_data
from dashboard.components.filters import render_filters
from dashboard.tabs.overview_tab import render_overview_tab
from dashboard.tabs.theme_analysis_tab import render_theme_analysis_tab
from dashboard.tabs.universities_tab import render_universities_tab
from dashboard.tabs.trends_tab import render_trends_tab
from dashboard.tabs.emerging_topics_tab import render_emerging_topics_tab
from dashboard.tabs.data_quality_tab import render_data_quality_tab

# Import config
from config.themes import BABCOCK_THEMES
from config.settings import ALL_UNIVERSITIES

# Page Configuration
st.set_page_config(
    page_title="Smarter Research Insights", 
    page_icon="", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Set modern Plotly theme with blue gradient colors
px.defaults.template = "plotly_dark"
px.defaults.color_discrete_sequence = [
    "#3b82f6", "#2563eb", "#06b6d4", "#8b5cf6", "#60a5fa",
    "#0ea5e9", "#a78bfa", "#0284c7", "#7c3aed", "#6366f1"
]

# Load external CSS
css_path = os.path.join(os.path.dirname(__file__), "theme.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load Data
try:
    papers_df, trends, mapping = load_data()
except FileNotFoundError as e:
    st.error(f"Data files not found: {e}. Run the pipeline first: python run_full_analysis.py")
    st.stop()

# Sidebar Filters
filtered, start_date, end_date, sel_themes, sel_sub_themes, sel_unis = render_filters(
    papers_df, ALL_UNIVERSITIES, BABCOCK_THEMES
)

# Header
st.markdown(
    "<div style='text-align: center; padding: 3rem 0 2rem 0;'>"
    "<h1 style='font-size: 3.5rem; font-weight: 800;'>Smarter Research Insights</h1>"
    "<p style='font-size: 1.1rem;'>AI-Powered Research Intelligence Dashboard</p>"
    "</div>",
    unsafe_allow_html=True
)

# Tabs
tab_overview, tab_theme, tab_unis, tab_trends, tab_emerging, tab_quality = st.tabs([
    "Overview", "Theme Analysis", "Universities", "Trends", "Emerging Topics", "Data Quality"
])

# Filter summary
sub_theme_text = f"<span class='badge'>Sub-Themes</span> {len(sel_sub_themes)}" if sel_sub_themes else ""
st.markdown(
    f"<div class='card-alt' style='display:flex;gap:1rem;align-items:center'>"
    f"<span class='badge'>Date</span> <b>{start_date}</b>  <b>{end_date}</b>"
    f"<span class='badge'>Themes</span> {len(sel_themes) if sel_themes else 0}"
    f"{sub_theme_text}"
    f"<span class='badge'>Universities</span> {len(sel_unis) if sel_unis else 0}"
    f"</div>",
    unsafe_allow_html=True
)

# Render Tabs
with tab_overview:
    render_overview_tab(filtered, papers_df, trends, mapping)

with tab_theme:
    render_theme_analysis_tab(filtered, papers_df, trends, mapping, BABCOCK_THEMES)

with tab_unis:
    render_universities_tab(filtered, papers_df)

with tab_trends:
    render_trends_tab(filtered, papers_df, trends)

with tab_emerging:
    render_emerging_topics_tab(filtered, mapping, start_date, end_date, papers_df)

with tab_quality:
    render_data_quality_tab(filtered, papers_df)
