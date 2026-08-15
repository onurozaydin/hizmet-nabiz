import json
from dataclasses import replace
from pathlib import Path

import pytest
import requests

from hizmet_nabiz.config import load_settings
from hizmet_nabiz.extract import ExtractionError, _get_page, build_query, extract_dataset


def test_query_is_bounded_and_ordered() -> None:
    source = load_settings(Path("configs/analysis.yml")).source
    query = build_query(source, 25000)
    assert query["$offset"] == 25000
    assert query["$order"] == "unique_key"
    assert "2025-01-01" in str(query["$where"])
    assert "incident_address" not in str(query["$select"])


class _Response:
    def __init__(self, payload: object, status_error: bool = False) -> None:
        self.payload = payload
        self.status_error = status_error

    def raise_for_status(self) -> None:
        if self.status_error:
            raise requests.HTTPError("boom")

    def json(self) -> object:
        return self.payload


class _Session:
    def __init__(self, pages: dict[int, object]) -> None:
        self.pages = pages

    def __enter__(self) -> "_Session":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def get(self, _url: str, *, params: dict[str, object], **_kwargs: object) -> _Response:
        return _Response(self.pages[int(params["$offset"])])


def _record(key: str) -> dict[str, str]:
    return {
        "unique_key": key,
        "created_date": "2025-01-01T00:00:00",
        "closed_date": "2025-01-01T01:00:00",
        "agency": "DOT",
        "agency_name": "Department of Transportation",
        "complaint_type": "Street Condition",
        "incident_zip": "10001",
        "borough": "MANHATTAN",
        "status": "Closed",
        "due_date": "2025-01-02T00:00:00",
        "community_board": "01 MANHATTAN",
        "open_data_channel_type": "ONLINE",
    }


def test_extract_writes_snapshot_and_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = replace(load_settings(Path("configs/analysis.yml")).source, page_size=2)
    fake = _Session({0: [_record("1"), _record("2")], 2: [_record("3")]})
    monkeypatch.setattr("hizmet_nabiz.extract.requests.Session", lambda: fake)
    output = tmp_path / "requests.csv.gz"
    manifest = tmp_path / "manifest.json"
    frame = extract_dataset(source, output, manifest)
    metadata = json.loads(manifest.read_text())
    assert len(frame) == 3
    assert metadata["rows"] == 3
    assert len(metadata["sha256"]) == 64


def test_get_page_rejects_non_list() -> None:
    source = load_settings(Path("configs/analysis.yml")).source
    with pytest.raises(ExtractionError, match="failed"):
        _get_page(_Session({0: {"error": "bad"}}), source, 0, attempts=1)  # type: ignore[arg-type]
