"""End-to-end analytical pipeline orchestration."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import pandas as pd

from hizmet_nabiz.config import Settings
from hizmet_nabiz.dashboard import render_dashboard
from hizmet_nabiz.io_utils import atomic_json_dump
from hizmet_nabiz.metrics import board_metrics, city_kpis, complaint_metrics, daily_metrics
from hizmet_nabiz.quality import assess_quality, enforce_quality
from hizmet_nabiz.scenario import allocate_capacity
from hizmet_nabiz.transform import prepare_requests

LOGGER = logging.getLogger(__name__)


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    normalized = frame.replace({float("inf"): None, float("-inf"): None})
    return cast(list[dict[str, Any]], json.loads(normalized.to_json(orient="records")))


def build_analysis(
    raw_path: Path,
    settings: Settings,
    output_dir: Path,
    dashboard_path: Path,
) -> dict[str, Any]:
    """Validate, transform, calculate KPIs, run a scenario, and render all artifacts."""
    raw = pd.read_csv(raw_path, dtype=str, compression="infer")
    quality = assess_quality(raw, settings.quality)
    enforce_quality(quality)
    prepared = prepare_requests(raw, settings.analysis)
    city = city_kpis(prepared)
    boards = board_metrics(prepared, settings.analysis)
    daily = daily_metrics(prepared)
    complaints = complaint_metrics(prepared)
    scenario = allocate_capacity(boards, settings.scenario)

    output_dir.mkdir(parents=True, exist_ok=True)
    boards.to_csv(output_dir / "board_metrics.csv", index=False)
    daily.to_csv(output_dir / "daily_metrics.csv", index=False)
    complaints.to_csv(output_dir / "complaint_metrics.csv", index=False)
    scenario.to_csv(output_dir / "capacity_scenario.csv", index=False)
    atomic_json_dump(quality.to_dict(), output_dir / "quality_report.json")

    payload = {
        "city": city,
        "boards": _records(boards),
        "daily": _records(daily),
        "complaints": _records(complaints),
        "scenario": _records(scenario),
        "quality": quality.to_dict(),
        "method": {
            "minimum_board_requests": settings.analysis.minimum_board_requests,
            "peer_minimum_requests": settings.analysis.peer_minimum_requests,
            "high_delay_quantile": settings.analysis.high_delay_quantile,
            "eb_prior_strength": settings.analysis.eb_prior_strength,
            "credible_interval": settings.analysis.credible_interval,
            "scenario": asdict(settings.scenario),
        },
        "source": {
            "dataset_id": settings.source.dataset_id,
            "dataset_name": settings.source.dataset_name,
            "publisher": settings.source.publisher,
            "created_from": settings.source.created_from,
            "created_to_exclusive": settings.source.created_to_exclusive,
            "catalog_url": settings.source.catalog_url,
        },
    }
    atomic_json_dump(payload, output_dir / "analysis_summary.json")
    render_dashboard(payload, dashboard_path)
    LOGGER.info("analysis complete rows=%s boards=%s", len(raw), len(boards))
    return payload
