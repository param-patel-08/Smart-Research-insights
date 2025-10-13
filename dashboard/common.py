import os
import sys
import json
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import (
    PROCESSED_PAPERS_CSV,
    TREND_ANALYSIS_PATH,
    TOPIC_MAPPING_PATH,
)
from config.themes import BABCOCK_THEMES


@st.cache_data
def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return json.loads(f.read())


@st.cache_data
def load_data():
    if not os.path.exists(PROCESSED_PAPERS_CSV):
        raise FileNotFoundError(PROCESSED_PAPERS_CSV)
    df = pd.read_csv(PROCESSED_PAPERS_CSV)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    if "university" in df.columns:
        df["university"] = (
            df["university"].fillna("Unknown").astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
        )
    trends = _load_json(TREND_ANALYSIS_PATH)
    mapping = _load_json(TOPIC_MAPPING_PATH)
    df["theme"] = df["topic_id"].astype(str).map(lambda t: mapping.get(str(t), {}).get("theme", "Other"))
    df["confidence"] = df["topic_id"].astype(str).map(lambda t: mapping.get(str(t), {}).get("confidence", 0))
    cyber_topics = {
        str(tid): data.get("all_scores", {}).get("Cybersecurity", 0)
        for tid, data in mapping.items()
        if data.get("all_scores", {}).get("Cybersecurity", 0) >= 0.12 and data.get("theme") != "Cybersecurity"
    }
    if cyber_topics:
        mask = df["topic_id"].astype(str).isin(cyber_topics.keys())
        if mask.any():
            df.loc[mask, "theme"] = "Cybersecurity"
            df.loc[mask, "confidence"] = df.loc[mask, "topic_id"].astype(str).map(cyber_topics)
    if df["confidence"].max() <= 1:
        df["confidence"] = (df["confidence"] * 100).round(0)
    if "citations" in df.columns and pd.api.types.is_numeric_dtype(df["citations"]):
        max_cit = max(1, df["citations"].max())
        df["citation_score"] = (df["citations"] / max_cit) * 100
    else:
        df["citation_score"] = 0
    days_old = (pd.Timestamp.now() - pd.to_datetime(df["date"]).fillna(pd.Timestamp.now())).dt.days
    df["recency_score"] = (100 - (days_old / 730) * 100).clip(lower=0, upper=100)
    df["relevance_score"] = (
        df["confidence"].fillna(0) * 0.40
        + df["citation_score"].fillna(0) * 0.30
        + df["recency_score"].fillna(0) * 0.30
    ).clip(0, 100)
    df["quarter"] = df["date"].dt.to_period("Q")
    return df, trends, mapping


def apply_fig_theme(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#0b0f19"),
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "theme.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def build_filters(papers_df: pd.DataFrame):
    min_date = papers_df["date"].min().date()
    max_date = papers_df["date"].max().date()
    cd1, cd2 = st.sidebar.columns(2)
    start_date = cd1.date_input("From", value=min_date, min_value=min_date, max_value=max_date, key="from_date")
    end_date = cd2.date_input("To", value=max_date, min_value=min_date, max_value=max_date, key="to_date")
    all_themes = sorted(list(BABCOCK_THEMES.keys()))
    sel_themes = st.sidebar.multiselect(" Themes", options=all_themes, default=all_themes, key="themes")
    all_unis = sorted(papers_df["university"].unique())
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
    min_conf = st.sidebar.slider("Min Confidence (%)", 0, 100, 0, 5, key="min_conf")
    max_cit = int(papers_df["citations"].max()) if "citations" in papers_df.columns else 100
    min_cit = st.sidebar.slider("Min Citations", 0, max_cit, 0, key="min_cit")
    kw = st.sidebar.text_input("Keyword(s)", value="", placeholder="e.g., autonomy, additive manufacturing", key="kw")
    if st.sidebar.button("Reset filters"):
        st.session_state["from_date"] = min_date
        st.session_state["to_date"] = max_date
        st.session_state["themes"] = all_themes
        st.session_state["all_unis_flag"] = True
        st.session_state["unis"] = all_unis
        st.session_state["min_conf"] = 0
        st.session_state["min_cit"] = 0
        st.session_state["kw"] = ""
        st.experimental_rerun()
    filtered = papers_df.copy()
    filtered = filtered[(filtered["date"].dt.date >= start_date) & (filtered["date"].dt.date <= end_date)]
    if sel_themes:
        filtered = filtered[filtered["theme"].isin(sel_themes)]
    if sel_unis:
        filtered = filtered[filtered["university"].isin(sel_unis)]
    filtered = filtered[filtered["confidence"] >= min_conf]
    if "citations" in filtered.columns:
        filtered = filtered[filtered["citations"] >= min_cit]
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
    ctx = {
        "start_date": start_date,
        "end_date": end_date,
        "sel_themes": sel_themes,
        "sel_unis": sel_unis,
    }
    return filtered, ctx
