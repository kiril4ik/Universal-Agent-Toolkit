# Adding a Skill or Rule Pack

1. Prefer official or actively maintained upstream projects.
2. Resolve an exact release/tag/commit.
3. Inspect the full `SKILL.md`, referenced scripts/hooks, permissions, network calls, secret access, and destructive behavior.
4. Record source, revision, license, and reason in `vendor/SOURCES.md` and `toolkit/manifest.json`.
5. Keep upstream material unchanged under `vendor/` when practical.
6. Put local overrides/project policy in a separate pack.
7. Define detection tags/profile/default behavior in the manifest.
8. Run `./scripts/verify-toolkit.sh`.
9. Test `preinstall.sh --dry-run` and a real install into a temporary repository.

Never introduce a pack whose install hook silently writes outside the target repository.
