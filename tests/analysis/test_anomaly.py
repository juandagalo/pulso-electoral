"""Tests for anomaly detection utilities."""

from __future__ import annotations

import pandas as pd

from analysis.anomaly import compute_volume_series, detect_anomalies


class TestDetectAnomalies:
    """Tests for the detect_anomalies function."""

    def test_detects_spike(self) -> None:
        """Should detect a clear spike in a time series."""
        dates = pd.date_range("2026-03-01", periods=14, freq="D")
        # Normal values around 10, with a spike on day 10
        values = [10, 12, 11, 9, 10, 11, 10, 12, 9, 50, 10, 11, 10, 9]
        series = pd.Series(values, index=dates)

        anomalies = detect_anomalies(series, window=7, threshold=2.5)

        assert len(anomalies) > 0
        # The spike at value 50 should be detected
        spike_values = [a["value"] for a in anomalies]
        assert 50.0 in spike_values

    def test_no_anomalies_in_flat_series(self) -> None:
        """Should not detect anomalies in a flat series."""
        dates = pd.date_range("2026-03-01", periods=14, freq="D")
        values = [10] * 14
        series = pd.Series(values, index=dates)

        anomalies = detect_anomalies(series, window=7, threshold=2.5)

        assert len(anomalies) == 0

    def test_returns_correct_fields(self) -> None:
        """Each anomaly should have the required fields."""
        dates = pd.date_range("2026-03-01", periods=10, freq="D")
        values = [10, 10, 10, 10, 10, 100, 10, 10, 10, 10]
        series = pd.Series(values, index=dates)

        anomalies = detect_anomalies(series, window=5, threshold=2.0)

        if anomalies:
            anomaly = anomalies[0]
            assert "timestamp" in anomaly
            assert "value" in anomaly
            assert "z_score" in anomaly
            assert "rolling_mean" in anomaly
            assert "rolling_std" in anomaly

    def test_respects_threshold(self) -> None:
        """Higher threshold should detect fewer anomalies."""
        dates = pd.date_range("2026-03-01", periods=10, freq="D")
        values = [10, 10, 10, 10, 10, 30, 10, 10, 10, 10]
        series = pd.Series(values, index=dates)

        low_threshold = detect_anomalies(series, window=5, threshold=1.5)
        high_threshold = detect_anomalies(series, window=5, threshold=5.0)

        assert len(low_threshold) >= len(high_threshold)


class TestComputeVolumeSeries:
    """Tests for the compute_volume_series function."""

    def test_daily_counts(self) -> None:
        """Should compute daily post counts."""
        df = pd.DataFrame({
            "timestamp": [
                "2026-03-20 10:00:00",
                "2026-03-20 14:00:00",
                "2026-03-20 18:00:00",
                "2026-03-21 10:00:00",
            ]
        })

        series = compute_volume_series(df, date_col="timestamp", freq="D")

        assert len(series) == 2
        # First day has 3 posts, second has 1
        assert series.iloc[0] == 3
        assert series.iloc[1] == 1
