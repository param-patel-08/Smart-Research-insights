"""
Universities tab - University rankings, deep dive, and comparison.
"""
import streamlit as st
import plotly.express as px

from dashboard.utils.visualizations import create_university_radar
from dashboard.utils.styling import apply_fig_theme


def render_universities_tab(filtered, papers_df):
    """
    Render the Universities tab content.
    
    Args:
        filtered: Filtered dataframe based on user selections
        papers_df: Full papers dataframe
    """
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
