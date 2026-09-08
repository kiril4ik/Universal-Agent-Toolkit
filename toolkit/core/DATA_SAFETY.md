# Data, Database, Docker & Deployment Safety

## Prime directive

**Production-like data is sacred. Treat every persistent database, volume, uploaded file store, and server configuration as valuable unless you have positive evidence that it is disposable.**

Never infer "local" means "safe to wipe". Developers often keep important local data.

## Docker persistence

Normal rebuild/restart/update flows must preserve data.

Preferred operations:

```text
docker compose build
docker compose up -d
docker compose restart <service>
```

Potentially destructive commands require explicit reasoning and approval unless the environment is positively disposable:

```text
docker compose down -v
docker volume rm ...
docker volume prune
docker system prune --volumes
rm -rf database-volume-path
```

- Use named volumes for persistent databases.
- Do not couple application image rebuilds to volume deletion.
- Deployment/setup scripts must not recreate persistent volumes on every run.
- Before changing volume names/mount paths, determine whether existing data must be migrated.

## Database commands

Never use destructive reset commands as routine migration/deployment:

```text
php artisan migrate:fresh
php artisan db:wipe
rails db:drop
django flush
DROP DATABASE
DROP SCHEMA
TRUNCATE ...
```

Do not replace normal incremental migrations with "drop all and recreate".

## Migrations

- Prefer forward, incremental, reversible migrations.
- Separate schema changes from large data backfills where practical.
- For destructive column/table changes, use expand/migrate/contract when uptime/data preservation matters.
- Verify application compatibility during rolling deployments.
- Do not silently delete data merely because a new schema no longer uses it.
- Estimate table size/locking impact for significant production migrations.

## Backup gate

Before significant or destructive changes to production-like data:

1. Identify the exact environment/database.
2. Determine current backup availability and freshness.
3. Create a new backup when the change risk warrants it.
4. Record backup location/identifier without exposing secrets.
5. Define the restore command/procedure.
6. Prefer verifying restore on a disposable target for high-risk work.
7. Only then perform the change.

Examples requiring the gate:
- dropping/renaming columns/tables with data;
- bulk rewrites/deletes;
- database engine/version migrations;
- changing volume topology;
- replacing database containers;
- production restore/import;
- significant migration batches where rollback is non-trivial.

## Environment detection

Before a high-impact command, verify environment using multiple signals where available: hostname, compose/project name, `.env` target, DB host/name, deployment path, cloud/account identifiers. If uncertain, stop.

## Existing servers

- Inspect existing services, ports, containers, reverse proxy, firewall, databases, and scheduled jobs before modifying them.
- Never overwrite unrelated Nginx/Apache/systemd/Docker configuration.
- Back up files before risky edits.
- Prefer additive/idempotent config and scoped reloads.

## Secrets

- Never print secrets in reports/logs.
- Never commit `.env`, private keys, access tokens, sensitive DB dumps, or credential files.
- Use least-privilege DB credentials for automation.

## Destructive-action approval

Before a destructive or irreversible action, state:

```text
Environment:
Target:
Why destructive action is necessary:
What data/config can be lost:
Backup/recovery status:
Safer alternative considered:
Exact command/action:
```

Then obtain explicit human approval unless it is positively identified as a disposable test fixture created for the current task.
