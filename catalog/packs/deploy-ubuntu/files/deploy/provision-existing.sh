#!/usr/bin/env bash
# Provision an EXISTING server that already runs other things.
#
# The difference from provision-clean.sh is the posture: this script assumes
# everything it finds belongs to someone else. It adds; it does not replace.
#
#   sudo ./provision-existing.sh --env ./deploy.env
#   sudo DRY_RUN=1 ./provision-existing.sh --env ./deploy.env
#
# Rules this script follows, and you should too:
#   * never overwrite a config file it did not write
#   * never restart a shared service - reload where possible, and say so first
#   * never install a package that is already present
#   * never take a port without checking it is free
#   * back up every file before editing it

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
# shellcheck source=lib/common.sh
. lib/common.sh

ENV_FILE="./deploy.env"
while [ $# -gt 0 ]; do
  case "$1" in
    --env) ENV_FILE="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

require_root
require_ubuntu
load_env "$ENV_FILE"
require_env APP_NAME APP_USER APP_DIR APP_DOMAIN APP_PORT

# --------------------------------------------------------- 0. look first

step "Surveying what is already here"
echo
./inspect-server.sh | sed 's/^/  | /'
echo

confirm "Continue and ADD ${APP_NAME} to this server?" \
  || die "aborted by operator"

# --------------------------------------------------------- 1. port safety

step "Port availability"
require_free_port "$APP_PORT"

# --------------------------------------------------------- 2. packages

step "Packages (installing only what is missing)"
MISSING=()
for p in ca-certificates curl gnupg git rsync jq; do
  has_pkg "$p" || MISSING+=("$p")
done
if [ ${#MISSING[@]} -eq 0 ]; then
  ok "all required packages already installed"
else
  log "missing: ${MISSING[*]}"
  # apt-get update only; never dist-upgrade someone else's server
  run apt-get update -qq
  run apt-get install -y --no-install-recommends "${MISSING[@]}"
fi
warn "no system upgrade was performed - that is deliberate on a shared server"

# --------------------------------------------------------- 3. app user

step "Application user"
if id -u "$APP_USER" >/dev/null 2>&1; then
  ok "user $APP_USER already exists (left as is)"
else
  run adduser --system --group --home "$APP_DIR" --shell /bin/bash "$APP_USER"
  ok "created $APP_USER"
fi

step "Directory layout"
for d in "$APP_DIR" "$APP_DIR/releases" "$APP_DIR/shared" "$APP_DIR/logs"; do
  [ -d "$d" ] && ok "exists: $d" || run mkdir -p "$d"
done
run chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

# --------------------------------------------------------- 4. container runtime

step "Container runtime"
if command -v docker >/dev/null 2>&1; then
  ok "docker present: $(docker --version) - not touching it"
  docker compose version >/dev/null 2>&1 \
    || warn "docker compose plugin missing; install it manually if you need compose"
else
  warn "docker is not installed on this server"
  if confirm "Install Docker? This affects the whole machine."; then
    run install -m 0755 -d /etc/apt/keyrings
    run bash -c 'curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg'
    run chmod a+r /etc/apt/keyrings/docker.gpg
    run bash -c 'echo "deb [arch=$(dpkg --print-architecture) \
signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        > /etc/apt/sources.list.d/docker.list'
    run apt-get update -qq
    run apt-get install -y docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin
  else
    warn "continuing without Docker - deploy.sh must not rely on it"
  fi
fi
id -nG "$APP_USER" 2>/dev/null | grep -qw docker || run usermod -aG docker "$APP_USER" || true

# --------------------------------------------------------- 5. reverse proxy

step "Reverse proxy"
PROXY=""
for s in nginx apache2 caddy traefik; do
  service_exists "$s" && { PROXY="$s"; break; }
done

case "$PROXY" in
  nginx)
    ok "nginx is already running this server's traffic"
    SITE="/etc/nginx/sites-available/${APP_NAME}"
    if [ -e "$SITE" ]; then
      warn "site file already exists: $SITE"
      warn "NOT overwriting it. Review it by hand if it needs changing."
    else
      if [ "$DRY_RUN" = "1" ]; then
        printf '   %s %s\n' "$(_c '2' 'would write NEW site file:')" "$SITE"
      else
        cat > "$SITE" <<NGINX
# Added by provision-existing.sh for ${APP_NAME}.
# This file is new. No other nginx configuration was modified.
server {
    listen 80;
    listen [::]:80;
    server_name ${APP_DOMAIN};

    location /.well-known/acme-challenge/ { root /var/www/html; }

    location / {
        proxy_pass         http://127.0.0.1:${APP_PORT};
        proxy_http_version 1.1;
        proxy_set_header   Host              \$host;
        proxy_set_header   X-Real-IP         \$remote_addr;
        proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto \$scheme;
        proxy_set_header   Upgrade           \$http_upgrade;
        proxy_set_header   Connection        "upgrade";
    }

    client_max_body_size 25m;
    access_log /var/log/nginx/${APP_NAME}.access.log;
    error_log  /var/log/nginx/${APP_NAME}.error.log;
}
NGINX
      fi
      run ln -sf "$SITE" "/etc/nginx/sites-enabled/${APP_NAME}"
    fi

    # Validate BEFORE reloading: a bad config would take down every site here.
    if run nginx -t; then
      if confirm "nginx config is valid. Reload nginx? (reload does not drop connections)"; then
        run systemctl reload nginx
        ok "nginx reloaded"
      else
        warn "not reloaded - your site is not live until you run: systemctl reload nginx"
      fi
    else
      die "nginx config test FAILED - not reloading. Fix $SITE before continuing."
    fi
    ;;
  "")
    warn "no reverse proxy found on this server"
    warn "install one deliberately, or expose ${APP_PORT} another way"
    ;;
  *)
    warn "this server uses $PROXY, not nginx"
    warn "add a vhost for ${APP_DOMAIN} -> 127.0.0.1:${APP_PORT} by hand."
    warn "this script will not edit a proxy it does not understand."
    ;;
esac

# --------------------------------------------------------- 6. firewall

step "Firewall"
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q '^Status: active'; then
  ok "ufw is active; existing rules left untouched"
  ufw status | grep -qE '^(80|443)' || \
    warn "ports 80/443 may not be open - check 'ufw status' yourself"
else
  warn "ufw inactive or absent - not enabling it on a shared server"
  warn "enabling a firewall here could cut off services you did not audit"
fi

# --------------------------------------------------------- 7. tls

step "TLS"
if [ -d "/etc/letsencrypt/live/${APP_DOMAIN}" ]; then
  ok "certificate already exists for ${APP_DOMAIN}"
elif [ "${SKIP_TLS:-0}" = "1" ]; then
  warn "SKIP_TLS=1"
elif command -v certbot >/dev/null 2>&1 && [ -n "${TLS_EMAIL:-}" ] && [ "$PROXY" = "nginx" ]; then
  if confirm "Request a certificate for ${APP_DOMAIN}? This edits the nginx site file."; then
    backup_file "/etc/nginx/sites-available/${APP_NAME}"
    run certbot --nginx -d "${APP_DOMAIN}" -m "${TLS_EMAIL}" \
        --agree-tos --non-interactive --redirect
  fi
else
  warn "skipping TLS: needs certbot, TLS_EMAIL and nginx"
fi

# --------------------------------------------------------- 8. database note

step "Database"
cat <<'DBNOTE'
  This script does not create or modify any database. On a shared server that
  is deliberate.

  When you create one:
    * create a NEW database and a NEW least-privilege user for this app
    * never reuse an existing application's credentials or superuser
    * confirm the backup story BEFORE the first byte of real data
    * read .agent-toolkit/core/SAFETY.md before touching an existing database
DBNOTE

step "Done"
cat <<SUMMARY

  ${APP_NAME} is provisioned additively on this server.

  Changed:  ${APP_DIR}, user ${APP_USER}, one new nginx site file
  Untouched: existing sites, existing services, firewall rules, packages
             already installed, and every database on this machine

  Next: ./deploy.sh --env ${ENV_FILE}
SUMMARY
