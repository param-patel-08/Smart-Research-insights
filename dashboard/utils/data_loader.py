"""Data loading and preprocessing utilities."""
import os
import json
import pandas as pd
import streamlit as st
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import (
    PROCESSED_PAPERS_CSV,
    TREND_ANALYSIS_PATH,
    TOPIC_MAPPING_PATH,
)


def _load_json(path: str):
    """Load JSON data from file."""
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return json.loads(f.read())


@st.cache_data
def load_data():
    """Load and preprocess all dashboard data."""
    if not os.path.exists(PROCESSED_PAPERS_CSV):
        raise FileNotFoundError(PROCESSED_PAPERS_CSV)
    df = pd.read_csv(PROCESSED_PAPERS_CSV)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    # Normalize university names to avoid mismatches (strip/condense spaces)
    if "university" in df.columns:
        df["university"] = (
            df["university"].fillna("Unknown").astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
        )

    trends = _load_json(TREND_ANALYSIS_PATH)
    mapping = _load_json(TOPIC_MAPPING_PATH)

    # PRESERVE original theme from CSV (assigned during collection)
    # BERTopic mapping is only used for confidence scores and topic details
    # If CSV doesn't have theme column, fall back to BERTopic mapping
    if "theme" not in df.columns:
        df["theme"] = df["topic_id"].astype(str).map(lambda t: mapping.get(str(t), {}).get("theme", "Other"))
    
    df["confidence"] = df["topic_id"].astype(str).map(lambda t: mapping.get(str(t), {}).get("confidence", 0))
    
    # ADD SUB-THEME MAPPING (from hierarchical structure)
    df["sub_theme"] = df["topic_id"].astype(str).map(lambda t: mapping.get(str(t), {}).get("sub_theme", None))
    df["sub_theme_confidence"] = df["topic_id"].astype(str).map(lambda t: mapping.get(str(t), {}).get("sub_theme_confidence", 0))

    # Reinstate Cybersecurity assignments when similarity score is strong but original mapping fell back to another theme.
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

    # Scoring
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
