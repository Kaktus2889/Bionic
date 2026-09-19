# Architecture

## Autonomous company loop
START changes durable company state to RUNNING. The worker discovers RUNNING companies from PostgreSQL and obtains a Redis distributed lock per company before a bounded cycle.

Goal -> KPI observation -> Strategy review -> validated Plan -> bounded Task graph -> Agent observe/retrieve/act/reflect -> domain result -> KPI observation -> periodic executive review -> strategy/plan adjustment.

PostgreSQL is authoritative. Redis coordinates locks and Action transport; worker restart does not erase company progress.

## Durable runtime
CompanyCycle has a unique company/tick identity and records phase, status and errors. Plan has a company/cycle key. Actions retain idempotency keys. These invariants make restart recovery safe and prevent duplicate materialization.

Simulation speeds x1/x5/x20/x100 map to bounded scheduler work per pass rather than unbounded recursion.

## Planning and AI
LLMs propose structured PlanProposal data only. Pydantic validates objective, bounded steps, owners and expected outcome. Invalid output receives controlled retry then deterministic fallback. Domain services materialize tasks; raw model text is never executed.

Provider selection is outside the domain: deterministic providers are default/CI; compatible HTTP providers can be enabled by ENV.

## Memory
Memory has a retention gate and bounded retrieval. pgvector stores embeddings. Ranking uses semantic distance plus importance, with deterministic fallback. EmbeddingProvider supports deterministic CI vectors and ENV-configured real HTTP embeddings.

## Observability
Activity is the explanation timeline. The autonomous-loop API combines goal, strategy, plans, KPIs, observations, cycles and timeline. WebSocket is a live projection; persisted state remains authoritative.

## Finance and signals
Posted ledger transactions remain the financial source of truth. KPI measurements derive from Tasks, ledger, Customers and Events. Strategy consumes these signals and recent memory.

## Invariants
- one company cycle per company/tick;
- one plan materialization per strategy cycle key;
- bounded plan size;
- approval before protected Action execution;
- no raw LLM output becomes an Action;
- tenant boundary on autonomous work;
- worker restart must not duplicate durable effects.
