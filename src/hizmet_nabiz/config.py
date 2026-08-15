"""Configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml


@dataclass(frozen=True)
class SourceConfig:
    dataset_id: str
    dataset_name: str
    publisher: str
    api_url: str
    catalog_url: str
    terms_url: str
    created_from: str
    created_to_exclusive: str
    page_size: int
    columns: tuple[str, ...]


@dataclass(frozen=True)
class QualityConfig:
    min_rows: int
    max_duplicate_key_rate: float
    min_created_date_parse_rate: float
    min_geography_coverage: float
    max_negative_duration_rate: float


@dataclass(frozen=True)
class AnalysisConfig:
    minimum_board_requests: int
    peer_minimum_requests: int
    high_delay_quantile: float
    eb_prior_strength: int
    credible_interval: float


@dataclass(frozen=True)
class ScenarioConfig:
    intervention_capacity_cases: int
    assumed_excess_delay_reduction: float
    max_capacity_share_per_board: float


@dataclass(frozen=True)
class Settings:
    seed: int
    source: SourceConfig
    quality: QualityConfig
    analysis: AnalysisConfig
    scenario: ScenarioConfig


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    return cast(dict[str, Any], value)


def load_settings(path: Path) -> Settings:
    """Load typed settings from YAML and reject unsafe or incomplete values."""
    raw = _mapping(yaml.safe_load(path.read_text(encoding="utf-8")), "root")
    project = _mapping(raw.get("project"), "project")
    source = _mapping(raw.get("source"), "source")
    quality = _mapping(raw.get("quality"), "quality")
    analysis = _mapping(raw.get("analysis"), "analysis")
    scenario = _mapping(raw.get("scenario"), "scenario")

    columns = source.get("columns")
    if not isinstance(columns, list) or not all(isinstance(item, str) for item in columns):
        raise ValueError("source.columns must be a list of strings")
    if not str(source["api_url"]).startswith("https://"):
        raise ValueError("source.api_url must use HTTPS")

    settings = Settings(
        seed=int(project["seed"]),
        source=SourceConfig(
            dataset_id=str(source["dataset_id"]),
            dataset_name=str(source["dataset_name"]),
            publisher=str(source["publisher"]),
            api_url=str(source["api_url"]),
            catalog_url=str(source["catalog_url"]),
            terms_url=str(source["terms_url"]),
            created_from=str(source["created_from"]),
            created_to_exclusive=str(source["created_to_exclusive"]),
            page_size=int(source["page_size"]),
            columns=tuple(columns),
        ),
        quality=QualityConfig(**quality),
        analysis=AnalysisConfig(**analysis),
        scenario=ScenarioConfig(**scenario),
    )
    if not 0 < settings.analysis.high_delay_quantile < 1:
        raise ValueError("high_delay_quantile must be between 0 and 1")
    if not 0 < settings.analysis.credible_interval < 1:
        raise ValueError("credible_interval must be between 0 and 1")
    return settings
