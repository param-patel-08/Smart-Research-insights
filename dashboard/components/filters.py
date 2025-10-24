"""
Sidebar filter panel component.
"""
import streamlit as st
import pandas as pd


def render_filters(papers_df, all_universities, strategic_themes):
    """
    Render sidebar filters and return filtered dataframe and selected values.
    
    Args:
        papers_df: Full papers dataframe
    all_universities: Dictionary of all universities
    strategic_themes: Dictionary of strategic themes
        
    Returns:
        Tuple: (filtered_df, start_date, end_date, sel_themes, sel_sub_themes, sel_unis)
    """
    st.sidebar.title(" Research Trends")
    
    # Logo
    try:
        st.sidebar.image(
            "https://dummyimage.com/260x60/111827/ffffff.png&text=RESEARCH+INSIGHTS",
            use_container_width=True,
        )
    except Exception:
        pass
    st.sidebar.markdown("---")
    
    # Date range filter
    min_date = papers_df["date"].min().date()
    max_date = papers_df["date"].max().date()
    cd1, cd2 = st.sidebar.columns(2)
    start_date = cd1.date_input("From", value=min_date, min_value=min_date, max_value=max_date, key="from_date")
    end_date = cd2.date_input("To", value=max_date, min_value=min_date, max_value=max_date, key="to_date")
    
    # Theme filter
    all_themes = sorted(list(strategic_themes.keys()))
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
    
    # University filter - only show AU/NZ institutions
    australasian_uni_names = set(all_universities.keys())
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
    
    # Keyword filter
    kw = st.sidebar.text_input("Keyword(s)", value="", placeholder="e.g., autonomy, additive manufacturing", key="kw")
    
    # Reset filters button
    if st.sidebar.button("Reset filters"):
        st.session_state["from_date"] = min_date
        st.session_state["to_date"] = max_date
        st.session_state["themes"] = all_themes
        st.session_state["sub_themes"] = []
        st.session_state["all_unis_flag"] = True
        st.session_state["unis"] = all_unis
        st.session_state["kw"] = ""
        st.rerun()
    
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
    
    return filtered, start_date, end_date, sel_themes, sel_sub_themes, sel_unis
