import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.themes import BABCOCK_THEMES
from dashboard.common import load_data, load_css, build_filters, apply_fig_theme
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    HAS_AGGRID = True
except Exception:
    HAS_AGGRID = False

st.set_page_config(page_title="Research Trend Analyzer - Theme Analysis", layout="wide")
load_css()

 

papers_df, trends, mapping = load_data()
filtered, ctx = build_filters(papers_df)

st.markdown('<p class="main-header">Theme Analysis</p>', unsafe_allow_html=True)

# Theme summary table
theme_order = list(BABCOCK_THEMES.keys())
theme_names = [t.replace('_', ' ').title() for t in theme_order]
summary = (
    filtered.groupby("theme").agg(
        papers=("title", "count"),
        universities=("university", pd.Series.nunique),
        topics=("topic_id", pd.Series.nunique),
    )
    if not filtered.empty
    else pd.DataFrame(columns=["papers", "universities", "topics"])
)
summary = summary.reindex(theme_order, fill_value=0).reset_index().rename(columns={"theme": "Theme Key"})
summary["Theme"] = summary["Theme Key"].str.replace("_", " ").str.title()
summary["Growth Rate (%)"] = summary["Theme Key"].map(
    lambda t: trends.get("theme_trends", {}).get(t, {}).get("growth_rate", 0) * 100
)
summary["Total Papers (Dataset)"] = summary["Theme Key"].map(
    lambda t: trends.get("theme_trends", {}).get(t, {}).get("total_papers", 0)
)
summary = summary[[
    "Theme",
    "papers",
    "Total Papers (Dataset)",
    "Growth Rate (%)",
    "universities",
    "topics",
]].rename(columns={
    "papers": "Papers (Filtered)",
    "universities": "Universities",
    "topics": "Topics",
})

st.markdown('<p class="sub-header">Theme Overview</p>', unsafe_allow_html=True)
if HAS_AGGRID:
    gb = GridOptionsBuilder.from_dataframe(summary)
    gb.configure_default_column(resizable=True, sortable=True, filter=True)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=15)
    grid_options = gb.build()
    AgGrid(
        summary,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.NO_UPDATE,
        height=380,
        fit_columns_on_grid_load=True,
    )
else:
    st.dataframe(summary, use_container_width=True, hide_index=True)

# Multi-theme trend chart
if not filtered.empty:
    quarters = sorted(filtered["quarter"].unique())
    idx = pd.MultiIndex.from_product([quarters, theme_order], names=["quarter", "theme"])
    theme_trend = filtered.groupby(["quarter", "theme"]).size().reindex(idx, fill_value=0).reset_index(name="count")
    theme_trend["quarter"] = theme_trend["quarter"].astype(str)
    theme_trend["theme"] = theme_trend["theme"].str.replace("_", " ").str.title()
    fig_theme_trend = px.line(theme_trend, x="quarter", y="count", color="theme", title="Quarterly Output by Theme")
    fig_theme_trend = apply_fig_theme(fig_theme_trend, height=360)
    fig_theme_trend.update_layout(hovermode="x unified")
    st.plotly_chart(fig_theme_trend, use_container_width=True)

# Default theme selection
default_index = 0
for idx, row in summary.iterrows():
    if row["Papers (Filtered)"] > 0:
        default_index = idx
        break

selected_theme_display = st.selectbox("Select Theme", theme_names, index=default_index)
selected_theme = selected_theme_display.replace(" ", "_")

theme_papers = filtered[filtered["theme"] == selected_theme]
if theme_papers.empty:
    st.warning(f"No papers found for {selected_theme_display}")
else:
    c1, c2, c3, c4 = st.columns(4)
    growth_rate = trends.get("theme_trends", {}).get(selected_theme, {}).get("growth_rate", 0)
    c1.metric("Total Papers", f"{len(theme_papers):,}")
    c2.metric("Growth Rate", f"{growth_rate*100:+.1f}%")
    c3.metric("Sub-Topics", theme_papers["topic_id"].nunique())
    c4.metric("Universities", theme_papers["university"].nunique())

    q = theme_papers.groupby("quarter").size().reset_index(name="count")
    q["quarter"] = q["quarter"].astype(str)
    fig = px.bar(q, x="quarter", y="count", color="count", color_continuous_scale="Greens", title=f"{selected_theme_display} - Quarterly Output")
    fig = apply_fig_theme(fig, height=340)
    st.plotly_chart(fig, use_container_width=True)

    uc = theme_papers["university"].value_counts().head(10)
    fig = px.bar(x=uc.values, y=uc.index, orientation="h", color=uc.values, color_continuous_scale="Greens", title=f"Top 10 Universities in {selected_theme_display}")
    fig = apply_fig_theme(fig, height=340)
    st.plotly_chart(fig, use_container_width=True)

    def find_adjacent_themes(papers: pd.DataFrame, theme_key: str, mapping_obj: dict) -> dict:
        adjacent: dict[str, int] = {}
        theme_p = papers[papers["theme"] == theme_key]
        for _, p in theme_p.iterrows():
            kw = set(mapping_obj.get(str(p["topic_id"]), {}).get("keywords", []))
            for _, data in mapping_obj.items():
                other_theme = data.get("theme")
                if not other_theme or other_theme in (theme_key, "Other"):
                    continue
                overlap = len(kw & set(data.get("keywords", [])))
                if overlap > 0:
                    adjacent[other_theme] = adjacent.get(other_theme, 0) + overlap
        return dict(sorted(adjacent.items(), key=lambda x: x[1], reverse=True))

    adj = find_adjacent_themes(filtered, selected_theme, mapping)
    if adj:
        adj_df = pd.DataFrame({"Theme": [t.replace("_", " ").title() for t in list(adj.keys())[:5]], "Connections": list(adj.values())[:5]})
        fig_adj = px.bar(adj_df, x="Connections", y="Theme", orientation="h", color="Connections", color_continuous_scale="Greens", title=f"Top Adjacent Themes to {selected_theme_display}")
        fig_adj = apply_fig_theme(fig_adj, height=300)
        st.plotly_chart(fig_adj, use_container_width=True)
    else:
        st.info("No significant adjacent themes detected for this theme")
