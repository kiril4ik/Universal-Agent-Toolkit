#!/usr/bin/env bash
set -euo pipefail

PROJECT="${1:-.}"
PROJECT="$(cd "$PROJECT" && pwd)"
RUNTIME="$PROJECT/.agent-toolkit/runtime"
mkdir -p "$RUNTIME"

need_node() {
  command -v npm >/dev/null 2>&1 || {
    echo "npm is required for local stdio MCP runtimes." >&2
    exit 1
  }
}

installed_version() {
  local pkg="$1"
  node -e "try{console.log(require('$RUNTIME/node_modules/$pkg/package.json').version)}catch(e){process.exit(1)}" 2>/dev/null || true
}

install_pkg() {
  local pkg="$1" version="$2"
  local current
  current="$(installed_version "$pkg")"
  if [[ "$current" == "$version" ]]; then
    echo "✓ $pkg@$version already installed — skip"
    return
  fi

  if [[ -n "$current" ]]; then
    echo "↻ $pkg installed at $current; requested $version"
  else
    echo "+ $pkg@$version"
  fi

  npm install --prefix "$RUNTIME" --no-save --save-exact "$pkg@$version"
}

need_node
[[ -f "$RUNTIME/package.json" ]] || printf '{"private":true}\n' > "$RUNTIME/package.json"

install_pkg "@playwright/mcp" "0.0.80"
install_pkg "@upstash/context7-mcp" "4.0.5"

echo "MCP runtimes are project-local under $RUNTIME"
