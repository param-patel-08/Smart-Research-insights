"""
Data Quality tab - Data quality metrics and distributions.
"""
import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
from io import BytesIO

from dashboard.utils.styling import apply_fig_theme


def render_data_quality_tab(filtered, papers_df):
    """
    Render the Data Quality tab content.
    
    Args:
        filtered: Filtered dataframe based on user selections
        papers_df: Full papers dataframe
    """
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
