# 09 - Environments

Local development, and the two deployment situations that actually occur.

Read `../core/SAFETY.md` before anything in this phase touches a database,
a volume or a server.

## Local development runs in Docker

Default to Docker Compose for local development, because it is the cheapest
way to make "works on my machine" true for everyone.

Requirements:

- **One command to start.** `docker compose up` and the app is reachable.
  If it needs six manual steps, write them into a script and call that.
- **Named volumes for anything persistent.** Never bind-mount a database data
  directory into the repository, and never store it in an anonymous volume.
- **Rebuilds must preserve data.** `docker compose build && docker compose up -d`
  must never destroy a developer's database. If your setup script wipes and
  reseeds, it is wrong - make seeding a separate, explicit command.
- **Hot reload for application code.** Mount source; do not rebuild to see a
  change.
- **Pinned base images.** `node:22.11-alpine`, not `node:latest`.
- **Health checks** on services others depend on, with dependants waiting for
  healthy - not just started.
- **`.env.example` committed, `.env` never.**

Document the escape hatches: how to reset deliberately, how to open a database
shell, how to run the tests inside the container, how to see logs.

The `docker` pack installs templates and rules for this.

## Deployment target A - a clean server

A repeatable path from a fresh Ubuntu install to a running application.

It must cover: base packages and updates; a non-root deploy user; firewall;
the container runtime or language runtime; directory layout and ownership;
the application itself; the database, with its data directory on persistent
storage; cache and queue workers; the scheduler; the reverse proxy; TLS
certificates and their renewal; log rotation; a health check that actually
proves the app serves traffic; and a backup job that runs before you need it.

Properties that matter more than completeness:

- **Idempotent.** Running it twice does not break anything. This is what makes
  it recoverable when it fails halfway.
- **Fails loudly and early.** `set -euo pipefail`, and check preconditions
  before mutating anything.
- **No secrets in the script.** Read them from the environment or a file that
  is not in the repository.
- **Prints what it is about to do** when it is about to do something
  irreversible.

## Deployment target B - an existing server

Harder, and far more dangerous, because other things are already running and
you did not install them.

**Inspect before you touch.** What is listening on which ports; what web
server is in front; what databases exist and who uses them; what cron and
systemd units are present; how much disk is left; what the firewall allows.

**Then obey these rules:**

- Never overwrite a reverse-proxy config you did not write. Add a new site
  file; leave the others alone.
- Never assume a port is free. Check, and fail if it is taken.
- Never restart a shared service without saying so first. Reload rather than
  restart where the service supports it.
- Back up any config file before editing it, with a timestamped copy.
- Never run a package upgrade that was not asked for.
- Create a new database and a least-privilege user for it. Do not reuse an
  existing superuser.
- Before touching an existing database: read the backup gate in
  `../core/SAFETY.md` and follow it.

**Provide a rollback.** For every deployment path, the answer to "it broke,
now what" must exist before the first deployment, not after.

## Output

Working `docker-compose.yml` and development setup; deployment scripts for
both targets; documented rollback; and a runbook covering deploy, rollback,
logs, database shell and backup restore.

Plus `.agent-toolkit/reports/09-environments.md`.
