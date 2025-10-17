"""
Trends tab - Sub-theme heatmap, impact analysis, and strategic recommendations.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.utils.visualizations import create_growth_heatmap, create_impact_bubble_chart
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
        # Need to pass mapping to create_impact_bubble_chart
        # For now, we'll check if it's available in the function call
        from dashboard.utils.data_loader import load_data
        _, _, mapping = load_data()
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
    fig.update_layout(title="", xaxis_title="Quarter", yaxis_title="Papers")
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
