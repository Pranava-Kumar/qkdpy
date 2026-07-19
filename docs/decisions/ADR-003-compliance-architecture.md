# ADR-003: Enterprise Config Audit Architecture

## Status
Accepted (class renamed from `ComplianceChecker` → `ConfigAudit` post-hoc; the architecture is unchanged)

## Date
2026-07-09

## Context
QKD deployments increasingly require compliance with emerging standards:

- **ETSI GS QKD 014** — KME-SA Interface (key delivery, authentication, status)
- **ETSI GS QKD 016** — Common Criteria Protection Profile (security target, audit)
- **ISO/IEC 23837-1/2** — QKD Security Requirements (key length, QBER thresholds)
- **NIST SP 800-57** — Key Management (key length, algorithm lifetime)
- **FIPS 140-2/140-3** — Cryptographic Module (approved algorithms, module integrity)
- **ISO 27001** — Information Security (access control, logging, crypto policy)

We need a compliance engine that:

- Runs a checklist of checks against QKDpy configuration
- Supports multiple standards with different check sets
- Produces structured reports (summary, per-check pass/fail, severity, recommendations)
- Can be extended without modifying the checker (new standards = new check lists)
- Exports to multiple formats (Markdown, HTML, JSON)

## Decision

Build a **pluggable config audit** with a `(standard) → list[checks]`
dispatch pattern.

### Architecture

```
ConfigAudit
│
├─ _check_etsi_qkd_014()         → list[ComplianceCheck]
├─ _check_etsi_qkd_016()         → list[ComplianceCheck]
├─ _check_iso_23837()            → list[ComplianceCheck]   (shared for 23837-1 and 23837-2)
├─ _check_nist_800_57()          → list[ComplianceCheck]
├─ _check_fips_140_2()           → list[ComplianceCheck]
└─ _check_iso_27001()            → list[ComplianceCheck]
```

Each `_check_*` method is a pure function that takes config and returns a list
of `ComplianceCheck` results.  The `ConfigAudit.check_compliance()` method
iterates the requested standards and dispatches via an ``if/elif`` chain to the
appropriate method, aggregating results into a `ComplianceReport`.

### Report structure

```
ComplianceReport
├─ report_id            ← str (hex token, 16 chars)
├─ generated_at         ← datetime
├─ standards_checked    ← list[ComplianceStandard]
├─ checks               ← list[ComplianceCheck]
│                        (check_id, requirement, description, passed,
│                         severity, details, recommendation)
├─ overall_compliant    ← bool (False if any CRITICAL or HIGH fails)
├─ passed_checks        ← int
├─ failed_checks        ← int
├─ get_failed_checks()  → filter
├─ get_summary()        → dict
├─ export_markdown()    → str
└─ export_html()        → str
```

### Check design

Each check has a stable `check_id` (e.g., `ETSI-014-001`), a human-readable
`requirement`, a `description`, a `severity` (critical/high/medium/low), and
a `recommendation` for remediation.  This ensures reports are actionable, not
just diagnostic.

### Product tier gating

Compliance checking is gated behind `Feature.COMPLIANCE_REPORTING` (ENTERPRISE)
and `Feature.COMPLIANCE_HTML_EXPORT` (ENTERPRISE) via the
`require_feature` decorator.  FREE-tier users cannot generate compliance
reports.

## Alternatives Considered

### Plugin-based (register standards via entry points)
- **Pros:** Third-party standards without modifying core
- **Cons:** Premature extensibility — we know all the standards we need to
  support for v1.  Plugins add complexity in discovery, validation, and error
  handling.
- **Rejected:** YAGNI.  Will revisit when a user requests a custom standard.

### YAML/DSL-defined checks (declarative, not code)
- **Pros:** Non-developers can add checks
- **Cons:** Every check evaluates Python objects (config dataclasses) against
  Python conditions.  A YAML DSL would need to reimplement Python expressions,
  or we'd end up with a `lambda: field` escaping mechanism that's harder to
  read than just writing Python.
- **Rejected:** Code-defined checks are simpler, more powerful, and equally
  testable.

## Consequences

- Adding a new standard requires writing one `_check_*` method and adding a
  new entry to the dispatch ``if/elif`` chain.  No base class changes needed.
- Report exporters are methods on `ComplianceReport`, not separate classes,
  because the report is a data container with no serialisation logic of its
  own.  If export formats proliferate (>5), extract to a `renderers/` package.
- The compliance engine is enterprise-gated but the core check logic has no
  licensing awareness — it returns results and lets the caller apply access
  control.  This keeps the engine testable in unit tests without setting a
  premium tier.
