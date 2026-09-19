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
## 2026-09-19 — Autonomous loop verified; roadmap advanced
- CI exposed two real defects: metadata-based historical bootstrap made 0003 see already-present columns, and ledger reads missed unflushed writes because sessions disable autoflush. Migration evolution was made compatibility-aware and ledger writes now flush before derived balance checks.
- Full CI run 35417252804 passed after the autonomous-loop fixes.
- Advanced roadmap into Goal Engine / Strategy / KPI foundation: durable Goal and KPI models, migration 0004, goal bootstrap, deterministic StrategyEngine evaluation and API/test coverage.
- CI then caught malformed migration source formatting in 0004; corrected it.
- Verified run 35417363691: Alembic upgrade -> downgrade base -> upgrade head, 4 pytest tests passed, Ruff correctness checks passed, frontend production build passed.

Next: recurring Scheduler operations, KPI time-series analytics, strategy reactions to Event/Finance/Customer signals, then LLM-backed planning behind the existing provider/router boundary.

## 2026-09-19 — Multi-cycle autonomous runtime
- START now persists RUNNING state consumed by the worker scheduler; PAUSED and ERROR are durable lifecycle states. x1/x5/x20/x100 are bounded scheduler work rates.
- Added Redis distributed company-cycle locking plus durable CompanyCycle idempotency, so worker restarts resume from PostgreSQL instead of ephemeral scheduler state.
- Added KPIObservation time series derived from tasks, ledger, customers and events: task completion, revenue, expenses, cash, burn, runway, customer count/satisfaction, churn and open critical events.
- Added persisted StrategyRevision with reason/signals/previous/new strategy/expected effect and periodic company review.
- Added bounded Plan domain and structured Pydantic PlanProposal. LLM proposes; domain validates and materializes a bounded task graph. Deterministic provider is CI/default; ENV-configured compatible HTTP provider is optional.
- Added AgentRuntime observe/retrieve/task transition/meaningful reflection loop. Reflection memory is only retained for completed meaningful work.
- Added autonomous-loop API and dashboard explanation timeline.
- Added pgvector memory embeddings behind EmbeddingProvider, with deterministic vectors for CI and real provider configuration by ENV.
- Added multi-cycle autonomy and crash-recovery tests.
- CI run 35417745225 found a backward-compatibility regression: the prior goal test expected a goal-linked KPI. Restored that invariant; run 35417794151 passed.
- pgvector rollout then exposed historical migration ordering: 0001 metadata bootstrap referenced Vector before extension creation. Fixed by enabling vector before metadata creation and making 0006 compatibility-aware. Run 35417935272 passed after the fix.

The autonomous runtime is intentionally bounded: no HR/payroll/market expansion was added. Next depth work should improve real agent ActionIntent planning, KPI trend windows and richer strategy policies rather than adding unrelated domains.
