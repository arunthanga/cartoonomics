# Knowledge base

The `docs/` tree is the project's knowledge base: the durable "why" behind
cartoonomics, kept in version control next to the code it governs. The product's
"what" lives in [`requirements.md`](../requirements.md) (the single source of
truth); this folder records the engineering decisions and the day-to-day map.

## Contents

| Area | Document | What it answers |
|---|---|---|
| Architecture decisions | [`adr/0001-technology-stack.md`](adr/0001-technology-stack.md) | Which stack, and why (resolves `requirements.md` §19 Q5). |
| Architecture decisions | [`adr/0002-repository-structure.md`](adr/0002-repository-structure.md) | Why the repo is a monorepo, and how the folders are partitioned. |
| Architecture reference | [`architecture/repository-layout.md`](architecture/repository-layout.md) | "Where does X go?" — the day-to-day layout map. |

## How this fits together

```text
requirements.md          # product & technical single source of truth (the "what")
   └─ docs/
      ├─ adr/             # architecture decision records (the "why", versioned)
      └─ architecture/    # reference maps & diagrams (the "where")
```

## Conventions

- **ADRs are append-only.** Record a decision and its rationale in a new
  `adr/NNNN-<slug>.md`; supersede rather than rewrite once one is Accepted.
- **Trace to requirements.** Every decision cites the `requirements.md` section
  or requirement ID (e.g. FR-1.2, §7.6) it serves.
- **The SSOT wins.** If a doc here disagrees with `requirements.md`, the SSOT is
  authoritative until explicitly amended.
