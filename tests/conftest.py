from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def requests_frame() -> pd.DataFrame:
    rng = np.random.default_rng(20250815)
    rows: list[dict[str, object]] = []
    boards = ["01 MANHATTAN", "02 BRONX", "03 BROOKLYN"]
    complaints = ["Noise", "Street Condition"]
    for index in range(360):
        board = boards[index % len(boards)]
        complaint = complaints[index % len(complaints)]
        created = pd.Timestamp("2025-01-01") + pd.Timedelta(minutes=index * 20)
        base = 4 if complaint == "Noise" else 18
        multiplier = {"01 MANHATTAN": 0.8, "02 BRONX": 1.8, "03 BROOKLYN": 1.0}[board]
        hours = max(0.2, float(rng.lognormal(np.log(base * multiplier), 0.35)))
        closed = created + pd.Timedelta(hours=hours)
        due = created + pd.Timedelta(hours=base * 1.5)
        rows.append(
            {
                "unique_key": str(10_000 + index),
                "created_date": created.isoformat(),
                "closed_date": closed.isoformat(),
                "agency": "NYPD" if complaint == "Noise" else "DOT",
                "agency_name": "Agency",
                "complaint_type": complaint,
                "incident_zip": "10001",
                "borough": board.split(" ", 1)[1],
                "status": "Closed",
                "due_date": due.isoformat(),
                "community_board": board,
                "open_data_channel_type": "ONLINE",
            }
        )
    return pd.DataFrame(rows)
