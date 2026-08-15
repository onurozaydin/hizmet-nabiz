"""Validated KPI calculations and reliability-aware geographic estimates."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import beta  # type: ignore[import-untyped]

from hizmet_nabiz.config import AnalysisConfig


def _safe_rate(numerator: float, denominator: float) -> float | None:
    return None if denominator == 0 else float(numerator / denominator)


def city_kpis(data: pd.DataFrame) -> dict[str, Any]:
    closed = data["resolution_hours"].dropna()
    due = data.loc[data["due_eligible"]]
    due_coverage = _safe_rate(float(len(due)), float(len(data)))
    observed_on_time = _safe_rate(float(due["on_time"].sum()), float(len(due)))
    decision_ready = due_coverage is not None and due_coverage >= 0.10
    return {
        "requests": len(data),
        "closed_rate": _safe_rate(float(data["is_closed"].sum()), float(len(data))),
        "median_resolution_hours": float(closed.median()),
        "p90_resolution_hours": float(closed.quantile(0.90)),
        "due_date_eligible_requests": len(due),
        "due_date_coverage": due_coverage,
        "on_time_rate_observed": observed_on_time,
        "on_time_rate": observed_on_time if decision_ready else None,
        "on_time_rate_decision_ready": decision_ready,
        "community_board_coverage": float(
            (
                data["community_board"].ne("")
                & ~data["community_board"].str.contains("Unspecified")
            ).mean()
        ),
    }


def board_metrics(data: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    eligible = data.loc[
        data["community_board"].ne("") & ~data["community_board"].str.contains("Unspecified")
    ].copy()
    closed = eligible.loc[eligible["resolution_hours"].notna()].copy()
    global_high_delay = float(closed["high_delay"].mean())
    prior_a = global_high_delay * config.eb_prior_strength
    prior_b = (1 - global_high_delay) * config.eb_prior_strength
    alpha_tail = (1 - config.credible_interval) / 2

    rows: list[dict[str, Any]] = []
    for board, group in eligible.groupby("community_board", observed=True):
        durations = group["resolution_hours"].dropna()
        if len(group) < config.minimum_board_requests or durations.empty:
            continue
        high_count = int(group.loc[group["resolution_hours"].notna(), "high_delay"].sum())
        closed_count = int(durations.size)
        posterior_a = prior_a + high_count
        posterior_b = prior_b + closed_count - high_count
        due = group.loc[group["due_eligible"]]
        residual = group["delay_residual_log"].dropna()
        delay_index = (
            float(math.exp(float(residual.mean()))) if not residual.empty else float("nan")
        )
        rows.append(
            {
                "community_board": str(board),
                "borough": str(group["borough"].mode().iloc[0]),
                "requests": len(group),
                "closed_requests": closed_count,
                "closed_rate": float(group["is_closed"].mean()),
                "median_resolution_hours": float(durations.median()),
                "p90_resolution_hours": float(durations.quantile(0.90)),
                "due_date_coverage": float(len(due) / len(group)),
                "on_time_rate": (
                    _safe_rate(float(due["on_time"].sum()), float(len(due)))
                    if len(due) >= 30
                    else None
                ),
                "high_delay_rate_raw": high_count / closed_count,
                "high_delay_rate_eb": posterior_a / (posterior_a + posterior_b),
                "high_delay_ci_low": float(beta.ppf(alpha_tail, posterior_a, posterior_b)),
                "high_delay_ci_high": float(beta.ppf(1 - alpha_tail, posterior_a, posterior_b)),
                "delay_index": delay_index,
                "excess_delay_hours": float(group["excess_delay_hours"].sum()),
                "addressable_cases": int((group["excess_delay_hours"] > 0).sum()),
            }
        )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["reliability_gap"] = result["high_delay_ci_high"] - result["high_delay_ci_low"]
    result["priority_score"] = (
        result["high_delay_rate_eb"]
        * result["delay_index"].clip(lower=0.25, upper=4)
        * np.log1p(result["addressable_cases"])
    )
    return result.sort_values(["priority_score", "community_board"], ascending=[False, True])


def daily_metrics(data: pd.DataFrame) -> pd.DataFrame:
    grouped = data.groupby("created_day", observed=True)
    return grouped.agg(
        requests=("unique_key", "size"),
        closed_rate=("is_closed", "mean"),
        median_resolution_hours=("resolution_hours", "median"),
        high_delay_rate=("high_delay", "mean"),
    ).reset_index()


def complaint_metrics(data: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    result = (
        data.groupby("complaint_type", observed=True)
        .agg(
            requests=("unique_key", "size"),
            median_resolution_hours=("resolution_hours", "median"),
            p90_resolution_hours=("resolution_hours", lambda values: values.quantile(0.90)),
            closed_rate=("is_closed", "mean"),
        )
        .reset_index()
        .sort_values(["requests", "complaint_type"], ascending=[False, True])
    )
    return result.head(top_n)
