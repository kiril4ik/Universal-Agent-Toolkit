# Deployment

The `deploy-ubuntu` pack ships working, tested bash — not a template you fill
in and hope.

```bash
uat install --project ~/app --agent claude-code --add deploy-ubuntu
```

It installs into `.agent-toolkit/deploy/`:

| Script | What it does | Run as |
|---|---|---|
| `inspect-server.sh` | read-only audit; changes nothing | any user |
| `provision-clean.sh` | fresh Ubuntu → ready to host the app | root |
| `provision-existing.sh` | adds the app to a server already running things | root |
| `deploy.sh` | ships a release, health-checks it, auto-reverts on failure | deploy user |
| `rollback.sh` | returns to a previous release | deploy user |

Plus `deploy.env.example` and `lib/common.sh`.

## One rule: inspect before you change anything

```bash
cd .agent-toolkit/deploy
cp deploy.env.example deploy.env && chmod 600 deploy.env
$EDITOR deploy.env

./inspect-server.sh --markdown > server-audit.md   # always, even on a clean box
```

Then pick **one** provisioning script:

```bash
sudo ./provision-clean.sh    --env ./deploy.env    # you own the whole machine
sudo ./provision-existing.sh --env ./deploy.env    # anything else is already there
```

Every script supports `DRY_RUN=1` to print what it would do without doing it.
Use it the first time, every time.

```bash
DRY_RUN=1 sudo ./provision-existing.sh --env ./deploy.env
```

## Clean vs existing is a posture, not a feature list

**`provision-clean.sh` assumes it owns the server.** It enables a firewall,
removes nginx's default site, and installs Docker without asking.

**`provision-existing.sh` assumes everything it finds belongs to someone
else:**

- shows you the audit and waits for confirmation before starting;
- fails if the app's port is already taken;
- installs only packages that are missing, and never upgrades the system;
- writes exactly one new nginx site file and refuses to modify existing ones;
- runs `nginx -t` before reloading, and asks before the reload;
- will not enable a firewall on a machine whose services it did not audit;
- never touches a database.

Slower, and much harder to take down someone else's site with. If you are not
certain which situation you are in, you are in the second one.

## The release model

```
$APP_DIR/
├── releases/
│   ├── 20260908T101500Z/
│   └── 20260908T143000Z/
├── shared/           .env, uploads - survives every deploy
└── current -> releases/20260908T143000Z
```

`deploy.sh` builds a whole new release directory and only then moves the
`current` symlink. If the health check fails, the symlink moves back and the
broken release stays on disk for you to inspect.

`rollback.sh` moves `current` to a previous release.

## What `deploy.sh` deliberately will not do

- **Roll back a migration.** Code rolls back; schema does not. If a release
  applied a destructive migration, rolling back the code is not enough — and
  `rollback.sh` says so before it acts.
- **Create your database.** Creating databases automatically on a server you
  did not audit is how data gets lost. Create it yourself, with a
  least-privilege user, and confirm the backup story first.
- **Invent a health check.** Set `HEALTH_PATH` to a route that actually
  exercises the app, not a static file. Without it, a broken release is
  reported as a successful deploy.

Each of these is a place where automation would look helpful and be
dangerous.

## Secrets

`deploy.env` holds **configuration, not secrets**. Real secrets belong in
`$APP_DIR/shared/.env` on the server — owned by the app user, mode 600, never
in git. `deploy.sh` symlinks that file into each release, so secrets survive
deploys without ever entering the repository.

## Before anything touches production data

Read [Core policy → Safety](CORE-POLICY.md#safety). The backup gate applies
to every migration, restore, volume change and database swap here:

1. Identify the exact environment and database.
2. Check backup availability and freshness.
3. Create a new backup when the risk warrants it.
4. Record where it is.
5. Define the restore procedure.
6. Verify the restore on a disposable target for high-risk work.
7. Only then perform the change.

## How it is verified

The scripts are exercised on `ubuntu:24.04`, including `nginx -t` against the
generated site config. Contributors changing anything in
`catalog/packs/deploy-ubuntu/` must pass `bash -n` at minimum, and should run
the scripts in a container before claiming they work — see
[`AGENTS.md`](../AGENTS.md).

Claiming a deploy script works because it "looks right" is exactly the
failure [Core policy → Verification](CORE-POLICY.md#verification) exists to
prevent.

## Related

- [Core policy](CORE-POLICY.md) — the safety posture these scripts implement
- [Planning workflow](WORKFLOW.md) — phase 09 decides the environments
- `.agent-toolkit/deploy/README.md` — the installed copy, always current
