# Release Notes

## v0.6.1 — 2026-07-16

### Highlights
- **Security hardening** of the QKD key pipeline and enterprise layer.
- **Bug fix**: corrected the insecure Eve-information bound in `key_distilation` (was a linear `qber*2` estimate; now uses binary entropy `h(QBER)`, preventing over-long final keys near the QBER threshold).
- **Honest enterprise layer**: `SoftwareHSM` is explicitly a non-production software simulation.

### What's New
- `core/secure_random.py`: added `secure_sample` / `secure_shuffle` helpers (CSPRNG-backed).
- `integrations/cirq_integration.py`: added `e91_with_cirq()` E91 protocol routine reusing the existing entanglement circuit helper.

### Fixes
- **Insecure RNG in security paths** routed through the CSPRNG:
  - `key_management/advanced_privacy_amplification.py` — subset selection in `xor_extract` (was `random.sample`).
  - `key_management/error_correction.py` — cascade/winnow permutations and LDPC matrix generation (was `random.shuffle`/`random.sample`).
  - `core/channels.py` — protocol-decision basis/gate choice in noise models (was `random.choice`). Physics-noise RNG left unchanged.
  - `protocols/sarg04.py` — QBER test-position selection (was `random.sample`, leaked checked positions).
- **Enterprise HSM** (`enterprise/hsm_interface.py`):
  - AES key derivation switched from raw `sha256(material + hardcoded suffix)` to **PBKDF2-HMAC-SHA256** with a per-key random salt (100k iterations).
  - Keys no longer stored as plaintext; stored wrapped + salt.
  - Cloud/PKCS#11 providers are explicit `NotImplementedError` stubs (not silently advertised).
- **Compliance honesty** (`enterprise/compliance.py`): "FIPS/HSM compliant" is no longer derived from a boolean flag; report states when only the software simulation is active.
- **License truthfulness** (`enterprise/licensing.py`): `set_active_tier` documents that no license key is cryptographically verified in this build.
- **Audit tamper-resistance** (`enterprise/audit.py`): chain links now use a keyed HMAC-SHA256 (in-process secret) instead of a plain hash chain.
- **Removed** dead duplicate `utils/secure_random.py` (byte-identical to `core/secure_random.py`, imported nowhere).
- **Packaging fix**: declare `colorama` (Windows-only) as a dependency and initialize it before structlog's `ConsoleRenderer(colors=True)` — previously a bare `pip install qkdpy` on Windows crashed at import with `SystemError: ConsoleRenderer ... requires the colorama package`.

### Verification
- **549 tests passed, 22 skipped, 0 failures** (`uv run pytest`).
- **mypy** (strict, `src/qkdpy`): no issues in 77 source files.
- **ruff**: all checks passed.
- **Coverage**: 73% (`pytest --cov=qkdpy`).

---

## v0.6.0 — 2026-07-15

### Highlights
- **561 passing tests** — full test suite passes with zero failures
- **New optional dependencies**: `cirq` and `pennylane` integration extras
- **CI-ready**: integration tests now validate all framework imports (Qiskit, Cirq, PennyLane)
- **Documentation overhaul**: expanded API reference, fixed stale URLs, updated version info

### What's New
- Added `[cirq]` and `[pennylane]` optional dependency groups in `pyproject.toml`
- Integration tests for Cirq and PennyLane now run unconditionally
- Expanded API docs covering key_management, ml, network, satellite, crypto, and integrations modules

### Fixes
- `EfficientQKDPredictor.predict()` now consistently returns `float32` (fixes dtype mismatch)
- Removed stale `test_results.txt`, empty `AGENTS.md`, and spurious `package.json`/`package-lock.json`
- Fixed placeholder `yourusername` URLs in `CONTRIBUTING.md` and `installation.md`
- Synced `docs/conf.py` release version with `pyproject.toml` (0.6.0)

---

## v0.2.0 Enterprise Upgrade

### Highlights

- **Enterprise-Grade Network Simulation**: Physically accurate entanglement swapping using `MultiQubitState`.
- **Advanced Machine Learning**: Integration with `scikit-learn` for Bayesian and Neural Network optimization of QKD parameters.
- **Enhanced Security**: Key rotation capabilities and NIST-style randomness verification (Block Frequency Test).
- **Expanded Integrations**: Support for the E91 protocol and realistic loss modeling in Qiskit.

### New Features

- **Network**: `perform_entanglement_swapping` now simulates quantum state teleportation.
- **ML**: `QKDOptimizer` now supports `GaussianProcessRegressor` and `MLPRegressor`.
- **Crypto**: Added `rotate_key` to `QuantumKeyExchange` and `statistical_randomness_test` improvements.
- **Protocols**: Full E91 implementation with Qiskit integration.

### Improvements

- **Performance**: Optimized CV-QKD simulation (~13.4 kbps key rate).
- **Testing**: Comprehensive test suite with 228 passing tests.
- **Documentation**: Updated examples and walkthroughs.

### Breaking Changes

- `QKDOptimizer` now prefers `scikit-learn` if installed.
- `QuantumKeyExchange` session management has been hardened.
