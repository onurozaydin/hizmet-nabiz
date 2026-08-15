# KPI contract

## Cohort and time semantics

The cohort is defined by `created_date >= 2025-01-01T00:00:00` and
`created_date < 2025-01-08T00:00:00`. NYC 311 source timestamps are floating local timestamps;
the analysis treats them consistently as local wall-clock values and does not apply a timezone
conversion. This is safe for duration subtraction within the same source convention and window,
but should be revisited for cross-system joins.

## Eligibility rules

- All-request metrics use every unique service request in the fixed cohort.
- Duration metrics require parseable `created_date`, parseable `closed_date`, and a non-negative
  difference. Invalid negative values are retained in the raw snapshot and excluded from duration
  denominators.
- On-time rate requires both `closed_date` and `due_date`; due-date coverage is displayed beside
  the rate to prevent over-generalization. The headline value is suppressed when coverage is
  below 10%, while the observed eligible-sample value remains in the JSON audit artifact.
- Board rankings exclude blank/Unspecified Community Boards and boards below the configured
  minimum request count.

## Peer adjustment

For closed request *i*, `log_duration_i = log1p(resolution_hours_i)`. The primary peer group is
`agency × complaint_type`. If it has fewer than 50 valid closed requests, the expected median and
high-delay threshold fall back to complaint type; if unavailable, they fall back to the city.

`delay_index_board = exp(mean(log_duration_i - peer_median_log_i))`

A value of 1.20 means the board’s geometric delay level is 20% above its matched peer expectation
on the transformed scale. It is descriptive, not causal.

## Reliability adjustment

`high_delay_i = log_duration_i > peer_75th_percentile_i`. Board rates use a beta-binomial empirical
Bayes posterior. The prior mean is the citywide high-delay rate and its strength is 40 pseudo-
observations. The dashboard reports the posterior mean and central 90% credible interval.

## Priority and scenario

The transparent priority score is:

`high_delay_rate_eb × clipped_delay_index × log1p(addressable_cases)`

It is a triage index, not a probability or utility estimate. Addressable cases have observed
duration above their peer median. The capacity scenario greedily assigns 500 case reviews by this
score, caps any board at 25% of capacity, and applies a hypothetical 25% reduction to observed
excess hours. No causal or budget claim is made.
