"""
Overview tab - Key insights, metrics, and research hierarchy.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from dashboard.utils.visualizations import create_sunburst_chart
from dashboard.utils.styling import create_section_header, apply_fig_theme
from dashboard.utils.insights import generate_insights
from config.themes import BABCOCK_THEMES


def render_overview_tab(filtered, papers_df, trends, mapping):
    """
    Render the Overview tab content.
    
    Args:
        filtered: Filtered dataframe based on user selections
        papers_df: Full papers dataframe
        trends: Trends data
        mapping: Topic mapping data
    """
    # Generate insights
    insights = generate_insights(papers_df, trends, mapping)
    
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
        title=" ",
        labels={"x": "Papers", "y": "Strategic Theme", "color": "Papers"}
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
            title=" ",
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
        fig_overall.update_layout(title="", xaxis_title="Quarter", yaxis_title="Papers")
        st.plotly_chart(fig_overall, use_container_width=True)
    else:
        st.info("No trend data available")
