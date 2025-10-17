"""
Smarter Research Insights - AI-Powered Research Intelligence Dashboard
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
st.set_page_config(
    page_title="Smarter Research Insights", 
    page_icon="🔬", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Modern Plotly theme with blue gradient colors
px.defaults.template = "plotly_dark"
px.defaults.color_discrete_sequence = [
    "#3b82f6",  # Primary Blue
    "#2563eb",  # Deep Blue
    "#06b6d4",  # Cyan
    "#8b5cf6",  # Purple
    "#60a5fa",  # Light Blue
    "#0ea5e9",  # Sky Blue
    "#a78bfa",  # Light Purple
    "#0284c7",  # Darker Cyan
    "#7c3aed",  # Violet
    "#6366f1"   # Indigo
]

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
                "icon": "",
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
                "icon": "",
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
            "icon": "",
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
                "icon": "",
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
            "icon": "",
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
    # Build hierarchy data - ensure we capture ALL themes and sub-themes
    hierarchy_data = []
    
    for _, row in df.iterrows():
        topic_id = str(row['topic_id'])
        parent_theme = row['theme']
        sub_theme = row.get('sub_theme')
        
        # Use 'Other' only if sub_theme is truly missing
        if pd.isna(sub_theme) or sub_theme == '' or sub_theme is None:
            sub_theme = 'Other'
        
        hierarchy_data.append({
            'parent_theme': parent_theme,
            'sub_theme': sub_theme,
            'topic_id': topic_id,
            'count': 1
        })
    
    hierarchy_df = pd.DataFrame(hierarchy_data)
    
    # Aggregate counts at each level
    theme_counts = hierarchy_df.groupby(['parent_theme']).size().reset_index(name='count')
    subtheme_counts = hierarchy_df.groupby(['parent_theme', 'sub_theme']).size().reset_index(name='count')
    topic_counts = hierarchy_df.groupby(['parent_theme', 'sub_theme', 'topic_id']).size().reset_index(name='count')
    
    # Build sunburst data structure
    labels = []
    parents = []
    values = []
    colors = []
    
    # Use a better color palette for dark theme - vibrant blues and purples
    color_palette = [
        '#3b82f6',  # Blue
        '#8b5cf6',  # Purple
        '#06b6d4',  # Cyan
        '#2563eb',  # Dark Blue
        '#a78bfa',  # Light Purple
        '#0ea5e9',  # Sky Blue
        '#60a5fa',  # Light Blue
        '#c084fc',  # Medium Purple
        '#0284c7',  # Darker Cyan
        '#7c3aed',  # Violet
        '#38bdf8',  # Lighter Cyan
        '#6366f1',  # Indigo
    ]
    
    theme_colors = {}
    
    # Add root
    labels.append('All Research')
    parents.append('')
    values.append(len(df))
    colors.append('#1e293b')  # Dark background for root
    
    # Add ALL themes (parent level)
    for i, (_, row) in enumerate(theme_counts.iterrows()):
        theme_name = row['parent_theme'].replace('_', ' ').title()
        labels.append(theme_name)
        parents.append('All Research')
        values.append(row['count'])
        theme_color = color_palette[i % len(color_palette)]
        colors.append(theme_color)
        theme_colors[row['parent_theme']] = theme_color
    
    # Add ALL sub-themes (middle level) - ensure all are included
    for _, row in subtheme_counts.iterrows():
        sub_name = row['sub_theme'].replace('_', ' ').title()
        parent_name = row['parent_theme'].replace('_', ' ').title()
        # Create unique label to avoid duplicates across themes
        unique_sub_label = f"{sub_name} ({parent_name})"
        labels.append(unique_sub_label)
        parents.append(parent_name)
        values.append(row['count'])
        # Use lighter shade of parent theme color for sub-themes
        base_color = theme_colors.get(row['parent_theme'], color_palette[0])
        colors.append(base_color + '99')  # Add transparency for lighter shade
    
    # DO NOT add topics - only show themes and sub-themes (2 levels)
    
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(
            colors=colors,
            line=dict(color='#0f172a', width=2)  # Dark borders between segments
        ),
        hovertemplate='<b>%{label}</b><br>Papers: %{value}<br>%{percentParent} of parent<extra></extra>',
        maxdepth=2  # Only show 2 levels: themes and sub-themes
    ))
    
    fig.update_layout(
        title="Research Hierarchy: Themes → Sub-Themes → Topics",
        height=650,
        font=dict(size=11, color='#f1f5f9'),
        margin=dict(t=50, l=0, r=0, b=0),
        paper_bgcolor='#1e293b',
        plot_bgcolor='#0f172a',
        title_font=dict(size=18, color='#f1f5f9')
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
    
    # Create color palette for nodes
    num_themes = len(themes)
    num_subthemes = len(subthemes)
    num_unis = len(unis)
    
    # Blue palette for themes
    theme_colors = ['#3b82f6', '#2563eb', '#06b6d4', '#8b5cf6', '#60a5fa', 
                    '#0ea5e9', '#a78bfa', '#0284c7', '#7c3aed', '#6366f1'] * 10
    # Lighter blue for sub-themes
    subtheme_colors = ['#60a5fa', '#93c5fd', '#7dd3fc', '#c4b5fd'] * 20
    # Cyan for universities
    uni_colors = ['#22d3ee', '#06b6d4', '#0891b2'] * 20
    
    node_colors = (theme_colors[:num_themes] + 
                   subtheme_colors[:num_subthemes] + 
                   uni_colors[:num_unis])
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="#0f172a", width=1),
            label=all_labels,
            color=node_colors
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color='rgba(59, 130, 246, 0.3)'  # Semi-transparent blue for links
        )
    )])
    
    fig.update_layout(
        title="Research Flow: Themes → Sub-Themes → Top Universities",
        height=700,
        font=dict(size=10, color='#f1f5f9'),
        paper_bgcolor='#1e293b',
        plot_bgcolor='#0f172a',
        title_font=dict(size=18, color='#f1f5f9')
    )
    
    return fig

def create_trend_timeline(df):
    """Advanced timeline with trend analysis"""
    # Monthly aggregation
    df_copy = df.copy()
    df_copy['year_month'] = df_copy['date'].dt.to_period('M')
    
    monthly_counts = df_copy.groupby(['year_month', 'theme']).size().reset_index(name='count')
    monthly_counts['year_month'] = monthly_counts['year_month'].dt.to_timestamp()
    
    # Use blue color palette instead of pastel
    blue_palette = [
        '#3b82f6', '#2563eb', '#06b6d4', '#8b5cf6', '#60a5fa',
        '#0ea5e9', '#a78bfa', '#0284c7', '#7c3aed', '#6366f1'
    ]
    
    fig = px.area(
        monthly_counts,
        x='year_month',
        y='count',
        color='theme',
        title="Research Publication Trends Over Time",
        labels={'year_month': 'Date', 'count': 'Papers Published', 'theme': 'Theme'},
        color_discrete_sequence=blue_palette
    )
    
    fig.update_layout(
        height=400,
        hovermode='x unified',
        legend=dict(
            orientation="v", 
            yanchor="top", 
            y=1, 
            xanchor="left", 
            x=1.02,
            bgcolor='rgba(30,41,59,0.9)',
            bordercolor='#334155',
            borderwidth=1,
            font=dict(size=11, color='#cbd5e1')
        ),
        paper_bgcolor='#1e293b',
        plot_bgcolor='#0f172a',
        font=dict(family='Inter, sans-serif', color='#f1f5f9', size=12),
        title_font=dict(size=18, color='#f1f5f9'),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='#334155',
            showline=True,
            linewidth=1,
            linecolor='#475569',
            color='#cbd5e1'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='#334155',
            showline=True,
            linewidth=1,
            linecolor='#475569',
            color='#cbd5e1'
        )
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

def filter_noisy_keywords(keywords):
    """Remove noisy/generic keywords"""
    noise_words = {
        'google', 'scholar', 'researchgate', 'pubmed', 'arxiv',
        'et', 'al', 'doi', 'http', 'https', 'www',
        'paper', 'study', 'research', 'analysis', 'approach',
        'method', 'results', 'data', 'using', 'based',
        'review', 'systematic', 'meta',
        'journal', 'conference', 'proceedings', 'article'
    }
    
    filtered = []
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower not in noise_words and len(kw) > 2:
            if not any(x in kw_lower for x in ['http', 'www', '.com', '.org']):
                filtered.append(kw)
    
    return filtered[:8]

def generate_topic_label_gpt(keywords, theme, sub_theme, paper_count, growth_rate):
    """Generate meaningful topic label using GPT"""
    import openai
    import os
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        # Fallback to cleaned keywords
        clean_kw = filter_noisy_keywords(keywords)
        if len(clean_kw) >= 2:
            return f"{theme.replace('_', ' ')}: {' & '.join(clean_kw[:2])}"
        return f"Topic in {theme.replace('_', ' ')}"
    
    try:
        openai.api_key = api_key
        
        clean_keywords = filter_noisy_keywords(keywords)
        if len(clean_keywords) < 3:
            clean_keywords = keywords[:8]
        
        keywords_str = ", ".join(clean_keywords[:8])
        domain = theme.replace('_', ' ').title()
        sub_context = f"\nSub-area: {sub_theme.replace('_', ' ')}" if sub_theme else ""
        
        prompt = f"""You are a research analyst identifying emerging topics.

Domain: {domain}{sub_context}
Keywords: {keywords_str}
Papers: {paper_count}
Growth: {growth_rate:.0f}%

Create a SHORT research topic label (2-4 words MAXIMUM) that:
- Describes the SPECIFIC focus
- Uses technical terms
- Is concise and memorable

Good examples:
- "Medical Image AI"
- "Blockchain Security"
- "Edge IoT"
- "Quantum Computing"

Generate ONLY the label (2-4 words MAX), no quotes."""

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You create SHORT (2-4 word) research labels. Never list keywords."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=30
        )
        
        label = response.choices[0].message.content.strip().strip('"').strip("'").strip('`')
        
        # Remove prefixes
        for prefix in ['Topic:', 'Label:', 'Research Topic:', 'Emerging Topic:']:
            if label.startswith(prefix):
                label = label[len(prefix):].strip()
        
        return label if len(label.split()) >= 3 else f"{domain}: {' & '.join(clean_keywords[:2])}"
        
    except Exception as e:
        # Fallback
        clean_kw = filter_noisy_keywords(keywords)
        if len(clean_kw) >= 2:
            return f"{theme.replace('_', ' ')}: {' & '.join(clean_kw[:2])}"
        return f"Topic in {theme.replace('_', ' ')}"

def create_emerging_topics_bubble(df, mapping, top_n=20):
    """
    Create bubble chart showing emerging topics with GPT-generated labels
    X-axis: Recency score (how recent)
    Y-axis: Growth rate (how fast growing)
    Size: Paper volume
    Color: Theme
    """
    # Calculate emergingness metrics for each topic
    emerging_data = []
    
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])
    latest_date = df_copy['date'].max()
    
    for topic_id in df_copy['topic_id'].unique():
        if topic_id == -1:  # Skip outliers
            continue
        
        topic_papers = df_copy[df_copy['topic_id'] == topic_id]
        
        if len(topic_papers) < 5:  # Skip small topics
            continue
        
        # Calculate recency score
        topic_papers['months_old'] = (latest_date - topic_papers['date']).dt.days / 30
        recency_score = np.exp(-topic_papers['months_old'].mean() / 12)  # Exponential decay
        
        # Calculate growth rate
        topic_papers['quarter'] = topic_papers['date'].dt.to_period('Q')
        quarterly_counts = topic_papers.groupby('quarter').size().sort_index()
        
        if len(quarterly_counts) >= 4:
            recent_avg = quarterly_counts.iloc[-2:].mean()
            older_avg = quarterly_counts.iloc[-4:-2].mean()
            growth_rate = ((recent_avg - older_avg) / max(older_avg, 1)) * 100
        elif len(quarterly_counts) >= 2:
            growth_rate = ((quarterly_counts.iloc[-1] - quarterly_counts.iloc[0]) / max(quarterly_counts.iloc[0], 1)) * 100
        else:
            growth_rate = 0
        
        # Get theme and keywords
        topic_id_str = str(topic_id)
        theme = topic_papers['theme'].iloc[0] if 'theme' in topic_papers.columns else 'Unknown'
        sub_theme = topic_papers['sub_theme'].iloc[0] if 'sub_theme' in topic_papers.columns else None
        
        keywords = []
        if topic_id_str in mapping:
            keywords = mapping[topic_id_str].get('keywords', [])[:10]
        
        emerging_data.append({
            'topic_id': topic_id,
            'keywords_list': keywords,
            'theme': theme,
            'sub_theme': sub_theme,
            'recency_score': recency_score * 100,  # Convert to percentage
            'growth_rate': growth_rate,
            'paper_count': len(topic_papers),
            'avg_citations': topic_papers['citations'].mean() if 'citations' in topic_papers.columns else 0,
            'keywords': ', '.join(filter_noisy_keywords(keywords)[:5])
        })
    
    emerging_df = pd.DataFrame(emerging_data)
    
    # Calculate emergingness score and filter top N
    emerging_df['emergingness'] = (
        0.4 * (emerging_df['recency_score'] / 100) +
        0.4 * ((emerging_df['growth_rate'] + 100) / 200) +  # Normalize growth
        0.2 * (emerging_df['paper_count'] / emerging_df['paper_count'].max())
    )
    
    emerging_df = emerging_df.nlargest(top_n, 'emergingness')
    
    # Generate GPT labels for top topics
    import streamlit as st
    with st.spinner('Generating AI-powered topic labels...'):
        labels = []
        for _, row in emerging_df.iterrows():
            label = generate_topic_label_gpt(
                keywords=row['keywords_list'],
                theme=row['theme'],
                sub_theme=row['sub_theme'],
                paper_count=row['paper_count'],
                growth_rate=row['growth_rate']
            )
            labels.append(label)
        emerging_df['topic_label'] = labels
    
    # Create bubble chart
    fig = px.scatter(
        emerging_df,
        x='recency_score',
        y='growth_rate',
        size='paper_count',
        color='theme',
        hover_name='topic_label',
        hover_data={
            'recency_score': ':.1f',
            'growth_rate': ':.1f',
            'paper_count': True,
            'avg_citations': ':.1f',
            'theme': False,
            'keywords': True
        },
        title=f"Top {top_n} Emerging Research Topics",
        labels={
            'recency_score': 'Recency Score (% papers in last 12 months)',
            'growth_rate': 'Growth Rate (%)',
            'paper_count': 'Papers',
            'theme': 'Theme'
        },
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    # Add quadrant lines
    median_recency = emerging_df['recency_score'].median()
    median_growth = emerging_df['growth_rate'].median()
    
    fig.add_hline(y=median_growth, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=median_recency, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Add annotations for quadrants
    max_recency = emerging_df['recency_score'].max()
    max_growth = emerging_df['growth_rate'].max()
    min_growth = emerging_df['growth_rate'].min()
    
    fig.add_annotation(
        x=max_recency * 0.85,
        y=max_growth * 0.85,
        text="Hot Topics<br>(Recent + Growing)",
        showarrow=False,
        font=dict(size=10, color="#3b82f6"),
        opacity=0.7
    )
    
    fig.add_annotation(
        x=median_recency * 0.5,
        y=max_growth * 0.85,
        text="Momentum<br>(Growing Fast)",
        showarrow=False,
        font=dict(size=10, color="blue"),
        opacity=0.7
    )
    
    fig.update_layout(
        height=600,
        showlegend=True,
        hovermode='closest'
    )
    
    return fig, emerging_df

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
sel_themes = st.sidebar.multiselect("Parent Themes", options=all_themes, default=all_themes, key="themes")

# Sub-theme filter (hierarchical)
all_sub_themes = sorted([st for st in papers_df["sub_theme"].dropna().unique() if st])
if all_sub_themes:
    sel_sub_themes = st.sidebar.multiselect(
        "Sub-Themes (optional)", 
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
kw = st.sidebar.text_input("Keyword(s)", value="", placeholder="e.g., autonomy, additive manufacturing", key="kw")

# Reset filters button restores defaults
if st.sidebar.button("Reset filters"):
    st.session_state["from_date"] = min_date
    st.session_state["to_date"] = max_date
    st.session_state["themes"] = all_themes
    st.session_state["sub_themes"] = []
    st.session_state["all_unis_flag"] = True
    st.session_state["unis"] = all_unis
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

# For charts
def apply_fig_theme(fig: go.Figure, height: int = 360) -> go.Figure:
    """Apply dark theme to plotly figures"""
    fig.update_layout(
        height=height,
        paper_bgcolor="#1e293b",
        plot_bgcolor="#0f172a",
        font=dict(family="Inter, sans-serif", color="#f1f5f9", size=12),
        margin=dict(l=60, r=40, t=60, b=50),
        title_font=dict(size=18, color="#f1f5f9"),
        legend=dict(
            bgcolor="rgba(30,41,59,0.9)",
            bordercolor="#334155",
            borderwidth=1,
            font=dict(size=11, color="#cbd5e1")
        ),
        hoverlabel=dict(
            bgcolor="#1e293b",
            font_size=12,
            font_family="Inter, sans-serif",
            font_color="#f1f5f9",
            bordercolor="#334155"
        )
    )
    
    # Update axes for dark theme
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#334155',
        showline=True,
        linewidth=1,
        linecolor='#475569',
        color='#cbd5e1'
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#334155',
        showline=True,
        linewidth=1,
        linecolor='#475569',
        color='#cbd5e1'
    )
    
    return fig

def create_metric_card(label: str, value: str, delta: str = None, delta_color: str = "normal"):
    """Create a modern metric card with gradient background"""
    delta_html = ""
    if delta:
        delta_class = "positive" if delta_color == "normal" or "+" in delta else "negative"
        delta_html = f'<div class="metric-delta {delta_class}">{delta}</div>'
    
    return f"""
    <div class="card card-gradient" style="text-align: center;">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """

def create_section_header(icon: str, title: str, subtitle: str = None):
    """Create a modern section header with icon"""
    subtitle_html = f'<p class="section-subtitle">{subtitle}</p>' if subtitle else ""
    return f"""
    <h2 class="section-title">
        <span style="font-size: 1.5rem;">{icon}</span>
        {title}
    </h2>
    {subtitle_html}
    """

def create_insight_card(title: str, message: str, icon: str = ""):
    """Create an insight card with modern styling"""
    icon_display = f"{icon} " if icon else ""
    return f"""
    <div class="card" style="border-left: 4px solid #3b82f6; background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);">
        <h4 style="color: #f1f5f9; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">
            {icon_display}{title}
        </h4>
        <p style="color: #cbd5e1; font-size: 0.95rem; margin: 0;">
            {message}
        </p>
    </div>
    """

# ---- Header ----
# Modern Header
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

"""Primary navigation as top-level tabs (no selectbox)."""
tab_overview, tab_theme, tab_unis, tab_trends, tab_emerging, tab_quality = st.tabs(["Overview", "Theme Analysis", "Universities", "Trends", "Emerging Topics", "Data Quality"])

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

with tab_overview:
    # === KEY INSIGHTS SECTION ===
    st.markdown(create_section_header(
        "", 
        "Key Insights & Recommendations",
        "AI-powered analysis of research trends and opportunities"
    ), unsafe_allow_html=True)
    
    if insights:
        # Show insights in a grid with modern cards
        insight_cols = st.columns(min(len(insights), 3))
        for idx, insight in enumerate(insights):
            col = insight_cols[idx % 3]
            
            # Modern gradient colors by type - Dark Blue theme with light text
            gradient_colors = {
                "emerging": "linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%)",
                "opportunity": "linear-gradient(135deg, #164e63 0%, #0c4a6e 100%)",
                "concentration": "linear-gradient(135deg, #92400e 0%, #b45309 100%)",
                "quality": "linear-gradient(135deg, #5b21b6 0%, #6d28d9 100%)",
                "trend": "linear-gradient(135deg, #1e40af 0%, #2563eb 100%)",
                "collaboration": "linear-gradient(135deg, #831843 0%, #9f1239 100%)"
            }
            bg = gradient_colors.get(insight['type'], "linear-gradient(135deg, #1e293b 0%, #334155 100%)")
            
            border_colors = {
                "emerging": "#3b82f6",
                "opportunity": "#2563eb",
                "concentration": "#f59e0b",
                "quality": "#8b5cf6",
                "trend": "#06b6d4",
                "collaboration": "#ec4899"
            }
            border = border_colors.get(insight['type'], "#64748b")
            
            with col:
                st.markdown(
                    f"""<div class='card' style='background:{bg}; border-left: 4px solid {border}; min-height: 180px;'>
                        <div style='font-size:2.5em; margin-bottom:0.75em;'>{insight['icon']}</div>
                        <div style='font-weight:700; color:#f1f5f9; margin-bottom:0.5em; font-size:1.1rem;'>{insight['title']}</div>
                        <div style='color:#cbd5e1; margin-bottom:0.75em; line-height:1.6;'>{insight['message']}</div>
                        <div style='font-size:0.875em; color:#94a3b8; font-style:italic; padding-top:0.5em; border-top:1px solid rgba(241,245,249,0.2);'>{insight['detail']}</div>
                    </div>""",
                    unsafe_allow_html=True
                )
    else:
        st.info("Analyzing research patterns to generate insights...")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # === MODERN KPI DASHBOARD ===
    st.markdown(create_section_header(
        "",
        "Research Metrics Overview",
        "Comprehensive statistics across the entire dataset"
    ), unsafe_allow_html=True)
    
    # KPIs Row - Show total dataset metrics with modern styling
    k1, k2, k3, k4, k5 = st.columns(5)
    
    with k1:
        st.metric("Total Papers", f"{len(papers_df):,}", delta=None)
    with k2:
        st.metric("Research Topics", len(mapping), delta=None)
    with k3:
        st.metric("Sub-Themes", papers_df["sub_theme"].nunique(), delta=None)
    with k4:
        st.metric("Universities", papers_df["university"].nunique(), delta=None)
    with k5:
        try:
            avg_growth = sum(p.get("growth_rate", 0) for p in trends.get("strategic_priorities", [])) / max(1, len(trends.get("strategic_priorities", [])))
            st.metric("Avg Growth Rate", f"{avg_growth*100:+.1f}%", delta=f"{avg_growth*100:.1f}%")
        except Exception:
            st.metric("Avg Growth Rate", "N/A", delta=None)

    st.markdown("<hr>", unsafe_allow_html=True)
    
    # === RESEARCH HIERARCHY VISUALIZATION ===
    st.markdown(create_section_header(
        "",
        "Research Hierarchy Explorer",
        "Interactive drill-down: Theme → Sub-Theme → Topic"
    ), unsafe_allow_html=True)
    
    st.markdown("*Click on any segment to zoom in. Click the center to zoom out. All themes and sub-themes are displayed.*")
    
    try:
        sunburst_fig = create_sunburst_chart(filtered, mapping)
        st.plotly_chart(sunburst_fig, use_container_width=True, key="overview_sunburst")
    except Exception as e:
        st.error(f"Could not generate hierarchy chart: {str(e)}")

    st.markdown("<hr>", unsafe_allow_html=True)

    # Papers per Theme Distribution
    st.markdown('<p class="sub-header">Papers per Strategic Theme</p>', unsafe_allow_html=True)
    theme_counts = papers_df.groupby("theme").size()
    theme_counts = theme_counts.reindex(list(BABCOCK_THEMES.keys()), fill_value=0)
    # Sort ascending so top is at top
    theme_counts_sorted = theme_counts.sort_values(ascending=True)
    fig = px.bar(
        x=theme_counts_sorted.values,
        y=[t.replace("_", " ").title() for t in theme_counts_sorted.index],
        orientation="h",
        color=theme_counts_sorted.values,
        color_continuous_scale="Blues",
        title="Papers per Theme (All Research Themes)"
    )
    fig = apply_fig_theme(fig, height=380)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # SUB-THEME OVERVIEW
    st.markdown('<p class="sub-header">Top Sub-Themes (Hierarchical Analysis)</p>', unsafe_allow_html=True)
    papers_with_sub = papers_df[papers_df["sub_theme"].notna()]
    if not papers_with_sub.empty:
        sub_theme_summary = papers_with_sub.groupby("sub_theme").agg(
            papers=("title", "count"),
            avg_confidence=("sub_theme_confidence", "mean")
        ).sort_values("papers", ascending=True).tail(15).reset_index()  # Changed to ascending=True and tail() to get top items in correct order
        sub_theme_summary["sub_theme"] = sub_theme_summary["sub_theme"].str.replace("_", " ").str.title()
        sub_theme_summary["avg_confidence"] = (sub_theme_summary["avg_confidence"] * 100).round(1)
        
        fig_sub_overview = px.bar(
            sub_theme_summary,
            x="papers",
            y="sub_theme",
            orientation="h",
            color="avg_confidence",
            color_continuous_scale="Blues",
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

with tab_theme:
    # Strategic Theme Priorities - Color-coded by growth rate
    st.markdown('<p class="sub-header">Strategic Theme Priorities</p>', unsafe_allow_html=True)
    st.markdown("*Research themes colored by growth rate: 🟢 Green (positive growth) • 🔴 Red (negative growth)*")
    
    priorities = trends.get("strategic_priorities", [])
    
    def get_growth_color_style_theme(growth_rate):
        """Generate darker, solid color gradients based on growth rate for dark theme"""
        growth_pct = growth_rate * 100
        
        if growth_pct >= 50:
            return {
                "bg": "linear-gradient(135deg, #065f46 0%, #047857 100%)",
                "border": "#10b981",
                "icon": "▲▲",
                "label": f"+{growth_pct:.0f}%",
                "color": "#ffffff",
                "icon_color": "#6ee7b7"
            }
        elif growth_pct >= 20:
            return {
                "bg": "linear-gradient(135deg, #047857 0%, #059669 100%)",
                "border": "#34d399",
                "icon": "▲",
                "label": f"+{growth_pct:.0f}%",
                "color": "#ffffff",
                "icon_color": "#a7f3d0"
            }
        elif growth_pct >= 5:
            return {
                "bg": "linear-gradient(135deg, #059669 0%, #10b981 100%)",
                "border": "#6ee7b7",
                "icon": "▲",
                "label": f"+{growth_pct:.0f}%",
                "color": "#ffffff",
                "icon_color": "#d1fae5"
            }
        elif growth_pct >= 0:
            return {
                "bg": "linear-gradient(135deg, #10b981 0%, #34d399 100%)",
                "border": "#a7f3d0",
                "icon": "→",
                "label": f"+{growth_pct:.1f}%",
                "color": "#ffffff",
                "icon_color": "#d1fae5"
            }
        elif growth_pct >= -5:
            return {
                "bg": "linear-gradient(135deg, #dc2626 0%, #ef4444 100%)",
                "border": "#fca5a5",
                "icon": "→",
                "label": f"{growth_pct:.1f}%",
                "color": "#ffffff",
                "icon_color": "#fecaca"
            }
        elif growth_pct >= -20:
            return {
                "bg": "linear-gradient(135deg, #b91c1c 0%, #dc2626 100%)",
                "border": "#f87171",
                "icon": "▼",
                "label": f"{growth_pct:.0f}%",
                "color": "#ffffff",
                "icon_color": "#fca5a5"
            }
        else:
            return {
                "bg": "linear-gradient(135deg, #991b1b 0%, #b91c1c 100%)",
                "border": "#ef4444",
                "icon": "▼▼",
                "label": f"{growth_pct:.0f}%",
                "color": "#ffffff",
                "icon_color": "#f87171"
            }
    
    grid = st.columns(3)
    for i, pr in enumerate(priorities):
        col = grid[i % 3]
        theme = pr.get("theme", "").replace("_", " ").title()
        growth = pr.get("growth_rate", 0)
        papers = pr.get("total_papers", 0)
        
        style = get_growth_color_style_theme(growth)
        
        with col:
            st.markdown(
                f"""
                <div class='card' style='
                    background: {style["bg"]};
                    border: 2px solid {style["border"]};
                    color: {style["color"]};
                    padding: 1rem;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
                    transition: all 0.2s ease;
                '>
                    <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;'>
                        <span style='font-size: 1.5rem; font-weight: bold; color: {style["icon_color"]};'>{style["icon"]}</span>
                        <span style='
                            font-size: 0.75rem;
                            font-weight: 700;
                            letter-spacing: 0.05em;
                            color: {style["color"]};
                            background: rgba(255, 255, 255, 0.15);
                            padding: 0.25rem 0.6rem;
                            border-radius: 5px;
                            border: 1px solid {style["border"]};
                        '>{style["label"]}</span>
                    </div>
                    <div style='font-size: 0.95rem; font-weight: 700; margin-bottom: 0.5rem; color: {style["color"]};'>
                        {theme}
                    </div>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid rgba(255, 255, 255, 0.2);'>
                        <div>
                            <div style='font-size: 1.25rem; font-weight: 800; color: {style["icon_color"]};'>{growth*100:+.1f}%</div>
                            <div style='font-size: 0.65rem; color: {style["color"]}; opacity: 0.8;'>Growth Rate</div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 1.25rem; font-weight: 800; color: {style["color"]};'>{papers:,}</div>
                            <div style='font-size: 0.65rem; color: {style["color"]}; opacity: 0.8;'>Papers</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # === PUBLICATION TRENDS ===
    st.markdown(create_section_header(
        "",
        "Publication Trends Over Time",
        "Monthly research output by theme"
    ), unsafe_allow_html=True)
    
    try:
        timeline_fig = create_trend_timeline(filtered)
        st.plotly_chart(timeline_fig, use_container_width=True, key="theme_timeline")
    except Exception as e:
        st.error(f"Could not generate timeline: {str(e)}")

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

    # ========== RESEARCH FLOW DIAGRAM ==========
    st.markdown('<p class="sub-header">Research Flow Analysis</p>', unsafe_allow_html=True)
    st.markdown("*Trace how research themes flow through specific sub-themes to leading universities. Width of flow = number of papers.*")
    try:
        sankey_fig = create_sankey_flow(filtered)
        st.plotly_chart(sankey_fig, use_container_width=True)
        
        # Add interpretation
        st.markdown(
            '<div style="padding: 1rem; background: #1e3a5f; border-left: 4px solid #3b82f6; border-radius: 0.5rem; color: #f1f5f9;">'
            '<strong style="color: #60a5fa;">Strategic Insight:</strong> Follow thick flows to identify which universities dominate specific sub-themes. Thin flows indicate collaboration opportunities.'
            '</div>',
            unsafe_allow_html=True
        )
    except Exception as e:
        st.warning(f"Sankey diagram could not be generated: {e}")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # === SUB-THEME ANALYSIS SECTION ===
    st.markdown('<p class="sub-header">Sub-Theme Analysis</p>', unsafe_allow_html=True)
    st.markdown("*Explore individual themes and their sub-themes in detail. Select a theme below to view its breakdown.*")
    
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
        fig = px.bar(q, x="quarter", y="count", color="count", color_continuous_scale="Blues", title=f"{selected_theme_display} - Quarterly Output")
        fig = apply_fig_theme(fig, height=340)
        st.plotly_chart(fig, use_container_width=True)
        
        # SUB-THEME BREAKDOWN for selected parent theme
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
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
            
            
            # Sub-theme distribution chart
            top_10_sub = sub_theme_counts.head(10).sort_values("Papers", ascending=True)  # Sort ascending for correct order
            fig_sub = px.bar(
                top_10_sub,
                x="Papers",
                y="Sub-Theme",
                orientation="h",
                color="Avg Confidence (%)",
                color_continuous_scale="Blues",
                title=f"Top 10 Sub-Themes in {selected_theme_display}"
            )
            fig_sub = apply_fig_theme(fig_sub, height=340)
            st.plotly_chart(fig_sub, use_container_width=True)
        else:
            st.info(f"No sub-theme data available for {selected_theme_display}")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        uc = theme_papers["university"].value_counts().head(10)
        uc_sorted = uc.sort_values(ascending=True)  # Sort ascending for correct order
        fig = px.bar(x=uc_sorted.values, y=uc_sorted.index, orientation="h", color=uc_sorted.values, color_continuous_scale="Blues", title=f"Top 10 Universities in {selected_theme_display}")
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
            adj_df = adj_df.sort_values("Connections", ascending=True)  # Sort ascending for correct order
            fig_adj = px.bar(adj_df, x="Connections", y="Theme", orientation="h", color="Connections", color_continuous_scale="Blues", title=f"Top Adjacent Themes to {selected_theme_display}")
            fig_adj = apply_fig_theme(fig_adj, height=300)
            st.plotly_chart(fig_adj, use_container_width=True)
        else:
            st.info("No significant adjacent themes detected for this theme")

with tab_unis:
    st.markdown('<p class="sub-header">Overall Research Output Rankings</p>', unsafe_allow_html=True)
    uc = papers_df["university"].value_counts()
    uc_top15 = uc.head(15).sort_values(ascending=True)  # Sort ascending for correct order
    fig = px.bar(x=uc_top15.values, y=uc_top15.index, orientation="h", color=uc_top15.values, color_continuous_scale="Blues", title="Top 15 Universities by Total Papers")
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
    st.markdown('<p class="sub-header">University Research Profile Comparison</p>', unsafe_allow_html=True)
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
                st.info("**Strategic Insight**: Larger area = stronger focus. Compare shapes to identify complementary strengths for potential collaborations.")
            else:
                st.info("Unable to generate radar chart with current data.")
        except Exception as e:
            st.warning(f"Radar chart could not be generated: {e}")
    else:
        st.info("Please select at least 2 universities to compare their research profiles.")

with tab_trends:
    # ========== SUB-THEME GROWTH HEATMAP ==========
    st.markdown('<p class="sub-header">Sub-Theme Activity Heatmap</p>', unsafe_allow_html=True)
    st.markdown("*Darker colors indicate higher research activity. Track emerging and declining sub-themes over time.*")
    try:
        heatmap_fig = create_growth_heatmap(filtered)
        st.plotly_chart(heatmap_fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Heatmap could not be generated: {e}")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # ========== IMPACT BUBBLE CHART ==========
    st.markdown('<p class="sub-header">Sub-Theme Impact Analysis</p>', unsafe_allow_html=True)
    st.markdown("*Quadrant Analysis: Top-right = High growth + High citations (invest here)*")
    try:
        bubble_fig = create_impact_bubble_chart(filtered, mapping)
        st.plotly_chart(bubble_fig, use_container_width=True)
        
        # Interpretation guide
        cols = st.columns(4)
        cols[0].markdown("**Stars**<br>High Growth<br>High Citations", unsafe_allow_html=True)
        cols[1].markdown("**Gems**<br>Low Growth<br>High Citations", unsafe_allow_html=True)
        cols[2].markdown("**Rising**<br>High Growth<br>Low Citations", unsafe_allow_html=True)
        cols[3].markdown("**Watch**<br>Low Growth<br>Low Citations", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Impact bubble chart could not be generated: {e}")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # === STRATEGIC RECOMMENDATIONS ===
    st.markdown('<p class="sub-header">Strategic Research Recommendations</p>', unsafe_allow_html=True)
    
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
        st.markdown("**High Growth Areas**")
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
        st.markdown("**Investment Opportunities**")
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
        st.markdown("**Collaboration Focus**")
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

with tab_emerging:
    st.markdown('<p class="sub-header">Emerging Research Topics</p>', unsafe_allow_html=True)
    st.markdown("*Identify hot topics based on recency, growth rate, and publication volume*")
    
    # Controls
    col1, col2 = st.columns([1, 2])
    with col1:
        top_n = st.slider("Number of topics to show", 10, 30, 20, step=5)
    with col2:
        use_all_themes = st.checkbox("Show ALL themes (recommended)", value=True, key="emerging_all_themes",
                                     help="Uncheck to apply sidebar theme filter. Recommended to keep CHECKED for full picture.")
    
    # Use appropriate dataset - ALWAYS USE ALL DATA FOR EMERGING TOPICS
    # This gives a complete picture across all research themes
    if use_all_themes:
        emerging_data = papers_df.copy()
        # Apply date filter (always respect date range)
        emerging_data = emerging_data[(emerging_data["date"].dt.date >= start_date) & (emerging_data["date"].dt.date <= end_date)]
        themes_count = emerging_data['theme'].nunique()
        st.success(f"Analyzing {len(emerging_data):,} papers across **ALL {themes_count} themes** for complete emerging topics landscape")
    else:
        emerging_data = filtered.copy()
        themes_count = emerging_data['theme'].nunique()
        st.warning(f"Analyzing {len(emerging_data):,} papers from **{themes_count} selected themes only** (sidebar filter applied)")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Debug: Show theme distribution
    with st.expander("Data Debug Info - Theme Distribution"):
        theme_dist = emerging_data['theme'].value_counts()
        st.write(f"**Total themes in data**: {len(theme_dist)}")
        st.write(f"**Total papers**: {len(emerging_data)}")
        st.dataframe(theme_dist.reset_index().rename(columns={'theme': 'Theme', 'count': 'Papers'}), use_container_width=True)
    
    # ========== EMERGING TOPICS BUBBLE CHART ==========
    st.markdown('<p class="sub-header">Emerging Topics Landscape</p>', unsafe_allow_html=True)
    st.markdown("""
    **How to read this chart:**
    - **X-axis (Recency)**: How recent the papers are (higher = more recent)
    - **Y-axis (Growth Rate)**: How fast the topic is growing (higher = faster growth)
    - **Bubble Size**: Number of papers in the topic
    - **Color**: Research theme
    - **Top-right quadrant**: Hot emerging topics - both recent AND growing fast
    """)
    
    try:
        bubble_fig, emerging_df = create_emerging_topics_bubble(emerging_data, mapping, top_n=top_n)
        st.plotly_chart(bubble_fig, use_container_width=True)
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # ========== TOP EMERGING TOPICS TABLE ==========
        st.markdown('<p class="sub-header">Top Emerging Topics Details</p>', unsafe_allow_html=True)
        
        # Add ranking
        emerging_df['Rank'] = range(1, len(emerging_df) + 1)
        
        # Format for display (removed emergingness column)
        display_df = emerging_df[[
            'Rank',
            'topic_label',
            'theme',
            'sub_theme',
            'paper_count',
            'recency_score',
            'growth_rate',
            'avg_citations'
        ]].copy()
        
        display_df.columns = [
            'Rank',
            'Topic',
            'Theme',
            'Sub-Theme',
            'Papers',
            'Recency %',
            'Growth %',
            'Avg Citations'
        ]
        
        # Format numbers
        display_df['Recency %'] = display_df['Recency %'].apply(lambda x: f"{x:.1f}%")
        display_df['Growth %'] = display_df['Growth %'].apply(lambda x: f"{x:.1f}%")
        display_df['Avg Citations'] = display_df['Avg Citations'].apply(lambda x: f"{x:.1f}")
        display_df['Theme'] = display_df['Theme'].str.replace('_', ' ')
        display_df['Sub-Theme'] = display_df['Sub-Theme'].fillna('—').str.replace('_', ' ')
        
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=600)
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # ========== STRATEGIC INSIGHTS ==========
        st.markdown('<p class="sub-header">Strategic Insights</p>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Hottest Topics**")
            st.markdown("*(Top-right quadrant: High recency + High growth)*")
            hot_topics = emerging_df[
                (emerging_df['recency_score'] > emerging_df['recency_score'].median()) &
                (emerging_df['growth_rate'] > emerging_df['growth_rate'].median())
            ].head(5)
            if len(hot_topics) > 0:
                for _, topic in hot_topics.iterrows():
                    st.markdown(f"- **{topic['topic_label']}**")
                    st.markdown(f"  *{topic['theme'].replace('_', ' ')}* ({topic['paper_count']} papers)")
            else:
                st.info("No topics in hot quadrant")
        
        with col2:
            st.markdown("**Momentum Leaders**")
            st.markdown("*(Highest growth rates)*")
            momentum_topics = emerging_df.nlargest(5, 'growth_rate')
            for _, topic in momentum_topics.iterrows():
                st.markdown(f"- **{topic['topic_label']}**")
                st.markdown(f"  Growth: {topic['growth_rate']:.1f}% ({topic['paper_count']} papers)")
        
        with col3:
            st.markdown("**Recent Surges**")
            st.markdown("*(Highest recency scores)*")
            recent_topics = emerging_df.nlargest(5, 'recency_score')
            for _, topic in recent_topics.iterrows():
                st.markdown(f"- **{topic['topic_label']}**")
                st.markdown(f"  Recency: {topic['recency_score']:.1f}% ({topic['paper_count']} papers)")
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # ========== THEME BREAKDOWN ==========
        st.markdown('<p class="sub-header">Emerging Topics by Theme</p>', unsafe_allow_html=True)
        
        theme_summary = emerging_df.groupby('theme').agg({
            'topic_id': 'count',
            'paper_count': 'sum',
            'emergingness': 'mean'
        }).reset_index()
        
        theme_summary.columns = ['Theme', 'Emerging Topics', 'Total Papers', 'Avg Emergingness']
        theme_summary['Theme'] = theme_summary['Theme'].str.replace('_', ' ')
        theme_summary = theme_summary.sort_values('Avg Emergingness', ascending=False)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_theme_bar = px.bar(
                theme_summary,
                x='Theme',
                y='Emerging Topics',
                color='Avg Emergingness',
                title="Number of Emerging Topics per Theme",
                color_continuous_scale='Viridis'
            )
            fig_theme_bar = apply_fig_theme(fig_theme_bar, height=350)
            st.plotly_chart(fig_theme_bar, use_container_width=True)
        
        with col2:
            st.dataframe(theme_summary, use_container_width=True, hide_index=True, height=350)
        
    except Exception as e:
        st.error(f"Could not generate emerging topics analysis: {e}")
        st.info("Make sure you have sufficient data with topic assignments and dates.")

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
        file_name=f"research_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
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
            file_name=f"research_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    except Exception:
        st.info("Install openpyxl for Excel export: pip install openpyxl")
