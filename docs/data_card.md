# Data card

## Dataset

- Name: 311 Service Requests from 2020 to Present
- ID: `erm2-nwe9`
- Publisher: NYC OpenData / NYC311
- Update pattern: daily according to the publisher
- Project window: 1–7 January 2025 inclusive
- Unit of observation: one service request

## Intended use

Operational exploration of service-request latency, reliability, and hypothetical case-review
allocation at Community Board level. Appropriate for portfolio demonstration and analyst
discussion; not appropriate for automated enforcement, personnel evaluation, benefit denial, or
claims of discrimination.

## Field minimization

The extractor deliberately omits incident address, street, intersections, coordinates, free-text
resolution descriptions, and facility names. The analysis uses only identifiers, timestamps,
agency/problem classifications, broad geography, status, due date, and intake channel.

## Known quality risks

- Values and schemas can change because the source is updated daily.
- `due_date` is not available for every request type.
- A closed status does not prove the reported condition was substantively resolved.
- Reporting behaviour varies by place and channel, so request volume is not underlying need.
- Floating timestamps do not carry explicit timezone offsets.

## Reproduction

`hizmet-nabiz fetch` stores a compressed CSV and a manifest with the exact first-page query,
pagination rules, retrieval timestamp, row/column counts, and SHA-256. The raw snapshot is not
committed. Processed aggregates and validation evidence are committed only after quality gates
pass.
