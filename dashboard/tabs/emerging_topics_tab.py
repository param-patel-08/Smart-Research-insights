"""
Emerging Topics tab - Identify and analyze emerging research topics.
"""
import streamlit as st
import plotly.express as px

from dashboard.utils.insights import create_emerging_topics_bubble
from dashboard.utils.visualizations import create_impact_bubble_chart
from dashboard.utils.styling import apply_fig_theme


def render_emerging_topics_tab(filtered, mapping, start_date, end_date, papers_df):
    """
    Render the Emerging Topics tab content.
    
    Args:
        filtered: Filtered dataframe based on user selections
        mapping: Topic mapping data
        start_date: Filter start date
        end_date: Filter end date
        papers_df: Full papers dataframe
    """
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
        
        # ========== SUB-THEME IMPACT ANALYSIS ==========
        st.markdown('<p class="sub-header">Sub-Theme Impact Analysis</p>', unsafe_allow_html=True)
        st.markdown("*Analyze growth vs citations to identify high-impact research areas. Theme names shown in bubbles.*")
        
        try:
            bubble_fig = create_impact_bubble_chart(emerging_data, mapping)
            st.plotly_chart(bubble_fig, use_container_width=True)
            
            # Interpretation guide
            cols = st.columns(4)
            cols[0].markdown(
                '<div style="padding: 0.5rem; background: #064e3b; border-radius: 0.5rem; text-align: center;">'
                '<strong style="color: #6ee7b7;">⭐ Stars</strong><br>'
                '<span style="color: #d1fae5; font-size: 0.85rem;">High Growth<br>High Citations</span>'
                '</div>',
                unsafe_allow_html=True
            )
            cols[1].markdown(
                '<div style="padding: 0.5rem; background: #1e3a8a; border-radius: 0.5rem; text-align: center;">'
                '<strong style="color: #93c5fd;">💎 Gems</strong><br>'
                '<span style="color: #bfdbfe; font-size: 0.85rem;">Low Growth<br>High Citations</span>'
                '</div>',
                unsafe_allow_html=True
            )
            cols[2].markdown(
                '<div style="padding: 0.5rem; background: #78350f; border-radius: 0.5rem; text-align: center;">'
                '<strong style="color: #fcd34d;">📈 Rising</strong><br>'
                '<span style="color: #fef3c7; font-size: 0.85rem;">High Growth<br>Low Citations</span>'
                '</div>',
                unsafe_allow_html=True
            )
            cols[3].markdown(
                '<div style="padding: 0.5rem; background: #334155; border-radius: 0.5rem; text-align: center;">'
                '<strong style="color: #cbd5e1;">👀 Watch</strong><br>'
                '<span style="color: #e2e8f0; font-size: 0.85rem;">Low Growth<br>Low Citations</span>'
                '</div>',
                unsafe_allow_html=True
            )
        except Exception as e:
            st.warning(f"Impact bubble chart could not be generated: {e}")
        
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
