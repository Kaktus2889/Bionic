# Architecture

## Vertical slice
Create Company -> spawn five persistent agents -> Start -> Tick -> Decision + Tasks + Message + Activity -> PostgreSQL -> REST/UI.

## Components
- API: FastAPI/Pydantic transport and transactions.
- Domain: company lifecycle and bounded AgentOrchestrator.
- Persistence: SQLAlchemy 2 + PostgreSQL; UUID keys, FKs, cascades and indexes.
- LLM: provider interface/router; vendor SDKs remain adapters.
- Redis: worker coordination and later WebSocket fanout.
- Web: Next.js dashboard.

## Invariants
Company is the tenant boundary. Agents cannot mutate another company. Autonomous ticks have action/message/LLM budgets. Autonomous mutations are auditable. External side effects will use Action + Permission + Approval. Full histories are never blindly sent to an LLM.

## Phases
Phase 1: Company, Agent, Task, Channel/Message, Decision, Activity, LLMUsage and vertical slice.
Phase 2: Action/Permission, memory, finance, events, worker, WebSocket.
Phase 3: customers, meetings, market simulation, pgvector retrieval, hiring, analytics.
