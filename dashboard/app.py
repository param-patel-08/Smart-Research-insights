"""
Babcock Research Trends - Enhanced Streamlit Dashboard (updated-test)
Implements global filters, adjacent themes, university trend alerts, strength ranking, and exports.
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
from pptx import Presentation
from pptx.util import Inches, Pt

# Add parent directory to import config
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import (
    PROCESSED_PAPERS_CSV,
    TREND_ANALYSIS_PATH,
    TOPIC_MAPPING_PATH,
)
from config.themes import BABCOCK_THEMES

st.set_page_config(page_title="Babcock Research Trends", page_icon="🔬", layout="wide")

st.markdown(
    """
    <style>
    .main-header{font-size:2.1rem;font-weight:700;color:#1f4788;margin:.3rem 0 1rem}
    .sub-header{font-size:1.25rem;font-weight:700;color:#2c5aa0;margin:1.2rem 0 .6rem}
    .metric-card{background:#e6e9f0;padding:1rem;border-radius:8px;border-left:4px solid #1f4788}
    .priority-high{background:#ef9a9a;border-left-color:#c62828}
    .priority-medium{background:#ffcc80;border-left-color:#ef6c00}
    .priority-low{background:#c8e6c9;border-left-color:#2e7d32}
    </style>
    """,
    unsafe_allow_html=True,
)

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

    trends = _load_json(TREND_ANALYSIS_PATH)
    mapping = _load_json(TOPIC_MAPPING_PATH)

    # Theme + confidence from mapping
    df["theme"] = df["topic_id"].astype(str).map(lambda t: mapping.get(str(t), {}).get("theme", "Other"))
    df["confidence"] = df["topic_id"].astype(str).map(lambda t: mapping.get(str(t), {}).get("confidence", 0))
    if df["confidence"].max() <= 1:
        df["confidence"] = (df["confidence"] * 100).round(0)

    # Relevance score (confidence 40, citations 30, recency 30)
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


def _pptx_from_summary(summary_title: str, kpis: dict, tables: dict | None = None) -> bytes:
    prs = Presentation()
    # Title slide
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = summary_title
    slide.placeholders[1].text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    # KPI slide
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    title = slide.shapes.title
    title.text = "Key Metrics"
    left = Inches(0.7)
    top = Inches(1.5)
    width = Inches(9)
    height = Inches(4)
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.clear()
    for k, v in kpis.items():
        p = tf.add_paragraph()
        p.text = f"• {k}: {v}"
        p.font.size = Pt(18)
    # Tables slide
    if tables:
        for t_title, df in tables.items():
            slide = prs.slides.add_slide(prs.slide_layouts[5])
            slide.shapes.title.text = t_title
            rows, cols = min(11, len(df) + 1), min(6, len(df.columns))
            table = slide.shapes.add_table(rows, cols, Inches(0.6), Inches(1.5), Inches(9.2), Inches(4.5)).table
            # headers
            for j, col in enumerate(df.columns[:cols]):
                table.cell(0, j).text = str(col)
            # rows
            for i in range(min(10, len(df))):
                for j, col in enumerate(df.columns[:cols]):
                    table.cell(i + 1, j).text = str(df.iloc[i][col])
    bio = BytesIO()
    prs.save(bio)
    return bio.getvalue()


def add_export_section(df: pd.DataFrame, page_name: str):
    st.markdown("---")
    st.markdown("## 📤 Export Options")
    c1, c2 = st.columns(2)
    with c1:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📊 Download CSV",
            data=csv,
            file_name=f"babcock_{page_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c2:
        try:
            from openpyxl import Workbook  # noqa: F401
            out = BytesIO()
            with pd.ExcelWriter(out, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Data", index=False)
                summary = pd.DataFrame(
                    {
                        "Metric": [
                            "Total Papers",
                            "Universities",
                            "Avg Confidence",
                            "Date Range",
                        ],
                        "Value": [
                            len(df),
                            df["university"].nunique() if "university" in df.columns else "N/A",
                            f"{df['confidence'].mean():.0f}%" if "confidence" in df.columns else "N/A",
                            f"{df['date'].min().date()} to {df['date'].max().date()}" if "date" in df.columns else "N/A",
                        ],
                    }
                )
                summary.to_excel(writer, sheet_name="Summary", index=False)
            st.download_button(
                label="📈 Download Excel",
                data=out.getvalue(),
                file_name=f"babcock_{page_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception:
            st.info("Install openpyxl for Excel export: pip install openpyxl")

    # PowerPoint export (KPIs + top table preview)
    try:
        kpis = {
            "Total Papers": len(df),
            "Universities": df["university"].nunique() if "university" in df.columns else "N/A",
            "Avg Confidence": f"{df['confidence'].mean():.0f}%" if 'confidence' in df.columns else 'N/A',
        }
        top_table = df.head(10).copy()
        pptx_bytes = _pptx_from_summary(f"Babcock — {page_name.replace('_',' ').title()}", kpis, {"Preview": top_table})
        st.download_button(
            label="📽️ Download PowerPoint",
            data=pptx_bytes,
            file_name=f"babcock_{page_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
        )
    except Exception:
        st.info("Install python-pptx for PPT export: pip install python-pptx")


# Load
try:
    papers_df, trends, mapping = load_data()
except FileNotFoundError as e:
    st.error(
        f"Data files not found: {e}. Run the pipeline first: `python run_full_analysis.py`"
    )
    st.stop()

# Sidebar: Global Filters
st.sidebar.title("🔬 Research Trends")
try:
    st.sidebar.image(
        "https://via.placeholder.com/300x80/1f4788/ffffff?text=BABCOCK",
        use_column_width=True,
    )
except Exception:
    pass
st.sidebar.markdown("---")

min_date = papers_df["date"].min().date()
max_date = papers_df["date"].max().date()
cd1, cd2 = st.sidebar.columns(2)
if "filters" not in st.session_state:
    st.session_state["filters"] = {
        "start": min_date,
        "end": max_date,
        "themes": None,
        "unis": None,
        "min_conf": 0,
        "min_cit": 0,
        "kw": "",
    }

start_date = cd1.date_input("From", value=st.session_state["filters"]["start"], min_value=min_date, max_value=max_date, key="flt_start")
end_date = cd2.date_input("To", value=st.session_state["filters"]["end"], min_value=min_date, max_value=max_date, key="flt_end")

all_themes = sorted([t for t in papers_df["theme"].unique() if t != "Other"]) if "theme" in papers_df.columns else []
sel_themes = st.sidebar.multiselect("🎯 Themes", options=all_themes, default=all_themes, key="flt_themes")
sel_unis = st.sidebar.multiselect(
    "🏛️ Universities",
    options=sorted(papers_df["university"].unique()),
    default=sorted(papers_df["university"].unique())[:10],
    key="flt_unis",
)
min_conf = st.sidebar.slider("Min Confidence (%)", 0, 100, st.session_state["filters"]["min_conf"], 5, key="flt_conf")
max_cit = int(papers_df["citations"].max()) if "citations" in papers_df.columns else 100
min_cit = st.sidebar.slider("Min Citations", 0, max_cit, st.session_state["filters"]["min_cit"], key="flt_cit")
kw = st.sidebar.text_input("🔎 Keyword(s)", value=st.session_state["filters"]["kw"], placeholder="e.g., autonomy, additive manufacturing", key="flt_kw")

cols_reset = st.sidebar.columns(2)
if cols_reset[0].button("Reset Filters"):
    st.session_state["filters"] = {
        "start": min_date,
        "end": max_date,
        "themes": all_themes,
        "unis": sorted(papers_df["university"].unique())[:10],
        "min_conf": 0,
        "min_cit": 0,
        "kw": "",
    }
    st.rerun()

st.session_state["filters"]["start"] = start_date
st.session_state["filters"]["end"] = end_date
st.session_state["filters"]["themes"] = sel_themes
st.session_state["filters"]["unis"] = sel_unis
st.session_state["filters"]["min_conf"] = min_conf
st.session_state["filters"]["min_cit"] = min_cit
st.session_state["filters"]["kw"] = kw

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

papers_df = filtered

# Freshness
st.sidebar.markdown("---")
if len(papers_df) > 0:
    last_dt = papers_df["date"].max()
    days_since = (pd.Timestamp.now() - last_dt).days
    status = "🟢 Fresh" if days_since < 7 else ("🟡 Recent" if days_since < 30 else "🔴 Needs Update")
    st.sidebar.info(f"{status}\n\nLast paper: {last_dt.strftime('%Y-%m-%d')} ({days_since} days ago)")

st.sidebar.markdown("---")
st.sidebar.metric("Total Papers", f"{len(papers_df):,}")
st.sidebar.metric("Topics Found", len(mapping))
st.sidebar.metric("Universities", papers_df["university"].nunique())

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["📊 Overview", "🎯 Theme Analysis", "⚡ Emerging Topics", "🏛️ Universities", "📈 Trends Over Time", "🧪 Data Quality"],
    label_visibility="collapsed",
)

# Overview
if page == "📊 Overview":
    st.markdown('<p class="main-header">🔬 Babcock Research Trends Dashboard</p>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📄 Papers Analyzed", f"{len(papers_df):,}")
    c2.metric("🧩 Topics", len(mapping))
    c3.metric("🏛️ Universities", papers_df["university"].nunique())
    try:
        avg_growth = sum(p["growth_rate"] for p in trends["strategic_priorities"]) / max(1, len(trends["strategic_priorities"]))
        c4.metric("📈 Avg Growth", f"{avg_growth*100:+.1f}%")
    except Exception:
        c4.metric("📈 Avg Growth", "N/A")

    st.markdown("---")
    st.markdown('<p class="sub-header">🎯 Strategic Theme Priorities</p>', unsafe_allow_html=True)
    for pr in trends.get("strategic_priorities", []):
        theme = pr["theme"].replace("_", " ").title()
        growth = pr.get("growth_rate", 0)
        papers = pr.get("total_papers", 0)
        category = pr.get("category", "LOW").lower()
        indicator = "🚀 HIGH GROWTH" if growth > 0.5 else ("📈 GROWING" if growth > 0.1 else ("➡️ STABLE" if growth >= 0 else "📉 DECLINING"))
        st.markdown(
            f"<div class='metric-card priority-{category}'><h4>{theme}</h4><p><strong>{indicator}</strong> ({category.upper()})</p><p>Growth: <strong>{growth*100:+.1f}%</strong> | Papers: <strong>{papers:,}</strong></p></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown('<p class="sub-header">📊 Papers per Strategic Theme</p>', unsafe_allow_html=True)
    theme_counts = papers_df["theme"].value_counts()
    theme_counts = theme_counts[theme_counts.index != "Other"]
    fig = px.bar(x=theme_counts.values, y=[t.replace("_", " ").title() for t in theme_counts.index], orientation="h", color=theme_counts.values, color_continuous_scale="Blues", title="Papers per Theme")
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# Theme Analysis
elif page == "🎯 Theme Analysis":
    st.markdown('<p class="main-header">🎯 Theme Analysis</p>', unsafe_allow_html=True)
    theme_names = [t.replace('_', ' ').title() for t in BABCOCK_THEMES.keys()]
    selected_theme_display = st.selectbox("Select Theme", theme_names)
    selected_theme = selected_theme_display.replace(" ", "_")
    theme_papers = papers_df[papers_df["theme"] == selected_theme]
    if theme_papers.empty:
        st.warning(f"No papers found for {selected_theme_display}")
        st.stop()

    col1, col2, col3, col4 = st.columns(4)
    growth_rate = trends.get("theme_trends", {}).get(selected_theme, {}).get("growth_rate", 0)
    col1.metric("Total Papers", f"{len(theme_papers):,}")
    col2.metric("Growth Rate", f"{growth_rate*100:+.1f}%")
    col3.metric("Sub-Topics", theme_papers["topic_id"].nunique())
    col4.metric("Universities", theme_papers["university"].nunique())

    # Trend and Top Universities
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📈 Trend Over Time")
        q = theme_papers.groupby("quarter").size().reset_index(name="count")
        q["quarter"] = q["quarter"].astype(str)
        fig = px.bar(q, x="quarter", y="count", color="count", color_continuous_scale="Blues", title=f"{selected_theme_display} - Quarterly Output")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("🏛️ Top Universities")
        uc = theme_papers["university"].value_counts().head(10)
        fig = px.bar(x=uc.values, y=uc.index, orientation="h", color=uc.values, color_continuous_scale="Greens", title=f"Top 10 Universities in {selected_theme_display}")
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    # Adjacent Themes via keyword overlap
    st.subheader("🔗 Adjacent Technology Themes")
    def find_adjacent_themes(papers: pd.DataFrame, theme_key: str, mapping_obj: dict) -> dict:
        adjacent: dict[str, int] = {}
        theme_p = papers[papers["theme"] == theme_key]
        for _, p in theme_p.iterrows():
            kw = set(mapping_obj.get(str(p["topic_id"]), {}).get("keywords", []))
            for otid, data in mapping_obj.items():
                other_theme = data.get("theme")
                if not other_theme or other_theme in (theme_key, "Other"):
                    continue
                overlap = len(kw & set(data.get("keywords", [])))
                if overlap > 0:
                    adjacent[other_theme] = adjacent.get(other_theme, 0) + overlap
        return dict(sorted(adjacent.items(), key=lambda x: x[1], reverse=True))

    adj = find_adjacent_themes(papers_df, selected_theme, mapping)
    if adj:
        adj_df = pd.DataFrame({"Theme": [t.replace("_", " ").title() for t in list(adj.keys())[:5]], "Connections": list(adj.values())[:5]})
        fig_adj = px.bar(adj_df, x="Connections", y="Theme", orientation="h", color="Connections", color_continuous_scale="Blues", title=f"Top Adjacent Themes to {selected_theme_display}")
        fig_adj.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_adj, use_container_width=True)
    else:
        st.info("No significant adjacent themes detected for this theme")

    st.markdown("---")
    # University Trend Alerts
    st.subheader("🚨 University Trend Alerts")
    thr = st.slider("Alert threshold (% change)", 20, 200, 50, 10)
    def detect_university_trends(papers: pd.DataFrame, theme_key: str, threshold: float = 50.0):
        alerts = []
        tp = papers[papers["theme"] == theme_key].copy()
        tp["quarter"] = tp["date"].dt.to_period("Q")
        if tp.empty:
            return []
        for uni in tp["university"].unique():
            up = tp[tp["university"] == uni]
            q = up.groupby("quarter").size().sort_index()
            if len(q) < 2:
                continue
            recent = q.iloc[-1]
            prev = q.iloc[-2]
            if prev == 0 and recent > 0:
                change, typ = 999, "NEW"
            elif prev > 0:
                change = (recent - prev) / prev * 100
                if change >= threshold:
                    typ = "SURGE"
                elif change <= -threshold:
                    typ = "DECLINE"
                else:
                    continue
            else:
                continue
            alerts.append({"university": uni, "type": typ, "change_pct": change, "recent": int(recent), "previous": int(prev), "quarters": {str(k): int(v) for k, v in q.iloc[-4:].items()},})
        return sorted(alerts, key=lambda x: abs(x["change_pct"]), reverse=True)

    alerts = detect_university_trends(papers_df, selected_theme, thr)
    if alerts:
        c1, c2, c3 = st.columns(3)
        c1.metric("🚀 Surging", sum(1 for a in alerts if a["type"] == "SURGE"))
        c2.metric("📉 Declining", sum(1 for a in alerts if a["type"] == "DECLINE"))
        c3.metric("🆕 New Entrants", sum(1 for a in alerts if a["type"] == "NEW"))
        for a in alerts[:10]:
            with st.expander(f"{a['university']} — {a['change_pct']:.0f}% ({a['type']})"):
                cc1, cc2, cc3 = st.columns(3)
                cc1.metric("Recent Quarter", f"{a['recent']} papers", delta=f"{a['recent']-a['previous']} vs prev")
                cc2.metric("Previous Quarter", f"{a['previous']} papers")
                cc3.metric("Change", f"{a['change_pct']:.0f}%")
                qdf = pd.DataFrame({"Quarter": list(a["quarters"].keys()), "Papers": list(a["quarters"].values())})
                figq = px.line(qdf, x="Quarter", y="Papers", markers=True, title=f"Quarterly Trend — {a['university']}")
                figq.update_layout(height=250, showlegend=False)
                st.plotly_chart(figq, use_container_width=True)
    else:
        st.info(f"No universities changed by more than ±{thr}% in {selected_theme_display}")

    st.markdown("---")
    st.subheader("📰 Recent Papers in This Theme")
    # Sort by relevance then date
    recent = theme_papers.sort_values(["relevance_score", "date"], ascending=[False, False]).head(10)
    for _, p in recent.iterrows():
        badge = f"<span style='background:#1f4788;color:#fff;padding:2px 6px;border-radius:6px;font-size:0.8rem;'>Relevance {p['relevance_score']:.0f}</span>"
        st.markdown(f"**{p['title']}**  {badge}", unsafe_allow_html=True)
        st.caption(f"🏛️ {p['university']} | 📅 {p['date'].strftime('%Y-%m-%d')}")
        if pd.notna(p.get("abstract")) and p.get("abstract"):
            with st.expander("View Abstract"):
                st.write(str(p["abstract"])[:500] + ("..." if len(str(p["abstract"])) > 500 else ""))
        st.markdown("---")

    add_export_section(theme_papers, "theme_analysis")

# Emerging Topics
elif page == "⚡ Emerging Topics":
    st.markdown('<p class="main-header">⚡ Emerging Research Topics</p>', unsafe_allow_html=True)
    min_growth = st.slider("Minimum Growth Rate", 0, 200, 50, 10, format="%d%%")
    emerging = [t for t in trends.get("emerging_topics", []) if t.get("growth_rate", 0) * 100 >= min_growth]
    st.info(f"{len(emerging)} topics with >{min_growth}% growth")
    for i, t in enumerate(emerging, 1):
        keys = ", ".join(t.get("keywords", [])[:8])
        theme = t.get("theme", "").replace("_", " ").title()
        growth = t.get("growth_rate", 0)
        with st.expander(f"#{i} - {keys} ({growth*100:+.0f}% growth) — {theme}"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Theme", theme)
            c2.metric("Growth", f"{growth*100:+.0f}%")
            c3.metric("Recent", f"{t.get('recent_quarter_count', 0)}")
            c4.metric("Previous", f"{t.get('previous_quarter_count', 0)}")
            topic_id = t.get("topic_id")
            if topic_id is not None and "topic_id" in papers_df.columns:
                demo = papers_df[papers_df["topic_id"] == topic_id].nlargest(3, "date")
                for _, p in demo.iterrows():
                    st.markdown(f"- **{p['title']}** — {p['university']} ({p['date'].strftime('%Y-%m-%d')})")
    add_export_section(papers_df, "emerging_topics")

# Universities
elif page == "🏛️ Universities":
    st.markdown('<p class="main-header">🏛️ University Analysis</p>', unsafe_allow_html=True)
    st.markdown("## 🏛️ University Rankings by Technology Theme")
    ranking_theme = st.selectbox("Rank universities by:", options=["All Themes"] + sorted([t for t in papers_df["theme"].unique() if t != "Other"]))

    def calc_strength(df: pd.DataFrame, uni: str, theme_key: str | None):
        if theme_key and theme_key != "All Themes":
            d = df[(df["university"] == uni) & (df["theme"] == theme_key)]
        else:
            d = df[df["university"] == uni]
        if d.empty:
            return {"score": 0, "papers": 0, "growth": 0.0, "cit": 0.0, "conf": 0.0}
        papers_ct = len(d)
        d = d.copy(); d["quarter"] = d["date"].dt.to_period("Q")
        q = d.groupby("quarter").size().sort_index()
        growth = 0.0
        if len(q) >= 2:
            prev, recent = q.iloc[-2], q.iloc[-1]
            growth = ((recent - prev) / prev * 100) if prev > 0 else 0.0
        cit = float(d.get("citations", pd.Series(dtype=float)).mean()) if "citations" in d.columns else 0.0
        conf = float(d.get("confidence", pd.Series(dtype=float)).mean()) if "confidence" in d.columns else 0.0
        score = papers_ct * 0.4 + max(0.0, growth) * 0.3 + cit * 0.2 + conf * 0.1
        return {"score": score, "papers": papers_ct, "growth": max(0.0, growth), "cit": cit, "conf": conf}

    ranks = []
    for u in sorted(papers_df["university"].unique()):
        m = calc_strength(papers_df, u, ranking_theme if ranking_theme != "All Themes" else None)
        ranks.append({
            "University": u,
            "Strength Score": round(m["score"], 1),
            "Papers": m["papers"],
            "Growth Rate (%)": round(m["growth"], 1),
            "Avg Citations": round(m["cit"], 1),
            "Avg Confidence (%)": round(m["conf"], 0),
        })
    rdf = pd.DataFrame(ranks).sort_values("Strength Score", ascending=False)
    rdf.insert(0, "Rank", range(1, len(rdf) + 1))
    st.dataframe(rdf, use_container_width=True, hide_index=True)
    st.download_button(
        label="📥 Download University Rankings (CSV)",
        data=rdf.to_csv(index=False),
        file_name=f"university_rankings_{ranking_theme.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.subheader("📊 Overall Research Output Rankings")
    uc = papers_df["university"].value_counts()
    fig = px.bar(x=uc.head(15).values, y=uc.head(15).index, orientation="h", color=uc.head(15).values, color_continuous_scale="Blues", title="Top 15 Universities by Total Papers")
    fig.update_layout(height=380, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🔍 University Deep Dive")
    sel_uni = st.selectbox("Select University", sorted(papers_df["university"].unique()))
    uni_p = papers_df[papers_df["university"] == sel_uni]
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

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🎯 Research Themes")
        tdist = uni_p["theme"].value_counts()
        fig = px.pie(values=tdist.values, names=[t.replace('_',' ').title() for t in tdist.index], title=f"{sel_uni} - Theme Distribution")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("📈 Output Over Time")
        q = uni_p.groupby("quarter").size().reset_index(name="count"); q["quarter"] = q["quarter"].astype(str)
        fig = px.line(q, x="quarter", y="count", markers=True, title=f"{sel_uni} - Quarterly Output")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"📰 Recent Papers from {sel_uni}")
    for _, p in uni_p.sort_values(["relevance_score", "date"], ascending=[False, False]).head(10).iterrows():
        st.markdown(f"**{p['title']}**")
        st.caption(f"🎯 {p['theme'].replace('_',' ').title()} | 📅 {p['date'].strftime('%Y-%m-%d')}")
        if pd.notna(p.get("abstract")) and p.get("abstract"):
            with st.expander("View Abstract"):
                st.write(str(p["abstract"])[:400] + ("..." if len(str(p["abstract"])) > 400 else ""))
        st.markdown("---")

    add_export_section(uni_p, "universities")

# Trends Over Time
elif page == "📈 Trends Over Time":
    st.markdown('<p class="main-header">📈 Temporal Trends Analysis</p>', unsafe_allow_html=True)
    st.subheader("📊 Overall Research Activity")
    qa = papers_df.groupby("quarter").size().reset_index(name="count"); qa["quarter"] = qa["quarter"].astype(str)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=qa["quarter"], y=qa["count"], mode="lines+markers", name="All Themes"))
    fig.update_layout(title="Overall Research Output", xaxis_title="Quarter", yaxis_title="Papers", height=380)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🎯 Trends by Theme")
    names = sorted([t.replace("_", " ").title() for t in papers_df["theme"].unique() if t != "Other"]) if "theme" in papers_df.columns else []
    picks = st.multiselect("Select Themes to Compare", names, default=names[:3])
    if picks:
        raw = [t.replace(" ", "_") for t in picks]
        f = papers_df[papers_df["theme"].isin(raw)]
        qt = f.groupby(["quarter", "theme"]).size().reset_index(name="count")
        qt["quarter"], qt["theme"] = qt["quarter"].astype(str), qt["theme"].str.replace("_", " ").str.title()
        fig = px.line(qt, x="quarter", y="count", color="theme", title="Research Output Trends")
        fig.update_layout(height=420, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📊 Growth Rates by Theme")
        rows = []
        for t in raw:
            tr = trends.get("theme_trends", {}).get(t, {})
            rows.append({"Theme": t.replace("_", " ").title(), "Total Papers": tr.get("total_papers", 0), "Avg Growth Rate": f"{tr.get('growth_rate', 0)*100:+.1f}%",})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    add_export_section(papers_df, "trends")

# Data Quality
elif page == "🧪 Data Quality":
    st.markdown('<p class="main-header">🧪 Data Quality</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    missing_abs = papers_df['abstract'].isna().sum() if 'abstract' in papers_df.columns else 0
    c1.metric("Missing Abstracts", f"{missing_abs:,}")
    c2.metric("Avg Confidence", f"{papers_df['confidence'].mean():.0f}%" if 'confidence' in papers_df.columns else 'N/A')
    c3.metric("Has Citations", f"{papers_df['citations'].notna().mean()*100:.0f}%" if 'citations' in papers_df.columns else 'N/A')

    st.markdown("---")
    colA, colB = st.columns(2)
    with colA:
        st.subheader("Confidence Distribution")
        if 'confidence' in papers_df.columns:
            fig = px.histogram(papers_df, x='confidence', nbins=20, title='Confidence (%)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No confidence field available")
    with colB:
        st.subheader("Citations Distribution")
        if 'citations' in papers_df.columns:
            fig = px.histogram(papers_df, x='citations', nbins=20, title='Citations')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No citations field available")

    st.markdown("---")
    st.subheader("Records with Missing Data")
    issues = []
    if 'abstract' in papers_df.columns:
        issues.append(papers_df[papers_df['abstract'].isna()].assign(issue='missing_abstract'))
    if 'citations' in papers_df.columns:
        issues.append(papers_df[papers_df['citations'].isna()].assign(issue='missing_citations'))
    if issues:
        issues_df = pd.concat(issues, ignore_index=True).drop_duplicates(subset=['title'])
        st.dataframe(issues_df[['title','university','date','issue','confidence']].sort_values('date', ascending=False), use_container_width=True)
        add_export_section(issues_df, 'data_quality')
    else:
        st.success("No data quality issues detected in filtered dataset")
