#!/usr/bin/env bash
# Roll back to the previous release, or to a named one.
#
#   ./rollback.sh --env ./deploy.env            # previous release
#   ./rollback.sh --env ./deploy.env --list     # show what is available
#   ./rollback.sh --env ./deploy.env --to 20260908T120000Z

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
# shellcheck source=lib/common.sh
. lib/common.sh

ENV_FILE="./deploy.env"; TARGET=""; LIST=0
while [ $# -gt 0 ]; do
  case "$1" in
    --env) ENV_FILE="$2"; shift 2 ;;
    --to) TARGET="$2"; shift 2 ;;
    --list) LIST=1; shift ;;
    -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

load_env "$ENV_FILE"
require_env APP_NAME APP_DIR APP_PORT

RELEASES="$APP_DIR/releases"; CURRENT="$APP_DIR/current"
[ -d "$RELEASES" ] || die "no releases directory at $RELEASES"
LIVE="$([ -L "$CURRENT" ] && readlink -f "$CURRENT" || echo '')"

if [ "$LIST" = "1" ]; then
  step "Available releases"
  find "$RELEASES" -maxdepth 1 -mindepth 1 -type d | sort -r | while read -r r; do
    mark="  "; [ "$(readlink -f "$r")" = "$LIVE" ] && mark="->"
    printf ' %s %s\n' "$mark" "$(basename "$r")"
  done
  exit 0
fi

if [ -z "$TARGET" ]; then
  TARGET="$(find "$RELEASES" -maxdepth 1 -mindepth 1 -type d | sort -r \
            | while read -r r; do
                [ "$(readlink -f "$r")" = "$LIVE" ] || { basename "$r"; break; }
              done)"
  [ -n "$TARGET" ] || die "no previous release found. Try --list."
fi

DEST="$RELEASES/$TARGET"
[ -d "$DEST" ] || die "release not found: $DEST (try --list)"

step "Rolling back ${APP_NAME}"
log "from: $(basename "${LIVE:-none}")"
log "to:   $TARGET"

cat <<'NOTE'

  Rolling back application code does NOT roll back database migrations.
  If the release you are leaving applied a schema change, the older code may
  not work against the current schema. Check before continuing.

NOTE

confirm "Proceed with rollback?" || die "aborted"

run ln -sfn "$DEST" "$CURRENT"
if [ -n "${RESTART_CMD:-}" ]; then
  ( cd "$CURRENT" && run bash -lc "$RESTART_CMD" ) || warn "restart reported an error"
elif service_exists "${APP_NAME}.service"; then
  run systemctl restart "${APP_NAME}"
fi

HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:${APP_PORT}${HEALTH_PATH:-/}}"
[ "$DRY_RUN" = "1" ] || wait_http "$HEALTH_URL" "${HEALTH_ATTEMPTS:-30}"
step "Rolled back to $TARGET"
