# Deployment

Four scripts, two situations, one rule: **inspect before you change anything.**

| Script | What it does | Run as |
|---|---|---|
| `inspect-server.sh` | Read-only audit. Changes nothing. | any user |
| `provision-clean.sh` | Fresh Ubuntu -> ready to host the app | root |
| `provision-existing.sh` | Adds the app to a server already running things | root |
| `deploy.sh` | Ships a release, health-checks it, auto-reverts on failure | deploy user |
| `rollback.sh` | Returns to a previous release | deploy user |

## Start here

```bash
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

## Clean vs existing is a posture, not a feature list

`provision-clean.sh` assumes it owns the server: it enables a firewall,
removes nginx's default site, and installs Docker without asking.

`provision-existing.sh` assumes everything it finds belongs to someone else:

- it shows you the audit and waits for confirmation before starting
- it fails if the app's port is already taken
- it installs only packages that are missing, and never upgrades the system
- it writes exactly one new nginx site file and refuses to modify existing ones
- it runs `nginx -t` before reloading, and asks before the reload
- it will not enable a firewall on a machine whose services it did not audit
- it never touches a database

Slower, and much harder to take down someone else's site with.

## The release model

```
$APP_DIR/
├── releases/
│   ├── 20260908T101500Z/
│   └── 20260908T143000Z/
├── shared/           .env, uploads - survives every deploy
└── current -> releases/20260908T143000Z
```

Deploying builds a whole new release directory and only then moves the
`current` symlink. If the health check fails, the symlink moves back and the
broken release stays on disk for you to inspect.

## What deploy.sh will not do for you

- **Roll back a migration.** Code rolls back; schema does not. If a release
  applied a destructive migration, rolling back the code is not enough - and
  `rollback.sh` says so before it acts.
- **Create your database.** Deliberate: creating databases automatically on a
  server you did not audit is how data gets lost. Create it yourself, with a
  least-privilege user, and confirm the backup story first.
- **Invent a health check.** Set `HEALTH_PATH` to a route that actually
  exercises the app - not a static file. Without it, a broken release is
  reported as a successful deploy.

## Secrets

`deploy.env` holds configuration, not secrets. Real secrets belong in
`$APP_DIR/shared/.env` on the server, owned by the app user, mode 600, never
in git. `deploy.sh` symlinks that file into each release.

## Before anything touches production data

Read `../core/SAFETY.md`. The backup gate applies to every migration,
restore, volume change and database swap in this directory.
