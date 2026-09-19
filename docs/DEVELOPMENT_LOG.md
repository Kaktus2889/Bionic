# Development Log

## 2026-09-19
- Confirmed Bionic was empty.
- Added architecture and ADR.
- Added PostgreSQL/pgvector + Redis Docker stack.
- Added FastAPI/SQLAlchemy/Alembic backend foundation.
- Added persistent Company/Agent/Task/Message/Decision/Activity/LLMUsage model design.
- Added deterministic five-agent bootstrap and bounded vertical-slice tick.
- Added minimal Next.js dashboard.
- Added API vertical-slice test.

Next: runtime/CI verification, WebSocket feed, Action/Permission engine, worker, memory and finance ledger.

## 2026-09-19 — Phase 2 foundation verified in CI
- Added GitHub Actions with PostgreSQL/pgvector + Redis services, Alembic upgrade/downgrade/upgrade verification, pytest, correctness lint gate, and Next.js production build.
- Added ActionEngine and role-based PermissionEngine with autonomy-aware approval decisions.
- Added persistent Memory model/service and company-goal memory bootstrap.
- Added CompanyAccount + Transaction ledger and FinanceEngine; initial capital is recorded as a non-simulated ledger entry.
- Added Redis queue worker boundary and WebSocket activity endpoint.
- Added migration 0002 and ADR 0002.
- CI failures found and fixed: setuptools discovered alembic as a package; SQLite in-memory tests used different connections; lint policy initially mixed formatting debt with correctness.
- Verified GitHub Actions run 35416836550: backend success, web success. Backend executed Alembic upgrade -> downgrade base -> upgrade head, pytest (2 passed), correctness Ruff checks; web production build passed.

Next: Event Engine + customer/meeting primitives, worker integration tests, WebSocket test, approval execution lifecycle, richer finance metrics and semantic-memory retrieval.

## 2026-09-19 — Autonomous loop expansion (verification pending)\n- Added durable Event Engine with routing, deduplication, retries and task/activity effects.\n- Added CRM customer/interactions/notes and context-to-memory flow.\n- Added executable meetings producing contributions, Decisions and action items.\n- Expanded Action lifecycle with approval, queueing, attempts, cancellation, retries and idempotency.\n- Redis worker now executes queued Actions; PostgreSQL remains authoritative.\n- Memory retrieval is bounded/ranked with retention gate and domain references.\n- Finance v2 derives balances/P&L from posted ledger entries; legacy mutable balance fields are no longer written.\n- Added APIs/dashboard observability and reconnecting Live Activity.\n- Added full autonomous-loop integration test using real CI PostgreSQL + Redis and WebSocket.\n- Added ADR 0003.\n\nCI verification follows; failures and fixes will be recorded before this milestone is marked verified.\n