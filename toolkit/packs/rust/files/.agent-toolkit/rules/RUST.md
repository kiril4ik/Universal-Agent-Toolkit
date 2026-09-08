# Rust Rules
- Follow the crate's Rust edition and MSRV.
- Prefer ownership/type modeling over runtime checks where practical.
- Avoid `unwrap`/`expect` in production paths unless the invariant is explicit and justified.
- Propagate contextual errors and isolate/review unsafe code.
- Run fmt, clippy, and tests before completion.
