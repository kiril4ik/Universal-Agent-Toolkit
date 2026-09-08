# TypeScript Rules
- Keep `strict` semantics unless the project explicitly differs.
- Avoid `any`; prefer `unknown` plus validation/narrowing at trust boundaries.
- Model states so invalid combinations are difficult to represent.
- Prefer explicit public interfaces and inferred local implementation types.
- Avoid non-null assertions when control flow can prove safety.
- Validate external JSON/runtime data; TypeScript types are not runtime validation.
