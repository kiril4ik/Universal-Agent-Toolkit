# Redis Rules
- Decide whether data is cache, queue state, lock state, session state, or durable-enough application data.
- Use TTLs deliberately for cache/session keys.
- Namespace keys predictably.
- Avoid unbounded scans and huge values/collections in hot paths.
- Design distributed locks with expiry and ownership semantics.
- Never flush shared Redis as a routine development/deployment step.
