#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 - <<'VERIFY_PY'
from pathlib import Path
import json, sys
r=Path('.')
required=[
    'README.md','AGENTS.md','toolkit/manifest.json',
    'toolkit/core/DATA_SAFETY.md','toolkit/core/GIT.md',
    'scripts/preinstall.sh','scripts/preinstall.py'
]
missing=[x for x in required if not (r/x).exists()]
if missing:
    print('Missing:', *missing, sep='\n- ')
    sys.exit(1)
m=json.loads((r/'toolkit/manifest.json').read_text())
ids=[p['id'] for p in m['packs']]
if len(ids)!=len(set(ids)):
    print('Duplicate pack ids')
    sys.exit(1)
for p in m['packs']:
    d=r/'toolkit/packs'/p['id']/'files'
    if not d.exists():
        print('Missing pack files dir:', p['id'])
        sys.exit(1)
print(f"OK: {len(ids)} packs, required core files present")
VERIFY_PY

python3 -m py_compile scripts/preinstall.py
bash -n scripts/preinstall.sh scripts/bootstrap-mcp-runtime.sh
echo "Toolkit verification passed."
