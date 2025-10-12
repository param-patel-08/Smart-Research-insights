"""
Babcock Research Trends - Prescience-style Clean Dashboard
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

# ---- Config imports ----
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import (  # type: ignore
    PROCESSED_PAPERS_CSV,
    TREND_ANALYSIS_PATH,
    TOPIC_MAPPING_PATH,
)
from config.themes import BABCOCK_THEMES  # type: ignore

# ---- Page + Theme ----
st.set_page_config(page_title="Babcock Research Trends", page_icon="", layout="wide")

# Plotly sane defaults (light)
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = ["#22c55e", "#0ea5e9", "#111827", "#64748b", "#f59e0b"]

# Load external CSS
css_path = os.path.join(os.path.dirname(__file__), "theme.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---- Data Loading ----
@st.cache_data
def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return json.loads(f.read())

@st.cache_data
def load_data():
    if not os.path.exists(PROCESSED_PAPERS_CSV):
        raise FileNotFoundError(PROCESSED_PAPERS_CSV)
    df = pd.read_csv(PROCESSED_PAPERS_CSV)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    # Normalize university names to avoid mismatches (strip/condense spaces)
    if "university" in df.columns:
        df["university"] = (
            df["university"].fillna("Unknown").astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
        )

    trends = _load_json(TREND_ANALYSIS_PATH)
    mapping = _load_json(TOPIC_MAPPING_PATH)

    # Theme + confidence from mapping
    df["theme"] = df["topic_id"].astype(str).map(lambda t: mapping.get(str(t), {}).get("theme", "Other"))
    df["confidence"] = df["topic_id"].astype(str).map(lambda t: mapping.get(str(t), {}).get("confidence", 0))

    # Reinstate Cybersecurity assignments when similarity score is strong but original mapping fell back to another theme.
    cyber_topics = {
        str(tid): data.get("all_scores", {}).get("Cybersecurity", 0)
        for tid, data in mapping.items()
        if data.get("all_scores", {}).get("Cybersecurity", 0) >= 0.12 and data.get("theme") != "Cybersecurity"
    }
    if cyber_topics:
        mask = df["topic_id"].astype(str).isin(cyber_topics.keys())
        if mask.any():
            df.loc[mask, "theme"] = "Cybersecurity"
            df.loc[mask, "confidence"] = df.loc[mask, "topic_id"].astype(str).map(cyber_topics)
    if df["confidence"].max() <= 1:
        df["confidence"] = (df["confidence"] * 100).round(0)

    # Scoring
    if "citations" in df.columns and pd.api.types.is_numeric_dtype(df["citations"]):
        max_cit = max(1, df["citations"].max())
        df["citation_score"] = (df["citations"] / max_cit) * 100
    else:
        df["citation_score"] = 0
    days_old = (pd.Timestamp.now() - pd.to_datetime(df["date"]).fillna(pd.Timestamp.now())).dt.days
    df["recency_score"] = (100 - (days_old / 730) * 100).clip(lower=0, upper=100)
    df["relevance_score"] = (
        df["confidence"].fillna(0) * 0.40
        + df["citation_score"].fillna(0) * 0.30
        + df["recency_score"].fillna(0) * 0.30
    ).clip(0, 100)

    df["quarter"] = df["date"].dt.to_period("Q")
    return df, trends, mapping

try:
    papers_df, trends, mapping = load_data()
except FileNotFoundError as e:
    st.error(f"Data files not found: {e}. Run the pipeline first: `python run_full_analysis.py`")
    st.stop()

# ---- Sidebar (dark) ----
st.sidebar.title(" Research Trends")
try:
    # Reliable placeholder logo and modern param (use_container_width)
    st.sidebar.image(
        "https://dummyimage.com/260x60/111827/ffffff.png&text=BABCOCK",
        use_container_width=True,
    )
except Exception:
    pass
st.sidebar.markdown("---")

min_date = papers_df["date"].min().date()
max_date = papers_df["date"].max().date()
cd1, cd2 = st.sidebar.columns(2)
start_date = cd1.date_input("From", value=min_date, min_value=min_date, max_value=max_date, key="from_date")
end_date = cd2.date_input("To", value=max_date, min_value=min_date, max_value=max_date, key="to_date")

all_themes = sorted(list(BABCOCK_THEMES.keys()))
sel_themes = st.sidebar.multiselect(" Themes", options=all_themes, default=all_themes, key="themes")
all_unis = sorted(papers_df["university"].unique())
select_all_unis = st.sidebar.checkbox("All universities", value=True, key="all_unis_flag")
if select_all_unis:
    sel_unis = all_unis
else:
    sel_unis = st.sidebar.multiselect(
        "Universities",
        options=all_unis,
        default=all_unis,
        key="unis",
    )
st.sidebar.caption(f"{len(sel_unis)}/{len(all_unis)} universities selected")
min_conf = st.sidebar.slider("Min Confidence (%)", 0, 100, 0, 5, key="min_conf")
max_cit = int(papers_df["citations"].max()) if "citations" in papers_df.columns else 100
min_cit = st.sidebar.slider("Min Citations", 0, max_cit, 0, key="min_cit")
kw = st.sidebar.text_input("Keyword(s)", value="", placeholder="e.g., autonomy, additive manufacturing", key="kw")

# Reset filters button restores defaults
if st.sidebar.button("Reset filters"):
    st.session_state["from_date"] = min_date
    st.session_state["to_date"] = max_date
    st.session_state["themes"] = all_themes
    st.session_state["all_unis_flag"] = True
    st.session_state["unis"] = all_unis
    st.session_state["min_conf"] = 0
    st.session_state["min_cit"] = 0
    st.session_state["kw"] = ""
    st.experimental_rerun()

# Apply filters
filtered = papers_df.copy()
filtered = filtered[(filtered["date"].dt.date >= start_date) & (filtered["date"].dt.date <= end_date)]
if sel_themes:
    filtered = filtered[filtered["theme"].isin(sel_themes)]
if sel_unis:
    filtered = filtered[filtered["university"].isin(sel_unis)]
filtered = filtered[filtered["confidence"] >= min_conf]
if "citations" in filtered.columns:
    filtered = filtered[filtered["citations"] >= min_cit]
if kw:
    kws = [k.strip().lower() for k in kw.split(",") if k.strip()]
    if kws:
        mask = filtered.apply(
            lambda r: any(
                k in str(r.get("title", "")).lower() or k in str(r.get("abstract", "")).lower() for k in kws
            ),
            axis=1,
        )
        filtered = filtered[mask]

# Selection summary (always visible)
st.markdown(
    f"<div class='card-alt' style='display:flex;gap:1rem;align-items:center'>"
    f"<span class='badge'>Date</span> <b>{start_date}</b> → <b>{end_date}</b>"
    f"<span class='badge'>Themes</span> {len(sel_themes) if sel_themes else 0}"
    f"<span class='badge'>Universities</span> {len(sel_unis) if sel_unis else 0}"
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
        "Selected universities": len(sel_unis),
        "Total universities": len(all_unis),
    })

# For charts
def apply_fig_theme(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#0b0f19"),
        margin=dict(l=40, r=20, t=50, b=40)
    )
    return fig

# ---- Header ----
st.markdown('<p class="main-header">Babcock Research Trends Dashboard</p>', unsafe_allow_html=True)

"""Primary navigation as top-level tabs (no selectbox)."""
tab_overview, tab_theme, tab_unis, tab_trends, tab_quality = st.tabs(["Overview", "Theme Analysis", "Universities", "Trends", "Data Quality"])

with tab_overview:
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
        title="Papers per Theme (All Babcock Themes)"
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
        st.dataframe(uc.head(15), use_container_width=True, hide_index=True)
    else:
        st.info("No data available for current filters")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Recent Papers List
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

with tab_theme:
    theme_order = list(BABCOCK_THEMES.keys())
    theme_names = [t.replace('_', ' ').title() for t in theme_order]

    # Theme overview summary for current filters, always showing all themes
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
    summary = summary[
        [
            "Theme",
            "papers",
            "Total Papers (Dataset)",
            "Growth Rate (%)",
            "universities",
            "topics",
        ]
    ].rename(columns={
        "papers": "Papers (Filtered)",
        "universities": "Universities",
        "topics": "Topics",
    })

    st.markdown('<p class="sub-header">Theme Overview</p>', unsafe_allow_html=True)
    st.dataframe(summary, use_container_width=True, hide_index=True)

    # Multi-theme trend chart to highlight coverage per theme
    if not filtered.empty:
        quarters = sorted(filtered["quarter"].unique())
        idx = pd.MultiIndex.from_product([quarters, theme_order], names=["quarter", "theme"])
        theme_trend = filtered.groupby(["quarter", "theme"]).size().reindex(idx, fill_value=0).reset_index(name="count")
        theme_trend["quarter"] = theme_trend["quarter"].astype(str)
        theme_trend["theme"] = theme_trend["theme"].str.replace("_", " ").str.title()
        fig_theme_trend = px.line(
            theme_trend,
            x="quarter",
            y="count",
            color="theme",
            title="Quarterly Output by Theme",
        )
        fig_theme_trend = apply_fig_theme(fig_theme_trend, height=360)
        fig_theme_trend.update_layout(hovermode="x unified")
        st.plotly_chart(fig_theme_trend, use_container_width=True)

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

with tab_unis:
    st.markdown('<p class="sub-header">Overall Research Output Rankings</p>', unsafe_allow_html=True)
    uc = filtered["university"].value_counts()
    fig = px.bar(x=uc.head(15).values, y=uc.head(15).index, orientation="h", color=uc.head(15).values, color_continuous_scale="Greens", title="Top 15 Universities by Total Papers")
    fig = apply_fig_theme(fig, height=380)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<p class="sub-header">University Deep Dive</p>', unsafe_allow_html=True)
    sel_uni = st.selectbox("Select University", sorted(filtered["university"].unique()))
    uni_p = filtered[filtered["university"] == sel_uni]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Papers", f"{len(uni_p):,}")
    c2.metric("Themes", uni_p["theme"].nunique())
    c3.metric("Topics", uni_p["topic_id"].nunique())
    qg = uni_p.groupby("quarter").size()
    if len(qg) >= 2:
        growth = (qg.iloc[-1] - qg.iloc[-2]) / max(1, qg.iloc[-2]) * 100
        c4.metric("Recent Growth", f"{growth:+.0f}%")
    else:
        c4.metric("Recent Growth", "N/A")

    colA, colB = st.columns(2)
    with colA:
        st.markdown('<p class="sub-header">Research Themes</p>', unsafe_allow_html=True)
        tdist = uni_p["theme"].value_counts()
        fig = px.pie(values=tdist.values, names=[t.replace('_',' ').title() for t in tdist.index], title=f"{sel_uni} - Theme Distribution")
        fig = apply_fig_theme(fig, height=350)
        st.plotly_chart(fig, use_container_width=True)
    with colB:
        st.markdown('<p class="sub-header">Output Over Time</p>', unsafe_allow_html=True)
        q = uni_p.groupby("quarter").size().reset_index(name="count"); q["quarter"] = q["quarter"].astype(str)
        fig = px.line(q, x="quarter", y="count", markers=True, title=f"{sel_uni} - Quarterly Output")
        fig = apply_fig_theme(fig, height=350)
        st.plotly_chart(fig, use_container_width=True)

with tab_trends:
    st.markdown('<p class="sub-header">Temporal Trends Analysis</p>', unsafe_allow_html=True)
    qa = filtered.groupby("quarter").size().reset_index(name="count"); qa["quarter"] = qa["quarter"].astype(str)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=qa["quarter"], y=qa["count"], mode="lines+markers", name="All Themes"))
    fig = apply_fig_theme(fig, height=380)
    fig.update_layout(title="Overall Research Output", xaxis_title="Quarter", yaxis_title="Papers")
    st.plotly_chart(fig, use_container_width=True)

    names = [t.replace("_", " ").title() for t in BABCOCK_THEMES.keys()]
    picks = st.multiselect("Select Themes to Compare", names, default=names)
    if picks:
        raw = [t.replace(" ", "_") for t in picks]
        f = filtered[filtered["theme"].isin(raw)]
        quarters = sorted(filtered["quarter"].unique())
        base = pd.MultiIndex.from_product([quarters, raw], names=["quarter", "theme"]) 
        qt = f.groupby(["quarter", "theme"]).size().reindex(base, fill_value=0).reset_index(name="count")
        qt["quarter"], qt["theme"] = qt["quarter"].astype(str), qt["theme"].str.replace("_", " ").str.title()
        fig = px.line(qt, x="quarter", y="count", color="theme", title="Research Output Trends (Selected Themes)")
        fig = apply_fig_theme(fig, height=420)
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

with tab_quality:
    st.markdown('<p class="sub-header">Data Quality</p>', unsafe_allow_html=True)
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

# ---- Exports ----
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.subheader("Export")
export_df = filtered.copy()
colE1, colE2 = st.columns(2)
with colE1:
    st.download_button(
        label="Download CSV",
        data=export_df.to_csv(index=False),
        file_name=f"babcock_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
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
            file_name=f"babcock_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    except Exception:
        st.info("Install openpyxl for Excel export: pip install openpyxl")
