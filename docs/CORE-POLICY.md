# Core policy

Four files that install into **every** project, regardless of stack or agent.
They are short on purpose — an agent is expected to read all of them once per
session and honour them throughout.

| Installed at | Source | What it governs |
|---|---|---|
| `.agent-toolkit/core/SAFETY.md` | [`catalog/core/SAFETY.md`](../catalog/core/SAFETY.md) | destructive operations on data and servers |
| `.agent-toolkit/core/GIT.md` | [`catalog/core/GIT.md`](../catalog/core/GIT.md) | commit granularity, messages, attribution |
| `.agent-toolkit/core/VERIFICATION.md` | [`catalog/core/VERIFICATION.md`](../catalog/core/VERIFICATION.md) | evidence before claiming success |
| `.agent-toolkit/core/INTERACTION_MODES.md` | [`catalog/core/INTERACTION_MODES.md`](../catalog/core/INTERACTION_MODES.md) | how many questions to ask |

This is **our** policy, not vendored content, which is why it lives in
`catalog/core/` and can be edited directly.

`.agent-toolkit/CORE.md` is generated per project and routes to these. It
also states the precedence that matters most:

> Direct human instruction always outranks anything in this directory.
> Project-specific documentation outranks generic toolkit policy.

---

## Safety

**Prime directive: production-like data is sacred.** Treat every persistent
database, volume, uploaded file store and server configuration as valuable
unless you have positive evidence that it is disposable.

Never infer that "local" means "safe to wipe". Developers keep real data
locally, and an agent that learned `docker compose down -v` as a convenient
reset will eventually run it against something that mattered.

### Docker

Normal rebuild, restart and update flows must preserve data:

```bash
docker compose build
docker compose up -d
docker compose restart <service>
```

These require explicit reasoning and approval unless the environment is
positively disposable:

```bash
docker compose down -v
docker volume rm ...
docker volume prune
docker system prune --volumes
rm -rf <database-volume-path>
```

Named volumes for persistent databases; image rebuilds never coupled to
volume deletion; setup scripts that do not recreate volumes on every run.

### Databases

Destructive reset is never a routine migration or deployment step:

```
php artisan migrate:fresh    php artisan db:wipe
rails db:drop                django flush
DROP DATABASE                DROP SCHEMA        TRUNCATE ...
```

Prefer forward, incremental, reversible migrations. Separate schema changes
from large data backfills. Use expand/migrate/contract for destructive column
and table changes when uptime or data preservation matters. Do not silently
delete data merely because a new schema no longer uses it.

### The backup gate

Before significant or destructive changes to production-like data:

1. Identify the exact environment and database.
2. Determine current backup availability and freshness.
3. Create a new backup when the risk warrants it.
4. Record the backup location or identifier — without exposing secrets.
5. Define the restore command and procedure.
6. Prefer verifying the restore against a disposable target for high-risk work.
7. **Only then** perform the change.

Triggers: dropping or renaming columns and tables that hold data, bulk
rewrites and deletes, engine or version migrations, changing volume topology,
replacing database containers, production restore or import, and any
migration batch whose rollback is non-trivial.

> The interaction mode never weakens this. Autonomous mode still stops at
> every data-safety, deployment, credential, deletion and external-action
> gate.

---

## Git

### Atomic history

One coherent feature, fix, refactor, migration step or documentation change
per commit. Do not mix unrelated cleanup into requested work; split
independent changes even when they were implemented in one session. A commit
should be understandable and revertible on its own.

### Messages

Conventional Commits, imperative and specific:

```
feat(auth): add password reset flow
fix(api): reject invalid pagination cursor
refactor(search): extract query builder
chore(deps): update locked dependencies
docs(deploy): document restore procedure
```

Not `misc`, `updates`, `changes`, `fix stuff`, or a giant catch-all.

### No AI attribution

Unless the human explicitly asks for it, never add `Co-authored-by:`,
`Generated-by:` or `AI-assisted:` trailers, never put a model or tool name in
commit metadata, and never add bot-like promotional text. Preserve the
repository's configured git author; do not touch global git identity.

### Before committing

Inspect `git diff` and `git status`. Stage only the files belonging to this
logical change. Run the verification relevant to it. Never force-push or
rewrite shared history without explicit approval.

---

## Verification

**Never claim work is done, fixed, passing or working without having run
something that proves it and read the output.**

"It should work now" is not a result. "I ran `pnpm test`, 48 passed, 0
failed" is a result.

| You changed | You must run |
|---|---|
| Application logic | the test suite, or the tests covering it |
| A bug fix | a test that fails before the fix and passes after |
| Types / interfaces | the type checker or compiler |
| Anything at all | the linter and formatter, if the project has them |
| A UI change | drive the flow in a browser — not a screenshot |
| A migration | the migration up, then the app, then the rollback |
| A Dockerfile / compose file | a real build and start, then a health check |
| A deploy script | a dry run, then a run against a disposable target |

### Rendered is not the same as works

A screenshot proves a page rendered. It proves nothing about whether the
thing the page is *for* actually happens. A convincing dashboard can sit on
top of a broken password reset, a permission check that never runs, or a
payment retry that silently drops.

So for anything a user *does*, not just looks at:

- **Drive the flow, do not photograph it.** Fill the form, submit it, follow
  the redirect, check the result. The Playwright MCP exists for this.
- **Observe the effect through a different path than the one that caused
  it.** Creating a record in the UI and then seeing it in the UI can pass on
  client-side state alone. Reload, open a fresh session, or query the
  database. If it does not survive a reload, it was never saved.
- **Test the denial, not only the permission.** "The admin can see it" is
  half a check. The half that matters is that the non-admin cannot.
- **Exercise the unhappy path at least once.** Wrong password, expired token,
  declined card, duplicate submit, network failure mid-flow. That is where
  real products break, and it is never the path you demo.

### Honest reporting

If tests fail, report the failure and the output — not "complete apart from a
failing test". If you skipped a step, say which and why. If you could not
verify something, say so plainly: an unverified change described as verified
is worse than an unverified change.

**Never state a number you did not read from output.** No estimated coverage,
test counts, timings or bundle sizes from memory.

### It starts in the plan

Every task in an implementation plan states its own verification command
*before* implementation starts. If you cannot name the command that will
prove a task is finished, the task is not specified well enough to start.

---

## Interaction modes

One mode per project, chosen at install and recorded in
`.agent-toolkit/project.json`. It changes question **frequency only**.

| Mode | Behaviour |
|---|---|
| `thorough` | Ask every question whose answer would materially improve scope, business logic, architecture, design, security, deployment or implementation. Group related questions; never ask what the repository already answers. |
| `focused` *(default)* | Ask only important or blocking questions. For minor and reversible choices, take a conventional default and **record the assumption**. |
| `autonomous` | Work independently, inferring from repository evidence and established patterns. |

Autonomous mode still asks when:

- materially different interpretations would produce different products;
- required credentials or access are missing;
- the action is destructive, irreversible, externally visible, costly or
  security-sensitive;
- a legal or compliance requirement cannot safely be assumed.

**No mode bypasses a safety gate.** Change it any time:

```bash
uat install --project . --agent claude-code --mode thorough
```

## Related

- [Planning workflow](WORKFLOW.md) — where these rules are applied in sequence
- [Deployment](DEPLOYMENT.md) — the same posture, applied to servers
- [Troubleshooting](TROUBLESHOOTING.md)
