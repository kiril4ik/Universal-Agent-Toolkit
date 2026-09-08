# Third-party notices

The Universal Agent Toolkit's own code and content — everything under
`bin/`, `src/`, `catalog/`, `docs/` and `tests/` — is MIT licensed. See
[`LICENSE`](LICENSE).

Everything under `vendor/` is a **verbatim snapshot of someone else's work**,
fetched from a pinned commit and left unmodified. It remains under its own
upstream licence, and those licences travel with it: where the upstream
repository ships a `LICENSE` file, that file is included in the snapshot at
`vendor/<id>/LICENSE`.

Installing a pack copies vendored content into your project. The upstream
licence applies to that copy too.

## Vendored upstreams

| Upstream | Licence | Licence file | Pinned commit | What it provides |
|---|---|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | MIT | `vendor/superpowers/LICENSE` | `b36e082` | 14 engineering-discipline skills — brainstorming, writing-plans, TDD, systematic debugging, verification |
| [github/awesome-copilot](https://github.com/github/awesome-copilot) | MIT | `vendor/awesome-copilot/LICENSE` | `f95f1b4` | 193 technology instruction guides; the primary source of stack rules |
| [PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) | CC0-1.0 | `vendor/awesome-cursorrules/LICENSE` | `b044f95` | 257 community rules, used to fill gaps |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | MIT — stated in the README; the repository ships no `LICENSE` file | — | `063bee9` | React and Next.js best practices, composition patterns, web design and writing guidelines |
| [vercel-labs/web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines) | MIT | `vendor/web-interface-guidelines/LICENSE` | `e3d624b` | Interface quality checklist |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | MIT | `vendor/ui-ux-pro-max/LICENSE` | `4aad058` | Design intelligence: style catalogues, palettes, font pairings |
| [emavv/karpathy-guidelines](https://github.com/emavv/karpathy-guidelines) | MIT — stated in the README; the repository ships no `LICENSE` file | — | `e02e9a4` | Anti-overcomplication guardrails |

The authoritative, machine-readable record — pins, licences, what is included
from each repository and why — is
[`catalog/vendor.json`](catalog/vendor.json). This page is generated from it
by hand; where the two disagree, `catalog/vendor.json` is correct.

Confirm the snapshots match their pins at any time:

```bash
./bin/uat vendor list      # pins, licences and verification state
./bin/uat vendor verify    # re-hash every file; a modified snapshot fails
```

### Partial vendoring

Two upstreams are deliberately vendored in part:

- **awesome-copilot** — only the `instructions/` directory. The rest of the
  repository is not used.
- **awesome-cursorrules** — only the `rules/` directory.
- **ui-ux-pro-max** — five skills (`ui-ux-pro-max`, `design-system`, `brand`,
  `banner-design`, `slides`). The `ui-styling` (5.7 MB) and `design` skills
  are left out for size and because they overlap with environment-specific
  tooling.

Selection happens at the directory level: nothing that *is* included is
altered, and each of these ships its upstream `LICENSE` and `README.md`
alongside the content. Exactly what was taken from each repository is
recorded in that snapshot's `vendor/<id>/SOURCE.json`.

## Not vendored

**[figma/mcp-server-guide](https://github.com/figma/mcp-server-guide)** — Figma's
agent skills are governed by the Figma Developer Terms rather than an
open-source licence, so redistribution inside this repository is not clearly
permitted. They are **not** included here.

The `mcp-figma` pack instead ships our own integration guide and explains how
to install Figma's official skills directly from source into your own
project, where Figma's terms apply to you directly.

This decision is recorded in the `not_vendored` section of
[`catalog/vendor.json`](catalog/vendor.json) so it stays visible rather than
looking like an oversight.

## Content you vendor yourself

`uat vendor add-local` snapshots a local directory — your own rules, a
company style guide — into `vendor/` with a licence string you supply:

```bash
uat vendor add-local ~/work/acme-rules --id acme --license "Proprietary - ACME internal"
```

That string is recorded in `catalog/vendor.json` and shown by
`uat vendor list`. The toolkit does not check it and cannot: **you are
responsible for having the right to redistribute anything you vendor**, and
for whether the resulting repository can be shared.

## Provenance policy

Two rules make the table above meaningful rather than decorative:

1. **Content under `vendor/` is never edited.** Every file is hashed against
   its pinned commit, and `uat vendor verify` fails loudly on any local
   modification. If an upstream is wrong, the fix is an overlay in
   `catalog/packs/` or our own policy in `catalog/core/` — never a patch to
   the snapshot.
2. **Provenance is never fabricated.** If `SOURCE.json` says a file came from
   a commit, it was fetched from that commit. Content written from memory is
   never labelled as vendored.

See [`docs/VENDORING.md`](docs/VENDORING.md) for how this is enforced.
