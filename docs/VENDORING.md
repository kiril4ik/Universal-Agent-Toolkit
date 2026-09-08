# Vendoring & provenance

Most of what the toolkit installs was written by someone else. This page is
how that content is fetched, trusted, and kept honest.

**The claim this repository makes:** every file under `vendor/` was fetched
from the commit its `SOURCE.json` names, and has not been touched since. That
claim is machine-checkable, and `uat vendor verify` is the check.

## The two rules

### 1. `vendor/` is never edited

Content under `vendor/` is a verbatim upstream snapshot. Every file is
hashed; `uat vendor verify` re-hashes and fails loudly on any local
modification. That failure is the feature.

If an upstream is wrong or incomplete, the fix is:

- an **overlay pack** in `catalog/packs/` that ships our own file, or
- our own policy in `catalog/core/`.

Never a patch to the snapshot.

### 2. Provenance is never fabricated

If `SOURCE.json` says a file came from a commit, it was fetched from that
commit. Content written from memory is never labelled as vendored. This is
the specific failure the rewrite of this repository existed to correct, and
it is why hashes exist rather than a promise.

## Commands

```bash
uat vendor list      # pins, licences and verification state
uat vendor verify    # re-hash every snapshot against its pin
uat vendor sync      # fetch upstreams at their pinned commits
uat vendor sync --only superpowers
uat vendor sync --force            # re-fetch even if unchanged
```

`uat doctor` runs verification as part of its self-check, so in practice you
get it for free before every change.

## What a snapshot looks like

```
vendor/superpowers/
├── SOURCE.json        provenance record
├── LICENSE            the upstream's own licence, vendored with it
├── README.md
└── skills/            the content
```

`SOURCE.json` is the record:

```jsonc
{
  "id": "superpowers",
  "repo": "https://github.com/obra/superpowers.git",
  "ref": "b36e0829c6d0140e93cfef2ca599b1b07d4a7797",
  "license": "MIT",
  "include": ["skills", "LICENSE", "README.md"],
  "content_sha256": "01cc92e34aa2fb...",
  "fetched_at": "2026-09-08T11:38:40+00:00",
  "notes": "Jesse Vincent's engineering-discipline skills…",
  "_policy": "Verbatim upstream snapshot. Do not edit."
}
```

`include` records exactly which directories were taken, so partial vendoring
is visible rather than looking like missing files.

## The upstreams

Seven, all with redistributable licences. Full table with licence files and
pinned commits in [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md); the
machine-readable source of truth is
[`catalog/vendor.json`](../catalog/vendor.json).

| Upstream | Licence | What | Size |
|---|---|---|---|
| obra/superpowers | MIT | 14 engineering-discipline skills | 492 KB |
| github/awesome-copilot | MIT | 193 technology instruction guides | 2.6 MB |
| PatrickJS/awesome-cursorrules | CC0-1.0 | 257 community rules, gap filling | 1.6 MB |
| vercel-labs/agent-skills | MIT | React/Next.js, composition, web design, writing | 656 KB |
| vercel-labs/web-interface-guidelines | MIT | interface quality checklist | 36 KB |
| nextlevelbuilder/ui-ux-pro-max-skill | MIT | design intelligence, palettes, font pairings | 4.0 MB |
| emavv/karpathy-guidelines | MIT | anti-overcomplication guardrails | 24 KB |

### Not vendored

Figma's agent skills are governed by the Figma Developer Terms rather than an
open-source licence, so they are not redistributed here. The `mcp-figma` pack
ships our own integration guide and explains how to install Figma's official
skills from source.

The decision is recorded in the `not_vendored` section of
`catalog/vendor.json` so it stays a visible choice rather than looking like
an oversight.

## One store, many pointers

`vendor/` and `catalog/packs/` are not two copies of the same content:

```
vendor/          9.4 MB   the actual content, fetched from pinned commits
catalog/packs/    328 KB   61 packs - mostly small JSON pointers into vendor/
```

A pack does not contain content. It says *which* vendored file to install,
what to call it, and when it applies:

```jsonc
{ "id": "go", "detect": ["go"],
  "vendor_maps": [{ "vendor": "awesome-copilot",
    "files": [{ "from": "instructions/go.instructions.md", "to": "rules/GO.md" }] }] }
```

So content lives exactly once. Adding a pack costs ~400 bytes, not a copy.
See [Packs & profiles](PACKS.md).

## Vendoring your own content

Not everything worth vendoring is a public git repository — house style
guides, a company's internal rules, a skill you wrote yourself:

```bash
uat vendor add-local ~/work/acme-rules \
    --id acme \
    --license "Proprietary - ACME internal" \
    --notes "House rules, exported from the wiki"
```

It snapshots the directory into `vendor/acme/`, content-hashes it, and
registers it in `catalog/vendor.json`. From then on it is treated exactly
like a git upstream:

- `vendor verify` catches any edit to the snapshot;
- `vendor sync` re-copies from the original path when it still exists, so a
  teammate who cloned the repository keeps the snapshot without needing your
  folder.

Then write a pack that points at it, exactly as for any other vendor.

> The `--license` string is recorded and displayed, never checked. You are
> responsible for having the right to redistribute anything you vendor, and
> for whether the resulting repository can be shared.

### Hand-copying does not work

Copying a directory into `vendor/` by hand leaves it invisible to `sync`,
`verify` and every pack — content with no provenance, which is precisely what
this design exists to prevent. `uat doctor` **fails** if it finds one, and
tells you to register it with `add-local` or delete it.

## Reachability

`uat doctor` enforces an asymmetry:

- An unmapped **skill** is a **failure**. A skill nothing can install is dead
  weight in the repository.
- An unmapped **rule document** is fine. There are ~410 of them, and
  `uat add-rule` reaches every one:

```bash
uat catalog --search wordpress
uat add-rule awesome-copilot:wordpress --project .
```

## Updating an upstream

1. Change `ref` in [`catalog/vendor.json`](../catalog/vendor.json) to the new
   commit.
2. `./bin/uat vendor sync --only <id>`
3. `./bin/uat doctor` — every pack's `vendor_maps` must still resolve. This
   is where an upstream that renamed or removed a file is caught.
4. `./bin/uat-test`
5. Commit the snapshot change and the pin change **together**, so the
   provenance record and the content never disagree in history.

Pin to a commit, never a branch or tag. A tag can move; a commit cannot.

## Related

- [Third-party notices](../THIRD_PARTY_NOTICES.md) — licences in full
- [Packs & profiles](PACKS.md) — how vendored content becomes installable
- [Architecture](ARCHITECTURE.md#trust-boundary)
