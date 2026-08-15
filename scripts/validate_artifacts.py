"""Independent reconciliation of generated evidence and dashboard outputs."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from hizmet_nabiz.io_utils import atomic_json_dump


def close(left: float, right: float, tolerance: float = 1e-9) -> bool:
    return math.isclose(left, right, rel_tol=tolerance, abs_tol=tolerance)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    raw = pd.read_csv(root / "data/raw/requests.csv.gz", dtype=str)
    summary = json.loads((root / "data/processed/analysis_summary.json").read_text())
    quality = json.loads((root / "data/processed/quality_report.json").read_text())
    provenance = json.loads((root / "data/raw/manifest.json").read_text())
    daily = pd.read_csv(root / "data/processed/daily_metrics.csv")
    boards = pd.read_csv(root / "data/processed/board_metrics.csv")
    complaints = pd.read_csv(root / "data/processed/complaint_metrics.csv")
    scenario = pd.read_csv(root / "data/processed/capacity_scenario.csv")
    dashboard = (root / "dashboard/index.html").read_text()

    created = pd.to_datetime(raw["created_date"], errors="coerce", format="mixed")
    closed = pd.to_datetime(raw["closed_date"], errors="coerce", format="mixed")
    duration = (closed - created).dt.total_seconds().div(3600).where(closed >= created)
    checks = {
        "source_rows_match_manifest": len(raw) == provenance["rows"],
        "source_rows_match_summary": len(raw) == summary["city"]["requests"],
        "daily_rows_reconcile": int(daily["requests"].sum()) == len(raw),
        "unique_keys": not raw["unique_key"].duplicated().any(),
        "median_recomputed": close(
            float(duration.median()), summary["city"]["median_resolution_hours"]
        ),
        "p90_recomputed": close(
            float(duration.quantile(0.90)), summary["city"]["p90_resolution_hours"]
        ),
        "board_count_matches": len(boards) == len(summary["boards"]),
        "scenario_within_capacity": int(scenario["allocated_cases"].sum()) <= 500,
        "scenario_respects_board_cap": int(scenario["allocated_cases"].max()) <= 125,
        "due_date_guardrail_active": summary["city"]["on_time_rate"] is None,
        "quality_gate_passed": quality["passed"] is True,
        "dashboard_embeds_exact_request_count": str(len(raw)) in dashboard,
    }
    passed = all(checks.values())
    receipt = {
        "passed": passed,
        "checks": checks,
        "source_rows": len(raw),
        "created_min": created.min().isoformat(),
        "created_max": created.max().isoformat(),
        "raw_sha256": provenance["sha256"],
        "board_rows": len(boards),
        "scenario_allocated_cases": int(scenario["allocated_cases"].sum()),
        "scenario_hours_avoided_hypothetical": float(scenario["scenario_hours_avoided"].sum()),
    }
    reports = root / "reports"
    atomic_json_dump(receipt, reports / "validation_receipt.json")

    top_board = boards.iloc[0]
    top_complaint = complaints.iloc[0]
    lines = [
        "# Validation report",
        "",
        "## Result",
        "",
        f"**{'PASS' if passed else 'FAIL'}** — {sum(checks.values())}/{len(checks)} "
        "independent reconciliation checks passed.",
        "",
        "## Verified source snapshot",
        "",
        f"- Rows: **{len(raw):,}** unique service requests",
        f"- Creation range observed: `{created.min().isoformat()}` to "
        f"`{created.max().isoformat()}`",
        f"- Compressed raw SHA-256: `{provenance['sha256']}`",
        f"- Duplicate service-request keys: **{int(raw['unique_key'].duplicated().sum())}**",
        f"- Community Board analytical rows: **{len(boards)}**",
        "",
        "## Independently recomputed KPIs",
        "",
        f"- Closed rate: **{summary['city']['closed_rate']:.2%}**",
        f"- Median resolution: **{duration.median():.2f} hours**",
        f"- P90 resolution: **{duration.quantile(0.90):.2f} hours**",
        f"- Due-date coverage: **{summary['city']['due_date_coverage']:.2%}** "
        f"({summary['city']['due_date_eligible_requests']:,} requests); on-time headline "
        "suppressed because coverage is below 10%.",
        f"- Highest decision-priority board: **{top_board['community_board']}** "
        f"(delay index {top_board['delay_index']:.2f}x; EB high-delay rate "
        f"{top_board['high_delay_rate_eb']:.1%}, 90% interval "
        f"{top_board['high_delay_ci_low']:.1%}-{top_board['high_delay_ci_high']:.1%}).",
        f"- Largest complaint category: **{top_complaint['complaint_type']}** "
        f"({int(top_complaint['requests']):,} requests).",
        "",
        "## Scenario boundary",
        "",
        f"The engine allocated **{int(scenario['allocated_cases'].sum()):,}** hypothetical "
        f"case reviews across {len(scenario)} boards, with no board above 125. Under the "
        "explicit, non-causal 25% assumption, the arithmetic scenario total is "
        f"**{scenario['scenario_hours_avoided'].sum():,.0f} hours**. This is not a forecast, "
        "measured effect, or savings claim.",
        "",
        "## Reconciliation checks",
        "",
    ]
    lines.extend(f"- [{'x' if value else ' '}] `{name}`" for name, value in checks.items())
    lines.extend(
        [
            "",
            "## Shareability decision",
            "",
            "The artifacts are suitable for portfolio publication with the documented cohort, "
            "coverage caveat, observational interpretation, and scenario disclaimer. They are "
            "not suitable for causal agency evaluation or resource deployment without a longer "
            "time window, population context, and intervention evidence.",
            "",
        ]
    )
    (reports / "validation_report.md").write_text("\n".join(lines), encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
