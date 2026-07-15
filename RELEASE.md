# Release Notes

## v0.6.0 — 2026-07-15

### Highlights
- **389 passing tests** — full test suite passes with zero failures
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
