# Security and privacy controls

- HTTPS-only source URL is validated at configuration load.
- Requests have connect/read timeouts, bounded exponential retry, a deterministic page size, and
  explicit selected columns.
- No token is required or embedded. `.env` is ignored; `.env.example` contains no secret.
- Address, coordinate, street, and free-text fields are not requested.
- Raw snapshots are excluded from Git; the non-sensitive provenance manifest is committed for
  auditability.
- JSON outputs are written atomically to reduce partial-artifact risk.
- GitHub Actions uses read-only repository permissions and pinned major action versions.
- Dependencies are exact-pinned in project metadata and the generated lock file.

Residual risks: the upstream schema may drift; dependency hashes are not yet enforced; action
tags are not pinned to immutable commit SHAs. These are documented rather than hidden.
