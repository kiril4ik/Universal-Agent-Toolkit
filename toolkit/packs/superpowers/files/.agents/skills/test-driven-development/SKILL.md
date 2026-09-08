---
name: test-driven-development
description: Use for features, bug fixes, refactoring, and behavior changes when automated testing is practical.
---

# Test-Driven Development

## Red → Green → Refactor

1. Write one focused test describing desired behavior.
2. Run it and verify it fails for the expected reason.
3. Write the smallest implementation that makes it pass.
4. Run the focused test and relevant suite.
5. Refactor only while green.
6. Repeat.

Tests should assert observable behavior, not merely mock call counts or implementation details. Prefer real code/dependencies when practical.

Exceptions such as throwaway spikes, generated artifacts, or configuration-only changes should be explicit rather than quietly bypassing tests.
