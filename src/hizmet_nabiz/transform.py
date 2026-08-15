"""Leakage-safe analytical feature construction."""

from __future__ import annotations

import numpy as np
import pandas as pd

from hizmet_nabiz.config import AnalysisConfig


def _expected_by_peer(closed: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    peer = ["agency", "complaint_type"]
    peer_stats = (
        closed.groupby(peer, observed=True)["log_resolution_hours"]
        .agg(peer_count="size", peer_median_log="median", peer_q="quantile")
        .reset_index()
    )
    # pandas cannot pass q through the named aggregation above; overwrite deterministically.
    quantiles = (
        closed.groupby(peer, observed=True)["log_resolution_hours"]
        .quantile(config.high_delay_quantile)
        .rename("peer_high_delay_log")
        .reset_index()
    )
    peer_stats = peer_stats.drop(columns="peer_q").merge(quantiles, on=peer, how="left")

    complaint_stats = (
        closed.groupby("complaint_type", observed=True)["log_resolution_hours"]
        .agg(complaint_median_log="median")
        .reset_index()
    )
    complaint_q = (
        closed.groupby("complaint_type", observed=True)["log_resolution_hours"]
        .quantile(config.high_delay_quantile)
        .rename("complaint_high_delay_log")
        .reset_index()
    )
    return peer_stats.merge(complaint_stats, on="complaint_type").merge(
        complaint_q, on="complaint_type"
    )


def prepare_requests(frame: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    """Create duration, SLA, and peer-adjusted delay fields without imputing outcomes."""
    data = frame.copy()
    for column in ("created_date", "closed_date", "due_date"):
        data[column] = pd.to_datetime(data[column], errors="coerce", format="mixed")
    data["community_board"] = data["community_board"].fillna("").astype(str).str.strip()
    data["borough"] = data["borough"].fillna("UNKNOWN").astype(str).str.upper()
    data["complaint_type"] = data["complaint_type"].fillna("UNKNOWN").astype(str)
    data["agency"] = data["agency"].fillna("UNKNOWN").astype(str)
    data["is_closed"] = data["closed_date"].notna()
    data["resolution_hours"] = (
        data["closed_date"] - data["created_date"]
    ).dt.total_seconds() / 3600
    data.loc[data["resolution_hours"] < 0, "resolution_hours"] = np.nan
    data["log_resolution_hours"] = np.log1p(data["resolution_hours"])
    data["due_eligible"] = data["due_date"].notna() & data["closed_date"].notna()
    data["on_time"] = data["due_eligible"] & (data["closed_date"] <= data["due_date"])

    closed = data.loc[data["resolution_hours"].notna()].copy()
    if closed.empty:
        raise ValueError("No valid closed requests are available for duration analysis")
    expectations = _expected_by_peer(closed, config)
    data = data.merge(expectations, on=["agency", "complaint_type"], how="left")
    global_median = float(closed["log_resolution_hours"].median())
    global_q = float(closed["log_resolution_hours"].quantile(config.high_delay_quantile))
    sparse = data["peer_count"].fillna(0) < config.peer_minimum_requests
    data["expected_log_hours"] = data["peer_median_log"].where(
        ~sparse, data["complaint_median_log"]
    )
    data["high_delay_threshold_log"] = data["peer_high_delay_log"].where(
        ~sparse, data["complaint_high_delay_log"]
    )
    data["expected_log_hours"] = data["expected_log_hours"].fillna(global_median)
    data["high_delay_threshold_log"] = data["high_delay_threshold_log"].fillna(global_q)
    data["delay_residual_log"] = data["log_resolution_hours"] - data["expected_log_hours"]
    data["high_delay"] = data["log_resolution_hours"].notna() & (
        data["log_resolution_hours"] > data["high_delay_threshold_log"]
    )
    expected_hours = np.expm1(data["expected_log_hours"])
    data["excess_delay_hours"] = (data["resolution_hours"] - expected_hours).clip(lower=0)
    data["created_day"] = data["created_date"].dt.strftime("%Y-%m-%d")
    return data
