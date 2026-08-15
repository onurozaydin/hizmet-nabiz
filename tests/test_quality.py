import pandas as pd
import pytest

from hizmet_nabiz.config import QualityConfig
from hizmet_nabiz.quality import DataQualityError, assess_quality, enforce_quality


def _config(min_rows: int = 10) -> QualityConfig:
    return QualityConfig(min_rows, 0.0, 0.99, 0.8, 0.01)


def test_quality_passes_fixture(requests_frame: pd.DataFrame) -> None:
    report = assess_quality(requests_frame, _config())
    assert report.passed
    assert report.to_dict()["rows"] == 360
    enforce_quality(report)


def test_quality_detects_duplicates(requests_frame: pd.DataFrame) -> None:
    requests_frame.loc[1, "unique_key"] = requests_frame.loc[0, "unique_key"]
    report = assess_quality(requests_frame, _config())
    assert not report.passed
    with pytest.raises(DataQualityError, match="duplicate"):
        enforce_quality(report)


def test_quality_rejects_missing_columns() -> None:
    with pytest.raises(DataQualityError, match="Missing"):
        assess_quality(pd.DataFrame({"unique_key": ["1"]}), _config())


def test_quality_rejects_empty(requests_frame: pd.DataFrame) -> None:
    with pytest.raises(DataQualityError, match="empty"):
        assess_quality(requests_frame.iloc[0:0], _config())
