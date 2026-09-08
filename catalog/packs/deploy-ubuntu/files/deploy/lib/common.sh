#!/usr/bin/env bash
# Shared helpers for the deployment scripts.
# Source this; do not execute it.

set -euo pipefail

# ---------------------------------------------------------------- output

_c() { if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then printf '\033[%sm%s\033[0m' "$1" "$2"; else printf '%s' "$2"; fi; }
log()   { printf '%s %s\n' "$(_c '36' '==>')" "$*"; }
ok()    { printf '%s %s\n' "$(_c '32' ' ok ')" "$*"; }
warn()  { printf '%s %s\n' "$(_c '33' 'warn')" "$*" >&2; }
die()   { printf '%s %s\n' "$(_c '31' 'FAIL')" "$*" >&2; exit 1; }

# Print a step that is about to change the system.
step()  { printf '\n%s %s\n' "$(_c '1' '--')" "$*"; }

# ---------------------------------------------------------------- guards

DRY_RUN="${DRY_RUN:-0}"

# run <command...> - respects DRY_RUN
run() {
  if [ "$DRY_RUN" = "1" ]; then
    printf '   %s %s\n' "$(_c '2' 'would run:')" "$*"
    return 0
  fi
  "$@"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

require_root() {
  [ "$(id -u)" -eq 0 ] || die "this script must run as root (use sudo)"
}

require_not_root() {
  [ "$(id -u)" -ne 0 ] || die "do not run this as root; run it as the deploy user"
}

require_ubuntu() {
  [ -r /etc/os-release ] || die "cannot read /etc/os-release; is this Ubuntu?"
  # shellcheck disable=SC1091
  . /etc/os-release
  case "${ID:-}" in
    ubuntu) ok "Ubuntu ${VERSION_ID:-unknown}" ;;
    debian) warn "Debian detected, not Ubuntu. Most steps work; verify before relying on this." ;;
    *) die "unsupported distribution: ${ID:-unknown}. This script targets Ubuntu." ;;
  esac
}

# confirm "question" - always prompts unless ASSUME_YES=1
confirm() {
  if [ "${ASSUME_YES:-0}" = "1" ]; then
    warn "auto-confirming: $1"
    return 0
  fi
  printf '%s [y/N] ' "$1"
  read -r reply </dev/tty || return 1
  case "$reply" in [yY]|[yY][eE][sS]) return 0 ;; *) return 1 ;; esac
}

# Gate for anything irreversible. Never bypassed by ASSUME_YES.
confirm_destructive() {
  local what="$1"
  printf '\n%s\n' "$(_c '31;1' 'DESTRUCTIVE ACTION')"
  printf '  %s\n\n' "$what"
  printf 'Type the word DESTROY to proceed: '
  local reply
  read -r reply </dev/tty || return 1
  [ "$reply" = "DESTROY" ] || { warn "not confirmed; skipping"; return 1; }
}

# ---------------------------------------------------------------- backups

BACKUP_DIR="${BACKUP_DIR:-/var/backups/agent-toolkit}"

# backup_file <path> - timestamped copy before any edit
backup_file() {
  local src="$1"
  [ -e "$src" ] || return 0
  local stamp dest
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  dest="${BACKUP_DIR}/$(echo "${src#/}" | tr '/' '_').${stamp}"
  run mkdir -p "$BACKUP_DIR"
  run cp -a "$src" "$dest"
  ok "backed up $src -> $dest"
}

# ---------------------------------------------------------------- probing

port_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -lntH "sport = :$port" 2>/dev/null | grep -q . && return 0
  elif command -v netstat >/dev/null 2>&1; then
    netstat -lnt 2>/dev/null | awk '{print $4}' | grep -qE "[:.]$port\$" && return 0
  fi
  return 1
}

require_free_port() {
  local port="$1"
  if port_in_use "$port"; then
    die "port $port is already in use. Choose another port or stop the service using it.
         Inspect with: ss -lntp 'sport = :$port'"
  fi
  ok "port $port is free"
}

service_exists() {
  systemctl list-unit-files 2>/dev/null | grep -q "^$1"
}

has_pkg() {
  dpkg -s "$1" >/dev/null 2>&1
}

# ---------------------------------------------------------------- health

# wait_http <url> <attempts> - poll until 2xx/3xx
wait_http() {
  local url="$1" attempts="${2:-30}" i
  require_cmd curl
  for i in $(seq 1 "$attempts"); do
    if curl -fsS -o /dev/null --max-time 5 "$url" 2>/dev/null; then
      ok "health check passed: $url"
      return 0
    fi
    sleep 2
  done
  die "health check never passed after $((attempts * 2))s: $url"
}

# ---------------------------------------------------------------- env

# load_env <file> - export KEY=VALUE lines, ignoring comments
load_env() {
  local f="$1"
  [ -r "$f" ] || die "environment file not found: $f (copy deploy.env.example)"
  set -a
  # shellcheck disable=SC1090
  . "$f"
  set +a
  ok "loaded environment from $f"
}

require_env() {
  local missing=0 v
  for v in "$@"; do
    if [ -z "${!v:-}" ]; then
      warn "missing required variable: $v"
      missing=1
    fi
  done
  [ "$missing" -eq 0 ] || die "set the missing variables in your env file and retry"
}
