# 05 - Rules

Make sure the repository holds best-practice rules for every technology the
stack actually uses - and nothing it does not.

## Install what the stack needs

From the toolkit repository:

```bash
uat detect  --project /path/to/project
uat install --project /path/to/project --agent <your-agent> --add <pack> <pack>
```

`uat detect` re-reads the project, so after phase 06 has introduced new
technologies it will recommend the packs that match.

Installing is additive and idempotent: existing files are never overwritten
without `--force`, and re-running is safe.

## Only what is used

A rule pack for a technology this project does not use is not free. It costs
context, it invites the agent to apply irrelevant advice, and it makes the
genuinely relevant rules harder to find.

If the stack changes later, install the new pack then. That is a one-command
operation, not a reason to install everything up front.

## Check the gaps

For each significant technology in `docs/stack.md`, confirm a rule file exists
in `.agent-toolkit/rules/`. Where one does not:

1. Check `uat catalog` for a pack that covers it.
2. If there is none, look for a high-quality public rule set and add it as a
   pinned vendor entry in the toolkit repository - do not paraphrase from
   memory, and do not rewrite what you vendor.
3. If nothing good exists, write a short project-specific rule file directly
   in `.agent-toolkit/rules/` and say plainly that it is your own, not a
   vendored best-practice document.

Never fabricate provenance. A rule file that claims to come from an upstream
project must actually come from it, byte for byte.

## Output

Updated `.agent-toolkit/rules/`, and a line in the report listing which packs
were added and which technologies still have no rule coverage.

Plus `.agent-toolkit/reports/05-rules.md`.
