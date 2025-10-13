import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from dashboard.common import load_data, load_css, build_filters, apply_fig_theme

st.set_page_config(page_title="Research Trend Analyzer - Universities", layout="wide")
load_css()

 

papers_df, trends, mapping = load_data()
filtered, ctx = build_filters(papers_df)

st.markdown('<p class="main-header">Universities</p>', unsafe_allow_html=True)

st.markdown('<p class="sub-header">Overall Research Output Rankings</p>', unsafe_allow_html=True)
uc = filtered["university"].value_counts()
fig = px.bar(x=uc.head(15).values, y=uc.head(15).index, orientation="h", color=uc.head(15).values, color_continuous_scale="Greens", title="Top 15 Universities by Total Papers")
fig = apply_fig_theme(fig, height=380)
st.plotly_chart(fig, use_container_width=True)

st.markdown('<p class="sub-header">University Deep Dive</p>', unsafe_allow_html=True)
sel_uni = st.selectbox("Select University", sorted(filtered["university"].unique()))
uni_p = filtered[filtered["university"] == sel_uni]

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
