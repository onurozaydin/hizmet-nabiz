from pathlib import Path

import pytest

from hizmet_nabiz.config import load_settings


def test_load_settings() -> None:
    settings = load_settings(Path("configs/analysis.yml"))
    assert settings.source.dataset_id == "erm2-nwe9"
    assert settings.source.api_url.startswith("https://")
    assert settings.analysis.high_delay_quantile == 0.75


def test_load_settings_rejects_unsafe_url(tmp_path: Path) -> None:
    content = Path("configs/analysis.yml").read_text().replace("https://data", "http://data")
    path = tmp_path / "bad.yml"
    path.write_text(content)
    with pytest.raises(ValueError, match="HTTPS"):
        load_settings(path)


def test_load_settings_rejects_bad_columns(tmp_path: Path) -> None:
    content = Path("configs/analysis.yml").read_text().replace("  columns:\n", "  columns: nope\n")
    path = tmp_path / "bad.yml"
    path.write_text(content)
    with pytest.raises(ValueError, match="columns"):
        load_settings(path)
