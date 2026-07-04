# `infra/k8s` (scaffold)

Deployment manifests / Helm charts for the deployable units (`apps/api`,
`apps/web`, `services/orchestrator`). Each unit is deployed independently from
its own image (see `infra/docker`), matching the independent-deployability goal
in [`ADR-0002`](../../docs/adr/0002-repository-structure.md) §3.
