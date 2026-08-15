"""Transparent, non-causal intervention capacity scenarios."""

from __future__ import annotations

import pandas as pd

from hizmet_nabiz.config import ScenarioConfig


def allocate_capacity(boards: pd.DataFrame, config: ScenarioConfig) -> pd.DataFrame:
    """Greedily allocate bounded case-review capacity by observed addressable delay impact."""
    if boards.empty:
        return boards.copy()
    remaining = config.intervention_capacity_cases
    per_board_cap = max(
        1,
        int(config.intervention_capacity_cases * config.max_capacity_share_per_board),
    )
    rows: list[dict[str, float | int | str]] = []
    ranked = boards.sort_values(["priority_score", "community_board"], ascending=[False, True])
    for record in ranked.to_dict(orient="records"):
        if remaining <= 0:
            break
        addressable = int(record["addressable_cases"])
        allocated = min(addressable, per_board_cap, remaining)
        if allocated <= 0:
            continue
        average_excess = float(record["excess_delay_hours"]) / max(addressable, 1)
        rows.append(
            {
                "community_board": str(record["community_board"]),
                "borough": str(record["borough"]),
                "allocated_cases": allocated,
                "share_of_capacity": allocated / config.intervention_capacity_cases,
                "observed_excess_hours_per_case": average_excess,
                "scenario_hours_avoided": (
                    allocated * average_excess * config.assumed_excess_delay_reduction
                ),
                "assumed_reduction": config.assumed_excess_delay_reduction,
            }
        )
        remaining -= allocated
    return pd.DataFrame(rows)
