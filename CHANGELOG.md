# Changelog

All notable changes to this project are documented here.

## [0.7.1] - 2026-07-20

### Added

- `ChannelBase` abstract base class in `core/channel_base.py` defining the contract (`transmit`, `get_statistics`, `reset_statistics`, `transmit_batch`, `set_eavesdropper`) for all channel implementations. `QuantumChannel` now inherits from it.
- `py.typed` marker for PEP 561 compliance, enabling downstream type checkers.
- Dedicated tests for `ChannelBase` ABC, `_require_sdk()` guard, MD5/SHA-1 rejection, and fidelity-based `entanglement_attack` detection.

### Changed

- **Star imports replaced** — `__init__.py` now uses explicit named imports from each subpackage instead of `from .X import *`, improving IDE navigation and static analysis.
- `BaseProtocol._cascade_error_correction` now delegates to `ErrorCorrection.cascade()` (multi-pass with random permutations) instead of a simplified single-pass duplicate.
- `BaseProtocol._universal_hashing_privacy_amplification` now delegates to `PrivacyAmplification.universal_hashing()`.
- `PrivacyAmplification.toeplitz_hashing` now accepts an optional `seed` parameter for reproducible audit runs, matching `universal_hashing`'s API.
- `EfficientQKDPredictor` uses a per-instance `np.random.Generator` (seeded from CSPRNG) instead of the global numpy RNG, making ML results reproducible.
- `QuantumChannel` constructor now raises `ValueError` for unknown `noise_model` values instead of silently ignoring them.

### Fixed

- **Version mismatch** — `__init__.__version__` now matches `pyproject.toml` (`0.7.1`).
- **QpiAI bridge crashes** — `Circuit`/`Statevector` methods now raise a clear `QpiAISDKError("Install with: pip install qkdpy[qpiai]")` instead of `TypeError: 'NoneType' object is not callable`.
- **Insecure RNG in physics noise** — `channels.py` `_apply_polarization_drift` and `_apply_phase_fluctuations` now use `secure_normal()` instead of `np.random.normal`. `extended_channels.py` uses `secure_choice` instead of `random.choice`.
- **Weak hash rejection** — `PrivacyAmplification.cryptographic_hash()` rejects `sha1` and `md5` with `ValueError` (collision vulnerabilities); added `sha384`, `blake2b`, `blake2s` as accepted algorithms.
- **Entanglement attack detection** — `QuantumChannel.entanglement_attack()` detection probability is now computed from the physical fidelity between pre/post-attack states (`disturbance = 1 - fidelity`), matching the theoretical 25% BB84 error bound, instead of a random coin flip.
- **Type annotation consistency** — `multiqubit.py` uses `from __future__ import annotations` and `X | None` syntax instead of `Optional[X]`.
- **LDPC divide-by-zero warning** — `ErrorCorrection.ldpc()` now clamps the `arctanh` argument to `(-1+ε, 1-ε)`, eliminating the `RuntimeWarning: divide by zero encountered in arctanh`.
- **PyPI classifier mismatch** — Removed `Programming Language :: Python :: 3.10` from classifiers (requires-python is `>=3.11`).
- **mypy visualization overrides removed** — `visualization.py` and `advanced_visualization.py` now pass type checking; the `ignore_errors = true` overrides have been removed from `pyproject.toml`.

## [0.7.0] - 2026-07-20

### Added

- **qpiai-qkd companion subpackage** (`qkdpy[qpiai]`) — standalone, pip-installable integration between qkdpy QKD protocols and the QpiAI Quantum SDK:
  - `QpiAIIntegration` bridge: protocol↔SDK mapping (BB84, E91, entanglement, GHZ), Qubit/Statevector conversion, local simulation with graceful no-key fallback, cloud submission via real `JobManager.submit_and_wait_for_results_qasm`
  - Wootters concurrence (`_compat.concurrence()`) computed from first principles (spin-flip formula) — does not rely on the SDK's absent `DensityMatrix.concurrence()`
  - `QPIAI_API_KEY`→`API_KEY` context manager (`_SdkKeyContext`) for SDK credential compatibility
  - IEC/ETSI-aligned interchange model: `KeyRequest`, `KeyDelivery` (ETSI GS QKD 014), `SAE2EStatus` (ETSI GS QKD 015), `ProtocolExchange` — all with `to_json()`/`from_json()`
  - Satellite/atmospheric physics mapping (`LinkPhysics`, `map_satellite_link`) wrapping `SatelliteQKD`, `FreeSpaceOpticalChannel`, MODTRAN, and Hufnagel-Valley turbulence
  - ML optimizer bridge (`OptimizerResult`, `optimize_protocol`, `detect_anomaly`) wrapping `QKDOptimizer`/`QKDAnomalyDetector`
  - Companion README (`README.qpiai-qkd.md`): protocols, physics, bridge, optimizer, interchange, install — Product Tiers below the fold
- **Enterprise hardening**:
  - `licensing.set_active_tier()` now refuses tiers with no valid license key (raises `LicenseError` instead of silently passing)
  - `ConfigAudit` (renamed from `ComplianceChecker`) — honest naming; the class does config auditing, not external compliance certification
  - `_hsm_is_hardware_backed()` now implements a real capability check against `HSMProvider` instead of always returning `False`
- `OptimizerResult`, `AnomalyReport`, and `ParameterHistoryEntry` TypedDicts for typed optimizer results
- `COMMERCIAL_NOTICE.md` — extracted from LICENSE (Apache-2.0 now stands alone at clean 199 lines)

### Fixed

- `Statevector(circuit)` `ValueError` caught when `API_KEY` is unset — falls back to inspection metadata instead of crashing
- `submit_to_cloud()` uses real `JobManager.submit_and_wait_for_results_qasm()` instead of the nonexistent `run_circuit`
- CHSH correlation formula corrected to standard 4-angle form: `S = cos(a-b) + cos(a-b') + cos(a'-b) - cos(a'-b')`
- QBER test assertion corrected from 0.5 to 0.25 (one mismatch in four bits)
- `py.typed` marker shipped for the companion subpackage
- Dependabot vulnerabilities and CodeQL alerts resolved
- CodeQL taint flow broken for clear-text logging in example

### Changed

- `integrations/qpiai_integration.py` rewritten as thin shim importing from `qpiai_qkd.bridge`
- Main README tagline: "Enterprise Compliance" → "config audit tooling"
- Product Tiers section moved below the fold (after Quick Start + ADRs)
- Enterprise feature descriptions in Features table amended with honesty qualifiers
- `founder-plan.md` checkpoint items marked done for enterprise hardening tasks
- ADR-003 title updated to "Enterprise Config Audit Architecture" with rename note
- Type-check runner bumped to Python 3.12

### Removed

- Stale `ComplianceChecker` references replaced with `ConfigAudit` across docs, ADRs, and source

### Added

- Raised test coverage from 73% to 85%: 325+ new tests across 10+ test files
- Added coverage tests for timing (17 tests, 32%→85%), crypto (20 tests, ~40%→90%+), extended_channels (12 tests, 59%→94%), gate_utils, helpers, qudit, measurements, network_core_extended (78 tests), qpiai_privacy (56 tests)
- Added `colorama>=0.4.6` as Windows dependency to fix import crash with structlog's `ConsoleRenderer(colors=True)`
- Added `qiskit` and `qpiai` optional extras to `pyproject.toml`
- `CHANGELOG.md`: initial Keep-a-Changelog format

### Fixed

- Windows import crash: `colorama.init()` now called before structlog `ConsoleRenderer` initialization
- PennyLane integration: replaced noise no-op with real `qml.NoiseModel` + `DepolarizingChannel` on `default.mixed`
- QpiAI `simulate()`: now performs full statevector → probability → bitstring sampling when API key is present
- Pre-commit: widened exclude pattern for `scripts/blackbox/` diagnostic scripts

### Removed

- Orphaned root-level diagnostic artifacts: `benchmarks/ml_vs_bruteforce.py`, `compile_comprehensive_report.py`, `compile_results.py`

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
