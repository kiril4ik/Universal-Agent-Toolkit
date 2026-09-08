# Verification Rules

Evidence before completion claims.

Before saying a task is complete:

1. Identify what command/check proves the claim.
2. Run it fresh.
3. Read the result and exit status.
4. Fix failures or report the real state.
5. Only then state completion.

Use the narrowest relevant verification during implementation and complete project verification before final delivery when practical.

For UI changes, browser-based verification with Playwright is expected when available. Test functional behavior, responsive layout, critical states, console/network errors, and accessibility basics rather than relying only on code inspection.
