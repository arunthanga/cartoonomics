# `contracts` — the CartoonSpec seam (scaffold)

> **Status: planned scaffold.** The **CartoonSpec** is the versioned contract
> between the Python analysis stack and the TypeScript render stack (ADR-0001 §3,
> [`ADR-0002`](../../docs/adr/0002-repository-structure.md) §1). This package is
> where that contract becomes a shared, generated artifact so the two sides can
> never silently diverge.

Single source of truth flow:

```text
packages/pipeline/src/cartoonomics/format/  (pydantic models — authoritative)
                     │  export
                     ▼
packages/contracts/schema/cartoon_spec.schema.json   (JSON Schema, versioned)
                     │  codegen (datamodel-codegen / json-schema-to-typescript)
                     ▼
packages/contracts/typescript/                        (generated TS types package)
                     │  import
                     ▼
apps/web/  and  apps/api/                              (consumers — never re-declare)
```

Expected shape when it lands:

```text
packages/contracts/
├─ schema/              # JSON Schema emitted from the pydantic models
├─ typescript/          # generated TS types, published as an internal package
└─ scripts/gen.py       # regenerate schema + types (wired into CI, ADR-0001 §7)
```

Until then, the authoritative models live in
`packages/pipeline/src/cartoonomics/format/` and the reference renderer in
`apps/web/` consumes the emitted JSON directly. Regression tests already guard
the contract (`packages/pipeline/tests/regression`).
