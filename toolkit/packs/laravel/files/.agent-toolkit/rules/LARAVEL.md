# Laravel Rules
- Follow the installed Laravel version and existing application conventions.
- Prefer Form Requests or explicit validators for request validation.
- Keep authorization server-side via policies/gates/permissions.
- Avoid N+1 queries; eager-load intentionally and verify hot-path query volume.
- Use transactions for multi-write invariants and keep them short.
- Jobs must be retry-safe where practical; design idempotency for external side effects.
- Use configuration/env boundaries correctly; do not scatter `env()` throughout application code.
- Migrations are incremental; never use `migrate:fresh` against valuable data.
- Test behavior with feature/unit tests appropriate to the layer.
