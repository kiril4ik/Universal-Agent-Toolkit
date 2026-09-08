---
name: verification-before-completion
description: Use before claiming work is complete, fixed, or passing, and before commits/PR handoff.
---

# Verification Before Completion

**No completion claims without fresh verification evidence.**

Before any success claim:

1. Identify the command/check that proves it.
2. Run it fresh and completely.
3. Read output and exit status.
4. Confirm it actually supports the claim.
5. Only then report success.

Tests passing does not automatically prove every requirement. Re-read the plan/spec and verify acceptance criteria.

For UI work, use Playwright/browser verification when available.
