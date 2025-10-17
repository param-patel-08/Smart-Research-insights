"""
Trends tab - Research output trends, lifecycle analysis, heatmap, and strategic recommendations.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.utils.visualizations import create_growth_heatmap
from dashboard.utils.styling import apply_fig_theme
from config.themes import BABCOCK_THEMES


def render_trends_tab(filtered, papers_df, trends):
    """
    Render the Trends tab content.
    
    Args:
        filtered: Filtered dataframe based on user selections
        papers_df: Full papers dataframe
        trends: Trends data
    """
    # ========== 1. RESEARCH OUTPUT TRENDS (SELECTED THEMES) ==========
    st.markdown('<p class="sub-header">Research Output Trends</p>', unsafe_allow_html=True)
    st.markdown("*Compare research output trajectories across themes over time.*")
    
    names = [t.replace("_", " ").title() for t in BABCOCK_THEMES.keys()]
    picks = st.multiselect("Select Themes to Compare", names, default=names[:3])
    
    if picks:
        # Convert selected names back to match original data format
        raw = []
        for pick in picks:
            pick_normalized = pick.replace(" ", "_").lower()
            # Find matching theme in actual data
            for theme in papers_df["theme"].unique():
                if theme.lower() == pick_normalized:
                    raw.append(theme)
                    break
        
        f = papers_df[papers_df["theme"].isin(raw)]
        quarters = sorted(papers_df["quarter"].unique())
        base = pd.MultiIndex.from_product([quarters, raw], names=["quarter", "theme"]) 
        qt = f.groupby(["quarter", "theme"]).size().reindex(base, fill_value=0).reset_index(name="count")
        qt["quarter"], qt["theme"] = qt["quarter"].astype(str), qt["theme"].str.replace("_", " ").str.title()
        
        fig = px.line(
            qt, 
            x="quarter", 
            y="count", 
            color="theme", 
            title=" ",
            labels={"quarter": "Quarter", "count": "Number of Papers", "theme": "Theme"},
            markers=True
        )
        fig = apply_fig_theme(fig, height=420)
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Please select at least one theme to view trends.")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # ========== 2. SUB-THEME LIFECYCLE ANALYSIS ==========
    st.markdown('<p class="sub-header">Sub-Theme Lifecycle Analysis</p>', unsafe_allow_html=True)
    st.markdown("*Track the rise and fall of specific sub-themes over time. Select sub-themes to analyze their trajectories.*")
    
    # Get all sub-themes for selection
    all_subthemes = sorted([s for s in papers_df['sub_theme'].dropna().unique() if s])
    
    # Default to top 5 most active sub-themes
    subtheme_counts = papers_df['sub_theme'].value_counts()
    default_subthemes = [s.replace('_', ' ') for s in subtheme_counts.head(5).index]
    
    selected_subthemes = st.multiselect(
        "Select Sub-Themes to Track",
        options=[s.replace('_', ' ') for s in all_subthemes],
        default=default_subthemes,
        max_selections=10
    )
    
    if selected_subthemes:
        # Convert back to match original data format (preserve exact casing from data)
        raw_subthemes = []
        for selected in selected_subthemes:
            selected_normalized = selected.replace(' ', '_').lower()
            # Find matching sub-theme in actual data
            for subtheme in papers_df['sub_theme'].dropna().unique():
                if subtheme.lower() == selected_normalized:
                    raw_subthemes.append(subtheme)
                    break
        
        # Create lifecycle data
        lifecycle_df = papers_df[papers_df['sub_theme'].isin(raw_subthemes)].copy()
        lifecycle_df['year_quarter'] = lifecycle_df['date'].dt.to_period('Q').astype(str)
        
        lifecycle_data = lifecycle_df.groupby(['sub_theme', 'year_quarter']).size().reset_index(name='count')
        lifecycle_data['sub_theme'] = lifecycle_data['sub_theme'].str.replace('_', ' ').str.title()
        
        # Create line chart
        fig = px.line(
            lifecycle_data,
            x='year_quarter',
            y='count',
            color='sub_theme',
            title=" ",
            labels={'year_quarter': 'Quarter', 'count': 'Number of Papers', 'sub_theme': 'Sub-Theme'},
            markers=True
        )
        
        fig = apply_fig_theme(fig, height=450)
        fig.update_layout(
            hovermode="x unified",
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Add interpretation
        st.markdown(
            '<div style="padding: 1rem; background: #1e3a5f; border-left: 4px solid #3b82f6; border-radius: 0.5rem; color: #f1f5f9;">'
            '<strong style="color: #60a5fa;">📈 Lifecycle Insights:</strong> Rising lines indicate growing sub-themes with momentum. '
            'Declining lines suggest mature or fading topics. Flat lines show stable, consistent research areas.'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        st.info("Please select at least one sub-theme to view its lifecycle trajectory.")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # ========== 3. SUB-THEME ACTIVITY HEATMAP ==========
    st.markdown('<p class="sub-header">Sub-Theme Activity Heatmap</p>', unsafe_allow_html=True)
    st.markdown("*Track research activity intensity across sub-themes over time. Warmer colors indicate higher activity.*")
    try:
        heatmap_fig = create_growth_heatmap(filtered)
        st.plotly_chart(heatmap_fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Heatmap could not be generated: {e}")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # ========== 4. STRATEGIC RESEARCH RECOMMENDATIONS ==========
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
                    f"<div class='card' style='background:#064e3b; border: 1px solid #059669; padding:0.5em;'>"
                    f"<div style='font-size:0.9em; font-weight:500; color:#d1fae5;'>{idx}. {subtheme}</div>"
                    f"<div style='font-size:0.8em; color:#6ee7b7;'>↗ {row['growth_rate']:.0f}% growth</div>"
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
                f"<div class='card' style='background:#1e3a8a; border: 1px solid #3b82f6; padding:0.5em;'>"
                f"<div style='font-size:0.9em; font-weight:500; color:#bfdbfe;'>{idx}. {opp['sub_theme']}</div>"
                f"<div style='font-size:0.8em; color:#93c5fd;'>Gap: {opp['potential']} papers</div>"
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
                    f"<div class='card' style='background:#78350f; border: 1px solid #f59e0b; padding:0.5em;'>"
                    f"<div style='font-size:0.9em; font-weight:500; color:#fef3c7;'>{idx}. {subtheme}</div>"
                    f"<div style='font-size:0.8em; color:#fcd34d;'>{int(row['unis'])} universities</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
