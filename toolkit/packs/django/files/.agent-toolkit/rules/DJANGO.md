# Django Rules
- Follow the installed Django version and project app conventions.
- Avoid N+1 queries with `select_related`/`prefetch_related` where appropriate.
- Keep authorization server-side and use CSRF/session/security settings correctly.
- Migrations are incremental and data-safe; never casually flush/drop valuable DBs.
- Add tests around views/services/models and transaction-sensitive behavior.
