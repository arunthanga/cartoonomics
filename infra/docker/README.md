# `infra/docker` (scaffold)

Dockerfiles (one per deployable: `apps/api`, `apps/web`, `services/orchestrator`)
and a `docker-compose.yml` that stands up the full local stack — service images
plus PostgreSQL/TimescaleDB and an S3-compatible object store (e.g. MinIO) —
for development and CI. Reproducible envs are the goal (ADR-0001 §1).
