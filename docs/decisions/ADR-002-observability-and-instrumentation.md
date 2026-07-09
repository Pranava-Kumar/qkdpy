# ADR-002: Observability and Instrumentation

## Status
Accepted

## Date
2026-07-09

## Context
QKDpy operations (protocol execution, ML training, compliance checks) are
historically silent — they produce results but emit no structured telemetry.
When something goes wrong, debugging means adding print statements and
re-running, because there is no record of what happened or how long it took.

We need:

- **Timing** — How long does each phase of a protocol run take?
- **Structured events** — Machine-readable events (not log prose) that can be
  filtered, aggregated, and alerted on
- **Operation context** — Correlation between related events (which protocol
  run, which config, which QBER)
- **Low ceremony** — Adding telemetry must not require boilerplate

## Decision

Adopt a **context-manager + decorator** pattern built on structlog for
structured event emission.

### Core abstractions

1. **`OperationSpan`** — A context manager that emits `operation_started` on
   entry and `operation_completed` / `operation_failed` on exit, with duration
   in milliseconds.  Accepts static context (kwargs) and dynamic metadata
   (`set_metadata()`).

2. **`@instrument(operation_name)`** — A decorator that wraps a function in an
   `OperationSpan`, automatically capturing arg metadata (keys only, not values,
   to avoid secrets in logs) and optional return-value has-result flags.

3. **`record_*` helpers** — Convenience functions for one-shot events:
   - `record_protocol_execution()` — protocol name, key length, QBER,
     final key size, security verdict, duration
   - `record_ml_training()` — model, input dim, samples, loss,
     convergence iterations
   - `record_qber_diagnostic()` — QBER vs threshold with proximity warning
     level escalation

### Integration pattern

```python
# Context manager for a block
with OperationSpan("protocol.execute", protocol="BB84") as span:
    result = protocol.run()
    span.set_metadata(qber=result.qber)

# Decorator for a method
@instrument("ml.train")
def train_model(self, data):
    ...

# One-shot event
record_qber_diagnostic(protocol="BB84", qber=0.09, threshold=0.11)
```

### Logging backend

All events go through `QKDLogger` (structlog), which renders them as either
pretty-printed console output (dev) or JSON (production).  The structured
fields are preserved in both formats.

### Why structlog over stdlib logging

- Keyword arguments in log calls become structured fields automatically
- JSON renderer for log aggregation (ELK, Datadog, etc.)
- No parsing required — `operation_failed` with `duration_ms` and `error_type`
  is immediately queryable
- Console renderer for human-friendly development output (same API, different
  processor chain)

## Alternatives Considered

### OpenTelemetry SDK
- **Pros:** Industry standard, distributed tracing, metric pipelines
- **Cons:** Heavy dependency for a Python library; designed for microservice
  observability, not in-process operation spans.  Over-engineering for the
  current scale.
- **Deferred:** The `OperationSpan` API is isomorphic to OTel spans — wrapping
  calls in a span with attributes.  Migrating to OTel later means changing the
  backend implementation without changing call sites.

### Manual timing with time.monotonic()
- **Pros:** No abstraction, no dependency
- **Cons:** Scattered `start = time.monotonic()` / `log.info(f"took {end-start}")`
  patterns that are inconsistent, unqueryable, and easy to forget.
- **Rejected:** The context manager pattern is lower ceremony than manual timing.

### print() / logging.debug() with f-strings
- **Pros:** Zero setup
- **Cons:** Unstructured prose cannot be filtered, aggregated, or alerted on.
  `operation_started` as a log event name is queryable; `"Starting operation"`
  as a string is not.
- **Rejected:** Loses all the value of structured logging.

## Consequences

- Adding a new `OperationSpan` or `@instrument` to a function is a one-line
  change with no upstream dependencies.
- Structured events are immediately visible in both console and JSON output
  without configuration changes.
- The lazy imports in ``protocols/base.py`` avoid a circular dependency between
  `protocols.base` → `utils.instrumentation` → `utils.__init__` → `protocols.base`
  (via advanced_quantum_visualization).
