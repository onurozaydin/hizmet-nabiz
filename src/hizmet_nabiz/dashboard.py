"""Portable, self-contained interactive dashboard rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape


def render_dashboard(payload: dict[str, Any], output_path: Path) -> None:
    env = Environment(
        loader=PackageLoader("hizmet_nabiz", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("dashboard.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        template.render(payload_json=json.dumps(payload, ensure_ascii=False)),
        encoding="utf-8",
    )
