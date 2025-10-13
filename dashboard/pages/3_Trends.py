import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.themes import BABCOCK_THEMES
from dashboard.common import load_data, load_css, build_filters, apply_fig_theme

st.set_page_config(page_title="Research Trend Analyzer - Trends", layout="wide")
load_css()

 

papers_df, trends, mapping = load_data()
filtered, ctx = build_filters(papers_df)

st.markdown('<p class="main-header">Trends</p>', unsafe_allow_html=True)

# Temporal Trends Analysis
st.markdown('<p class="sub-header">Temporal Trends Analysis</p>', unsafe_allow_html=True)
qa = filtered.groupby("quarter").size().reset_index(name="count")
qa["quarter"] = qa["quarter"].astype(str)
fig = go.Figure()
fig.add_trace(go.Scatter(x=qa["quarter"], y=qa["count"], mode="lines+markers", name="All Themes"))
fig = apply_fig_theme(fig, height=380)
fig.update_layout(title="Overall Research Output", xaxis_title="Quarter", yaxis_title="Papers")
st.plotly_chart(fig, use_container_width=True)

# Multi-theme comparison
names = [t.replace("_", " ").title() for t in BABCOCK_THEMES.keys()]
picks = st.multiselect("Select Themes to Compare", names, default=names)
if picks:
    raw = [t.replace(" ", "_") for t in picks]
    f = filtered[filtered["theme"].isin(raw)]
    quarters = sorted(filtered["quarter"].unique())
    base = pd.MultiIndex.from_product([quarters, raw], names=["quarter", "theme"]) 
    qt = f.groupby(["quarter", "theme"]).size().reindex(base, fill_value=0).reset_index(name="count")
    qt["quarter"] = qt["quarter"].astype(str)
    qt["theme"] = qt["theme"].str.replace("_", " ").str.title()
    fig = px.line(qt, x="quarter", y="count", color="theme", title="Research Output Trends (Selected Themes)")
    fig = apply_fig_theme(fig, height=420)
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Select at least one theme to compare.")
