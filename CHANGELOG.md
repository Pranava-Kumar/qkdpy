# Changelog

All notable changes to this project are documented here.

## [0.6.1] - 2026-07-16

### Security

- Routed insecure RNG in security-critical paths through the CSPRNG:
  - `key_management/advanced_privacy_amplification.py` — subset selection in `xor_extract` (was `random.sample`).
  - `key_management/error_correction.py` — cascade/winnow permutations and LDPC matrix generation (was `random.shuffle`/`random.sample`).
  - `core/channels.py` — protocol-decision basis/gate choice in noise models (was `random.choice`; physics-noise RNG left unchanged).
  - `protocols/sarg04.py` — QBER test-position selection (was `random.sample`, which leaked checked positions).
- Hardened the enterprise HSM (`enterprise/hsm_interface.py`): AES key derivation switched from `sha256(material + hardcoded suffix)` to PBKDF2-HMAC-SHA256 with a per-key random salt (100k iterations); keys now stored wrapped + salt; Cloud/PKCS#11 providers are explicit `NotImplementedError` stubs.
- Made `SoftwareHSM` explicitly a non-production software simulation.
- Made compliance reporting honest (`enterprise/compliance.py`): "FIPS/HSM compliant" is no longer derived from a boolean flag; the report states when only the software simulation is active.
- Made license truthfulness explicit (`enterprise/licensing.py`): `set_active_tier` documents that no license key is cryptographically verified in this build.
- Added tamper-resistance to the audit chain (`enterprise/audit.py`): links now use a keyed HMAC-SHA256 (in-process secret) instead of a plain hash chain.

### Added

- `core/secure_random.py`: `secure_sample` / `secure_shuffle` helpers (CSPRNG-backed).
- `integrations/cirq_integration.py`: `e91_with_cirq()` E91 protocol routine reusing the existing entanglement circuit helper.

### Fixed

- Corrected the insecure Eve-information bound in `key_distilation`: was a linear `qber*2` estimate, now uses binary entropy `h(QBER)`, preventing over-long final keys near the QBER threshold.
- Declared `colorama` (Windows-only) as a dependency and initialized it before structlog's `ConsoleRenderer(colors=True)` — previously a bare `pip install qkdpy` on Windows crashed at import with `SystemError: ConsoleRenderer ... requires the colorama package`.
- Removed dead duplicate `utils/secure_random.py` (byte-identical to `core/secure_random.py`, imported nowhere).

## [0.6.0] - 2026-07-15

### Added

- Optional `[cirq]` and `[pennylane]` dependency groups in `pyproject.toml`.
- Integration tests for Cirq and PennyLane now run unconditionally (CI-ready framework import validation).
- Expanded API documentation covering key_management, ml, network, satellite, crypto, and integrations modules.

### Fixed

- `EfficientQKDPredictor.predict()` now consistently returns `float32` (fixes dtype mismatch).
- Removed stale `test_results.txt`, empty `AGENTS.md`, and spurious `package.json`/`package-lock.json`.
- Fixed placeholder `yourusername` URLs in `CONTRIBUTING.md` and `installation.md`.
- Synced `docs/conf.py` release version with `pyproject.toml` (0.6.0).

## [0.2.0] - Enterprise Upgrade

### Added

- Enterprise-grade network simulation: physically accurate entanglement swapping using `MultiQubitState` (`perform_entanglement_swapping` now simulates quantum state teleportation).
- Machine learning integration with `scikit-learn` for Bayesian and Neural Network QKD parameter optimization (`QKDOptimizer` now supports `GaussianProcessRegressor` and `MLPRegressor`).
- Enhanced security: key rotation (`rotate_key` on `QuantumKeyExchange`) and NIST-style randomness verification (Block Frequency Test).
- Full E91 protocol implementation with Qiskit integration, plus realistic loss modeling.

### Changed

- CV-QKD simulation performance optimized (~13.4 kbps key rate).
- `QKDOptimizer` now prefers `scikit-learn` if installed.
- `QuantumKeyExchange` session management hardened.

See [RELEASE.md](RELEASE.md) for full release notes.
