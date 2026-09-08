#!/usr/bin/env bash
# Deploy a release. Atomic symlink switch, health-checked, reversible.
#
#   ./deploy.sh --env ./deploy.env
#   ./deploy.sh --env ./deploy.env --ref v1.4.2
#   DRY_RUN=1 ./deploy.sh --env ./deploy.env
#
# Layout it maintains:
#   $APP_DIR/releases/<timestamp>/   each deploy, kept for rollback
#   $APP_DIR/shared/                 .env, uploads, anything that must persist
#   $APP_DIR/current -> releases/…   the live symlink

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
# shellcheck source=lib/common.sh
. lib/common.sh

ENV_FILE="./deploy.env"; REF=""
while [ $# -gt 0 ]; do
  case "$1" in
    --env) ENV_FILE="$2"; shift 2 ;;
    --ref) REF="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

load_env "$ENV_FILE"
require_env APP_NAME APP_DIR APP_PORT
REF="${REF:-${APP_REF:-main}}"

RELEASES="$APP_DIR/releases"
SHARED="$APP_DIR/shared"
CURRENT="$APP_DIR/current"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
NEW="$RELEASES/$STAMP"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:${APP_PORT}${HEALTH_PATH:-/}}"

step "Deploying ${APP_NAME} @ ${REF}"
log "release: $STAMP"

# ------------------------------------------------------------- 1. fetch code
step "Fetching source"
run mkdir -p "$RELEASES" "$SHARED"
if [ -n "${APP_REPO:-}" ]; then
  run git clone --depth 1 --branch "$REF" "$APP_REPO" "$NEW"
else
  # Deploying from the current working tree (CI or local push model).
  SRC="${APP_SOURCE:-$PWD/../..}"
  [ -d "$SRC" ] || die "APP_SOURCE not found: $SRC"
  run mkdir -p "$NEW"
  run rsync -a --delete \
      --exclude '.git' --exclude 'node_modules' --exclude '.env' \
      --exclude '.agent-toolkit/reports' \
      "$SRC"/ "$NEW"/
fi
ok "source at $NEW"

# ------------------------------------------------------------- 2. shared state
step "Linking shared state"
[ -f "$SHARED/.env" ] || warn "no $SHARED/.env - the app may not start"
run ln -sfn "$SHARED/.env" "$NEW/.env"
for item in ${SHARED_PATHS:-}; do
  run mkdir -p "$SHARED/$item"
  run rm -rf "$NEW/$item"
  run ln -sfn "$SHARED/$item" "$NEW/$item"
  ok "shared: $item"
done

# ------------------------------------------------------------- 3. build
step "Build"
if [ -n "${BUILD_CMD:-}" ]; then
  if [ ! -d "$NEW" ]; then
    # Dry run: the release directory was never created, so there is nothing
    # to cd into. Report the command instead of failing on a missing path.
    printf '   %s %s\n' "$(_c '2' 'would run in the release dir:')" "$BUILD_CMD"
  else
    ( cd "$NEW" && run bash -lc "$BUILD_CMD" ) || die "build failed - nothing was switched"
    ok "build succeeded"
  fi
else
  warn "BUILD_CMD not set - skipping build"
fi

# ------------------------------------------------------------- 4. migrations
step "Database migrations"
if [ -n "${MIGRATE_CMD:-}" ]; then
  cat <<'WARNING'
  Migrations change data. Before running them against production-like data,
  confirm a current backup exists and that you know the restore procedure.
  See .agent-toolkit/core/SAFETY.md.
WARNING
  if [ ! -d "$NEW" ]; then
    printf '   %s %s\n' "$(_c '2' 'would run in the release dir:')" "$MIGRATE_CMD"
  elif confirm "Run migrations now?"; then
    ( cd "$NEW" && run bash -lc "$MIGRATE_CMD" ) || die "migration failed - not switching"
    ok "migrations applied"
  else
    warn "migrations skipped - the new release may not match the schema"
  fi
else
  ok "no MIGRATE_CMD configured"
fi

# ------------------------------------------------------------- 5. switch
step "Switching to the new release"
PREVIOUS=""
[ -L "$CURRENT" ] && PREVIOUS="$(readlink -f "$CURRENT")"
run ln -sfn "$NEW" "$CURRENT"
ok "current -> $NEW"

# ------------------------------------------------------------- 6. restart
#
# One restart path, used by the deploy AND the rollback. The rollback used to
# honour RESTART_CMD only, so a systemd-managed app rolled its symlink back and
# then kept serving the broken release. It also must never abort the script:
# a failed restart is precisely when the rollback is needed.
restart_app() {
  if [ -n "${RESTART_CMD:-}" ]; then
    if [ ! -e "$CURRENT" ]; then
      printf '   %s %s\n' "$(_c '2' 'would run in the release dir:')" "$RESTART_CMD"
      return 0
    fi
    ( cd "$CURRENT" && run bash -lc "$RESTART_CMD" ) || {
      warn "restart command reported an error"
      return 1
    }
  elif service_exists "${APP_NAME}.service"; then
    run systemctl restart "${APP_NAME}" || {
      warn "systemctl restart ${APP_NAME} failed"
      return 1
    }
  else
    warn "no RESTART_CMD and no ${APP_NAME}.service - restart the app yourself"
  fi
  return 0
}

# roll_back <reason> - symlink back, restart the old release, verify, exit
roll_back() {
  warn "$1 - rolling back"
  [ -n "$PREVIOUS" ] || die "no previous release to roll back to. Investigate $NEW."
  ln -sfn "$PREVIOUS" "$CURRENT"
  restart_app || warn "the rolled-back release did not restart cleanly"
  if [ "$DRY_RUN" != "1" ] && ! wait_http "$HEALTH_URL" "${HEALTH_ATTEMPTS:-30}"; then
    die "rolled back to $PREVIOUS but it is NOT healthy either. This is not a
         release problem - check the database, the environment file and any
         shared service. The failed release is at $NEW."
  fi
  die "rolled back to $PREVIOUS (verified healthy).
       The failed release is still at $NEW for inspection."
}

step "Restarting the application"
restart_app || roll_back "the new release failed to start"

# ------------------------------------------------------------- 7. health
step "Health check"
if [ "$DRY_RUN" = "1" ]; then
  warn "dry run: skipping health check"
elif wait_http "$HEALTH_URL" "${HEALTH_ATTEMPTS:-30}"; then
  ok "the new release is serving traffic"
else
  roll_back "health check failed"
fi

# ------------------------------------------------------------- 8. prune
step "Pruning old releases"
KEEP="${KEEP_RELEASES:-5}"
if [ ! -d "$RELEASES" ]; then
  # Dry run on a server that has never been deployed to: nothing was created,
  # so there is nothing to prune. Not an error.
  ok "no releases directory yet - nothing to prune"
  COUNT=0
else
  COUNT="$(find "$RELEASES" -maxdepth 1 -mindepth 1 -type d | wc -l | tr -d ' ')"
fi
if [ "$COUNT" -gt "$KEEP" ]; then
  # Never remove the live release, whatever its age.
  LIVE="$(readlink -f "$CURRENT")"
  find "$RELEASES" -maxdepth 1 -mindepth 1 -type d | sort | head -n "-$KEEP" | while read -r old; do
    [ "$(readlink -f "$old")" = "$LIVE" ] && continue
    run rm -rf "$old"
    ok "removed old release $(basename "$old")"
  done
else
  ok "$COUNT release(s), keeping up to $KEEP"
fi

step "Deployed"
printf '\n  %s is live at %s\n  release: %s\n  rollback: ./rollback.sh --env %s\n\n' \
  "$APP_NAME" "$HEALTH_URL" "$STAMP" "$ENV_FILE"
