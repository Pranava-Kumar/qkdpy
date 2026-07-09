# ADR-001: Product Tier Licensing Model

## Status
Accepted

## Date
2026-07-09

## Context
QKDpy is evolving from a pure open-source simulation library into a tiered commercial product. We need a mechanism to:

- Define which features belong to which product tier (FREE / ENTERPRISE / PREMIUM)
- Gate features at runtime so unlicensed callers get a clear error instead of silent degradation
- Support license key activation without code changes
- Make the tier visible to tooling, tests, and configuration

The tier model must be **cumulative** (each tier includes everything in the tier below it)
so that upgrading is additive and there are no "holes" in the feature matrix.

## Decision

Introduce a lightweight **feature-flag-as-code** module (`enterprise/licensing.py`)
with three core concepts:

1. **`ProductTier` enum** — `FREE`, `ENTERPRISE`, `PREMIUM` (in ascending order)
2. **`Feature` enum** — One member per gateable feature (e.g., `COMPLIANCE_REPORTING`,
   `QUANTUM_SAFE_MIGRATION`).  Each feature belongs to exactly one tier.
3. **`require_feature(feature)` decorator** — Wraps any function; raises `LicenseError`
   at call time if the feature is not available in the current tier. The error message
   includes the required tier name.

A module-level `TIER_FEATURES` dict maps `ProductTier → set[Feature]` and is the
single source of truth for tier membership.  The active tier is stored as a module
global and defaults to `FREE`.

### Configuration integration

`EnterpriseConfig.product_tier` is a string field read from the `QKDPY_PRODUCT_TIER`
environment variable or `set_config()`.  `set_config()` automatically calls
`set_active_tier()` so the licensing module stays in sync without manual
coordination.

### Usage pattern

```python
@require_feature(Feature.COMPLIANCE_HTML_EXPORT)
def export_html(self) -> str:
    ...
```

A FREE-tier caller gets:

```
LicenseError: 'compliance_html_export' requires the Enterprise tier or higher.
Current tier: free
```

## Alternatives Considered

### Separate packages (qkdpy-free / qkdpy-enterprise / qkdpy-premium on PyPI)
- **Pros:** Clear separation, no runtime gating logic needed
- **Cons:** Massive maintenance overhead (three packages, three release pipelines).
  Impossible to trial upgrade without reinstall.  Breaks `pip install qkdpy[enterprise]`
  patterns users expect.
- **Rejected:** Too operationally expensive for the value.

### License server with remote validation
- **Pros:** Harder to crack, central enforcement, usage analytics
- **Cons:** Requires network access, introduces a single point of failure,
  over-engineering for a library that runs primarily in dev/on-prem environments.
- **Deferred:** Can be added as an optional `LicenseValidator` plugin without
  changing any of the decorator call sites, since `set_active_tier()` is the
  only entry point.

### Configuration-based gating (if config.x then enable)
- **Pros:** No decorator boilerplate
- **Cons:** Scattered `if config.enterprise.enable_hsm` checks throughout the
  codebase. Easy to miss a gate. No way to audit what features are available
  programmatically (`feature_available(Feature.X)`).  Not self-documenting.
- **Rejected:** The decorator is explicit, searchable, and testable.

## Consequences

- Every enterprise/premium feature is **opt-in at call time** — FREE users can
  reference enterprise modules without errors; only execution is blocked.
- Adding a new tiered feature requires: (1) adding a `Feature` enum member,
  (2) adding it to the right tier's set in `TIER_FEATURES`, (3) decorating the
  entry point function.
- The module global is not thread-safe for runtime tier switching, but tier is
  set once at startup (via config) and never hot-swapped in practice.
- A CLI or dashboard can call `feature_available(Feature.X)` to report tier
  status without executing any gated code.
