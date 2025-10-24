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

# Import config
from config.themes import STRATEGIC_THEMES
from config.settings import ALL_UNIVERSITIES

# Page Configuration
st.set_page_config(
    page_title="Smarter Research Insights", 
    page_icon="", 
    layout="wide",
    initial_sidebar_state="collapsed",
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

# Add dark theme styling for popover
st.markdown("""
    <style>
    /* Text colors in popover */
    div[data-baseweb="popover"] label {
        color: #cbd5e1 !important;
    }
    
    div[data-baseweb="popover"] p {
        color: #cbd5e1 !important;
    }
    
    /* Date input fields */
    div[data-baseweb="popover"] input[type="text"],
    div[data-baseweb="popover"] input[type="date"] {
        background-color: #0f172a !important;
        color: #cbd5e1 !important;
        border: 1px solid #334155 !important;
    }
    
    /* Placeholder text styling */
    div[data-baseweb="popover"] input::placeholder {
        color: #94a3b8 !important;
        font-style: italic !important;
        opacity: 1 !important;
    }
    
    /* Multiselect widget */
    div[data-baseweb="popover"] div[data-baseweb="select"],
    div[data-baseweb="popover"] div[data-baseweb="select"] > div {
        background-color: #0f172a !important;
        border: 1px solid #334155 !important;
    }
    
    /* Multiselect placeholder text */
    div[data-baseweb="popover"] div[data-baseweb="select"] *,
    div[data-baseweb="select"] * {
        color: #cbd5e1 !important;
    }
    
    div[data-baseweb="popover"] div[data-baseweb="select"] div[role="button"],
    div[data-baseweb="popover"] div[data-baseweb="select"] div[role="button"] *,
    div[data-baseweb="select"] div[role="button"],
    div[data-baseweb="select"] div[role="button"] * {
        color: #94a3b8 !important;
    }
    
    /* Tags in multiselect */
    div[data-baseweb="popover"] span[data-baseweb="tag"] {
        background-color: rgba(59, 130, 246, 0.2) !important;
        border: 1px solid #3b82f6 !important;
        color: #60a5fa !important;
    }
    
    /* Dividers */
    div[data-baseweb="popover"] hr {
        border-color: #334155 !important;
        background-color: #334155 !important;
        opacity: 1 !important;
    }
    
    /* Buttons */
    div[data-baseweb="popover"] button {
        color: #cbd5e1 !important;
    }
    
    /* Checkbox */
    div[data-baseweb="popover"] input[type="checkbox"] {
        accent-color: #3b82f6 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Load Data
try:
    papers_df, trends, mapping = load_data()
except FileNotFoundError as e:
    st.error(f"Data files not found: {e}. Run the pipeline first: python run_full_analysis.py")
    st.stop()

# Sidebar Filters
filtered, start_date, end_date, sel_themes, sel_sub_themes, sel_unis = render_filters(
    papers_df, ALL_UNIVERSITIES, STRATEGIC_THEMES
)

# Header
st.markdown(
    "<div style='text-align: center; padding: 0rem 0 1rem 0;'>"
    "<h1 style='font-size: 3.5rem; font-weight: 800;'>Smarter Research Insights</h1>"
    "<p style='font-size: 1.1rem;'>AI-Powered Research Intelligence Dashboard</p>"
    "</div>",
    unsafe_allow_html=True
)

# Tabs
tab_overview, tab_theme, tab_unis, tab_trends, tab_emerging = st.tabs([
    "Overview", "Theme Analysis", "Universities", "Trends", "Emerging Topics"
])

# Function to render filter summary row
def render_filter_summary():
    sub_theme_text = f"<span class='badge'>Sub-Themes</span> {len(sel_sub_themes)}" if sel_sub_themes else ""
    
    # Use columns to split the filter summary and filter button
    summary_col1, summary_col2 = st.columns([5, 1])
    
    with summary_col1:
        st.markdown(
            f"<div class='card-alt' style='display:flex;gap:1rem;align-items:center;margin-bottom:1.5rem'>"
            f"<span class='badge'>Date</span> <b>{start_date}</b> to <b>{end_date}</b>"
            f"<span class='badge'>Themes</span> {len(sel_themes) if sel_themes else 0}"
            f"{sub_theme_text}"
            f"<span class='badge'>Universities</span> {len(sel_unis) if sel_unis else 0}"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with summary_col2:
        with st.popover("Filters", use_container_width=True):
            # Date range filter
            min_date = papers_df["date"].min().date()
            max_date = papers_df["date"].max().date()
            st.markdown('<p style="color: #cbd5e1; font-weight: 600; margin-bottom: 0.5rem; font-size: 0.95rem;">Date Range</p>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                new_start_date = st.date_input("From", value=start_date, min_value=min_date, max_value=max_date, key=f"inline_from_date_{st.session_state.get('active_tab', 'overview')}")
            with col2:
                new_end_date = st.date_input("To", value=end_date, min_value=min_date, max_value=max_date, key=f"inline_to_date_{st.session_state.get('active_tab', 'overview')}")
            
            st.divider()
            
            # Theme filter
            st.markdown('<p style="color: #cbd5e1; font-weight: 600; margin-bottom: 0.5rem; font-size: 0.95rem;">Parent Themes</p>', unsafe_allow_html=True)
            all_themes = sorted(list(STRATEGIC_THEMES.keys()))
            new_sel_themes = st.multiselect("Themes", options=all_themes, default=sel_themes, key=f"inline_themes_{st.session_state.get('active_tab', 'overview')}", label_visibility="collapsed")
            
            st.divider()
            
            # Sub-theme filter
            st.markdown('<p style="color: #cbd5e1; font-weight: 600; margin-bottom: 0.5rem; font-size: 0.95rem;">Sub-Themes (Optional)</p>', unsafe_allow_html=True)
            all_sub_themes = sorted([st for st in papers_df["sub_theme"].dropna().unique() if st])
            new_sel_sub_themes = st.multiselect("Sub-themes", options=all_sub_themes, default=sel_sub_themes, key=f"inline_sub_themes_{st.session_state.get('active_tab', 'overview')}", label_visibility="collapsed")
            
            st.divider()
            
            # University filter
            st.markdown('<p style="color: #cbd5e1; font-weight: 600; margin-bottom: 0.5rem; font-size: 0.95rem;">Universities</p>', unsafe_allow_html=True)
            australasian_uni_names = set(ALL_UNIVERSITIES.keys())
            all_unis_in_data = papers_df["university"].unique()
            all_unis = sorted([u for u in all_unis_in_data if u in australasian_uni_names])
            
            select_all_unis = st.checkbox("Select All Universities", value=(len(sel_unis) == len(all_unis)), key=f"inline_all_unis_{st.session_state.get('active_tab', 'overview')}")
            if not select_all_unis:
                new_sel_unis = st.multiselect("Universities", options=all_unis, default=sel_unis, key=f"inline_unis_{st.session_state.get('active_tab', 'overview')}", label_visibility="collapsed")
            else:
                new_sel_unis = all_unis
            
            st.divider()
            
            # Keyword filter
            st.markdown('<p style="color: #cbd5e1; font-weight: 600; margin-bottom: 0.5rem; font-size: 0.95rem;">Keywords (Optional)</p>', unsafe_allow_html=True)
            new_kw = st.text_input("Keywords", value="", placeholder="e.g., autonomy, AI", key=f"inline_kw_{st.session_state.get('active_tab', 'overview')}", label_visibility="collapsed")
            
            st.divider()
            
            # Apply and Reset buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Apply Filters", use_container_width=True, type="primary", key=f"apply_{st.session_state.get('active_tab', 'overview')}"):
                    st.session_state["from_date"] = new_start_date
                    st.session_state["to_date"] = new_end_date
                    st.session_state["themes"] = new_sel_themes
                    st.session_state["sub_themes"] = new_sel_sub_themes
                    st.session_state["unis"] = new_sel_unis
                    st.session_state["all_unis_flag"] = select_all_unis
                    st.session_state["kw"] = new_kw
                    st.rerun()
            with col2:
                if st.button("Reset", use_container_width=True, key=f"reset_{st.session_state.get('active_tab', 'overview')}"):
                    st.session_state["from_date"] = min_date
                    st.session_state["to_date"] = max_date
                    st.session_state["themes"] = all_themes
                    st.session_state["sub_themes"] = []
                    st.session_state["all_unis_flag"] = True
                    st.session_state["unis"] = all_unis
                    st.session_state["kw"] = ""
                    st.rerun()

# Render Tabs
with tab_overview:
    st.session_state['active_tab'] = 'overview'
    render_filter_summary()
    render_overview_tab(filtered, papers_df, trends, mapping)

with tab_theme:
    st.session_state['active_tab'] = 'theme'
    render_filter_summary()
    render_theme_analysis_tab(filtered, papers_df, trends, mapping, STRATEGIC_THEMES)

with tab_unis:
    st.session_state['active_tab'] = 'unis'
    render_filter_summary()
    render_universities_tab(filtered, papers_df)

with tab_trends:
    st.session_state['active_tab'] = 'trends'
    render_filter_summary()
    render_trends_tab(filtered, papers_df, trends)

with tab_emerging:
    st.session_state['active_tab'] = 'emerging'
    render_filter_summary()
    render_emerging_topics_tab(filtered, mapping, start_date, end_date, papers_df)
