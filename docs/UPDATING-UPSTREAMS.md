# Updating Upstreams

Updates are a deliberate toolkit-maintenance action, never part of ordinary project planning.

For each upstream:

1. Check the current release/commit and changelog.
2. Review changes to instructions, scripts, hooks, dependencies, external endpoints, and permissions.
3. Diff against the pinned snapshot.
4. Re-run safety review.
5. Update snapshot and manifest revision together.
6. Document local patches if any.
7. Run toolkit verification and a sample bootstrap.

Do not use mutable `main` references inside project-installed skills if a pinned revision is available.
