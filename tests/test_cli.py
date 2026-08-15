from __future__ import annotations

from pathlib import Path

import pytest

from hizmet_nabiz.cli import main
from hizmet_nabiz.logging_utils import JsonFormatter, configure_logging


def test_cli_routes_commands(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[str] = []
    monkeypatch.setattr("hizmet_nabiz.cli.extract_dataset", lambda *_args: calls.append("fetch"))
    monkeypatch.setattr("hizmet_nabiz.cli.build_analysis", lambda *_args: calls.append("build"))
    config = Path("configs/analysis.yml")
    assert main(["--config", str(config), "fetch", "--output", str(tmp_path / "x")]) == 0
    assert main(["--config", str(config), "build", "--input", str(tmp_path / "x")]) == 0
    assert main(["--config", str(config), "all", "--input", str(tmp_path / "x")]) == 0
    assert calls == ["fetch", "build", "fetch", "build"]


def test_cli_returns_one_on_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail(*_args: object) -> None:
        raise OSError("unavailable")

    monkeypatch.setattr("hizmet_nabiz.cli.extract_dataset", fail)
    assert main(["fetch"]) == 1
    assert "unavailable" in capsys.readouterr().err


def test_json_logging_formatter() -> None:
    import logging

    configure_logging()
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "hello", (), None)
    assert '"message": "hello"' in JsonFormatter().format(record)
