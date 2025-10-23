# Dashboard Refactoring Guide

## Project Structure

```
dashboard/
├── app.py                          # Main application file (orchestrator)
├── theme.css                       # CSS styling
├── utils/                          # Utility modules
│   ├── __init__.py
│   ├── data_loader.py             # ✅ CREATED - Data loading functions
│   ├── visualizations.py          # ✅ CREATED - Chart creation functions
│   ├── styling.py                 # ✅ CREATED - UI helper functions
│   └── insights.py                # TODO - Insight generation
├── components/                     # Reusable components
│   ├── __init__.py
│   └── filters.py                 # TODO - Sidebar filter panel
└── tabs/                          # Tab content modules
    ├── __init__.py
    ├── overview_tab.py            # TODO - Overview tab
    ├── theme_analysis_tab.py      # TODO - Theme Analysis tab
    ├── universities_tab.py        # TODO - Universities tab
    ├── trends_tab.py              # TODO - Trends tab
    └── emerging_topics_tab.py     # TODO - Emerging Topics tab
```

## Completed Files

### 1. ✅ utils/data_loader.py
Contains:
- `_load_json()` - Load JSON files
- `load_data()` - Main data loading with preprocessing

### 2. ✅ utils/visualizations.py  
Contains:
- `create_sunburst_chart()` - Hierarchical sunburst
- `create_sankey_flow()` - Research flow diagram
- `create_trend_timeline()` - Publication trends
- `create_growth_heatmap()` - Sub-theme heatmap
- `create_impact_bubble_chart()` - Bubble chart
- `create_university_radar()` - Radar comparison

### 3. ✅ utils/styling.py
Contains:
- `apply_fig_theme()` - Apply dark theme to charts
- `create_metric_card()` - Metric card HTML
- `create_section_header()` - Section header HTML
- `create_insight_card()` - Insight card HTML
- `get_growth_color_style()` - Growth rate color styling

## Remaining Files to Create

### utils/insights.py
Should contain:
- `generate_insights()` - Generate actionable insights
- `filter_noisy_keywords()` - Filter keywords
- `generate_topic_label_gpt()` - GPT label generation
- `create_emerging_topics_bubble()` - Emerging topics chart

Extract from app.py lines 128-860 (approximately)

### components/filters.py
Should contain:
- `render_filters()` - Render sidebar filters and return filtered data

Function signature:
```python
def render_filters(papers_df, all_universities, all_themes):
    \"\"\"Render sidebar filters and return filtered data.\"\"\"
    # Sidebar rendering code
    # Return filtered_df, start_date, end_date, sel_themes, sel_sub_themes, sel_unis
```

Extract from app.py lines 905-985 (approximately)

### tabs/overview_tab.py
Should contain:
- `render_overview_tab()` - Render entire Overview tab content

Extract from app.py lines 1110-1270 (with tab_overview:)

### tabs/theme_analysis_tab.py
Should contain:
- `render_theme_analysis_tab()` - Render Theme Analysis tab
- Helper function `find_adjacent_themes()`

Extract from app.py lines 1271-1561 (with tab_theme:)

### tabs/universities_tab.py
Should contain:
- `render_universities_tab()` - Render Universities tab

Extract from app.py lines 1562-1626 (with tab_unis:)

### tabs/trends_tab.py
Should contain:
- `render_trends_tab()` - Render Trends tab

Extract from app.py lines 1627-1766 (with tab_trends:)

### tabs/emerging_topics_tab.py
Should contain:
- `render_emerging_topics_tab()` - Render Emerging Topics tab

Extract from app.py lines 1767-end (with tab_emerging:)

## New app.py Structure

```python
\"\"\"
Smarter Research Insights - AI-Powered Research Intelligence Dashboard
\"\"\"
import os
import streamlit as st
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import utilities
from dashboard.utils.data_loader import load_data
from dashboard.components.filters import render_filters
from dashboard.tabs.overview_tab import render_overview_tab
from dashboard.tabs.theme_analysis_tab import render_theme_analysis_tab
from dashboard.tabs.universities_tab import render_universities_tab
from dashboard.tabs.trends_tab import render_trends_tab
from dashboard.tabs.emerging_topics_tab import render_emerging_topics_tab

# Import config
from config.themes import BABCOCK_THEMES
from config.settings import ALL_UNIVERSITIES

# ---- Page Configuration ----
st.set_page_config(
    page_title="Smarter Research Insights", 
    page_icon="🔬", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Load external CSS
css_path = os.path.join(os.path.dirname(__file__), "theme.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---- Load Data ----
try:
    papers_df, trends, mapping = load_data()
except FileNotFoundError as e:
    st.error(f"Data files not found: {e}. Run the pipeline first: `python run_full_analysis.py`")
    st.stop()

# ---- Sidebar Filters ----
filtered, start_date, end_date, sel_themes, sel_sub_themes, sel_unis = render_filters(
    papers_df, ALL_UNIVERSITIES, BABCOCK_THEMES
)

# ---- Header ----
st.markdown('''
<div style="text-align: center; padding: 3rem 0 2rem 0;">
    <h1 style="
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 50%, #e2e8f0 100%);
        -webkit-background-clip: text;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    ">Smarter Research Insights</h1>
    <p style="
        font-size: 1.1rem;
        color: var(--text-secondary);
        font-weight: 400;
        letter-spacing: 0.02em;
    ">AI-Powered Research Intelligence Dashboard</p>
</div>
''', unsafe_allow_html=True)

# ---- Tabs ----
tab_overview, tab_theme, tab_unis, tab_trends, tab_emerging, tab_quality = st.tabs([
    "Overview", "Theme Analysis", "Universities", "Trends", "Emerging Topics", "Data Quality"
])

# Filter summary
sub_theme_text = f"<span class='badge'>Sub-Themes</span> {len(sel_sub_themes)}" if sel_sub_themes else ""
st.markdown(
    f"<div class='card-alt' style='display:flex;gap:1rem;align-items:center'>"
    f"<span class='badge'>Date</span> <b>{start_date}</b> → <b>{end_date}</b>"
    f"<span class='badge'>Themes</span> {len(sel_themes) if sel_themes else 0}"
    f"{sub_theme_text}"
    f"<span class='badge'>Universities</span> {len(sel_unis) if sel_unis else 0}"
    f"</div>",
    unsafe_allow_html=True,
)

# ---- Render Tabs ----
with tab_overview:
    render_overview_tab(filtered, papers_df, trends, mapping)

with tab_theme:
    render_theme_analysis_tab(filtered, papers_df, trends, mapping, BABCOCK_THEMES)

with tab_unis:
    render_universities_tab(filtered, papers_df)

with tab_trends:
    render_trends_tab(filtered, papers_df, trends)

with tab_emerging:
    render_emerging_topics_tab(filtered, mapping)

with tab_quality:
    st.info("Data Quality tab content here")
```

## Migration Steps

1. ✅ Create directory structure
2. ✅ Create utils/data_loader.py
3. ✅ Create utils/visualizations.py
4. ✅ Create utils/styling.py
5. ⏳ Create utils/insights.py
6. ⏳ Create components/filters.py
7. ⏳ Create tabs/overview_tab.py
8. ⏳ Create tabs/theme_analysis_tab.py
9. ⏳ Create tabs/universities_tab.py
10. ⏳ Create tabs/trends_tab.py
11. ⏳ Create tabs/emerging_topics_tab.py
12. ⏳ Replace app.py with new orchestrator version
13. ⏳ Test all functionality

## Benefits

- **Maintainability**: Each module has a single responsibility
- **Reusability**: Functions can be imported and reused
- **Testability**: Each module can be unit tested independently
- **Readability**: Clear separation of concerns
- **Scalability**: Easy to add new tabs or features

## Notes

- All tab render functions should accept necessary data as parameters
- Import statements should be at the top of each file
- Keep the same function signatures for compatibility
- CSS remains in theme.css (no changes needed)
