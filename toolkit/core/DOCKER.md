# Docker Rules

- Prefer Docker Compose for reproducible multi-service local development when practical.
- Keep application runtime dependencies in images/containers rather than requiring many host-level packages.
- Use named persistent volumes for databases/data stores.
- Rebuilds and normal restarts must preserve persistent data.
- Provide health checks for critical services where useful.
- Pin major/minor image versions rather than floating `latest` for reproducible environments.
- Use multi-stage production builds when they materially reduce attack surface/image size.
- Do not bake secrets into images.
- `.env.example` may contain names/default-safe values, never real secrets.
- Separate development conveniences from production image/runtime configuration.
- Never use volume deletion as a routine "fix Docker" step; follow `DATA_SAFETY.md`.
