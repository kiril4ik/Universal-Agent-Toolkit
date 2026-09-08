# PostgreSQL Rules
- Preserve data and follow mandatory data-safety rules.
- Use transactions for multi-statement invariants and understand isolation/locking needs.
- Add indexes from real query patterns; validate with `EXPLAIN (ANALYZE, BUFFERS)` when performance matters.
- Avoid unbounded hot-path scans and accidental per-row queries.
- Prefer additive/backward-compatible migrations for live systems.
- Back up before destructive/high-risk production-like changes.
