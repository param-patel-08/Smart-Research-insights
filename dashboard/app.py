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
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import streamlit as st
import numpy as np
from collections import defaultdict

# ---- Config imports ----
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import (  # type: ignore
    PROCESSED_PAPERS_CSV,
    TREND_ANALYSIS_PATH,
    TOPIC_MAPPING_PATH,
    ALL_UNIVERSITIES,
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

    # PRESERVE original theme from CSV (assigned during collection)
    # BERTopic mapping is only used for confidence scores and topic details
    # If CSV doesn't have theme column, fall back to BERTopic mapping
    if "theme" not in df.columns:
        df["theme"] = df["topic_id"].astype(str).map(lambda t: mapping.get(str(t), {}).get("theme", "Other"))
    
    df["confidence"] = df["topic_id"].astype(str).map(lambda t: mapping.get(str(t), {}).get("confidence", 0))
    
    # ADD SUB-THEME MAPPING (from hierarchical structure)
    df["sub_theme"] = df["topic_id"].astype(str).map(lambda t: mapping.get(str(t), {}).get("sub_theme", None))
    df["sub_theme_confidence"] = df["topic_id"].astype(str).map(lambda t: mapping.get(str(t), {}).get("sub_theme_confidence", 0))

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

def generate_insights(df, trends, mapping):
    """Generate actionable insights from the data"""
    insights = []
    
    # 1. Emerging Sub-Themes (fastest growing)
    sub_theme_growth = df.groupby(['sub_theme', df['date'].dt.year]).size().unstack(fill_value=0)
    if len(sub_theme_growth.columns) >= 2:
        recent_year = sub_theme_growth.columns[-1]
        prev_year = sub_theme_growth.columns[-2]
        growth_rates = ((sub_theme_growth[recent_year] - sub_theme_growth[prev_year]) / 
                       (sub_theme_growth[prev_year] + 1) * 100)
        top_emerging = growth_rates.nlargest(3)
        
        if len(top_emerging) > 0 and top_emerging.iloc[0] > 20:
            insights.append({
                "type": "emerging",
                "icon": "🚀",
                "title": "Rapid Growth Detected",
                "message": f"{top_emerging.index[0]} showing {top_emerging.iloc[0]:.0f}% growth",
                "detail": f"From {int(sub_theme_growth.loc[top_emerging.index[0], prev_year])} papers ({prev_year}) to {int(sub_theme_growth.loc[top_emerging.index[0], recent_year])} ({recent_year})"
            })
    
    # 2. Collaboration Opportunities (low research volume but high strategic priority)
    theme_counts = df.groupby('theme').size()
    high_priority_themes = [p['theme'] for p in trends.get('strategic_priorities', [])[:3]]
    for theme in high_priority_themes:
        if theme in theme_counts and theme_counts[theme] < 1500:
            insights.append({
                "type": "opportunity",
                "icon": "💡",
                "title": "Collaboration Gap",
                "message": f"{theme.replace('_', ' ')} is high priority but underrepresented",
                "detail": f"Only {theme_counts[theme]:,} papers vs {theme_counts.max():,} in leading theme"
            })
            break
    
    # 3. Research Concentration
    top_unis = df['university'].value_counts()
    concentration = (top_unis.head(3).sum() / len(df) * 100)
    if concentration > 40:
        insights.append({
            "type": "concentration",
            "icon": "🎯",
            "title": "Research Concentration",
            "message": f"Top 3 universities produce {concentration:.0f}% of research",
            "detail": f"{top_unis.index[0]} leads with {top_unis.iloc[0]:,} papers"
        })
    
    # 4. Quality vs Quantity
    if 'quality_score' in df.columns:
        high_quality = df[df['quality_score'] > 70]
        quality_by_theme = high_quality.groupby('theme').size().sort_values(ascending=False)
        if len(quality_by_theme) > 0:
            top_quality_theme = quality_by_theme.index[0]
            quality_pct = (quality_by_theme.iloc[0] / df[df['theme']==top_quality_theme].shape[0] * 100)
            insights.append({
                "type": "quality",
                "icon": "⭐",
                "title": "Quality Leader",
                "message": f"{top_quality_theme.replace('_', ' ')} has highest quality research",
                "detail": f"{quality_pct:.0f}% of papers score >70 quality"
            })
    
    # 5. Temporal Trends
    recent_6m = df[df['date'] >= (df['date'].max() - pd.Timedelta(days=180))]
    recent_growth = len(recent_6m) / (len(df) - len(recent_6m)) * 100 if len(df) > len(recent_6m) else 0
    if recent_growth > 15:
        insights.append({
            "type": "trend",
            "icon": "📈",
            "title": "Accelerating Research",
            "message": f"Last 6 months show {recent_growth:.0f}% increase",
            "detail": f"{len(recent_6m):,} recent papers indicate strong momentum"
        })
    
    # 6. Cross-theme opportunities
    if 'all_scores' in str(mapping.values()):
        # Find topics that span multiple themes (good for collaboration)
        multi_theme_topics = []
        for topic_id, data in mapping.items():
            all_scores = data.get('all_scores', {})
            high_scores = [t for t, s in all_scores.items() if s > 0.3]
            if len(high_scores) > 1:
                multi_theme_topics.append(topic_id)
        
        if len(multi_theme_topics) > 5:
            insights.append({
                "type": "collaboration",
                "icon": "🤝",
                "title": "Cross-Theme Potential",
                "message": f"{len(multi_theme_topics)} topics span multiple themes",
                "detail": "Strong opportunity for interdisciplinary collaboration"
            })
    
    return insights[:5]  # Return top 5 insights

# ========== ADVANCED VISUALIZATIONS ==========

def create_sunburst_chart(df, mapping):
    """Create hierarchical sunburst: Theme > Sub-theme > Topic"""
    # Build hierarchy data
    hierarchy_data = []
    
    for _, row in df.iterrows():
        topic_id = str(row['topic_id'])
        if topic_id in mapping:
            topic_info = mapping[topic_id]
            parent_theme = row['theme']
            sub_theme = row.get('sub_theme') or 'Other'
            
            hierarchy_data.append({
                'parent_theme': parent_theme,
                'sub_theme': sub_theme,
                'topic_id': topic_id,
                'count': 1
            })
    
    hierarchy_df = pd.DataFrame(hierarchy_data)
    
    # Aggregate counts
    theme_counts = hierarchy_df.groupby(['parent_theme']).size().reset_index(name='count')
    subtheme_counts = hierarchy_df.groupby(['parent_theme', 'sub_theme']).size().reset_index(name='count')
    topic_counts = hierarchy_df.groupby(['parent_theme', 'sub_theme', 'topic_id']).size().reset_index(name='count')
    
    # Build sunburst data
    labels = ['All Research']
    parents = ['']
    values = [len(df)]
    colors = []
    
    color_map = px.colors.qualitative.Set3
    
    # Add themes
    for i, (_, row) in enumerate(theme_counts.iterrows()):
        labels.append(row['parent_theme'].replace('_', ' '))
        parents.append('All Research')
        values.append(row['count'])
        colors.append(color_map[i % len(color_map)])
    
    # Add sub-themes
    for _, row in subtheme_counts.iterrows():
        labels.append(row['sub_theme'].replace('_', ' '))
        parents.append(row['parent_theme'].replace('_', ' '))
        values.append(row['count'])
    
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(
            line=dict(color='white', width=2)
        ),
        hovertemplate='<b>%{label}</b><br>Papers: %{value}<br>%{percentParent}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Research Hierarchy: Themes → Sub-Themes → Topics",
        height=600,
        font=dict(size=11),
        margin=dict(t=50, l=0, r=0, b=0)
    )
    
    return fig

def create_growth_heatmap(df):
    """Create time-series heatmap showing sub-theme growth"""
    # Group by sub-theme and quarter
    df_copy = df.copy()
    df_copy['year_quarter'] = df_copy['date'].dt.to_period('Q').astype(str)
    
    heatmap_data = df_copy.groupby(['sub_theme', 'year_quarter']).size().unstack(fill_value=0)
    
    # Filter to sub-themes with decent activity
    active_subthemes = heatmap_data.sum(axis=1).nlargest(15).index
    heatmap_data = heatmap_data.loc[active_subthemes]
    
    # Clean labels
    heatmap_data.index = [idx.replace('_', ' ') for idx in heatmap_data.index]
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='Viridis',
        text=heatmap_data.values,
        texttemplate='%{text}',
        textfont={"size": 8},
        hovertemplate='<b>%{y}</b><br>%{x}<br>Papers: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Sub-Theme Activity Over Time (Quarterly)",
        xaxis_title="Quarter",
        yaxis_title="Sub-Theme",
        height=500,
        font=dict(size=10)
    )
    
    return fig

def create_impact_bubble_chart(df, mapping):
    """Bubble chart: Growth vs Citations vs Volume"""
    # Calculate metrics by sub-theme
    df_copy = df.copy()
    df_copy['year'] = df_copy['date'].dt.year
    
    metrics = []
    for sub_theme in df_copy['sub_theme'].dropna().unique():
        sub_df = df_copy[df_copy['sub_theme'] == sub_theme]
        
        if len(sub_df) < 5:  # Skip small samples
            continue
        
        # Growth rate (2023 vs 2024)
        growth_2023 = len(sub_df[sub_df['year'] == 2023])
        growth_2024 = len(sub_df[sub_df['year'] == 2024])
        growth_rate = ((growth_2024 - growth_2023) / (growth_2023 + 1)) * 100 if growth_2023 > 0 else 0
        
        # Average citations
        avg_citations = sub_df['citations'].mean()
        
        # Get parent theme
        parent_theme = sub_df['theme'].mode()[0] if len(sub_df) > 0 else 'Other'
        
        metrics.append({
            'sub_theme': sub_theme.replace('_', ' '),
            'growth_rate': growth_rate,
            'avg_citations': avg_citations,
            'paper_count': len(sub_df),
            'parent_theme': parent_theme.replace('_', ' ')
        })
    
    metrics_df = pd.DataFrame(metrics)
    
    fig = px.scatter(
        metrics_df,
        x='growth_rate',
        y='avg_citations',
        size='paper_count',
        color='parent_theme',
        hover_name='sub_theme',
        hover_data={'growth_rate': ':.1f%', 'avg_citations': ':.0f', 'paper_count': True},
        labels={
            'growth_rate': 'Growth Rate 2023→2024 (%)',
            'avg_citations': 'Average Citations',
            'paper_count': 'Papers',
            'parent_theme': 'Theme'
        },
        title="Sub-Theme Impact Analysis: Growth vs Citations",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    fig.update_traces(marker=dict(line=dict(width=1, color='white')))
    fig.update_layout(height=550, showlegend=True)
    
    # Add quadrant lines
    median_growth = metrics_df['growth_rate'].median()
    median_citations = metrics_df['avg_citations'].median()
    
    fig.add_hline(y=median_citations, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=median_growth, line_dash="dash", line_color="gray", opacity=0.5)
    
    return fig

def create_sankey_flow(df):
    """Sankey diagram: Theme → Sub-Theme → University"""
    # Get top 10 universities and top 15 sub-themes
    top_unis = df['university'].value_counts().head(10).index
    top_subthemes = df['sub_theme'].value_counts().head(15).index
    
    df_filtered = df[df['university'].isin(top_unis) & df['sub_theme'].isin(top_subthemes)]
    
    # Create node labels
    themes = df_filtered['theme'].unique()
    subthemes = df_filtered['sub_theme'].unique()
    unis = top_unis
    
    all_labels = (
        [t.replace('_', ' ') for t in themes] + 
        [s.replace('_', ' ') for s in subthemes] + 
        list(unis)
    )
    
    # Create mappings
    label_to_idx = {label: idx for idx, label in enumerate(all_labels)}
    
    # Build flows
    sources = []
    targets = []
    values = []
    
    # Theme → Sub-theme flows
    for theme in themes:
        theme_label = theme.replace('_', ' ')
        for subtheme in subthemes:
            subtheme_label = subtheme.replace('_', ' ')
            count = len(df_filtered[(df_filtered['theme'] == theme) & (df_filtered['sub_theme'] == subtheme)])
            if count > 0:
                sources.append(label_to_idx[theme_label])
                targets.append(label_to_idx[subtheme_label])
                values.append(count)
    
    # Sub-theme → University flows
    for subtheme in subthemes:
        subtheme_label = subtheme.replace('_', ' ')
        for uni in unis:
            count = len(df_filtered[(df_filtered['sub_theme'] == subtheme) & (df_filtered['university'] == uni)])
            if count > 0:
                sources.append(label_to_idx[subtheme_label])
                targets.append(label_to_idx[uni])
                values.append(count)
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=all_labels,
            color='lightblue'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values
        )
    )])
    
    fig.update_layout(
        title="Research Flow: Themes → Sub-Themes → Top Universities",
        height=700,
        font=dict(size=10)
    )
    
    return fig

def create_trend_timeline(df):
    """Advanced timeline with trend analysis"""
    # Monthly aggregation
    df_copy = df.copy()
    df_copy['year_month'] = df_copy['date'].dt.to_period('M')
    
    monthly_counts = df_copy.groupby(['year_month', 'theme']).size().reset_index(name='count')
    monthly_counts['year_month'] = monthly_counts['year_month'].dt.to_timestamp()
    
    fig = px.area(
        monthly_counts,
        x='year_month',
        y='count',
        color='theme',
        title="Research Publication Trends Over Time",
        labels={'year_month': 'Date', 'count': 'Papers Published', 'theme': 'Theme'},
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_layout(
        height=400,
        hovermode='x unified',
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
    )
    
    return fig

def create_university_radar(df, selected_unis):
    """Radar chart comparing universities across sub-themes"""
    if not selected_unis or len(selected_unis) < 2:
        return None
    
    # Get top sub-themes
    top_subthemes = df['sub_theme'].value_counts().head(10).index
    
    fig = go.Figure()
    
    for uni in selected_unis[:5]:  # Max 5 for readability
        uni_data = df[df['university'] == uni]
        counts = []
        for subtheme in top_subthemes:
            count = len(uni_data[uni_data['sub_theme'] == subtheme])
            counts.append(count)
        
        fig.add_trace(go.Scatterpolar(
            r=counts,
            theta=[s.replace('_', ' ')[:20] for s in top_subthemes],
            fill='toself',
            name=uni
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max([max(counts) for counts in [df[df['university'] == u]['sub_theme'].value_counts() for u in selected_unis]])])),
        showlegend=True,
        title="University Research Profile Comparison",
        height=500
    )
    
    return fig

try:
    papers_df, trends, mapping = load_data()
    insights = generate_insights(papers_df, trends, mapping)
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
sel_themes = st.sidebar.multiselect("🎯 Parent Themes", options=all_themes, default=all_themes, key="themes")

# Sub-theme filter (hierarchical)
all_sub_themes = sorted([st for st in papers_df["sub_theme"].dropna().unique() if st])
if all_sub_themes:
    sel_sub_themes = st.sidebar.multiselect(
        "🔍 Sub-Themes (optional)", 
        options=all_sub_themes, 
        default=[], 
        key="sub_themes",
        help="Filter by specific sub-themes for more granular analysis"
    )
else:
    sel_sub_themes = []

# Filter universities to only show AU/NZ institutions
# Papers may list co-author institutions, but we only want to show AU/NZ in dashboard
australasian_uni_names = set(ALL_UNIVERSITIES.keys())
all_unis_in_data = papers_df["university"].unique()
all_unis = sorted([u for u in all_unis_in_data if u in australasian_uni_names])

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
    st.session_state["sub_themes"] = []
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
if sel_sub_themes:
    filtered = filtered[filtered["sub_theme"].isin(sel_sub_themes)]
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
    # === KEY INSIGHTS SECTION ===
    st.markdown('<p class="sub-header">🎯 Key Insights & Recommendations</p>', unsafe_allow_html=True)
    
    if insights:
        insight_cols = st.columns(min(len(insights), 3))
        for idx, insight in enumerate(insights):
            col = insight_cols[idx % 3]
            
            # Color coding by type
            bg_colors = {
                "emerging": "#dcfce7",      # green - new opportunities
                "opportunity": "#dbeafe",   # blue - gaps to fill
                "concentration": "#fef3c7", # yellow - awareness
                "quality": "#f3e8ff",       # purple - excellence
                "trend": "#e0f2fe",         # cyan - patterns
                "collaboration": "#fce7f3"  # pink - partnerships
            }
            bg = bg_colors.get(insight['type'], "#f1f5f9")
            
            with col:
                st.markdown(
                    f"<div class='card' style='background:{bg}; border-left: 4px solid #22c55e;'>"
                    f"<div style='font-size:2em; margin-bottom:0.5em;'>{insight['icon']}</div>"
                    f"<div style='font-weight:600; color:#111827; margin-bottom:0.3em;'>{insight['title']}</div>"
                    f"<div style='color:#374151; margin-bottom:0.5em;'>{insight['message']}</div>"
                    f"<div style='font-size:0.85em; color:#6b7280; font-style:italic;'>{insight['detail']}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
    else:
        st.info("Analyzing research patterns to generate insights...")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # KPIs Row - Show total dataset metrics, not filtered
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("📄 Papers", f"{len(papers_df):,}")
    k2.metric("🎯 Topics", len(mapping))
    k3.metric("🔍 Sub-Themes", papers_df["sub_theme"].nunique())
    k4.metric("🏛️ Universities", papers_df["university"].nunique())
    try:
        avg_growth = sum(p.get("growth_rate", 0) for p in trends.get("strategic_priorities", [])) / max(1, len(trends.get("strategic_priorities", [])))
        k5.metric("📈 Avg Growth", f"{avg_growth*100:+.1f}%")
    except Exception:
        k5.metric("📈 Avg Growth", "N/A")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # ========== HIERARCHICAL SUNBURST CHART ==========
    st.markdown('<p class="sub-header">🎡 Research Hierarchy Explorer</p>', unsafe_allow_html=True)
    st.markdown("*Click on segments to drill down into Theme → Sub-Theme → Topic levels*")
    try:
        sunburst_fig = create_sunburst_chart(filtered, mapping)
        st.plotly_chart(sunburst_fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Sunburst chart could not be generated: {e}")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # ========== PUBLICATION TIMELINE ==========
    st.markdown('<p class="sub-header">📊 Publication Trends Over Time</p>', unsafe_allow_html=True)
    try:
        timeline_fig = create_trend_timeline(filtered)
        st.plotly_chart(timeline_fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Timeline could not be generated: {e}")

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
    theme_counts = papers_df.groupby("theme").size()
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

    # SUB-THEME OVERVIEW
    st.markdown('<p class="sub-header">🔍 Top Sub-Themes (Hierarchical Analysis)</p>', unsafe_allow_html=True)
    papers_with_sub = papers_df[papers_df["sub_theme"].notna()]
    if not papers_with_sub.empty:
        sub_theme_summary = papers_with_sub.groupby("sub_theme").agg(
            papers=("title", "count"),
            avg_confidence=("sub_theme_confidence", "mean")
        ).sort_values("papers", ascending=False).head(15).reset_index()
        sub_theme_summary["sub_theme"] = sub_theme_summary["sub_theme"].str.replace("_", " ").str.title()
        sub_theme_summary["avg_confidence"] = (sub_theme_summary["avg_confidence"] * 100).round(1)
        
        fig_sub_overview = px.bar(
            sub_theme_summary,
            x="papers",
            y="sub_theme",
            orientation="h",
            color="avg_confidence",
            color_continuous_scale="Greens",
            title="Top 15 Sub-Themes Across All Themes",
            labels={"papers": "Papers", "sub_theme": "Sub-Theme", "avg_confidence": "Avg Confidence (%)"}
        )
        fig_sub_overview = apply_fig_theme(fig_sub_overview, height=420)
        st.plotly_chart(fig_sub_overview, use_container_width=True)
        
        # Sub-theme statistics
        col1, col2, col3 = st.columns(3)
        col1.metric("Unique Sub-Themes", len(papers_with_sub["sub_theme"].unique()))
        col2.metric("Papers with Sub-Themes", f"{len(papers_with_sub):,}")
        col3.metric("Coverage", f"{(len(papers_with_sub)/len(papers_df)*100):.1f}%")
    else:
        st.info("No sub-theme data available in the dataset")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Overall Output Over Time
    st.markdown('<p class="sub-header">Overall Research Activity</p>', unsafe_allow_html=True)
    qa = papers_df.groupby("quarter").size().reset_index(name="count")
    if not qa.empty:
        qa["quarter"] = qa["quarter"].astype(str)
        fig_overall = go.Figure()
        fig_overall.add_trace(go.Scatter(x=qa["quarter"], y=qa["count"], mode="lines+markers", name="All Themes"))
        fig_overall = apply_fig_theme(fig_overall, height=360)
        fig_overall.update_layout(title="Overall Research Output", xaxis_title="Quarter", yaxis_title="Papers")
        st.plotly_chart(fig_overall, use_container_width=True)
    else:
        st.info("No trend data available")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Top Universities
    st.markdown('<p class="sub-header">Top Universities</p>', unsafe_allow_html=True)
    if not papers_df.empty:
        uc = papers_df["university"].value_counts().reset_index()
        uc.columns = ["University", "Papers"]
        st.dataframe(uc.head(15), use_container_width=True, hide_index=True)
    else:
        st.info("No data available")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Recent Papers List
    st.markdown('<p class="sub-header">Top Recent Papers</p>', unsafe_allow_html=True)
    recent = papers_df.sort_values(["relevance_score", "date"], ascending=[False, False]).head(10)
    for _, r in recent.iterrows():
        sub_theme_text = f" > {str(r.get('sub_theme','')).replace('_',' ').title()}" if pd.notna(r.get('sub_theme')) else ""
        st.markdown(
            f"<div class='card'><div class='kpi'><div class='label'>{r.get('university','')} | "
            f"{str(r.get('theme','')).replace('_',' ').title()}{sub_theme_text} | {pd.to_datetime(r.get('date')).strftime('%Y-%m-%d') if pd.notna(r.get('date')) else ''}</div>"
            f"<div class='value'>{r.get('title','(untitled)')}</div>"
            f"<span class='badge'>Relevance {r.get('relevance_score',0):.0f}</span></div></div>",
            unsafe_allow_html=True,
        )

with tab_theme:
    # === RESEARCH IMPACT ANALYSIS ===
    st.markdown('<p class="sub-header">🎓 Research Impact & Quality Analysis</p>', unsafe_allow_html=True)
    
    impact_cols = st.columns(4)
    
    with impact_cols[0]:
        if 'quality_score' in papers_df.columns:
            high_impact = papers_df[papers_df['quality_score'] > 70]
            st.metric(
                "High Impact Papers",
                f"{len(high_impact):,}",
                delta=f"{len(high_impact)/len(papers_df)*100:.1f}% of total"
            )
        else:
            st.metric("High Impact Papers", f"{len(papers_df[papers_df['citations'] > papers_df['citations'].quantile(0.75)]):,}" if 'citations' in papers_df.columns else "N/A")
    
    with impact_cols[1]:
        if 'citations' in papers_df.columns:
            median_citations = papers_df['citations'].median()
            st.metric("Median Citations", f"{int(median_citations)}")
        else:
            st.metric("Median Citations", "N/A")
    
    with impact_cols[2]:
        collab_papers = papers_df[papers_df['university'].str.contains(',|;', na=False, regex=True)]
        collab_rate = len(collab_papers) / len(papers_df) * 100 if len(papers_df) > 0 else 0
        st.metric("Collaboration Rate", f"{collab_rate:.1f}%")
    
    with impact_cols[3]:
        recent_6m = papers_df[papers_df['date'] >= (papers_df['date'].max() - pd.Timedelta(days=180))]
        momentum = len(recent_6m) / len(papers_df) * 100 if len(papers_df) > 0 else 0
        st.metric("Recent Output", f"{momentum:.1f}%", delta="Last 6 months")
    
    # Quality by Theme
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    if 'quality_score' in papers_df.columns:
        st.markdown('<p class="sub-header">Quality Score by Theme</p>', unsafe_allow_html=True)
        
        quality_by_theme = papers_df.groupby('theme').agg({
            'quality_score': ['mean', 'median', 'std'],
            'title': 'count'
        }).round(1)
        quality_by_theme.columns = ['Avg Quality', 'Median Quality', 'Std Dev', 'Paper Count']
        quality_by_theme = quality_by_theme.sort_values('Avg Quality', ascending=False)
        quality_by_theme.index = quality_by_theme.index.str.replace('_', ' ').str.title()
        
        col_q1, col_q2 = st.columns([2, 1])
        with col_q1:
            fig_quality = px.bar(
                quality_by_theme.reset_index(),
                x='theme',
                y='Avg Quality',
                title='Average Quality Score by Theme',
                color='Avg Quality',
                color_continuous_scale='Greens'
            )
            fig_quality = apply_fig_theme(fig_quality, height=300)
            st.plotly_chart(fig_quality, use_container_width=True)
        
        with col_q2:
            st.dataframe(quality_by_theme, use_container_width=True, height=300)
    elif 'citations' in papers_df.columns:
        st.markdown('<p class="sub-header">Citation Impact by Theme</p>', unsafe_allow_html=True)
        
        citation_by_theme = papers_df.groupby('theme').agg({
            'citations': ['mean', 'median'],
            'title': 'count'
        }).round(1)
        citation_by_theme.columns = ['Avg Citations', 'Median Citations', 'Paper Count']
        citation_by_theme = citation_by_theme.sort_values('Avg Citations', ascending=False)
        citation_by_theme.index = citation_by_theme.index.str.replace('_', ' ').str.title()
        
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            fig_cit = px.bar(
                citation_by_theme.reset_index(),
                x='theme',
                y='Avg Citations',
                title='Average Citations by Theme',
                color='Avg Citations',
                color_continuous_scale='Blues'
            )
            fig_cit = apply_fig_theme(fig_cit, height=300)
            st.plotly_chart(fig_cit, use_container_width=True)
        
        with col_c2:
            st.dataframe(citation_by_theme, use_container_width=True, height=300)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    theme_order = list(BABCOCK_THEMES.keys())
    theme_names = [t.replace('_', ' ').title() for t in theme_order]

    # Theme overview summary for all papers
    summary = (
        papers_df.groupby("theme").agg(
            papers=("title", "count"),
            universities=("university", pd.Series.nunique),
            topics=("topic_id", pd.Series.nunique),
        )
        if not papers_df.empty
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
        "papers": "Total Papers",
        "universities": "Universities",
        "topics": "Topics",
    })

    st.markdown('<p class="sub-header">Theme Overview</p>', unsafe_allow_html=True)
    st.dataframe(summary, use_container_width=True, hide_index=True)

    # Multi-theme trend chart to highlight coverage per theme
    if not papers_df.empty:
        quarters = sorted(papers_df["quarter"].unique())
        idx = pd.MultiIndex.from_product([quarters, theme_order], names=["quarter", "theme"])
        theme_trend = papers_df.groupby(["quarter", "theme"]).size().reindex(idx, fill_value=0).reset_index(name="count")
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
        if row["Total Papers"] > 0:
            default_index = idx
            break

    selected_theme_display = st.selectbox("Select Theme", theme_names, index=default_index)
    selected_theme = selected_theme_display.replace(" ", "_")
    theme_papers = papers_df[papers_df["theme"] == selected_theme]
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
        
        # ========== RESEARCH FLOW DIAGRAM ==========
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown('<p class="sub-header">🌊 Research Flow Analysis</p>', unsafe_allow_html=True)
        st.markdown("*Trace how research themes flow through specific sub-themes to leading universities. Width of flow = number of papers.*")
        try:
            sankey_fig = create_sankey_flow(filtered)
            st.plotly_chart(sankey_fig, use_container_width=True)
            
            # Add interpretation
            st.info("💡 **Strategic Insight**: Follow thick flows to identify which universities dominate specific sub-themes. Thin flows indicate collaboration opportunities.")
        except Exception as e:
            st.warning(f"Sankey diagram could not be generated: {e}")

        # SUB-THEME BREAKDOWN for selected parent theme
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown('<p class="sub-header">🔍 Sub-Theme Breakdown</p>', unsafe_allow_html=True)
        
        theme_with_sub = theme_papers[theme_papers["sub_theme"].notna()]
        if not theme_with_sub.empty:
            sub_theme_counts = theme_with_sub.groupby("sub_theme").agg(
                papers=("title", "count"),
                avg_confidence=("sub_theme_confidence", "mean"),
                universities=("university", pd.Series.nunique)
            ).sort_values("papers", ascending=False).reset_index()
            sub_theme_counts["sub_theme"] = sub_theme_counts["sub_theme"].str.replace("_", " ").str.title()
            sub_theme_counts["avg_confidence"] = (sub_theme_counts["avg_confidence"] * 100).round(1)
            sub_theme_counts.columns = ["Sub-Theme", "Papers", "Avg Confidence (%)", "Universities"]
            
            st.dataframe(sub_theme_counts, use_container_width=True, hide_index=True)
            
            # Sub-theme distribution chart
            fig_sub = px.bar(
                sub_theme_counts.head(10),
                x="Papers",
                y="Sub-Theme",
                orientation="h",
                color="Avg Confidence (%)",
                color_continuous_scale="Greens",
                title=f"Top 10 Sub-Themes in {selected_theme_display}"
            )
            fig_sub = apply_fig_theme(fig_sub, height=340)
            st.plotly_chart(fig_sub, use_container_width=True)
        else:
            st.info(f"No sub-theme data available for {selected_theme_display}")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

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

        adj = find_adjacent_themes(papers_df, selected_theme, mapping)
        if adj:
            adj_df = pd.DataFrame({"Theme": [t.replace("_", " ").title() for t in list(adj.keys())[:5]], "Connections": list(adj.values())[:5]})
            fig_adj = px.bar(adj_df, x="Connections", y="Theme", orientation="h", color="Connections", color_continuous_scale="Greens", title=f"Top Adjacent Themes to {selected_theme_display}")
            fig_adj = apply_fig_theme(fig_adj, height=300)
            st.plotly_chart(fig_adj, use_container_width=True)
        else:
            st.info("No significant adjacent themes detected for this theme")

with tab_unis:
    st.markdown('<p class="sub-header">Overall Research Output Rankings</p>', unsafe_allow_html=True)
    uc = papers_df["university"].value_counts()
    fig = px.bar(x=uc.head(15).values, y=uc.head(15).index, orientation="h", color=uc.head(15).values, color_continuous_scale="Greens", title="Top 15 Universities by Total Papers")
    fig = apply_fig_theme(fig, height=380)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<p class="sub-header">University Deep Dive</p>', unsafe_allow_html=True)
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
    
    # ========== UNIVERSITY COMPARISON RADAR ==========
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown('<p class="sub-header">🎯 University Research Profile Comparison</p>', unsafe_allow_html=True)
    st.markdown("*Compare research focus across sub-themes for selected universities*")
    
    # Multi-select for universities
    all_unis = sorted(papers_df["university"].unique())
    default_unis = all_unis[:min(3, len(all_unis))]  # Default to top 3
    selected_unis = st.multiselect(
        "Select Universities to Compare (2-5)",
        options=all_unis,
        default=default_unis,
        max_selections=5
    )
    
    if len(selected_unis) >= 2:
        try:
            radar_fig = create_university_radar(filtered, selected_unis)
            if radar_fig:
                st.plotly_chart(radar_fig, use_container_width=True)
                st.info("💡 **Strategic Insight**: Larger area = stronger focus. Compare shapes to identify complementary strengths for potential collaborations.")
            else:
                st.info("Unable to generate radar chart with current data.")
        except Exception as e:
            st.warning(f"Radar chart could not be generated: {e}")
    else:
        st.info("👆 Please select at least 2 universities to compare their research profiles.")

with tab_trends:
    # ========== SUB-THEME GROWTH HEATMAP ==========
    st.markdown('<p class="sub-header">🔥 Sub-Theme Activity Heatmap</p>', unsafe_allow_html=True)
    st.markdown("*Darker colors indicate higher research activity. Track emerging and declining sub-themes over time.*")
    try:
        heatmap_fig = create_growth_heatmap(filtered)
        st.plotly_chart(heatmap_fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Heatmap could not be generated: {e}")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # ========== IMPACT BUBBLE CHART ==========
    st.markdown('<p class="sub-header">💎 Sub-Theme Impact Analysis</p>', unsafe_allow_html=True)
    st.markdown("*Quadrant Analysis: Top-right = High growth + High citations (★ invest here)*")
    try:
        bubble_fig = create_impact_bubble_chart(filtered, mapping)
        st.plotly_chart(bubble_fig, use_container_width=True)
        
        # Interpretation guide
        cols = st.columns(4)
        cols[0].markdown("**🌟 Stars**<br>↗High Growth<br>⬆High Citations", unsafe_allow_html=True)
        cols[1].markdown("**💎 Gems**<br>→Low Growth<br>⬆High Citations", unsafe_allow_html=True)
        cols[2].markdown("**🚀 Rising**<br>↗High Growth<br>→Low Citations", unsafe_allow_html=True)
        cols[3].markdown("**⚠️ Watch**<br>→Low Growth<br>→Low Citations", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Impact bubble chart could not be generated: {e}")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # === STRATEGIC RECOMMENDATIONS ===
    st.markdown('<p class="sub-header">📊 Strategic Research Recommendations</p>', unsafe_allow_html=True)
    
    # Calculate growth rates and gaps
    recent_year = papers_df['date'].dt.year.max()
    prev_year = recent_year - 1
    
    recent_df = papers_df[papers_df['date'].dt.year == recent_year]
    prev_df = papers_df[papers_df['date'].dt.year == prev_year]
    
    # Sub-theme analysis
    recent_subthemes = recent_df.groupby('sub_theme').size()
    prev_subthemes = prev_df.groupby('sub_theme').size()
    
    growth_analysis = pd.DataFrame({
        'recent': recent_subthemes,
        'previous': prev_subthemes
    }).fillna(0)
    growth_analysis['growth_rate'] = ((growth_analysis['recent'] - growth_analysis['previous']) / 
                                       (growth_analysis['previous'] + 1) * 100)
    growth_analysis['total'] = growth_analysis['recent'] + growth_analysis['previous']
    
    # Recommendations
    rec_cols = st.columns(3)
    
    with rec_cols[0]:
        st.markdown("**🚀 High Growth Areas**")
        high_growth = growth_analysis.nlargest(5, 'growth_rate')
        for idx, (subtheme, row) in enumerate(high_growth.iterrows(), 1):
            if pd.notna(subtheme) and row['growth_rate'] > 0:
                st.markdown(
                    f"<div class='card' style='background:#dcfce7; padding:0.5em;'>"
                    f"<div style='font-size:0.9em; font-weight:500;'>{idx}. {subtheme}</div>"
                    f"<div style='font-size:0.8em; color:#059669;'>↗ {row['growth_rate']:.0f}% growth</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
    
    with rec_cols[1]:
        st.markdown("**💡 Investment Opportunities**")
        # High strategic value but low volume
        priorities = trends.get("strategic_priorities", [])
        priority_themes = [p['theme'] for p in priorities[:5]]
        
        opportunities = []
        for theme in priority_themes:
            theme_papers = papers_df[papers_df['theme'] == theme]
            if len(theme_papers) < 2000:  # Under-researched
                sub_counts = theme_papers['sub_theme'].value_counts()
                if len(sub_counts) > 0:
                    opportunities.append({
                        'theme': theme,
                        'sub_theme': sub_counts.index[0],
                        'count': sub_counts.iloc[0],
                        'potential': 2000 - len(theme_papers)
                    })
        
        for idx, opp in enumerate(opportunities[:5], 1):
            st.markdown(
                f"<div class='card' style='background:#dbeafe; padding:0.5em;'>"
                f"<div style='font-size:0.9em; font-weight:500;'>{idx}. {opp['sub_theme']}</div>"
                f"<div style='font-size:0.8em; color:#0369a1;'>Gap: {opp['potential']} papers</div>"
                f"</div>",
                unsafe_allow_html=True
            )
    
    with rec_cols[2]:
        st.markdown("**🎯 Collaboration Focus**")
        # Find sub-themes with multiple universities
        collab_potential = papers_df.groupby('sub_theme').agg({
            'university': 'nunique',
            'title': 'count'
        }).rename(columns={'university': 'unis', 'title': 'papers'})
        collab_potential = collab_potential[collab_potential['unis'] >= 3].nlargest(5, 'unis')
        
        for idx, (subtheme, row) in enumerate(collab_potential.iterrows(), 1):
            if pd.notna(subtheme):
                st.markdown(
                    f"<div class='card' style='background:#fef3c7; padding:0.5em;'>"
                    f"<div style='font-size:0.9em; font-weight:500;'>{idx}. {subtheme}</div>"
                    f"<div style='font-size:0.8em; color:#d97706;'>{int(row['unis'])} universities</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # === TEMPORAL TRENDS ===
    st.markdown('<p class="sub-header">Temporal Trends Analysis</p>', unsafe_allow_html=True)
    qa = papers_df.groupby("quarter").size().reset_index(name="count"); qa["quarter"] = qa["quarter"].astype(str)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=qa["quarter"], y=qa["count"], mode="lines+markers", name="All Themes"))
    fig = apply_fig_theme(fig, height=380)
    fig.update_layout(title="Overall Research Output", xaxis_title="Quarter", yaxis_title="Papers")
    st.plotly_chart(fig, use_container_width=True)

    names = [t.replace("_", " ").title() for t in BABCOCK_THEMES.keys()]
    picks = st.multiselect("Select Themes to Compare", names, default=names)
    if picks:
        raw = [t.replace(" ", "_") for t in picks]
        f = papers_df[papers_df["theme"].isin(raw)]
        quarters = sorted(papers_df["quarter"].unique())
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
    missing_abs = papers_df['abstract'].isna().sum() if 'abstract' in papers_df.columns else 0
    c1.metric("Missing Abstracts", f"{missing_abs:,}")
    c2.metric("Avg Confidence", f"{papers_df['confidence'].mean():.0f}%" if 'confidence' in papers_df.columns else 'N/A')
    c3.metric("Has Citations", f"{papers_df['citations'].notna().mean()*100:.0f}%" if 'citations' in papers_df.columns else 'N/A')

    st.markdown("---")
    colA, colB = st.columns(2)
    with colA:
        st.markdown('<p class="sub-header">Confidence Distribution</p>', unsafe_allow_html=True)
        if 'confidence' in papers_df.columns:
            fig = px.histogram(papers_df, x='confidence', nbins=20, title='Confidence (%)')
            fig = apply_fig_theme(fig, height=320)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No confidence field available")
    with colB:
        st.markdown('<p class="sub-header">Citations Distribution</p>', unsafe_allow_html=True)
        if 'citations' in papers_df.columns:
            fig = px.histogram(papers_df, x='citations', nbins=20, title='Citations')
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
