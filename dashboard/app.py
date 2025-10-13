"""
Research Trend Analyzer - Prescience-style Clean Dashboard
Light main content, dark sidebar, green accent. High-contrast charts and cards.
"""
import os
import sys
import json
from io import BytesIO
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    HAS_AGGRID = True
except Exception:
    HAS_AGGRID = False

# ---- Config imports ----
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from dashboard.common import load_data, load_css, build_filters, apply_fig_theme
from config.themes import BABCOCK_THEMES  # type: ignore

# ---- Page + Theme ----
st.set_page_config(page_title="Research Trend Analyzer", page_icon="", layout="wide")

# Plotly sane defaults (light)
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = ["#22c55e", "#0ea5e9", "#111827", "#64748b", "#f59e0b"]

# Load external CSS
load_css()

# ---- Data Loading ----

try:
    papers_df, trends, mapping = load_data()
except FileNotFoundError as e:
    st.error(f"Data files not found: {e}. Run the pipeline first: `python run_full_analysis.py`")
    st.stop()

# ---- Sidebar (filters only) ----

filtered, ctx = build_filters(papers_df)

# Selection summary (always visible)
st.markdown(
    f"<div class='card-alt' style='display:flex;gap:1rem;align-items:center'>"
    f"<span class='badge'>Date</span> <b>{ctx['start_date']}</b> → <b>{ctx['end_date']}</b>"
    f"<span class='badge'>Themes</span> {len(ctx['sel_themes']) if ctx['sel_themes'] else 0}"
    f"<span class='badge'>Universities</span> {len(ctx['sel_unis']) if ctx['sel_unis'] else 0}"
    f"</div>",
    unsafe_allow_html=True,
)

# Sidebar diagnostics
with st.sidebar.expander("Filter diagnostics"):
    rows_after = len(filtered)
    unis_after = int(filtered["university"].nunique()) if "university" in filtered.columns else 0
    st.write({
        "Rows after filters": rows_after,
        "Universities after filters": unis_after,
        "Selected universities": len(ctx['sel_unis']),
        "Total universities": int(papers_df["university"].nunique()) if "university" in papers_df.columns else 0,
    })

# For charts

# ---- Header ----
st.markdown('<p class="main-header">Research Trend Analyzer</p>', unsafe_allow_html=True)
# KPIs Row
k1, k2, k3, k4 = st.columns(4)
k1.metric("Papers", f"{len(filtered):,}")
k2.metric("Topics", len(mapping))
k3.metric("Universities", filtered["university"].nunique())
try:
    avg_growth = sum(p.get("growth_rate", 0) for p in trends.get("strategic_priorities", [])) / max(1, len(trends.get("strategic_priorities", [])))
    k4.metric("Average Growth", f"{avg_growth*100:+.1f}%")
except Exception:
    k4.metric("Average Growth", "N/A")

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# Strategic Theme Priorities
st.markdown('<p class="sub-header">Strategic Theme Priorities</p>', unsafe_allow_html=True)
grid = st.columns(3)
priorities = trends.get("strategic_priorities", [])
for i, pr in enumerate(priorities):
    col = grid[i % 3]
    theme = pr.get("theme", "").replace("_", " ").title()
    growth = pr.get("growth_rate", 0)
    papers = pr.get("total_papers", 0)
    category = str(pr.get("category", "LOW")).lower()
    bg = "#e2f7ea" if category == "high" else ("#fde68a" if category == "medium" else "#f1f5f9")
    with col.container():
        st.markdown(
            f"<div class='card' style='background:{bg}'>"
            f"<div class='kpi'><div class='label'>{theme}</div>"
            f"<div class='value'>{growth*100:+.1f}%</div>"
            f"<div class='label'>Papers: {papers:,}</div></div></div>",
            unsafe_allow_html=True,
        )

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# Papers per Theme Distribution
st.markdown('<p class="sub-header">Papers per Strategic Theme</p>', unsafe_allow_html=True)
theme_counts = filtered.groupby("theme").size()
theme_counts = theme_counts.reindex(list(BABCOCK_THEMES.keys()), fill_value=0)
fig = px.bar(
    x=theme_counts.values,
    y=[t.replace("_", " ").title() for t in theme_counts.index],
    orientation="h",
    color=theme_counts.values,
    color_continuous_scale="Greens",
    title="Papers per Theme (All Themes)"
)
fig = apply_fig_theme(fig, height=380)
st.plotly_chart(fig, use_container_width=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# Overall Output Over Time (filtered)
st.markdown('<p class="sub-header">Overall Research Activity</p>', unsafe_allow_html=True)
qa = filtered.groupby("quarter").size().reset_index(name="count")
if not qa.empty:
    qa["quarter"] = qa["quarter"].astype(str)
    fig_overall = go.Figure()
    fig_overall.add_trace(go.Scatter(x=qa["quarter"], y=qa["count"], mode="lines+markers", name="All Themes"))
    fig_overall = apply_fig_theme(fig_overall, height=360)
    fig_overall.update_layout(title="Overall Research Output", xaxis_title="Quarter", yaxis_title="Papers")
    st.plotly_chart(fig_overall, use_container_width=True)
else:
    st.info("No trend data for current filters")

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# Top Universities (Filtered)
st.markdown('<p class="sub-header">Top Universities (Filtered)</p>', unsafe_allow_html=True)
if not filtered.empty:
    uc = filtered["university"].value_counts().reset_index()
    uc.columns = ["University", "Papers"]
    top_uc = uc.head(15)
    if HAS_AGGRID:
        gb = GridOptionsBuilder.from_dataframe(top_uc)
        gb.configure_default_column(resizable=True, sortable=True, filter=True)
        gb.configure_pagination(paginationAutoPageSize=True)
        grid_options = gb.build()
        AgGrid(
            top_uc,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.NO_UPDATE,
            height=400,
            fit_columns_on_grid_load=True,
        )
    else:
        st.dataframe(top_uc, use_container_width=True, hide_index=True)
else:
    st.info("No data available for current filters")

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# Top Recent Papers
st.markdown('<p class="sub-header">Top Recent Papers</p>', unsafe_allow_html=True)
recent = filtered.sort_values(["relevance_score", "date"], ascending=[False, False]).head(10)
for _, r in recent.iterrows():
    st.markdown(
        f"<div class='card'><div class='kpi'><div class='label'>{r.get('university','')} | "
        f"{str(r.get('theme','')).replace('_',' ').title()} | {pd.to_datetime(r.get('date')).strftime('%Y-%m-%d') if pd.notna(r.get('date')) else ''}</div>"
        f"<div class='value'>{r.get('title','(untitled)')}</div>"
        f"<span class='badge'>Relevance {r.get('relevance_score',0):.0f}</span></div></div>",
        unsafe_allow_html=True,
    )

# ---- Exports ----
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.subheader("Export")
export_df = filtered.copy()
colE1, colE2 = st.columns(2)
with colE1:
    st.download_button(
        label="Download CSV",
        data=export_df.to_csv(index=False),
        file_name=f"rta_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
with colE2:
    try:
        from openpyxl import Workbook  # noqa: F401
        out = BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            export_df.to_excel(writer, sheet_name="Data", index=False)
            summary = pd.DataFrame(
                {
                    "Metric": [
                        "Total Papers",
                        "Universities",
                        "Avg Confidence",
                        "Date Range",
                    ],
                    "Value": [
                        len(export_df),
                        export_df["university"].nunique() if "university" in export_df.columns else "N/A",
                        f"{export_df['confidence'].mean():.0f}%" if "confidence" in export_df.columns else "N/A",
                        f"{export_df['date'].min().date()} to {export_df['date'].max().date()}" if "date" in export_df.columns else "N/A",
                    ],
                }
            )
            summary.to_excel(writer, sheet_name="Summary", index=False)
        st.download_button(
            label="Download Excel",
            data=out.getvalue(),
            file_name=f"rta_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    except Exception:
        st.info("Install openpyxl for Excel export: pip install openpyxl")
