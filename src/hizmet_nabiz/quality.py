"""Data contracts and quality gates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from hizmet_nabiz.config import QualityConfig


@dataclass(frozen=True)
class CheckResult:
    name: str
    value: float
    threshold: float
    operator: str
    passed: bool


@dataclass(frozen=True)
class QualityReport:
    passed: bool
    rows: int
    checks: tuple[CheckResult, ...]
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "rows": self.rows,
            "checks": [asdict(check) for check in self.checks],
            "notes": list(self.notes),
        }


class DataQualityError(ValueError):
    """Raised when a dataset fails a blocking quality contract."""


REQUIRED_COLUMNS = {
    "unique_key",
    "created_date",
    "closed_date",
    "agency",
    "complaint_type",
    "borough",
    "community_board",
}


def assess_quality(frame: pd.DataFrame, config: QualityConfig) -> QualityReport:
    """Assess source grain, completeness, parseability, and impossible timestamps."""
    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing:
        raise DataQualityError(f"Missing required columns: {', '.join(missing)}")
    rows = len(frame)
    if rows == 0:
        raise DataQualityError("Dataset is empty")

    created = pd.to_datetime(frame["created_date"], errors="coerce", format="mixed")
    closed = pd.to_datetime(frame["closed_date"], errors="coerce", format="mixed")
    duplicate_rate = float(frame["unique_key"].duplicated().mean())
    created_parse_rate = float(created.notna().mean())
    geography = frame["community_board"].fillna("").astype(str).str.strip()
    geography_coverage = float((geography.ne("") & ~geography.str.contains("Unspecified")).mean())
    has_duration = created.notna() & closed.notna()
    negative_duration_rate = float(
        ((closed < created) & has_duration).sum() / max(has_duration.sum(), 1)
    )

    checks = (
        CheckResult(
            "row_count", float(rows), float(config.min_rows), ">=", rows >= config.min_rows
        ),
        CheckResult(
            "duplicate_key_rate",
            duplicate_rate,
            config.max_duplicate_key_rate,
            "<=",
            duplicate_rate <= config.max_duplicate_key_rate,
        ),
        CheckResult(
            "created_date_parse_rate",
            created_parse_rate,
            config.min_created_date_parse_rate,
            ">=",
            created_parse_rate >= config.min_created_date_parse_rate,
        ),
        CheckResult(
            "community_board_coverage",
            geography_coverage,
            config.min_geography_coverage,
            ">=",
            geography_coverage >= config.min_geography_coverage,
        ),
        CheckResult(
            "negative_duration_rate",
            negative_duration_rate,
            config.max_negative_duration_rate,
            "<=",
            negative_duration_rate <= config.max_negative_duration_rate,
        ),
    )
    notes = (
        "Closed-date missingness is retained because open requests are analytically meaningful.",
        "Rows with negative resolution time are quarantined from duration metrics, "
        "not silently fixed.",
    )
    return QualityReport(all(check.passed for check in checks), rows, checks, notes)


def enforce_quality(report: QualityReport) -> None:
    failures = [check.name for check in report.checks if not check.passed]
    if failures:
        raise DataQualityError(f"Blocking data-quality checks failed: {', '.join(failures)}")
