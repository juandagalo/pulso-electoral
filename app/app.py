"""Lightweight Streamlit dashboard for Pulso Electoral Colombia 2026.

# Optional interactive dashboard — notebooks are the primary deliverable
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

logger = logging.getLogger(__name__)

# Add src to path so we can import utilities
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# --- Page Config ---
st.set_page_config(
    page_title="Pulso Electoral Colombia 2026",
    page_icon="\U0001f1e8\U0001f1f4",
    layout="wide",
)

# --- Constants ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA_PATH = PROJECT_ROOT / "data" / "sample" / "sample_posts.json"
DB_PATH = PROJECT_ROOT / "data" / "pulso_electoral.duckdb"
DB_PATH_ALT = PROJECT_ROOT / "data" / "pulso_electoral.db"
ACLED_DIR = PROJECT_ROOT / "data" / "01_raw" / "acled"

# Colombia flag colors for charts
COLORS_COLOMBIA = {
    "gold": "#FCD116",
    "blue": "#003893",
    "red": "#CE1126",
}

SENTIMENT_COLORS = {
    "POS": "#27AE60",
    "NEU": "#F39C12",
    "NEG": "#E74C3C",
}

# Thresholds for demo sentiment bucketing and freshness
_SENT_NEG_UPPER = 3
_SENT_NEU_UPPER = 6
_FRESHNESS_STALE_DAYS = 3
_ANOMALY_HIGH_Z = 3

# --- Custom CSS ---
st.markdown(
    """
<style>
    .stMetric .metric-container { background-color: #1E1E2E; border-radius: 8px; padding: 12px; }
    div[data-testid="stMetricValue"] { font-size: 2rem; }
    .freshness-green { color: #27AE60; font-weight: bold; }
    .freshness-yellow { color: #F39C12; font-weight: bold; }
    .freshness-red { color: #E74C3C; font-weight: bold; }
    .about-section { font-size: 0.85em; color: #AAAAAA; }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------
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
    db_path = DB_PATH if DB_PATH.exists() else DB_PATH_ALT
    if db_path.exists():
        try:
            import duckdb

            conn = duckdb.connect(str(db_path), read_only=True)
            df: pd.DataFrame = conn.execute("SELECT * FROM posts").fetchdf()
            conn.close()
        except Exception:
            logger.debug(
                "Could not load posts from DuckDB at %s", db_path, exc_info=True
            )
            return pd.DataFrame()
        else:
            return df
    return pd.DataFrame()


@st.cache_data
def load_acled_data() -> pd.DataFrame:
    """Load ACLED conflict event data from DuckDB, files, or demo fallback."""
    # 1) Try loading from DuckDB first
    db_path = DB_PATH if DB_PATH.exists() else DB_PATH_ALT
    if db_path.exists():
        try:
            import duckdb

            conn = duckdb.connect(str(db_path), read_only=True)
            df: pd.DataFrame = conn.execute("SELECT * FROM acled_events").fetchdf()
            conn.close()
            if not df.empty:
                return df
        except Exception:
            logger.debug(
                "Could not load ACLED from DuckDB at %s", db_path, exc_info=True
            )

    # 2) Try loading from CSV/Parquet files
    acled_files = list(ACLED_DIR.glob("*.csv")) + list(ACLED_DIR.glob("*.parquet"))
    if acled_files:
        try:
            frames = []
            for fp in acled_files:
                if fp.suffix == ".csv":
                    frames.append(pd.read_csv(fp))
                elif fp.suffix == ".parquet":
                    frames.append(pd.read_parquet(fp))
            if frames:
                return pd.concat(frames, ignore_index=True)
        except Exception:
            logger.debug("Could not load ACLED data", exc_info=True)

    # 3) Demo data as fallback
    return _build_demo_acled_data()


def _build_demo_acled_data() -> pd.DataFrame:
    """Generate demo ACLED-style events for Colombian cities."""
    events: list[dict[str, Any]] = [
        {
            "event_date": "2026-03-05",
            "event_type": "Protests",
            "sub_event_type": "Peaceful protest",
            "city": "Bogota",
            "latitude": 4.7110,
            "longitude": -74.0721,
            "fatalities": 0,
            "notes": "Estudiantes marchan por reforma educativa en la Plaza de Bolivar.",
        },
        {
            "event_date": "2026-03-07",
            "event_type": "Violence against civilians",
            "sub_event_type": "Attack",
            "city": "Tumaco",
            "latitude": 1.7986,
            "longitude": -78.7644,
            "fatalities": 1,
            "notes": "Asesinato de lider social en zona rural de Tumaco, Narino.",
        },
        {
            "event_date": "2026-03-10",
            "event_type": "Protests",
            "sub_event_type": "Protest with intervention",
            "city": "Cali",
            "latitude": 3.4516,
            "longitude": -76.5320,
            "fatalities": 0,
            "notes": "Protesta de trabajadores en Cali dispersada con gases lacrimogenos.",
        },
        {
            "event_date": "2026-03-12",
            "event_type": "Battles",
            "sub_event_type": "Armed clash",
            "city": "Arauca",
            "latitude": 7.0847,
            "longitude": -70.7592,
            "fatalities": 3,
            "notes": "Enfrentamiento entre ELN y disidencias FARC en zona fronteriza.",
        },
        {
            "event_date": "2026-03-14",
            "event_type": "Violence against civilians",
            "sub_event_type": "Attack",
            "city": "Buenaventura",
            "latitude": 3.8801,
            "longitude": -77.0197,
            "fatalities": 2,
            "notes": "Amenazas y ataques contra comunidad afrocolombiana desplazada.",
        },
        {
            "event_date": "2026-03-15",
            "event_type": "Protests",
            "sub_event_type": "Peaceful protest",
            "city": "Medellin",
            "latitude": 6.2442,
            "longitude": -75.5812,
            "fatalities": 0,
            "notes": "Manifestacion pacifica por derechos de mujeres en Parque de los Deseos.",
        },
        {
            "event_date": "2026-03-17",
            "event_type": "Strategic developments",
            "sub_event_type": "Arrests",
            "city": "Cucuta",
            "latitude": 7.8939,
            "longitude": -72.5078,
            "fatalities": 0,
            "notes": "Captura de red de financiacion ilegal de campanas electorales.",
        },
        {
            "event_date": "2026-03-18",
            "event_type": "Violence against civilians",
            "sub_event_type": "Attack",
            "city": "Popayan",
            "latitude": 2.4419,
            "longitude": -76.6061,
            "fatalities": 1,
            "notes": "Amenazas contra candidato al Congreso en el departamento del Cauca.",
        },
        {
            "event_date": "2026-03-19",
            "event_type": "Protests",
            "sub_event_type": "Peaceful protest",
            "city": "Barranquilla",
            "latitude": 10.9685,
            "longitude": -74.7813,
            "fatalities": 0,
            "notes": "Marcha contra la corrupcion electoral en el Caribe colombiano.",
        },
        {
            "event_date": "2026-03-20",
            "event_type": "Battles",
            "sub_event_type": "Armed clash",
            "city": "Tibu",
            "latitude": 8.6397,
            "longitude": -73.3327,
            "fatalities": 5,
            "notes": "Combate entre Ejercito y grupo armado en region del Catatumbo.",
        },
        {
            "event_date": "2026-03-21",
            "event_type": "Protests",
            "sub_event_type": "Protest with intervention",
            "city": "Bogota",
            "latitude": 4.6097,
            "longitude": -74.0818,
            "fatalities": 0,
            "notes": "ESMAD interviene manifestacion estudiantil en la Universidad Nacional.",
        },
        {
            "event_date": "2026-03-22",
            "event_type": "Violence against civilians",
            "sub_event_type": "Attack",
            "city": "Quibdo",
            "latitude": 5.6919,
            "longitude": -76.6583,
            "fatalities": 1,
            "notes": "Asesinato de periodista comunitario en el Choco.",
        },
    ]
    return pd.DataFrame(events)


def get_posts() -> pd.DataFrame:
    """Get posts from DB or sample data as fallback."""
    db_posts = load_db_posts()
    if not db_posts.empty:
        return db_posts
    return load_sample_posts()


def _get_last_collection_time(df: pd.DataFrame) -> datetime | None:
    """Determine last collection timestamp from available data."""
    # Try DuckDB metadata first
    db_path = DB_PATH if DB_PATH.exists() else DB_PATH_ALT
    if db_path.exists():
        try:
            import duckdb

            conn = duckdb.connect(str(db_path), read_only=True)
            result = conn.execute("SELECT MAX(collected_at) FROM posts").fetchone()
            conn.close()
            if result and result[0]:
                return pd.Timestamp(result[0]).to_pydatetime()
        except Exception:
            logger.debug("Could not read collection timestamp from DB", exc_info=True)

    # Fall back to max timestamp in data
    if not df.empty and "timestamp" in df.columns:
        try:
            ts = pd.to_datetime(df["timestamp"]).max()
            return ts.to_pydatetime()
        except Exception:
            logger.debug("Could not parse timestamps from data", exc_info=True)
    return None


def _generate_demo_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """Generate plausible demo sentiment scores for sample data."""
    import hashlib

    sentiments = []
    for text in df["text"].fillna(""):
        # Deterministic "sentiment" from text hash for consistency across reloads
        h = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)  # noqa: S324
        remainder = h % 10
        if remainder < _SENT_NEG_UPPER:
            sentiments.append({"sentiment": "NEG", "confidence": 0.6 + (h % 30) / 100})
        elif remainder < _SENT_NEU_UPPER:
            sentiments.append({"sentiment": "NEU", "confidence": 0.5 + (h % 40) / 100})
        else:
            sentiments.append({"sentiment": "POS", "confidence": 0.55 + (h % 35) / 100})
    return pd.DataFrame(sentiments)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("\U0001f1e8\U0001f1f4 Pulso Electoral")
st.sidebar.markdown("**Colombia 2026**")
st.sidebar.markdown("Social Listening & Digital Manipulation Research")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    [
        "\U0001f4ca Overview",
        "\U0001f321\ufe0f Sentiment Thermometer",
        "\U0001f4c8 Volume & Anomalies",
        "\U0001f5fa\ufe0f Geographic Map",
        "\U0001f50d Platform Comparison",
        "\U0001f4c2 Data Explorer",
    ],
)

st.sidebar.divider()

# --- Data Freshness Indicator ---
df = get_posts()
last_collection = _get_last_collection_time(df)

st.sidebar.markdown("### \U0001f310 Data Freshness")
if last_collection is not None:
    now = datetime.now(tz=UTC)
    last_aware = (
        last_collection.replace(tzinfo=UTC)
        if last_collection.tzinfo is None
        else last_collection
    )
    days_ago = (now - last_aware).total_seconds() / 86400

    if days_ago < 1:
        freshness_class = "freshness-green"
        freshness_icon = "\U0001f7e2"
        freshness_label = "Fresh"
    elif days_ago < _FRESHNESS_STALE_DAYS:
        freshness_class = "freshness-yellow"
        freshness_icon = "\U0001f7e1"
        freshness_label = "Recent"
    else:
        freshness_class = "freshness-red"
        freshness_icon = "\U0001f534"
        freshness_label = "Stale"

    st.sidebar.markdown(
        f"{freshness_icon} <span class='{freshness_class}'>{freshness_label}</span>"
        f" &mdash; {days_ago:.1f} days ago",
        unsafe_allow_html=True,
    )
    st.sidebar.caption(f"Last data: {last_aware.strftime('%Y-%m-%d %H:%M UTC')}")
else:
    st.sidebar.markdown(
        "\U0001f7e1 <span class='freshness-yellow'>Demo Mode</span> &mdash; using sample data",
        unsafe_allow_html=True,
    )
    st.sidebar.caption("Run collection notebooks to get live data.")

st.sidebar.divider()

# --- About section ---
with st.sidebar.expander("\u2139\ufe0f About this project"):
    st.markdown(
        """
<div class='about-section'>

**Pulso Electoral** monitors Colombia's 2026 election cycle for digital
manipulation, hate speech, and civic space threats.

Built as a work sample for the **CIVICUS Digital Democracy Initiative**
consulting application.

**Methodology**: Multi-source social listening (RSS, GDELT, ACLED) +
NLP analysis (sentiment, NER, topic modeling) + anomaly detection.

**Tech**: Python \u00b7 DuckDB \u00b7 HuggingFace \u00b7 spaCy \u00b7 Streamlit

Notebooks are the primary deliverable.
</div>
""",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# PAGE: Overview
# ---------------------------------------------------------------------------
if page == "\U0001f4ca Overview":
    st.title("\U0001f1e8\U0001f1f4 Pulso Electoral Colombia 2026")
    st.markdown("Social Listening & Digital Manipulation Research for **CIVICUS DDI**")
    st.divider()

    if df.empty:
        st.warning(
            "No data available. Run collection notebooks first, or check data/sample/."
        )
    else:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Posts", len(df))
        col2.metric("Sources", df["source"].nunique() if "source" in df.columns else 0)
        col3.metric(
            "Platforms", df["platform"].nunique() if "platform" in df.columns else 0
        )
        col4.metric("Authors", df["author"].nunique() if "author" in df.columns else 0)

        st.divider()

        left, right = st.columns(2)

        # Platform distribution
        with left:
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
                    color_discrete_sequence=[
                        COLORS_COLOMBIA["gold"],
                        COLORS_COLOMBIA["blue"],
                        COLORS_COLOMBIA["red"],
                    ],
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        # Source distribution
        with right:
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
                    color_discrete_sequence=[COLORS_COLOMBIA["blue"]],
                )
                st.plotly_chart(fig, use_container_width=True)

        # Timeline sparkline
        if "timestamp" in df.columns:
            st.subheader("\U0001f4c5 Collection Timeline")
            df_time = df.copy()
            df_time["date"] = pd.to_datetime(df_time["timestamp"]).dt.date
            daily = df_time.groupby("date").size().reset_index(name="Posts")
            fig = px.area(
                daily,
                x="date",
                y="Posts",
                title="Daily Post Volume",
                color_discrete_sequence=[COLORS_COLOMBIA["gold"]],
            )
            fig.update_layout(xaxis_title="Date", yaxis_title="Posts")
            st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# PAGE: Sentiment Thermometer
# ---------------------------------------------------------------------------
elif page == "\U0001f321\ufe0f Sentiment Thermometer":
    st.title("\U0001f321\ufe0f Sentiment Thermometer")
    st.markdown("Emotional pulse of Colombia's electoral discourse.")
    st.divider()

    if df.empty:
        st.warning("No data available.")
    else:
        # Check if sentiment column exists in data (from NLP pipeline)
        has_sentiment = "sentiment" in df.columns

        if has_sentiment:
            df_sent = df.copy()
        else:
            st.info(
                "\U0001f4a1 **Demo mode** — Sentiment scores are illustrative. "
                "Run the NLP analysis notebooks to compute real sentiment."
            )
            demo_sent = _generate_demo_sentiment(df)
            df_sent = df.copy()
            df_sent["sentiment"] = demo_sent["sentiment"]
            df_sent["confidence"] = demo_sent["confidence"]

        # --- Overall sentiment distribution ---
        sent_counts = df_sent["sentiment"].value_counts()
        total = len(df_sent)

        col1, col2, col3 = st.columns(3)
        for col, label in zip([col1, col2, col3], ["POS", "NEU", "NEG"], strict=False):
            count = int(sent_counts.get(label, 0))
            pct = count / total * 100 if total > 0 else 0
            icon = {
                "POS": "\U0001f7e2",
                "NEU": "\U0001f7e1",
                "NEG": "\U0001f534",
            }[label]
            col.metric(f"{icon} {label}", f"{count} ({pct:.0f}%)")

        st.divider()

        left, right = st.columns(2)

        # Donut chart
        with left:
            st.subheader("Sentiment Distribution")
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=["Positive", "Neutral", "Negative"],
                        values=[
                            int(sent_counts.get("POS", 0)),
                            int(sent_counts.get("NEU", 0)),
                            int(sent_counts.get("NEG", 0)),
                        ],
                        hole=0.5,
                        marker_colors=[
                            SENTIMENT_COLORS["POS"],
                            SENTIMENT_COLORS["NEU"],
                            SENTIMENT_COLORS["NEG"],
                        ],
                        textinfo="label+percent",
                    )
                ]
            )
            fig.update_layout(
                showlegend=False,
                margin={"t": 20, "b": 20, "l": 20, "r": 20},
                height=350,
            )
            st.plotly_chart(fig, use_container_width=True)

        # Sentiment gauge
        with right:
            st.subheader("Positivity Index")
            pos_ratio = (
                int(sent_counts.get("POS", 0)) / total * 100 if total > 0 else 50
            )
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=pos_ratio,
                    number={"suffix": "%"},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": COLORS_COLOMBIA["gold"]},
                        "steps": [
                            {"range": [0, 33], "color": "#E74C3C"},
                            {"range": [33, 66], "color": "#F39C12"},
                            {"range": [66, 100], "color": "#27AE60"},
                        ],
                        "threshold": {
                            "line": {"color": "white", "width": 3},
                            "thickness": 0.8,
                            "value": pos_ratio,
                        },
                    },
                    title={"text": "% Positive Sentiment"},
                )
            )
            fig.update_layout(height=350, margin={"t": 60, "b": 20})
            st.plotly_chart(fig, use_container_width=True)

        # Sentiment over time
        if "timestamp" in df_sent.columns:
            st.subheader("\U0001f4c8 Sentiment Over Time")
            df_time = df_sent.copy()
            df_time["date"] = pd.to_datetime(df_time["timestamp"]).dt.date
            sent_by_day = (
                df_time.groupby(["date", "sentiment"]).size().reset_index(name="count")
            )
            fig = px.line(
                sent_by_day,
                x="date",
                y="count",
                color="sentiment",
                title="Sentiment Trend by Day",
                color_discrete_map=SENTIMENT_COLORS,
                markers=True,
            )
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Posts",
                legend_title="Sentiment",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Top positive / negative posts
        st.subheader("\U0001f4dd Top Posts by Sentiment")
        tab_pos, tab_neg = st.tabs(
            ["\U0001f7e2 Most Positive", "\U0001f534 Most Negative"]
        )

        with tab_pos:
            pos_posts = df_sent[df_sent["sentiment"] == "POS"]
            if "confidence" in pos_posts.columns:
                pos_posts = pos_posts.sort_values("confidence", ascending=False)
            for _, row in pos_posts.head(5).iterrows():
                with st.expander(
                    f"\U0001f7e2 {row.get('source', 'Unknown')} — "
                    f"{str(row.get('timestamp', ''))[:10]}"
                ):
                    st.write(row["text"])

        with tab_neg:
            neg_posts = df_sent[df_sent["sentiment"] == "NEG"]
            if "confidence" in neg_posts.columns:
                neg_posts = neg_posts.sort_values("confidence", ascending=False)
            for _, row in neg_posts.head(5).iterrows():
                with st.expander(
                    f"\U0001f534 {row.get('source', 'Unknown')} — "
                    f"{str(row.get('timestamp', ''))[:10]}"
                ):
                    st.write(row["text"])


# ---------------------------------------------------------------------------
# PAGE: Volume & Anomalies
# ---------------------------------------------------------------------------
elif page == "\U0001f4c8 Volume & Anomalies":
    st.title("\U0001f4c8 Volume & Anomaly Detection")
    st.markdown("Detect unusual spikes in election discourse volume.")
    st.divider()

    if df.empty:
        st.warning("No data available.")
    else:
        from analysis.anomaly import compute_volume_series, detect_anomalies

        df_vol = df.copy()
        df_vol["timestamp"] = pd.to_datetime(df_vol["timestamp"])

        # Compute volume series
        volume = compute_volume_series(df_vol, date_col="timestamp", freq="D")

        # Detect anomalies
        anomalies = detect_anomalies(volume, window=3, threshold=1.8)

        # Key metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Days Monitored", len(volume))
        col2.metric(
            "Avg Daily Volume", f"{volume.mean():.1f}" if len(volume) > 0 else "0"
        )
        col3.metric(
            "\u26a0\ufe0f Anomalies Detected",
            len(anomalies),
        )

        st.divider()

        # Main volume chart with anomaly markers
        st.subheader("\U0001f4ca Daily Post Volume")

        vol_df = volume.reset_index()
        vol_df.columns = ["Date", "Volume"]

        fig = go.Figure()

        # Area chart for volume
        fig.add_trace(
            go.Scatter(
                x=vol_df["Date"],
                y=vol_df["Volume"],
                mode="lines",
                fill="tozeroy",
                name="Post Volume",
                line={"color": COLORS_COLOMBIA["blue"], "width": 2},
                fillcolor="rgba(0, 56, 147, 0.3)",
            )
        )

        # Anomaly markers
        if anomalies:
            anom_df = pd.DataFrame(anomalies)
            anom_df["timestamp"] = pd.to_datetime(anom_df["timestamp"])
            fig.add_trace(
                go.Scatter(
                    x=anom_df["timestamp"],
                    y=anom_df["value"],
                    mode="markers",
                    name="\u26a0\ufe0f Anomaly",
                    marker={
                        "color": COLORS_COLOMBIA["red"],
                        "size": 14,
                        "symbol": "triangle-up",
                        "line": {"width": 2, "color": "white"},
                    },
                    text=[f"Z-score: {a['z_score']:.2f}" for a in anomalies],
                    hovertemplate=(
                        "<b>Anomaly</b><br>Date: %{x}<br>Volume: %{y}<br>%{text}<extra></extra>"
                    ),
                )
            )

            # Rolling mean line
            fig.add_trace(
                go.Scatter(
                    x=anom_df["timestamp"],
                    y=anom_df["rolling_mean"],
                    mode="lines",
                    name="Rolling Mean",
                    line={"color": COLORS_COLOMBIA["gold"], "width": 1, "dash": "dash"},
                )
            )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Posts",
            hovermode="x unified",
            legend={"orientation": "h", "y": -0.15},
        )
        st.plotly_chart(fig, use_container_width=True)

        # Anomaly details
        if anomalies:
            st.subheader("\u26a0\ufe0f Anomaly Alerts")
            for anom in anomalies:
                ts = str(anom["timestamp"])[:10]
                z = anom["z_score"]
                val = anom["value"]
                mean = anom["rolling_mean"]
                severity = (
                    "\U0001f534 High"
                    if abs(z) > _ANOMALY_HIGH_Z
                    else "\U0001f7e1 Moderate"
                )
                st.warning(
                    f"**{ts}** — {severity} (z={z:.2f}): "
                    f"{int(val)} posts vs {mean:.1f} avg "
                    f"({val / mean:.1f}x baseline)"
                    if mean > 0
                    else f"**{ts}** — {severity} (z={z:.2f}): {int(val)} posts"
                )
        else:
            st.success("No anomalies detected in the current dataset.")

        st.divider()

        # Source breakdown over time
        if "source" in df_vol.columns:
            st.subheader("\U0001f4da Source Breakdown Over Time")
            df_src = df_vol.copy()
            df_src["date"] = df_src["timestamp"].dt.date
            src_daily = (
                df_src.groupby(["date", "source"]).size().reset_index(name="count")
            )
            # Keep top 8 sources for readability
            top_sources = df_src["source"].value_counts().head(8).index.tolist()
            src_daily_top = src_daily[src_daily["source"].isin(top_sources)]

            fig = px.area(
                src_daily_top,
                x="date",
                y="count",
                color="source",
                title="Daily Volume by Source (Top 8)",
            )
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Posts",
                legend_title="Source",
            )
            st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# PAGE: Geographic Map
# ---------------------------------------------------------------------------
elif page == "\U0001f5fa\ufe0f Geographic Map":
    st.title("\U0001f5fa\ufe0f Geographic Correlation Map")
    st.markdown(
        "Conflict events, political violence, and civic space threats across Colombia."
    )
    st.divider()

    acled_df = load_acled_data()

    if acled_df.empty:
        st.warning("No ACLED data available.")
    else:
        # Check for required columns
        lat_col = next((c for c in ["latitude", "lat"] if c in acled_df.columns), None)
        lon_col = next(
            (c for c in ["longitude", "lon", "lng"] if c in acled_df.columns), None
        )

        if lat_col is None or lon_col is None:
            st.error("ACLED data missing latitude/longitude columns.")
        else:
            # Detect if using real or demo data
            _is_demo = "city" in acled_df.columns and "event_id" not in acled_df.columns
            if _is_demo:
                st.info(
                    "\U0001f4a1 **Demo mode** — Showing illustrative conflict events. "
                    "Run the ACLED collection notebook and data loader for real data."
                )

            # Location column — real ACLED uses 'location', demo uses 'city'
            _loc_col = "location" if "location" in acled_df.columns else "city"

            # Parse dates for filtering
            acled_df["_event_date"] = pd.to_datetime(
                acled_df["event_date"], errors="coerce"
            )
            acled_with_dates = acled_df.dropna(subset=["_event_date"])

            # --- Date range filter ---
            if not acled_with_dates.empty:
                from datetime import timedelta

                min_date = acled_with_dates["_event_date"].min().date()
                max_date = acled_with_dates["_event_date"].max().date()

                # Default to last 2 years to avoid overloading map with 31K markers
                _two_years_ago = max_date - timedelta(days=730)
                default_start = max(min_date, _two_years_ago)

                date_col1, date_col2 = st.columns(2)
                with date_col1:
                    start_date = st.date_input(
                        "Start Date",
                        value=default_start,
                        min_value=min_date,
                        max_value=max_date,
                    )
                with date_col2:
                    end_date = st.date_input(
                        "End Date",
                        value=max_date,
                        min_value=min_date,
                        max_value=max_date,
                    )

                # Apply date filter
                filtered_acled = acled_with_dates[
                    (acled_with_dates["_event_date"].dt.date >= start_date)
                    & (acled_with_dates["_event_date"].dt.date <= end_date)
                ].copy()
            else:
                filtered_acled = acled_df.copy()

            # --- Event type filter ---
            event_types = ["All"]
            if "event_type" in filtered_acled.columns:
                event_types += sorted(filtered_acled["event_type"].unique().tolist())
            selected_type = st.selectbox("Filter by Event Type", event_types)

            if selected_type != "All" and "event_type" in filtered_acled.columns:
                filtered_acled = filtered_acled[
                    filtered_acled["event_type"] == selected_type
                ]

            # --- Metrics row ---
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Events (filtered)", f"{len(filtered_acled):,}")

            if "event_type" in filtered_acled.columns:
                col2.metric("Event Types", filtered_acled["event_type"].nunique())

            if "fatalities" in filtered_acled.columns:
                col3.metric(
                    "Total Fatalities",
                    f"{int(filtered_acled['fatalities'].sum()):,}",
                )
            if _loc_col in filtered_acled.columns:
                col4.metric("Locations", f"{filtered_acled[_loc_col].nunique():,}")

            st.divider()

            # Color map for event types
            event_colors: dict[str, str] = {
                "Protests": "blue",
                "Violence against civilians": "red",
                "Battles": "darkred",
                "Strategic developments": "green",
                "Riots": "orange",
                "Explosions/Remote violence": "purple",
            }

            # --- Limit markers to avoid browser performance issues ---
            _map_marker_limit = 2000
            map_df = filtered_acled.copy()
            if len(map_df) > _map_marker_limit:
                map_df = map_df.sort_values("_event_date", ascending=False).head(
                    _map_marker_limit
                )
                st.caption(
                    f"Showing {_map_marker_limit:,} most recent events of "
                    f"{len(filtered_acled):,} total (for map performance)."
                )

            # Build Folium map centered on Colombia
            m = folium.Map(
                location=[4.5709, -74.2973],
                zoom_start=6,
                tiles="CartoDB dark_matter",
            )

            for _, row in map_df.iterrows():
                lat = row[lat_col]
                lon = row[lon_col]
                if pd.isna(lat) or pd.isna(lon):
                    continue
                event_type = row.get("event_type", "Unknown")
                color = event_colors.get(str(event_type), "gray")
                location_name = row.get(_loc_col, "Unknown")
                notes = str(row.get("notes", ""))[:300]
                date = str(row.get("event_date", ""))[:10]
                fatalities = int(row.get("fatalities", 0))
                sub_event = row.get("sub_event_type", "")
                actor = row.get("actor1", "")

                popup_html = (
                    f"<div style='width:280px;font-family:sans-serif;font-size:12px'>"
                    f"<b style='color:{color};font-size:14px'>{event_type}</b><br>"
                    f"<i>{sub_event}</i><br>"
                    f"<b>{location_name}</b> &mdash; {date}<br>"
                )
                if actor:
                    popup_html += f"<b>Actor:</b> {actor}<br>"
                popup_html += (
                    f"<hr style='margin:4px 0'>"
                    f"{notes}<br>"
                    f"<small><b>Fatalities: {fatalities}</b></small>"
                    f"</div>"
                )

                folium.CircleMarker(
                    location=[float(lat), float(lon)],
                    radius=6 + min(fatalities * 2, 20),
                    color=color,
                    fill=True,
                    fill_opacity=0.7,
                    popup=folium.Popup(popup_html, max_width=320),
                    tooltip=f"{event_type} — {location_name} ({date})",
                ).add_to(m)

            st_folium(m, width=None, height=550, use_container_width=True)

            # --- Summary below the map ---
            _fat_text = ""
            if "fatalities" in filtered_acled.columns:
                _fat_text = (
                    f" | **{int(filtered_acled['fatalities'].sum()):,} fatalities**"
                )
            _type_text = ""
            if selected_type != "All":
                _type_text = f" (type: {selected_type})"
            st.markdown(
                f"**{len(filtered_acled):,} events** in selected date range"
                + _type_text
                + _fat_text
            )

            st.divider()

            # --- Charts side by side ---
            if "event_type" in filtered_acled.columns:
                left_chart, right_chart = st.columns(2)

                with left_chart:
                    st.subheader("\U0001f4ca Event Type Distribution")
                    type_counts = (
                        filtered_acled["event_type"].value_counts().reset_index()
                    )
                    type_counts.columns = ["Event Type", "Count"]
                    fig = px.bar(
                        type_counts,
                        x="Count",
                        y="Event Type",
                        orientation="h",
                        color="Event Type",
                        color_discrete_map={
                            "Protests": "#3498DB",
                            "Violence against civilians": "#E74C3C",
                            "Battles": "#8E44AD",
                            "Strategic developments": "#27AE60",
                            "Riots": "#F39C12",
                            "Explosions/Remote violence": "#9B59B6",
                        },
                    )
                    fig.update_layout(showlegend=False, height=350)
                    st.plotly_chart(fig, use_container_width=True)

                with right_chart:
                    st.subheader("\U0001f4c8 Events Over Time")
                    if "_event_date" in filtered_acled.columns:
                        time_df = filtered_acled.copy()
                        time_df["month"] = (
                            time_df["_event_date"].dt.to_period("M").astype(str)
                        )
                        monthly = (
                            time_df.groupby(["month", "event_type"])
                            .size()
                            .reset_index(name="count")
                        )
                        fig = px.area(
                            monthly,
                            x="month",
                            y="count",
                            color="event_type",
                            title="Monthly Event Volume by Type",
                            color_discrete_map={
                                "Protests": "#3498DB",
                                "Violence against civilians": "#E74C3C",
                                "Battles": "#8E44AD",
                                "Strategic developments": "#27AE60",
                                "Riots": "#F39C12",
                                "Explosions/Remote violence": "#9B59B6",
                            },
                        )
                        fig.update_layout(
                            xaxis_title="Month",
                            yaxis_title="Events",
                            legend_title="Event Type",
                            height=350,
                        )
                        st.plotly_chart(fig, use_container_width=True)

            # --- Top locations table ---
            if (
                _loc_col in filtered_acled.columns
                and "fatalities" in filtered_acled.columns
            ):
                st.subheader("\U0001f4cd Top Affected Locations")
                top_locations = (
                    filtered_acled.groupby(_loc_col)
                    .agg(events=(_loc_col, "count"), fatalities=("fatalities", "sum"))
                    .sort_values("events", ascending=False)
                    .head(15)
                    .reset_index()
                )
                top_locations.columns = ["Location", "Events", "Fatalities"]
                st.dataframe(top_locations, use_container_width=True, height=300)


# ---------------------------------------------------------------------------
# PAGE: Platform Comparison
# ---------------------------------------------------------------------------
elif page == "\U0001f50d Platform Comparison":
    st.title("\U0001f50d Platform Comparison")
    st.markdown("Compare discourse patterns across data sources.")
    st.divider()

    if df.empty:
        st.warning("No data available.")
    elif "platform" in df.columns and "text" in df.columns:
        # Text length by platform
        df_analysis = df.copy()
        df_analysis["text_length"] = df_analysis["text"].str.len()

        left, right = st.columns(2)

        with left:
            st.subheader("Text Length Distribution by Platform")
            fig = px.box(
                df_analysis,
                x="platform",
                y="text_length",
                title="Text Length by Platform",
                color="platform",
                color_discrete_sequence=[
                    COLORS_COLOMBIA["gold"],
                    COLORS_COLOMBIA["blue"],
                    COLORS_COLOMBIA["red"],
                ],
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with right:
            st.subheader("Posts per Source")
            src_platform = (
                df_analysis.groupby(["platform", "source"])
                .size()
                .reset_index(name="count")
            )
            fig = px.treemap(
                src_platform,
                path=["platform", "source"],
                values="count",
                title="Source Hierarchy by Platform",
                color_discrete_sequence=[
                    COLORS_COLOMBIA["gold"],
                    COLORS_COLOMBIA["blue"],
                ],
            )
            st.plotly_chart(fig, use_container_width=True)

        # Summary table
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


# ---------------------------------------------------------------------------
# PAGE: Data Explorer
# ---------------------------------------------------------------------------
elif page == "\U0001f4c2 Data Explorer":
    st.title("\U0001f4c2 Data Explorer")
    st.markdown("Browse and filter collected posts.")
    st.divider()

    if df.empty:
        st.warning("No data available.")
    else:
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            platforms = ["All", *sorted(df["platform"].unique().tolist())]
            selected_platform = st.selectbox("Platform", platforms)
        with col2:
            sources = ["All", *sorted(df["source"].unique().tolist())]
            selected_source = st.selectbox("Source", sources)
        with col3:
            search_text = st.text_input("Search text", "")

        # Apply filters
        filtered = df.copy()
        if selected_platform != "All":
            filtered = filtered[filtered["platform"] == selected_platform]
        if selected_source != "All":
            filtered = filtered[filtered["source"] == selected_source]
        if search_text:
            filtered = filtered[
                filtered["text"].str.contains(search_text, case=False, na=False)
            ]

        st.markdown(f"**Showing {len(filtered)} of {len(df)} posts**")
        display_cols = [
            c
            for c in ["text", "source", "platform", "author", "timestamp"]
            if c in filtered.columns
        ]
        st.dataframe(
            filtered[display_cols],
            use_container_width=True,
            height=500,
        )
