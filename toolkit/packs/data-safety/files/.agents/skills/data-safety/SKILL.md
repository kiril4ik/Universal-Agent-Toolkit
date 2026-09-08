---
name: data-safety
description: "Protect databases, Docker volumes, migrations, backups, and production-like data during development and deployment."
---

# Data Safety

Before database, migration, Docker-volume, restore/import, or deployment work, read `.agent-toolkit/rules/DATA_SAFETY.md`.

The default assumption is that persistent data matters. Normal Docker rebuild/restart paths must preserve database volumes. Never use destructive reset commands as a convenience.

For significant production-like schema/data changes, identify the environment, create/verify a backup when risk warrants it, define recovery, and only then proceed.
