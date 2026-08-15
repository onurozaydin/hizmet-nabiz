"""Build and execute the reader-facing validation notebook."""

# mypy: disable-error-code="no-untyped-call"

from __future__ import annotations

import ast
import contextlib
import io
import subprocess
import sys
from pathlib import Path
from typing import Any

import nbformat


def _execute_in_process(notebook: Any) -> None:
    """Execute cells sequentially when sandbox policy blocks Jupyter kernel sockets."""
    namespace: dict[str, Any] = {"__name__": "__main__"}
    execution_count = 0
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        execution_count += 1
        module = ast.parse(cell["source"], mode="exec")
        final_expression = None
        if module.body:
            last_statement = module.body[-1]
            if isinstance(last_statement, ast.Expr):
                final_expression = ast.Expression(last_statement.value)
                module.body.pop()
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            exec(compile(module, "<notebook>", "exec"), namespace)
            result = (
                eval(compile(final_expression, "<notebook>", "eval"), namespace)
                if final_expression is not None
                else None
            )
        outputs = []
        if stream.getvalue():
            outputs.append(nbformat.v4.new_output("stream", name="stdout", text=stream.getvalue()))
        if result is not None:
            outputs.append(
                nbformat.v4.new_output(
                    "execute_result",
                    data={"text/plain": repr(result)},
                    execution_count=execution_count,
                    metadata={},
                )
            )
        cell["execution_count"] = execution_count
        cell["outputs"] = outputs


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    notebook = nbformat.v4.new_notebook()
    notebook["metadata"]["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    notebook["metadata"]["language_info"] = {"name": "python", "version": "3.11+"}
    notebook["metadata"]["execution"] = {
        "status": "passed",
        "mode": "sequential_in_process",
        "reason": "The build sandbox blocks Jupyter kernel sockets; cells still execute in order.",
    }
    notebook["cells"] = [
        nbformat.v4.new_markdown_cell(
            "# HizmetNabiz validation companion\n\n"
            "## tl;dr\n\n"
            "The fixed official-data cohort contains **90,565** unique requests. All five "
            "blocking quality checks and all independent reconciliation checks pass. Median "
            "resolution is **11.47 hours** and P90 is **233.86 hours**. Due-date coverage is "
            "only **0.34%**, so the on-time headline is suppressed. `15 BROOKLYN` is the first "
            "investigation candidate under the explicit triage index; this is observational, "
            "not a causal fairness conclusion."
        ),
        nbformat.v4.new_markdown_cell(
            "## Context & Methods\n\n"
            "This audit notebook reads only committed analytical artifacts and the compact "
            "source manifest. It independently checks reconciliation and surfaces a bounded "
            "priority table for review.\n\n"
            "### Key Assumptions\n\n"
            "- The cohort is requests created from 1 January through 7 January 2025.\n"
            "- Duration is descriptive administrative latency, not resident-perceived resolution.\n"
            "- Peer adjustment uses agency x complaint type, with documented sparse fallbacks.\n"
            "- The scenario's 25% reduction is hypothetical and non-causal."
        ),
        nbformat.v4.new_code_cell(
            "import json\n"
            "from pathlib import Path\n\n"
            "import pandas as pd\n\n"
            "ROOT = Path.cwd()\n"
            "summary = json.loads((ROOT / 'data/processed/analysis_summary.json').read_text())\n"
            "quality = json.loads((ROOT / 'data/processed/quality_report.json').read_text())\n"
            "receipt = json.loads((ROOT / 'reports/validation_receipt.json').read_text())\n"
            "boards = pd.read_csv(ROOT / 'data/processed/board_metrics.csv')\n"
            "scenario = pd.read_csv(ROOT / 'data/processed/capacity_scenario.csv')"
        ),
        nbformat.v4.new_markdown_cell("## Data\n\n### 1. Inspect source and quality coverage"),
        nbformat.v4.new_code_cell(
            "pd.DataFrame(quality['checks'])[[\n"
            "    'name', 'value', 'operator', 'threshold', 'passed'\n"
            "]]"
        ),
        nbformat.v4.new_markdown_cell("## Results\n\n### 2. Verify headline metrics"),
        nbformat.v4.new_code_cell(
            "pd.Series({\n"
            "    'requests': summary['city']['requests'],\n"
            "    'closed_rate': summary['city']['closed_rate'],\n"
            "    'median_resolution_hours': summary['city']['median_resolution_hours'],\n"
            "    'p90_resolution_hours': summary['city']['p90_resolution_hours'],\n"
            "    'due_date_coverage': summary['city']['due_date_coverage'],\n"
            "    'on_time_decision_ready': summary['city']['on_time_rate_decision_ready'],\n"
            "})"
        ),
        nbformat.v4.new_markdown_cell(
            "### 3. Review the reliability-adjusted investigation shortlist"
        ),
        nbformat.v4.new_code_cell(
            "boards[[\n"
            "    'community_board', 'borough', 'requests', 'delay_index',\n"
            "    'high_delay_rate_eb', 'high_delay_ci_low', 'high_delay_ci_high',\n"
            "    'excess_delay_hours'\n"
            "]].head(8).round(3)"
        ),
        nbformat.v4.new_markdown_cell("### 4. Re-run artifact invariants"),
        nbformat.v4.new_code_cell(
            "assert receipt['passed'] is True\n"
            "assert all(receipt['checks'].values())\n"
            "assert summary['city']['requests'] == 90_565\n"
            "assert summary['city']['on_time_rate'] is None\n"
            "assert scenario['allocated_cases'].sum() <= 500\n"
            "assert scenario['allocated_cases'].max() <= 125\n"
            "{\n"
            "    'reconciliation_checks': len(receipt['checks']),\n"
            "    'all_passed': all(receipt['checks'].values()),\n"
            "    'scenario_allocated_cases': int(scenario['allocated_cases'].sum()),\n"
            "}"
        ),
        nbformat.v4.new_markdown_cell(
            "## Takeaways\n\n"
            "- The cohort and published artifacts reconcile at 90,565 requests.\n"
            "- Long-tail latency is material: P90 is about 20 times the median, so a mean-only "
            "dashboard would be inadequate.\n"
            "- The due-date metric fails its coverage guardrail and is correctly suppressed.\n"
            "- The priority table is a disciplined investigation queue, not evidence that any "
            "board or agency caused unequal outcomes.\n"
            "- A longer, seasonally stratified cohort and population context are required before "
            "operational deployment."
        ),
    ]
    cell_ids = [
        "tldr",
        "context-methods",
        "load-artifacts",
        "data-heading",
        "quality-table",
        "results-heading",
        "headline-metrics",
        "shortlist-heading",
        "shortlist-table",
        "invariants-heading",
        "invariants",
        "takeaways",
    ]
    for cell, cell_id in zip(notebook["cells"], cell_ids, strict=True):
        cell["id"] = cell_id
    output = root / "notebooks/01_validation_companion.ipynb"
    current = Path.cwd()
    try:
        if current != root:
            raise RuntimeError("Run this script from the repository root")
        _execute_in_process(notebook)
    finally:
        # Explicit finally keeps validation state clear if a code cell raises.
        notebook["metadata"]["execution"]["working_directory"] = str(current.name)
    nbformat.validate(notebook)
    nbformat.write(notebook, output)
    ruff = Path(sys.executable).with_name("ruff")
    subprocess.run([str(ruff), "format", str(output)], check=True)
    nbformat.validate(nbformat.read(output, as_version=4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
