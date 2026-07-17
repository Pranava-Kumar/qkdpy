# API Reference

## Core Module

### Qubit

```{eval-rst}
.. autoclass:: qkdpy.core.qubit.Qubit
   :members:
   :undoc-members:
   :show-inheritance:
```

### Quantum Gate

```{eval-rst}
.. autoclass:: qkdpy.core.gates.QuantumGate
   :members:
   :undoc-members:
   :show-inheritance:
```

### Quantum Channel

```{eval-rst}
.. autoclass:: qkdpy.core.channels.QuantumChannel
   :members:
   :undoc-members:
   :show-inheritance:
```

### Measurement

```{eval-rst}
.. autoclass:: qkdpy.core.measurements.Measurement
   :members:
   :undoc-members:
   :show-inheritance:
```

### Secure Random

```{eval-rst}
.. automodule:: qkdpy.core.secure_random
   :members:
   :undoc-members:
   :show-inheritance:
```

CSPRNG-backed `secure_sample` and `secure_shuffle` helpers for security-critical paths (v0.6.1).

## Protocols Module

### BB84

```{eval-rst}
.. autoclass:: qkdpy.protocols.bb84.BB84
   :members:
   :undoc-members:
   :show-inheritance:
```

### HDQKD

```{eval-rst}
.. autoclass:: qkdpy.protocols.hd_qkd.HDQKD
   :members:
   :undoc-members:
   :show-inheritance:
```

## Enterprise Module

### Licensing

```{eval-rst}
.. automodule:: qkdpy.enterprise.licensing
   :members:
   :undoc-members:
   :show-inheritance:
```

### Compliance

```{eval-rst}
.. automodule:: qkdpy.enterprise.compliance
   :members:
   :undoc-members:
   :show-inheritance:
```

### Quantum-Safe Migration

```{eval-rst}
.. automodule:: qkdpy.enterprise.quantum_safe
   :members:
   :undoc-members:
   :show-inheritance:
```

### HSM Interface

```{eval-rst}
.. automodule:: qkdpy.enterprise.hsm_interface
   :members:
   :undoc-members:
   :show-inheritance:
```

### Audit Logging

```{eval-rst}
.. automodule:: qkdpy.enterprise.audit
   :members:
   :undoc-members:
   :show-inheritance:
```

## Utilities Module

### Instrumentation

```{eval-rst}
.. automodule:: qkdpy.utils.instrumentation
   :members:
   :undoc-members:
   :show-inheritance:
```

## Key Management Module

### Quantum Key Manager

```{eval-rst}
.. automodule:: qkdpy.key_management.key_manager
   :members:
   :undoc-members:
   :show-inheritance:
```

### Advanced Error Correction

```{eval-rst}
.. automodule:: qkdpy.key_management.advanced_error_correction
   :members:
   :undoc-members:
   :show-inheritance:
```

### Key Distillation

```{eval-rst}
.. automodule:: qkdpy.key_management.key_distillation
   :members:
   :undoc-members:
   :show-inheritance:
```

Post-processing pipeline including the binary entropy Eve bound (`h(QBER)`) fix applied in v0.6.1.

## Network Module

### Quantum Network

```{eval-rst}
.. automodule:: qkdpy.network.quantum_network
   :members:
   :undoc-members:
   :show-inheritance:
```

## Machine Learning Module

### QKD Optimizer

```{eval-rst}
.. automodule:: qkdpy.ml.qkd_optimizer
   :members:
   :undoc-members:
   :show-inheritance:
```

### Efficient Models

```{eval-rst}
.. automodule:: qkdpy.ml.efficient_models
   :members:
   :undoc-members:
   :show-inheritance:
```

### Knowledge Distillation

```{eval-rst}
.. automodule:: qkdpy.ml.knowledge_distillation
   :members:
   :undoc-members:
   :show-inheritance:
```

## Integrations Module

### Qiskit Integration

```{eval-rst}
.. automodule:: qkdpy.integrations.qiskit_integration
   :members:
   :undoc-members:
   :show-inheritance:
```

### Cirq Integration

```{eval-rst}
.. automodule:: qkdpy.integrations.cirq_integration
   :members:
   :undoc-members:
   :show-inheritance:
```

Includes `e91_with_cirq()` for entanglement-based E91 protocol simulation (added v0.6.1).

### PennyLane Integration

```{eval-rst}
.. automodule:: qkdpy.integrations.pennylane_integration
   :members:
   :undoc-members:
   :show-inheritance:
```

Noise model support via `qml.NoiseModel` with `DepolarizingChannel` on `default.mixed` device (v0.6.2).

### QpiAI Integration

```{eval-rst}
.. automodule:: qkdpy.integrations.qpiai_integration
   :members:
   :undoc-members:
   :show-inheritance:
```

QpiAI Quantum SDK bridge with circuit conversion, BB84/E91 circuits, and statevector simulation with CSPRNG-backed probability sampling (v0.6.1, v0.6.2).

## Crypto Module

### Encryption

```{eval-rst}
.. automodule:: qkdpy.crypto.encryption
   :members:
   :undoc-members:
   :show-inheritance:
```

### Decryption

```{eval-rst}
.. automodule:: qkdpy.crypto.decryption
   :members:
   :undoc-members:
   :show-inheritance:
```

### Authentication

```{eval-rst}
.. automodule:: qkdpy.crypto.authentication
   :members:
   :undoc-members:
   :show-inheritance:
```

### Key Exchange

```{eval-rst}
.. automodule:: qkdpy.crypto.key_exchange
   :members:
   :undoc-members:
   :show-inheritance:
```

## Project Files

- `CHANGELOG.md` — Release history in Keep-a-Changelog format (added v0.6.2)
