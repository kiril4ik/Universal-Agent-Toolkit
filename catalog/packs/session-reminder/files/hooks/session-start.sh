#!/usr/bin/env bash
# Printed into the agent's context at the start of every session.
#
# Instructions the agent has to go looking for are instructions it will
# sometimes skip. This puts the load-bearing ones in front of it every time,
# and keeps them short enough that they stay cheap.
#
# Registered as a SessionStart hook. Prints to stdout and exits 0; it must
# never block a session, so every failure path degrades to silence.

set -uo pipefail

root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
tk="$root/.agent-toolkit"
[ -d "$tk" ] || exit 0

mode="unknown"
if [ -r "$tk/project.json" ]; then
  mode="$(sed -n 's/.*"mode"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$tk/project.json" | head -1)"
  [ -n "$mode" ] || mode="unknown"
fi

# Which phases have reports, so the reminder reflects real progress.
done_count=0
next_phase="00 triage"
if [ -d "$tk/reports" ]; then
  done_count="$(find "$tk/reports" -name '[0-9][0-9]-*.md' 2>/dev/null | wc -l | tr -d ' ')"
  for n in 00 01 02 03 04 05 06 07 08 09 10 11 12; do
    if ! ls "$tk/reports/$n-"*.md >/dev/null 2>&1; then
      next_phase="$n"
      break
    fi
  done
fi

cat <<BANNER
<agent-toolkit>
This project is governed by the Universal Agent Toolkit. Read
.agent-toolkit/CORE.md before acting. Interaction mode: ${mode}.

NON-NEGOTIABLE
  1. Planning work runs through .agent-toolkit/workflow/README.md.
     Classify with 00-triage.md FIRST and say the classification out loud.
     No implementation before the gate in 11-gate.md and a human approval.
  2. Read .agent-toolkit/core/SAFETY.md before ANY database, migration,
     Docker volume, deployment or server change. "It's only local" is not
     an exemption.
  3. Never claim work is done without running the verification command and
     reading its output. See .agent-toolkit/core/VERIFICATION.md.
  4. Read only the stack rules relevant to what you are touching, from
     .agent-toolkit/rules/. Do not load the rest.

WORKFLOW STATE
  ${done_count} phase report(s) written; next phase: ${next_phase}
  Read .agent-toolkit/reports/ before re-planning anything - those are
  decisions already made.

Phases own the sequence and the gates. Skills own the technique inside a
phase. Where a skill's instructions conflict with the workflow, the
"Precedence" section of workflow/README.md decides.
</agent-toolkit>
BANNER
exit 0
