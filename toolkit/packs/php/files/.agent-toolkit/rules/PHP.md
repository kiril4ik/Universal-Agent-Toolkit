# PHP Rules
- Target the PHP version declared by the project; do not use newer syntax accidentally.
- Use strict types where consistent with the codebase.
- Prefer typed parameters, returns, and properties.
- Follow PSR-12 or the project's formatter.
- Avoid dynamic properties and hidden global state.
- Handle exceptions at meaningful boundaries; do not swallow errors.
- Use Composer lock files for applications.
- Run configured static analysis and tests before completion.
