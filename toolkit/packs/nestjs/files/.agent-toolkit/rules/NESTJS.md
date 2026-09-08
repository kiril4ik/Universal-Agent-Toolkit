# NestJS Rules
- Keep controllers thin and business logic in focused providers/use cases.
- Use DTO validation/transformation at external boundaries.
- Make module boundaries explicit and avoid circular dependencies.
- Keep auth guards/authorization server-side.
- Scope DB transactions intentionally and test critical module behavior.
