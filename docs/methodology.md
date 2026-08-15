# Methodology

## Decision frame

Audience: municipal service operations analyst. Decision: where to investigate process friction
or allocate a bounded case-review intervention. Outcome: reduce persistent, addressable delay
without treating high-volume or noisy districts as automatically worse.

## Analysis sequence

1. Pull a deterministic creation cohort from the official API in key-ordered pages.
2. Enforce source-grain, parsing, geography, duplication, and impossible-duration checks.
3. Calculate robust latency metrics without imputing open requests.
4. Estimate agency × complaint-type peer expectations on log-transformed duration.
5. Apply complaint-level/city fallbacks for sparse peer groups.
6. Aggregate peer residuals and high-delay outcomes by Community Board.
7. Shrink high-delay rates with an empirical-Bayes beta-binomial model.
8. Rank with reliability, intensity, and impact; run a bounded non-causal capacity scenario.
9. Reconcile dashboard cards, CSV tables, and JSON evidence from the same metric frames.

## Statistical rationale

The median and P90 are reported because service times are right-skewed. `log1p` makes
multiplicative differences interpretable and avoids undefined values at zero. Peer adjustment
addresses observed case mix. Empirical Bayes shrinkage reduces variance in smaller groups while
credible intervals expose remaining uncertainty.

No hypothesis test is used as a ranking shortcut. With many boards, statistical significance
would conflate sample size with operational importance. The project instead reports uncertainty,
effect intensity, and addressable workload together.

## Validation

The highest-impact metrics are independently checked in tests: daily totals reconcile to the
cohort, category totals reconcile to the cohort, slower synthetic boards receive higher adjusted
delay, posterior intervals are ordered, and scenario allocation cannot exceed total or per-board
capacity.
