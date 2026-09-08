# Local development with Docker

The goal: **one command starts the project, and a rebuild never destroys data.**

```bash
docker compose up -d          # start
docker compose logs -f app    # watch
docker compose down           # stop, KEEPING volumes
```

`compose.reference.yml` in this directory is a worked example - copy the
patterns, not the file.

## The rules that matter

### 1. Persistent data lives in named volumes

```yaml
volumes:
  db-data:            # named: survives `down`, survives rebuilds

services:
  db:
    volumes:
      - db-data:/var/lib/postgresql/data
```

Never bind-mount a database data directory into the repository. Never rely on
an anonymous volume - those are collected by `docker compose down -v` and by
`docker volume prune`, which is exactly the accident this rule prevents.

### 2. A rebuild must never wipe data

These are safe and are the normal loop:

```bash
docker compose build
docker compose up -d
docker compose restart app
```

These destroy data and require deliberate intent:

```bash
docker compose down -v          # deletes named volumes
docker volume prune             # deletes unused volumes
docker system prune --volumes   # deletes a great deal more
```

Your setup script may create and seed an *empty* database. It must never drop
an existing one. Make reseeding a separate, explicitly-named command.

### 3. Source is mounted, not baked, in development

```yaml
services:
  app:
    volumes:
      - ./src:/app/src           # edit locally, see it immediately
      - /app/node_modules        # keep the container's install
```

If you must rebuild the image to see a code change, the setup is wrong.

### 4. Pin base images

`node:22.11-alpine`, not `node:latest`. Unpinned tags mean the environment
changes under you and "works on my machine" comes back.

### 5. Health checks, and dependants that wait for them

```yaml
services:
  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d app"]
      interval: 5s
      timeout: 3s
      retries: 10
  app:
    depends_on:
      db:
        condition: service_healthy    # not just service_started
```

`service_started` only means the process launched. Racing a database that has
not finished starting is a top source of flaky local setups and flaky CI.

### 6. Configuration comes from the environment

Commit `.env.example`. Never commit `.env`. Never hard-code a credential in
`compose.yml`, even a local one - it teaches the pattern that ships to
production.

## Useful commands to document for your project

```bash
docker compose exec app sh              # shell in the app container
docker compose exec db psql -U app app  # database shell
docker compose logs -f --tail=100       # logs
docker compose run --rm app npm test    # tests, in the container

# Deliberate reset - destroys local data. Requires typing the words.
docker compose down -v && docker compose up -d
```

Put these in your project README. A developer who cannot find the database
shell command will eventually reach for something more destructive.

## Before running any destructive Docker command

Read `../core/SAFETY.md`. "It is only local" is not a reason - developers keep
real work in local databases.
