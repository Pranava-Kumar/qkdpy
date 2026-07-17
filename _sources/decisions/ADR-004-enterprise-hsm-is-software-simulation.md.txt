# ADR-004: Enterprise HSM is a Software Simulation

## Status
Accepted

## Date
2026-07-16

## Context
The `enterprise` layer advertises an "HSM" abstraction (`hsm_interface.py`)
with a `HSMProvider` enum listing `SOFTWARE`, `PKCS11`, `AWS_CLOUDHSM`,
`AZURE_HSM`, and `GOOGLE_CLOUD_HSM`. Surrounding machinery
(`licensing.py` tier gating, `compliance.py` checks) presented this as
enterprise-grade. A security audit found the reality diverges from the
presentation in three ways:

1. **Key derivation was not a KDF.** AES-256-GCM keys were derived from
   arbitrary-length key material via raw `hashlib.sha256(key_material + b"qkdpy.hsm.aesgcm")`
   — a hardcoded, non-secret suffix, no salt, no iteration count. An attacker
   holding the (plaintext, in-memory) key material could recompute the AES key
   trivially; the suffix added zero secrecy.
2. **Keys were stored in plaintext in process memory.** `SoftwareHSM` held raw key
   bytes in a plain dict, readable by any in-process code, debugger, or memory dump.
3. **"Compliance" was config-self-reporting.** `compliance.py` derived
   "FIPS/HSM compliant" from a boolean config flag (`enable_hsm`) even when only
   the software simulator was active. Cloud/PKCS#11 providers were unimplemented stubs.

The module already self-labels "NOT FOR PRODUCTION USE", but the naming and the
compliance/licensing machinery risked misleading users into believing keys were
hardware-protected. We needed to make the simulation honest and stop over-claiming.

## Decision
1. **Replace raw-SHA derivation with a real KDF.** `_derive_aes_key(key_material, salt)`
   now uses `PBKDF2HMAC` (SHA-256, 100,000 iterations) with a random 16-byte
   per-key salt generated via `secrets.token_bytes` and stored alongside the key handle.
   The AES-GCM encryption path is unchanged; only the key origin is hardened.
2. **Stop storing/treating keys as hardware-backed.** `SoftwareHSM` stores keys
   wrapped + salt, never plaintext; `close()` behavior unchanged. The cloud/PKCS#11
   provider stubs are explicitly `NotImplementedError` with docstrings clarifying they are
   not implemented in this build.
3. **Make compliance truthful.** `compliance.py` no longer infers hardware
   conformance from a flag. `enable_hsm` records only a *request*; the report states
   when only the software simulation is active that the deployment is NOT
   hardware-backed. `overall_compliant` is computed from actual `critical_failures`,
   not a boolean.
4. **Document licensing as a demo gate.** `licensing.set_active_tier` is
   annotated to state plainly that no license key is cryptographically verified in this
   build — the tier is an in-memory variable the caller controls.
5. **Add keyed-HMAC tamper resistance to the audit chain.** `audit.py`'s
   `compute_hash` now produces an HMAC-SHA256 over the event, keyed by an
   in-process 32-byte secret (`secrets.token_bytes`). This turns the chain from
   corruption-evident into tamper-resistant (a log writer cannot forge chain links
   without the secret).

## Consequences
- The `SoftwareHSM` remains a non-production software simulation; this ADR does NOT
  make it production-safe. It is hardened and honestly labeled.
- Derived AES keys are now salted and iteration-stretched; identical key material with
  different salts yields different AES keys.
- Audit logs resist malicious tampering by an attacker without the in-process secret
  (memory-only default; no persistence unless `storage_path` is supplied).
- Compliance reports will no longer claim hardware-backed FIPS/HSM status when only the
  software simulator is in use.
- Cloud/PKCS#11 HSM backends remain out of scope and will `NotImplementedError`.
