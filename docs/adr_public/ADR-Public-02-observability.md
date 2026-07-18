# Observability & Instrumentation — Public Overview

**Date:** 2026-07-18
**Status:** Active

## Context

A library used for research and for enterprise key-material modeling
needs to be debuggable and operable. Users want to understand how
long a protocol run took, which parameters drove a result, and
where a simulation diverged — without instrumenting their own code.

## Decision

QKDpy ships built-in, structured observability:

- **`OperationSpan`** — a context manager that times any block and
  emits `start` / `complete` / `failure` events with metadata.
- **`@instrument`** — a decorator that automatically records a
  function call with its arguments and outcome.
- **`record_*` helpers** — domain events for protocol execution,
  ML training, and QBER diagnostics.
- **`structlog` backend** — JSON output for log aggregation
  (ELK, Datadog, etc.) or pretty console output for local use.
- **Correlation IDs** — trace a single operation across components.

## Consequences

- Free-tier users get full local debugging and structured logs.
- Enterprise deployments can pipe the same events into their
  existing observability stack.
- No external telemetry leaves the user's environment; the library
  only writes to whatever sink the user configures.

This approach keeps the library transparent: every emitted event is
produced by code in the open-source tree, with no hidden
call-outs.
