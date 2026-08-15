"""Reproducible, bounded extraction from NYC Open Data."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from hizmet_nabiz.config import SourceConfig
from hizmet_nabiz.io_utils import atomic_json_dump, sha256_file

LOGGER = logging.getLogger(__name__)


class ExtractionError(RuntimeError):
    """Raised when the official source cannot be extracted safely."""


def build_query(source: SourceConfig, offset: int) -> dict[str, str | int]:
    """Return the exact Socrata query used for a deterministic page."""
    return {
        "$select": ",".join(source.columns),
        "$where": (
            f"created_date >= '{source.created_from}' "
            f"and created_date < '{source.created_to_exclusive}'"
        ),
        "$order": "unique_key",
        "$limit": source.page_size,
        "$offset": offset,
    }


def _get_page(
    session: requests.Session,
    source: SourceConfig,
    offset: int,
    *,
    attempts: int = 4,
) -> list[dict[str, Any]]:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = session.get(
                source.api_url,
                params=build_query(source, offset),
                timeout=(10, 60),
                headers={"User-Agent": "HizmetNabiz/0.1 portfolio-research"},
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                raise ExtractionError("Socrata returned a non-list response")
            return data
        except (requests.RequestException, ValueError, ExtractionError) as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(2**attempt)
    raise ExtractionError(f"Extraction failed at offset {offset}: {last_error}")


def extract_dataset(source: SourceConfig, output_path: Path, manifest_path: Path) -> pd.DataFrame:
    """Download the fixed analysis window, persist a compressed snapshot, and record provenance."""
    pages: list[pd.DataFrame] = []
    offset = 0
    with requests.Session() as session:
        while True:
            records = _get_page(session, source, offset)
            LOGGER.info("downloaded page offset=%s rows=%s", offset, len(records))
            if not records:
                break
            pages.append(pd.DataFrame.from_records(records))
            if len(records) < source.page_size:
                break
            offset += source.page_size

    if not pages:
        raise ExtractionError("The official API returned no rows for the configured window")
    frame = pd.concat(pages, ignore_index=True).reindex(columns=list(source.columns))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False, compression="gzip")
    retrieved_at = datetime.now(UTC).isoformat()
    manifest = {
        "dataset_id": source.dataset_id,
        "dataset_name": source.dataset_name,
        "publisher": source.publisher,
        "api_url": source.api_url,
        "catalog_url": source.catalog_url,
        "terms_url": source.terms_url,
        "retrieved_at_utc": retrieved_at,
        "query": build_query(source, 0),
        "pagination": {"page_size": source.page_size, "order": "unique_key"},
        "rows": len(frame),
        "columns": list(frame.columns),
        "file": output_path.name,
        "sha256": sha256_file(output_path),
    }
    atomic_json_dump(manifest, manifest_path)
    return frame
