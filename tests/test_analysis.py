from __future__ import annotations

import pandas as pd

from hizmet_nabiz.config import AnalysisConfig, ScenarioConfig
from hizmet_nabiz.metrics import board_metrics, city_kpis, complaint_metrics, daily_metrics
from hizmet_nabiz.scenario import allocate_capacity
from hizmet_nabiz.transform import prepare_requests


def _analysis_config() -> AnalysisConfig:
    return AnalysisConfig(50, 30, 0.75, 40, 0.90)


def test_peer_adjustment_and_shrinkage(requests_frame: pd.DataFrame) -> None:
    prepared = prepare_requests(requests_frame, _analysis_config())
    boards = board_metrics(prepared, _analysis_config())
    bronx = boards.loc[boards["community_board"] == "02 BRONX"].iloc[0]
    manhattan = boards.loc[boards["community_board"] == "01 MANHATTAN"].iloc[0]
    assert bronx["delay_index"] > manhattan["delay_index"]
    assert 0 < bronx["high_delay_rate_eb"] < 1
    assert bronx["high_delay_ci_low"] < bronx["high_delay_ci_high"]


def test_kpi_outputs_reconcile(requests_frame: pd.DataFrame) -> None:
    prepared = prepare_requests(requests_frame, _analysis_config())
    city = city_kpis(prepared)
    daily = daily_metrics(prepared)
    complaints = complaint_metrics(prepared)
    assert city["requests"] == int(daily["requests"].sum()) == len(requests_frame)
    assert int(complaints["requests"].sum()) == len(requests_frame)
    assert city["median_resolution_hours"] > 0
    assert 0 <= city["on_time_rate"] <= 1


def test_capacity_is_bounded(requests_frame: pd.DataFrame) -> None:
    prepared = prepare_requests(requests_frame, _analysis_config())
    boards = board_metrics(prepared, _analysis_config())
    config = ScenarioConfig(60, 0.25, 0.5)
    scenario = allocate_capacity(boards, config)
    assert scenario["allocated_cases"].sum() <= 60
    assert scenario["allocated_cases"].max() <= 30
    assert (scenario["scenario_hours_avoided"] >= 0).all()


def test_empty_capacity_input() -> None:
    empty = allocate_capacity(pd.DataFrame(), ScenarioConfig(10, 0.2, 0.5))
    assert empty.empty


def test_invalid_duration_is_quarantined(requests_frame: pd.DataFrame) -> None:
    requests_frame.loc[0, "closed_date"] = "2024-12-31T00:00:00"
    prepared = prepare_requests(requests_frame, _analysis_config())
    assert pd.isna(prepared.loc[0, "resolution_hours"])
