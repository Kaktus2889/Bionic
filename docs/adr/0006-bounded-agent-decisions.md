# ADR 0006: Bounded agent decision pipeline

Status: Accepted

Agents never receive unrestricted company state or execute raw LLM output. ObservationBuilder applies role scope. IntentPlanner accepts only Pydantic ActionIntent arrays and falls back deterministically after controlled failures. ActionEvaluator selects among candidates; ActionPolicy and PermissionEngine remain authoritative for tools, permissions, budget, duplicates, confidence/risk and delegation bounds.

Decision traces persist concise rationale and evidence, not hidden chain-of-thought. ActionResult feeds the next observation. Meaningful reflection may propose typed memory or a strategy signal but cannot execute actions. InformationRequest is the durable mechanism for missing evidence.

This design intentionally prefers requesting information, review or escalation over risky low-confidence execution.
