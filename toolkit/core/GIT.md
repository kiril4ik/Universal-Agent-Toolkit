# Git & Commit Rules

## Atomic history

- Commit one coherent feature, fix, refactor, migration step, or documentation change at a time.
- Do not mix unrelated cleanup with requested work.
- Split independent changes even if implemented in the same session.
- A commit should be understandable and revertible on its own when practical.
- Do not commit known-broken intermediate states unless an explicit private-branch workflow requires it.

## Messages

Prefer Conventional Commits:

```text
feat(auth): add password reset flow
fix(api): reject invalid pagination cursor
refactor(search): extract query builder
chore(deps): update locked dependencies
docs(deploy): document restore procedure
```

Use imperative, specific subjects. Avoid `misc`, `updates`, `changes`, `fix stuff`, or giant catch-all commits.

## No AI attribution

Unless the human explicitly asks for it, never add:

- `Co-authored-by:` trailers;
- `Generated-by:` / `AI-assisted:` trailers;
- Claude, ChatGPT, Codex, Gemini, Copilot, or model names in commit metadata/messages;
- bot-like promotional text.

Preserve the human repository's configured Git author. Do not alter global Git identity.

## Before commit

- inspect `git diff` and `git status`;
- stage only files belonging to the logical change;
- run verification relevant to that change;
- do not include unrelated pre-existing modifications;
- never force-push or rewrite shared history without explicit approval.
