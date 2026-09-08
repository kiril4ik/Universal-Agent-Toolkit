#!/usr/bin/env bash
# Read-only audit of a server. Changes nothing.
#
# Run this FIRST on any server you did not personally provision. Deploying
# onto an existing server without knowing what is already there is how you
# take down someone else's application.
#
#   ./inspect-server.sh              # human readable
#   ./inspect-server.sh --markdown   # paste into a report

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
# shellcheck source=lib/common.sh
. lib/common.sh

MD=0
[ "${1:-}" = "--markdown" ] && MD=1

section() {
  if [ "$MD" = "1" ]; then printf '\n## %s\n\n```\n' "$1"; else step "$1"; fi
}
endsection() { [ "$MD" = "1" ] && printf '```\n' || true; }

[ "$MD" = "1" ] && printf '# Server inspection - %s\n\nGenerated %s\n' \
  "$(hostname)" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

section "Identity and OS"
  hostname -f 2>/dev/null || hostname
  [ -r /etc/os-release ] && grep -E '^(PRETTY_NAME|VERSION_ID)=' /etc/os-release
  uname -r
  echo "uptime:$(uptime -p 2>/dev/null || true)"
endsection

section "Resources"
  echo "-- cpu/memory --"
  nproc 2>/dev/null | sed 's/^/cpus: /'
  free -h 2>/dev/null || true
  echo
  echo "-- disk --"
  df -h -x tmpfs -x devtmpfs 2>/dev/null || df -h
endsection

section "Listening ports"
  if command -v ss >/dev/null 2>&1; then
    ss -lntup 2>/dev/null || ss -lntu
  else
    netstat -lntup 2>/dev/null || warn "neither ss nor netstat available"
  fi
endsection

section "Web servers and reverse proxies"
  for s in nginx apache2 caddy traefik haproxy; do
    if service_exists "$s"; then
      printf '%-10s installed  (%s)\n' "$s" "$(systemctl is-active "$s" 2>/dev/null || echo unknown)"
    fi
  done
  [ -d /etc/nginx/sites-enabled ] && {
    echo "-- nginx sites-enabled --"
    ls -1 /etc/nginx/sites-enabled 2>/dev/null || true
  }
  [ -d /etc/nginx/conf.d ] && {
    echo "-- nginx conf.d --"
    ls -1 /etc/nginx/conf.d 2>/dev/null || true
  }
endsection

section "Databases and data services"
  for s in postgresql mysql mariadb redis-server mongod elasticsearch rabbitmq-server; do
    service_exists "$s" && printf '%-18s installed  (%s)\n' "$s" \
      "$(systemctl is-active "$s" 2>/dev/null || echo unknown)"
  done
  command -v psql  >/dev/null 2>&1 && psql --version
  command -v mysql >/dev/null 2>&1 && mysql --version
  command -v redis-server >/dev/null 2>&1 && redis-server --version | head -1
endsection

section "Container runtime"
  if command -v docker >/dev/null 2>&1; then
    docker --version
    docker compose version 2>/dev/null || warn "docker compose plugin not installed"
    echo "-- running containers --"
    docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null \
      || warn "cannot list containers (permission? add your user to the docker group)"
    echo "-- volumes (DATA LIVES HERE - never prune blindly) --"
    docker volume ls 2>/dev/null || true
  else
    echo "docker not installed"
  fi
endsection

section "Language runtimes"
  for c in node npm pnpm yarn python3 pip3 php composer go rustc java ruby; do
    if command -v "$c" >/dev/null 2>&1; then
      printf '%-10s %s\n' "$c" "$("$c" --version 2>&1 | head -1)"
    fi
  done
endsection

section "Firewall"
  if command -v ufw >/dev/null 2>&1; then
    ufw status verbose 2>/dev/null || warn "ufw status needs root"
  fi
  command -v iptables >/dev/null 2>&1 && iptables -S 2>/dev/null | head -20
endsection

section "Scheduled work"
  echo "-- system crontab --"
  [ -r /etc/crontab ] && grep -vE '^\s*(#|$)' /etc/crontab | head -20
  echo "-- cron.d --"
  ls -1 /etc/cron.d 2>/dev/null || true
  echo "-- systemd timers --"
  systemctl list-timers --no-pager 2>/dev/null | head -15 || true
endsection

section "TLS certificates"
  if command -v certbot >/dev/null 2>&1; then
    certbot certificates 2>/dev/null | grep -E 'Certificate Name|Domains|Expiry' || true
  else
    echo "certbot not installed"
  fi
endsection

if [ "$MD" = "1" ]; then
  cat <<'EOF'

## Before deploying here

Answer these from the output above:

- [ ] Which ports are free for this application?
- [ ] Is there a reverse proxy already? Which config files must NOT be touched?
- [ ] Does a database server already exist? Will you create a new database and
      a least-privilege user, rather than reusing an existing one?
- [ ] Is there enough disk for the application, its data and its backups?
- [ ] What else runs here that must keep running during deployment?
- [ ] Which existing services would a restart disrupt?
EOF
else
  step "Done - nothing was changed"
  cat <<'EOF'

  Before deploying to this server, be able to answer:
    - which ports are free
    - which reverse-proxy configs must not be touched
    - whether a database server already exists
    - what else runs here that must keep running
EOF
fi
