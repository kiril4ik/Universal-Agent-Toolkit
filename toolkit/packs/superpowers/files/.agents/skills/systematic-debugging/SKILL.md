---
name: systematic-debugging
description: Use when encountering a bug, test failure, performance problem, build failure, or unexpected behavior before proposing fixes.
---

# Systematic Debugging

**Core rule: no fix without root-cause investigation first.**

## Phase 1 — evidence

1. Read errors/stack traces completely.
2. Reproduce consistently.
3. Check recent changes and environment differences.
4. Trace data across component boundaries.
5. Follow the bad value/state backward to its origin.

## Phase 2 — compare patterns

Find similar working code/reference behavior. List relevant differences and dependencies. Do not assume small differences are irrelevant.

## Phase 3 — hypothesis

State one falsifiable hypothesis. Test it with the smallest change/diagnostic possible. One variable at a time.

## Phase 4 — fix

1. Create a failing regression test/reproduction when practical.
2. Implement the smallest root-cause fix.
3. Run targeted and relevant regression verification.
4. If repeated fixes fail, stop stacking patches and reconsider the architecture.

Never hide uncertainty or guess repeatedly under time pressure.
