# `infra/terraform` (scaffold)

Infrastructure as code for the managed cloud resources: the PostgreSQL canonical
store (§13), TimescaleDB / partitioned tables for price & NAV series, the
S3-compatible object store for immutable raw filings (TA-1, FR-1.5), and any
queues used by `services/orchestrator`. Secrets stay environment-driven (TA-4).
