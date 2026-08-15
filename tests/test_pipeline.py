from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from hizmet_nabiz.config import load_settings
from hizmet_nabiz.pipeline import build_analysis


def test_pipeline_writes_reconciling_artifacts(
    tmp_path: Path, requests_frame: pd.DataFrame
) -> None:
    raw = tmp_path / "requests.csv.gz"
    requests_frame.to_csv(raw, index=False, compression="gzip")
    settings = load_settings(Path("configs/analysis.yml"))
    settings = settings.__class__(
        seed=settings.seed,
        source=settings.source,
        quality=settings.quality.__class__(10, 0.0, 0.99, 0.8, 0.01),
        analysis=settings.analysis.__class__(50, 30, 0.75, 40, 0.90),
        scenario=settings.scenario.__class__(60, 0.25, 0.5),
    )
    output = tmp_path / "processed"
    dashboard = tmp_path / "dashboard.html"
    payload = build_analysis(raw, settings, output, dashboard)
    assert payload["city"]["requests"] == 360
    assert dashboard.exists()
    assert "HizmetNabiz" in dashboard.read_text()
    report = json.loads((output / "quality_report.json").read_text())
    assert report["passed"] is True
