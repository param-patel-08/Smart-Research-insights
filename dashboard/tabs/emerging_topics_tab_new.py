"""
Emerging Topics tab - Identify and analyze emerging research topics.
"""
import streamlit as st
import plotly.express as px

from dashboard.utils.insights import create_emerging_topics_bubble
from dashboard.utils.styling import apply_fig_theme
from config.themes import STRATEGIC_THEMES


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
    col1, col2 = st.columns([1, 1])
    with col1:
        top_n = st.slider("Number of Topics to Show", 10, 30, 20, step=5)
    with col2:
        # Theme selection
        theme_names = [t.replace("_", " ").title() for t in STRATEGIC_THEMES.keys()]
        selected_themes = st.multiselect(
            "Select Themes to Analyze",
            options=["All Themes"] + theme_names,
            default=["All Themes"]
        )
    
    # Filter data based on theme selection
    if "All Themes" in selected_themes or not selected_themes:
        emerging_data = papers_df.copy()
        emerging_data = emerging_data[(emerging_data["date"].dt.date >= start_date) & (emerging_data["date"].dt.date <= end_date)]
        themes_count = emerging_data['theme'].nunique()
    else:
        # Convert back to original theme format
        raw_themes = []
        for selected in selected_themes:
            selected_normalized = selected.replace(" ", "_").lower()
            for theme in papers_df["theme"].unique():
                if theme.lower() == selected_normalized:
                    raw_themes.append(theme)
                    break
        
        emerging_data = papers_df[papers_df["theme"].isin(raw_themes)].copy()
        emerging_data = emerging_data[(emerging_data["date"].dt.date >= start_date) & (emerging_data["date"].dt.date <= end_date)]
        themes_count = len(raw_themes)
    
    st.markdown(
        f'<div style="padding: 0.75rem; background: #1e3a5f; border-left: 4px solid #3b82f6; border-radius: 0.5rem; margin: 1rem 0;">'
        f'<span style="color: #93c5fd;">📊 Analyzing <strong style="color: #60a5fa;">{len(emerging_data):,}</strong> papers across '
        f'<strong style="color: #60a5fa;">{themes_count}</strong> theme(s)</span>'
        f'</div>',
        unsafe_allow_html=True
    )
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # ========== EMERGING TOPICS BUBBLE CHART ==========
    st.markdown('<p class="sub-header">Emerging Topics Bubble Chart</p>', unsafe_allow_html=True)
    st.markdown(
        '<div style="padding: 0.5rem 1rem; background: rgba(59, 130, 246, 0.1); border-radius: 0.5rem; margin-bottom: 1rem;">'
        '<span style="color: #93c5fd; font-size: 0.9rem;">'
        '<strong>X-axis:</strong> Recency Score (higher = more recent) | '
        '<strong>Y-axis:</strong> Growth Rate (higher = faster growth) | '
        '<strong>Size:</strong> Number of papers | '
        '<strong>Top-right:</strong> Hot emerging topics'
        '</span>'
        '</div>',
        unsafe_allow_html=True
    )
    
    try:
        bubble_fig, emerging_df = create_emerging_topics_bubble(emerging_data, mapping, top_n=top_n)
        st.plotly_chart(bubble_fig, use_container_width=True)
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # ========== STRATEGIC INSIGHTS ==========
        st.markdown('<p class="sub-header">Strategic Insights</p>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(
                '<div style="background: linear-gradient(135deg, #064e3b 0%, #065f46 100%); '
                'padding: 1.25rem; border-radius: 12px; border: 1px solid #059669; min-height: 280px;">'
                '<div style="display: flex; align-items: center; margin-bottom: 1rem;">'
                '<span style="font-size: 2rem; margin-right: 0.5rem;">🔥</span>'
                '<h3 style="color: #6ee7b7; margin: 0; font-size: 1.1rem;">Hottest Topics</h3>'
                '</div>'
                '<p style="color: #d1fae5; font-size: 0.85rem; margin-bottom: 1rem;">High recency + High growth</p>',
                unsafe_allow_html=True
            )
            hot_topics = emerging_df[
                (emerging_df['recency_score'] > emerging_df['recency_score'].median()) &
                (emerging_df['growth_rate'] > emerging_df['growth_rate'].median())
            ].head(5)
            if len(hot_topics) > 0:
                for idx, topic in hot_topics.iterrows():
                    st.markdown(
                        f'<div style="background: rgba(16, 185, 129, 0.1); padding: 0.5rem; '
                        f'border-radius: 6px; margin-bottom: 0.5rem; border-left: 3px solid #10b981;">'
                        f'<div style="color: #d1fae5; font-weight: 600; font-size: 0.9rem;">{topic["topic_label"]}</div>'
                        f'<div style="color: #6ee7b7; font-size: 0.75rem;">{topic["theme"].replace("_", " ")} • {topic["paper_count"]} papers</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.markdown('<p style="color: #94a3b8; font-size: 0.85rem;">No topics in hot quadrant</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(
                '<div style="background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); '
                'padding: 1.25rem; border-radius: 12px; border: 1px solid #3b82f6; min-height: 280px;">'
                '<div style="display: flex; align-items: center; margin-bottom: 1rem;">'
                '<span style="font-size: 2rem; margin-right: 0.5rem;">📈</span>'
                '<h3 style="color: #93c5fd; margin: 0; font-size: 1.1rem;">Momentum Leaders</h3>'
                '</div>'
                '<p style="color: #bfdbfe; font-size: 0.85rem; margin-bottom: 1rem;">Highest growth rates</p>',
                unsafe_allow_html=True
            )
            momentum_topics = emerging_df.nlargest(5, 'growth_rate')
            for idx, topic in momentum_topics.iterrows():
                st.markdown(
                    f'<div style="background: rgba(59, 130, 246, 0.1); padding: 0.5rem; '
                    f'border-radius: 6px; margin-bottom: 0.5rem; border-left: 3px solid #3b82f6;">'
                    f'<div style="color: #bfdbfe; font-weight: 600; font-size: 0.9rem;">{topic["topic_label"]}</div>'
                    f'<div style="color: #93c5fd; font-size: 0.75rem;">Growth: {topic["growth_rate"]:.1f}% • {topic["paper_count"]} papers</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown(
                '<div style="background: linear-gradient(135deg, #78350f 0%, #92400e 100%); '
                'padding: 1.25rem; border-radius: 12px; border: 1px solid #f59e0b; min-height: 280px;">'
                '<div style="display: flex; align-items: center; margin-bottom: 1rem;">'
                '<span style="font-size: 2rem; margin-right: 0.5rem;">⚡</span>'
                '<h3 style="color: #fcd34d; margin: 0; font-size: 1.1rem;">Recent Surges</h3>'
                '</div>'
                '<p style="color: #fef3c7; font-size: 0.85rem; margin-bottom: 1rem;">Highest recency scores</p>',
                unsafe_allow_html=True
            )
            recent_topics = emerging_df.nlargest(5, 'recency_score')
            for idx, topic in recent_topics.iterrows():
                st.markdown(
                    f'<div style="background: rgba(245, 158, 11, 0.1); padding: 0.5rem; '
                    f'border-radius: 6px; margin-bottom: 0.5rem; border-left: 3px solid #f59e0b;">'
                    f'<div style="color: #fef3c7; font-weight: 600; font-size: 0.9rem;">{topic["topic_label"]}</div>'
                    f'<div style="color: #fcd34d; font-size: 0.75rem;">Recency: {topic["recency_score"]:.1f}% • {topic["paper_count"]} papers</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # ========== TOP EMERGING TOPICS TABLE ==========
        st.markdown('<p class="sub-header">Top Emerging Topics</p>', unsafe_allow_html=True)
        st.markdown(
            '<div style="padding: 0.5rem 1rem; background: rgba(100, 116, 139, 0.1); border-radius: 0.5rem; margin-bottom: 1rem;">'
            '<span style="color: #94a3b8; font-size: 0.9rem;">Detailed breakdown of emerging research topics ranked by emergingness score</span>'
            '</div>',
            unsafe_allow_html=True
        )
        
        # Add ranking
        emerging_df['Rank'] = range(1, len(emerging_df) + 1)
        
        # Format for display
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
        display_df['Theme'] = display_df['Theme'].str.replace('_', ' ').str.title()
        display_df['Sub-Theme'] = display_df['Sub-Theme'].fillna('—').str.replace('_', ' ').str.title()
        display_df['Topic'] = display_df['Topic'].str.title()
        
        # Apply dark theme styling to dataframe
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=500,
            column_config={
                "Rank": st.column_config.NumberColumn(
                    "Rank",
                    help="Ranking based on emergingness score",
                    width="small"
                ),
                "Topic": st.column_config.TextColumn(
                    "Topic",
                    help="AI-generated topic label",
                    width="large"
                ),
                "Papers": st.column_config.NumberColumn(
                    "Papers",
                    help="Number of papers in this topic",
                    width="small"
                ),
                "Recency %": st.column_config.TextColumn(
                    "Recency %",
                    help="How recent the papers are",
                    width="small"
                ),
                "Growth %": st.column_config.TextColumn(
                    "Growth %",
                    help="Growth rate over time",
                    width="small"
                ),
                "Avg Citations": st.column_config.TextColumn(
                    "Avg Citations",
                    help="Average citations per paper",
                    width="small"
                )
            }
        )
        
    except Exception as e:
        st.error(f"Could not generate emerging topics analysis: {e}")
        st.info("Make sure you have sufficient data with topic assignments and dates.")
