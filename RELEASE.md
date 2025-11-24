# Release Notes - v0.2.0 Enterprise Upgrade

## Highlights

- **Enterprise-Grade Network Simulation**: Physically accurate entanglement swapping using `MultiQubitState`.
- **Advanced Machine Learning**: Integration with `scikit-learn` for Bayesian and Neural Network optimization of QKD parameters.
- **Enhanced Security**: Key rotation capabilities and NIST-style randomness verification (Block Frequency Test).
- **Expanded Integrations**: Support for the E91 protocol and realistic loss modeling in Qiskit.

## New Features

- **Network**: `perform_entanglement_swapping` now simulates quantum state teleportation.
- **ML**: `QKDOptimizer` now supports `GaussianProcessRegressor` and `MLPRegressor`.
- **Crypto**: Added `rotate_key` to `QuantumKeyExchange` and `statistical_randomness_test` improvements.
- **Protocols**: Full E91 implementation with Qiskit integration.

## Improvements

- **Performance**: Optimized CV-QKD simulation (~13.4 kbps key rate).
- **Testing**: Comprehensive test suite with 228 passing tests.
- **Documentation**: Updated examples and walkthroughs.

## Breaking Changes

- `QKDOptimizer` now prefers `scikit-learn` if installed.
- `QuantumKeyExchange` session management has been hardened.
