# Universal Agent Toolkit — Agent Instructions

This repository is a reusable **toolkit builder**, not an application project.

## Primary objective

Maintain a high-quality, pinned, repository-local library of AI coding resources and safely copy only relevant resources into target projects.

## Before changing this repository

1. Read `README.md` and `docs/ARCHITECTURE.md`.
2. Treat `vendor/` as upstream snapshots. Do not casually rewrite vendored content.
3. Put our policy in `toolkit/core/` or `toolkit/packs/`, not inside vendor snapshots.
4. Keep `scripts/preinstall.sh` and `scripts/preinstall.py` idempotent.
5. Never overwrite target-project files by default.
6. Never install globally.

## Project interaction mode

When bootstrapping a target software project, the first workflow choice is:

1. Thorough
2. Focused (default)
3. Autonomous

The choice controls clarifying-question behavior. It never weakens destructive-operation safety gates.

## Safety

Read `toolkit/core/DATA_SAFETY.md` before database, Docker, deployment, migration, restore/import, or server changes.

## Git

Read `toolkit/core/GIT.md`. Commits must be atomic/coherent and must not add AI attribution or `Co-authored-by` trailers unless explicitly requested by the human.

## Verification

Before claiming toolkit work is complete, run `./scripts/verify-toolkit.sh`.
