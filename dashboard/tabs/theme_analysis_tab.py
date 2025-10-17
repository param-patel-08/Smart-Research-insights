"""
Theme Analysis tab - Detailed theme breakdown, publication trends, and sub-theme analysis.
"""
import streamlit as st
import pandas as pd
import plotly.express as px

from dashboard.utils.visualizations import create_trend_timeline, create_sankey_flow
from dashboard.utils.styling import create_section_header, apply_fig_theme


def find_adjacent_themes(papers: pd.DataFrame, theme_key: str, mapping_obj: dict) -> dict:
    """Find themes adjacent to the selected theme based on keyword overlap."""
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


def get_growth_color_style_theme(growth_rate):
    """Generate super dark color gradients based on growth rate for dark theme"""
    growth_pct = growth_rate * 100
    
    if growth_pct >= 50:
        return {
            "bg": "linear-gradient(135deg, #052e16 0%, #064e3b 100%)",  # Super dark green
            "border": "#10b981",
            "icon": "▲▲",
            "label": f"+{growth_pct:.0f}%",
            "color": "#ffffff",
            "icon_color": "#34d399"
        }
    elif growth_pct >= 20:
        return {
            "bg": "linear-gradient(135deg, #064e3b 0%, #065f46 100%)",  # Super dark green
            "border": "#34d399",
            "icon": "▲",
            "label": f"+{growth_pct:.0f}%",
            "color": "#ffffff",
            "icon_color": "#6ee7b7"
        }
    elif growth_pct >= 5:
        return {
            "bg": "linear-gradient(135deg, #065f46 0%, #047857 100%)",  # Dark green
            "border": "#6ee7b7",
            "icon": "▲",
            "label": f"+{growth_pct:.0f}%",
            "color": "#ffffff",
            "icon_color": "#a7f3d0"
        }
    elif growth_pct >= 0:
        return {
            "bg": "linear-gradient(135deg, #047857 0%, #059669 100%)",  # Dark green
            "border": "#a7f3d0",
            "icon": "→",
            "label": f"+{growth_pct:.1f}%",
            "color": "#ffffff",
            "icon_color": "#d1fae5"
        }
    elif growth_pct >= -5:
        return {
            "bg": "linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%)",  # Super dark red
            "border": "#fca5a5",
            "icon": "→",
            "label": f"{growth_pct:.1f}%",
            "color": "#ffffff",
            "icon_color": "#fca5a5"
        }
    elif growth_pct >= -20:
        return {
            "bg": "linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%)",  # Super dark red
            "border": "#f87171",
            "icon": "▼",
            "label": f"{growth_pct:.0f}%",
            "color": "#ffffff",
            "icon_color": "#f87171"
        }
    else:
        return {
            "bg": "linear-gradient(135deg, #1a0000 0%, #450a0a 100%)",  # Extremely dark red
            "border": "#ef4444",
            "icon": "▼▼",
            "label": f"{growth_pct:.0f}%",
            "color": "#ffffff",
            "icon_color": "#ef4444"
        }


def render_theme_analysis_tab(filtered, papers_df, trends, mapping, babcock_themes):
    """
    Render the Theme Analysis tab content.
    
    Args:
        filtered: Filtered dataframe based on user selections
        papers_df: Full papers dataframe
        trends: Trends data
        mapping: Topic mapping data
        babcock_themes: Dictionary of Babcock themes
    """
    # Strategic Theme Priorities - Color-coded by growth rate
    st.markdown('<p class="sub-header">Strategic Theme Priorities</p>', unsafe_allow_html=True)
    st.markdown("*Research themes colored by growth rate: 🟢 Green (positive growth) • 🔴 Red (negative growth)*")
    
    priorities = trends.get("strategic_priorities", [])
    
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
                    border: 1px solid {style["border"]};
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
    
    theme_order = list(babcock_themes.keys())
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

        adj = find_adjacent_themes(papers_df, selected_theme, mapping)
        if adj:
            adj_df = pd.DataFrame({"Theme": [t.replace("_", " ").title() for t in list(adj.keys())[:5]], "Connections": list(adj.values())[:5]})
            adj_df = adj_df.sort_values("Connections", ascending=True)  # Sort ascending for correct order
            fig_adj = px.bar(adj_df, x="Connections", y="Theme", orientation="h", color="Connections", color_continuous_scale="Blues", title=f"Top Adjacent Themes to {selected_theme_display}")
            fig_adj = apply_fig_theme(fig_adj, height=300)
            st.plotly_chart(fig_adj, use_container_width=True)
        else:
            st.info("No significant adjacent themes detected for this theme")
