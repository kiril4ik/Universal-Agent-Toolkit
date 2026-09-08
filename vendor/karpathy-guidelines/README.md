# Karpathy Guidelines for AI Agents

Universal behavioral principles to reduce agent mistakes across all task types — coding, research, configuration, file operations, writing, and communication. Derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on LLM agent pitfalls.

Source inspiration: [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)

## The Four Principles

1. **Think Before Acting** — State assumptions. Surface tradeoffs. Don't hide confusion.
2. **Simplicity First** — Minimum action to solve the problem. Nothing speculative.
3. **Surgical Changes** — Touch only what must change. Match existing conventions.
4. **Goal-Driven Execution** — Define verifiable success criteria. Loop until verified.

## Repo Structure

```
├── hermes/
│   └── SOUL.md                              # Always-active persona (compact, slot #1)
├── hermes-skill/
│   ├── SKILL.md                             # Full Hermes skill with deployment table
│   └── references/examples.md               # Wrong vs. right patterns (code-focused)
└── codex/
    └── karpathy-guidelines/
        ├── SKILL.md                         # Generalized skill for OpenAI Codex
        ├── agents/openai.yaml               # Codex agent metadata
        └── references/examples.md           # Generalized wrong vs. right patterns
```

## Deployment

| Platform | What | Location | Activation |
|----------|------|----------|------------|
| Hermes | `SOUL.md` | `~/.hermes/SOUL.md` | Always active (system prompt slot #1) |
| Hermes | skill | `~/.hermes/skills/software-development/karpathy-guidelines/` | On-demand via `skill_view` |
| Codex | skill | `%USERPROFILE%\.codex\skills\karpathy-guidelines\` | Auto-triggered by description match |
| Claude Code | CLAUDE.md | `CLAUDE.md` (per-project or global) | Per-session context |

## How to Use

### Hermes (SOUL.md)
Copy `hermes/SOUL.md` or merge its contents into `~/.hermes/SOUL.md`. Reloads per message — no restart needed.

### Hermes (Skill)
Copy `hermes-skill/` to `~/.hermes/skills/software-development/karpathy-guidelines/`.

### Codex
Copy `codex/karpathy-guidelines/` to `%USERPROFILE%\.codex\skills\karpathy-guidelines\`. Auto-discovers on next Codex launch.

## License

MIT — see source [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) for original.
