# Symfony Rules
- Follow the installed Symfony and PHP versions.
- Prefer dependency injection and autowiring over service location.
- Keep controllers thin; move domain/application logic into focused services/handlers.
- Use Validator, Security voters, Messenger, Serializer, and Workflow where they match the problem.
- Make Messenger handlers retry-safe/idempotent for external side effects.
- Keep Doctrine migrations incremental and data-safe.
- Run project static analysis and PHPUnit before completion.
