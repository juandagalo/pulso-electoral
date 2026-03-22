"""Lightweight Streamlit dashboard for Pulso Electoral Colombia 2026.

# Optional interactive dashboard — notebooks are the primary deliverable
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Add src to path so we can import utilities
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# --- Page Config ---
st.set_page_config(
    page_title="Pulso Electoral Colombia 2026",
    page_icon="🇨🇴",
    layout="wide",
)

# --- Constants ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA_PATH = PROJECT_ROOT / "data" / "sample" / "sample_posts.json"
DB_PATH = PROJECT_ROOT / "data" / "pulso_electoral.db"


# --- Data Loading ---
@st.cache_data
def load_sample_posts() -> pd.DataFrame:
    """Load sample posts from JSON file."""
    if SAMPLE_DATA_PATH.exists():
        with open(SAMPLE_DATA_PATH) as f:
            posts = json.load(f)
        return pd.DataFrame(posts)
    return pd.DataFrame()


@st.cache_data
def load_db_posts() -> pd.DataFrame:
    """Load posts from DuckDB if available."""
    if DB_PATH.exists():
        try:
            import duckdb

            conn = duckdb.connect(str(DB_PATH), read_only=True)
            df = conn.execute("SELECT * FROM posts").fetchdf()
            conn.close()
            return df
        except Exception:  # noqa: BLE001
            pass
    return pd.DataFrame()


def get_posts() -> pd.DataFrame:
    """Get posts from DB or sample data as fallback."""
    db_posts = load_db_posts()
    if not db_posts.empty:
        return db_posts
    return load_sample_posts()


# --- Sidebar ---
st.sidebar.title("Pulso Electoral")
st.sidebar.markdown("**Colombia 2026**")
st.sidebar.markdown("Social Listening & Digital Manipulation Research")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Platform Comparison", "Data Explorer"],
)

st.sidebar.divider()
st.sidebar.markdown("*CIVICUS DDI Work Sample*")
st.sidebar.markdown("Notebooks are the primary deliverable.")

# --- Load Data ---
df = get_posts()

# --- Pages ---
if page == "Overview":
    st.title("Pulso Electoral Colombia 2026")
    st.markdown(
        "Social Listening & Digital Manipulation Research for **CIVICUS DDI**"
    )
    st.divider()

    if df.empty:
        st.warning("No data available. Run collection notebooks first, or check data/sample/.")
    else:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Posts", len(df))
        col2.metric("Sources", df["source"].nunique() if "source" in df.columns else 0)
        col3.metric("Platforms", df["platform"].nunique() if "platform" in df.columns else 0)
        col4.metric("Authors", df["author"].nunique() if "author" in df.columns else 0)

        st.divider()

        # Platform distribution
        if "platform" in df.columns:
            st.subheader("Posts by Platform")
            platform_counts = df["platform"].value_counts().reset_index()
            platform_counts.columns = ["Platform", "Count"]
            fig = px.bar(
                platform_counts,
                x="Platform",
                y="Count",
                color="Platform",
                title="Post Distribution by Platform",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Source distribution
        if "source" in df.columns:
            st.subheader("Posts by Source")
            source_counts = df["source"].value_counts().head(15).reset_index()
            source_counts.columns = ["Source", "Count"]
            fig = px.bar(
                source_counts,
                x="Count",
                y="Source",
                orientation="h",
                title="Top 15 Sources",
            )
            st.plotly_chart(fig, use_container_width=True)

elif page == "Platform Comparison":
    st.title("Platform Comparison")
    st.markdown("Compare discourse patterns across data sources.")
    st.divider()

    if df.empty:
        st.warning("No data available.")
    else:
        if "platform" in df.columns and "text" in df.columns:
            # Text length by platform
            df_analysis = df.copy()
            df_analysis["text_length"] = df_analysis["text"].str.len()

            st.subheader("Text Length Distribution by Platform")
            fig = px.box(
                df_analysis,
                x="platform",
                y="text_length",
                title="Text Length by Platform",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Post counts
            st.subheader("Volume by Platform")
            platform_summary = (
                df_analysis.groupby("platform")
                .agg(
                    post_count=("id", "count"),
                    avg_text_length=("text_length", "mean"),
                    unique_authors=("author", "nunique"),
                )
                .reset_index()
            )
            st.dataframe(platform_summary, use_container_width=True)

elif page == "Data Explorer":
    st.title("Data Explorer")
    st.markdown("Browse and filter collected posts.")
    st.divider()

    if df.empty:
        st.warning("No data available.")
    else:
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            platforms = ["All"] + sorted(df["platform"].unique().tolist())
            selected_platform = st.selectbox("Platform", platforms)
        with col2:
            search_text = st.text_input("Search text", "")

        # Apply filters
        filtered = df.copy()
        if selected_platform != "All":
            filtered = filtered[filtered["platform"] == selected_platform]
        if search_text:
            filtered = filtered[
                filtered["text"].str.contains(search_text, case=False, na=False)
            ]

        st.markdown(f"**Showing {len(filtered)} of {len(df)} posts**")
        st.dataframe(
            filtered[["text", "source", "platform", "author", "timestamp"]],
            use_container_width=True,
            height=500,
        )
