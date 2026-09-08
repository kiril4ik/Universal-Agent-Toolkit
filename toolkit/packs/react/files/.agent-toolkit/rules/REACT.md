# React Rules
- Use function components and hooks consistent with the installed React version.
- Keep state minimal; derive values during render rather than synchronizing duplicate state with effects.
- Use effects for synchronization with external systems, not ordinary derivation.
- Do not define components inside render unless intentionally ephemeral.
- Keep accessibility and semantic HTML first-class.
- Avoid premature memoization; measure expensive paths.
- Keep server/client boundaries explicit in frameworks that support them.
- Add behavior tests and use Playwright for important UI flows.
