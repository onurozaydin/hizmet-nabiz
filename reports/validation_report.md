# Validation report

## Result

**PASS** — 12/12 independent reconciliation checks passed.

## Verified source snapshot

- Rows: **90,565** unique service requests
- Creation range observed: `2025-01-01T00:00:12` to `2025-01-07T23:59:58`
- Compressed raw SHA-256: `07bfb34477bb4b8470542e863663f28f220497fb65a09f147883101ae9f31cac`
- Duplicate service-request keys: **0**
- Community Board analytical rows: **59**

## Independently recomputed KPIs

- Closed rate: **99.30%**
- Median resolution: **11.47 hours**
- P90 resolution: **233.86 hours**
- Due-date coverage: **0.34%** (308 requests); on-time headline suppressed because coverage is below 10%.
- Highest decision-priority board: **15 BROOKLYN** (delay index 1.45x; EB high-delay rate 38.2%, 90% interval 35.8%-40.5%).
- Largest complaint category: **Noise - Residential** (30,254 requests).

## Scenario boundary

The engine allocated **500** hypothetical case reviews across 4 boards, with no board above 125. Under the explicit, non-causal 25% assumption, the arithmetic scenario total is **27,912 hours**. This is not a forecast, measured effect, or savings claim.

## Reconciliation checks

- [x] `source_rows_match_manifest`
- [x] `source_rows_match_summary`
- [x] `daily_rows_reconcile`
- [x] `unique_keys`
- [x] `median_recomputed`
- [x] `p90_recomputed`
- [x] `board_count_matches`
- [x] `scenario_within_capacity`
- [x] `scenario_respects_board_cap`
- [x] `due_date_guardrail_active`
- [x] `quality_gate_passed`
- [x] `dashboard_embeds_exact_request_count`

## Shareability decision

The artifacts are suitable for portfolio publication with the documented cohort, coverage caveat, observational interpretation, and scenario disclaimer. They are not suitable for causal agency evaluation or resource deployment without a longer time window, population context, and intervention evidence.
