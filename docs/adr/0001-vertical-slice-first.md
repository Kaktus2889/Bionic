# ADR 0001: Vertical slice first

Status: Accepted

Implement a transactional synchronous company tick behind an orchestrator service before distributed scheduling. A Redis worker can invoke the same service later. This proves persistence and domain behavior without duplicating business logic.
