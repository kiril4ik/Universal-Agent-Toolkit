# Data & Infrastructure Safety

The canonical rules are `toolkit/core/DATA_SAFETY.md`.

Key invariant: **treat persistent data as valuable unless the environment is positively proven disposable.**

A Docker rebuild is not permission to delete volumes. A migration is not permission to recreate a database. A deployment script is not permission to overwrite unrelated server configuration.
