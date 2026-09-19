# ADR 0003: Durable autonomous workflow

Status: Accepted

Events, customers, meetings, actions, memories and ledger entries are durable PostgreSQL state. Redis is transport only and never authoritative.

Events use company-scoped idempotency keys and route into real tasks plus memory. Meetings execute participant contributions from bounded retrieved context and persist a Decision plus action item.

Actions use an explicit state machine. Approval-required actions cannot enter the queue until approved. Redis carries only action IDs; workers reload and lock authoritative state before execution. Attempts and Activity form the audit trail. Execution is idempotent at terminal success and retryable before the configured limit.

Memory retention uses an importance/content gate. Retrieval is bounded and ranked deterministically without an external embeddings dependency. This keeps CI deterministic while leaving pgvector available for a future embedding adapter.

Finance uses posted ledger transactions as the source of truth. Account.balance and Company.cash are retained only for backward schema/API compatibility and are not mutated by FinanceEngine v2. Transfers net to zero; pending/void entries do not affect balance.
