# ADR 0005: Durable autonomous runtime

Status: Accepted

Bionic schedules companies from durable PostgreSQL RUNNING state rather than ephemeral timers. Redis provides a per-company distributed lock, while CompanyCycle unique company/tick identity provides database-level idempotency.

Each cycle measures domain-derived KPIs, reviews strategy, materializes at most one bounded validated plan for a strategy cycle, advances agent work, reflects only on meaningful completion, re-measures KPIs, and records Activity.

LLMs are advisory. Structured PlanProposal output is Pydantic-validated with controlled retry and deterministic fallback. Permission/Action services remain the authority for side effects.

KPI observations are append-only time-series records. Strategy revisions persist reason, signals, previous/new strategy and expected effect.

Memory semantic retrieval uses pgvector through an EmbeddingProvider. Deterministic embeddings are the CI/default fallback; real HTTP-compatible embedding endpoints are configured only through environment variables.
