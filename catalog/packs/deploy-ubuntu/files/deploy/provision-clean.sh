#!/usr/bin/env bash
# Provision a CLEAN Ubuntu server from scratch.
#
# Assumes: a fresh Ubuntu install you own, running as root.
# Idempotent: safe to re-run. Every step checks before it acts.
#
#   sudo ./provision-clean.sh --env ./deploy.env
#   sudo DRY_RUN=1 ./provision-clean.sh --env ./deploy.env    # show, change nothing
#
# If the server already runs anything you care about, use
# provision-existing.sh instead - this script assumes it owns the machine.

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
# shellcheck source=lib/common.sh
. lib/common.sh

ENV_FILE="./deploy.env"
while [ $# -gt 0 ]; do
  case "$1" in
    --env) ENV_FILE="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

require_root
require_ubuntu
load_env "$ENV_FILE"
require_env APP_NAME APP_USER APP_DIR APP_DOMAIN APP_PORT

# --------------------------------------------------------------- 1. packages

step "Base packages"
export DEBIAN_FRONTEND=noninteractive
run apt-get update -qq
run apt-get install -y --no-install-recommends \
  ca-certificates curl gnupg git ufw unattended-upgrades \
  rsync jq tzdata logrotate
ok "base packages present"

# --------------------------------------------------------------- 2. app user

step "Application user: $APP_USER"
if id -u "$APP_USER" >/dev/null 2>&1; then
  ok "user $APP_USER already exists"
else
  run adduser --system --group --home "$APP_DIR" --shell /bin/bash "$APP_USER"
  ok "created system user $APP_USER"
fi

# --------------------------------------------------------------- 3. layout

step "Directory layout"
for d in "$APP_DIR" "$APP_DIR/releases" "$APP_DIR/shared" "$APP_DIR/logs" "$BACKUP_DIR"; do
  run mkdir -p "$d"
done
run chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
run chmod 750 "$APP_DIR"
ok "layout ready under $APP_DIR"

# --------------------------------------------------------------- 4. firewall

step "Firewall"
if [ "${SKIP_FIREWALL:-0}" = "1" ]; then
  warn "SKIP_FIREWALL=1, leaving firewall untouched"
else
  run ufw allow OpenSSH
  run ufw allow 80/tcp
  run ufw allow 443/tcp
  # The app port stays closed: traffic reaches it through the reverse proxy.
  if ufw status | grep -q '^Status: active'; then
    ok "ufw already active"
  else
    run ufw --force enable
    ok "ufw enabled (SSH, HTTP, HTTPS)"
  fi
fi

# --------------------------------------------------------------- 5. docker

step "Docker"
if command -v docker >/dev/null 2>&1; then
  ok "docker already installed: $(docker --version)"
else
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
  ok "docker installed"
fi
run systemctl enable --now docker
run usermod -aG docker "$APP_USER" || true

# --------------------------------------------------------------- 6. proxy

step "Reverse proxy (nginx)"
if ! command -v nginx >/dev/null 2>&1; then
  run apt-get install -y nginx
fi

SITE="/etc/nginx/sites-available/${APP_NAME}"
if [ -e "$SITE" ]; then
  ok "site config already exists: $SITE (not overwritten)"
else
  if [ "$DRY_RUN" = "1" ]; then
    printf '   %s %s\n' "$(_c '2' 'would write:')" "$SITE"
  else
    cat > "$SITE" <<NGINX
# Managed by provision-clean.sh for ${APP_NAME}.
server {
    listen 80;
    listen [::]:80;
    server_name ${APP_DOMAIN};

    # Certbot writes its challenge here.
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
        proxy_read_timeout 60s;
    }

    client_max_body_size 25m;
    access_log /var/log/nginx/${APP_NAME}.access.log;
    error_log  /var/log/nginx/${APP_NAME}.error.log;
}
NGINX
  fi
  run ln -sf "$SITE" "/etc/nginx/sites-enabled/${APP_NAME}"
  ok "nginx site created"
fi

# Only the default site is safe to remove on a clean server.
[ -e /etc/nginx/sites-enabled/default ] && run rm -f /etc/nginx/sites-enabled/default

run nginx -t
run systemctl reload nginx
ok "nginx configured for ${APP_DOMAIN} -> 127.0.0.1:${APP_PORT}"

# --------------------------------------------------------------- 7. tls

step "TLS certificate"
if [ "${SKIP_TLS:-0}" = "1" ]; then
  warn "SKIP_TLS=1, no certificate requested"
elif [ -d "/etc/letsencrypt/live/${APP_DOMAIN}" ]; then
  ok "certificate already exists for ${APP_DOMAIN}"
else
  run apt-get install -y certbot python3-certbot-nginx
  if [ -z "${TLS_EMAIL:-}" ]; then
    warn "TLS_EMAIL not set - skipping certificate issuance"
    warn "run later: certbot --nginx -d ${APP_DOMAIN} -m you@example.com --agree-tos"
  else
    run certbot --nginx -d "${APP_DOMAIN}" -m "${TLS_EMAIL}" \
        --agree-tos --non-interactive --redirect
    ok "certificate issued; renewal timer installed by the certbot package"
  fi
fi

# --------------------------------------------------------------- 8. logs

step "Log rotation"
LR="/etc/logrotate.d/${APP_NAME}"
if [ -e "$LR" ]; then
  ok "logrotate config already exists"
elif [ "$DRY_RUN" = "1" ]; then
  printf '   %s %s\n' "$(_c '2' 'would write:')" "$LR"
else
  cat > "$LR" <<LOGROTATE
${APP_DIR}/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su ${APP_USER} ${APP_USER}
}
LOGROTATE
  ok "logrotate configured"
fi

# --------------------------------------------------------------- 9. summary

step "Provisioning complete"
cat <<SUMMARY

  application   ${APP_NAME}
  user          ${APP_USER}
  directory     ${APP_DIR}
  domain        ${APP_DOMAIN}
  upstream      127.0.0.1:${APP_PORT}
  backups       ${BACKUP_DIR}

  Next:
    1. put your application code in ${APP_DIR}
    2. create ${APP_DIR}/shared/.env with production settings (never commit it)
    3. run ./deploy.sh --env ${ENV_FILE}

  This script did NOT create a database. Create one deliberately, with a
  least-privilege user, and record how to back it up before you store
  anything you care about.
SUMMARY
