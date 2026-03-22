"""Anomaly detection using rolling z-scores on time series."""

from __future__ import annotations

import pandas as pd


def detect_anomalies(
    series: pd.Series,
    window: int = 7,
    threshold: float = 2.5,
) -> list[dict]:
    """Detect anomalies in a time series using rolling z-score.

    Parameters
    ----------
    series : pd.Series
        Time series data (indexed by datetime, values are counts/volumes).
    window : int
        Rolling window size in periods. Defaults to 7.
    threshold : float
        Z-score threshold for flagging anomalies. Defaults to 2.5.

    Returns
    -------
    list[dict]
        List of anomaly dicts with keys: timestamp, value, z_score, rolling_mean,
        rolling_std.
    """
    rolling_mean = series.rolling(window=window, min_periods=1).mean()
    rolling_std = series.rolling(window=window, min_periods=1).std()

    # Avoid division by zero
    rolling_std = rolling_std.replace(0, 1e-10)

    z_scores = (series - rolling_mean) / rolling_std

    anomalies = []
    for idx in z_scores.index:
        z = z_scores[idx]
        if abs(z) >= threshold:
            anomalies.append(
                {
                    "timestamp": str(idx),
                    "value": float(series[idx]),
                    "z_score": float(z),
                    "rolling_mean": float(rolling_mean[idx]),
                    "rolling_std": float(rolling_std[idx]),
                }
            )

    return anomalies


def compute_volume_series(
    df: pd.DataFrame,
    date_col: str = "timestamp",
    freq: str = "D",
) -> pd.Series:
    """Compute post volume time series from a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a date/timestamp column.
    date_col : str
        Name of the date column. Defaults to 'timestamp'.
    freq : str
        Frequency for resampling ('D' for daily, 'H' for hourly). Defaults to 'D'.

    Returns
    -------
    pd.Series
        Time series of post counts at the given frequency.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col)
    return df.resample(freq).size()
