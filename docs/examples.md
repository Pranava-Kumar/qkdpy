# Examples

## Advanced Usage

QKDpy also supports advanced protocols and features:

```python
from qkdpy import (
    DeviceIndependentQKD,
    QuantumKeyManager,
    QuantumRandomNumberGenerator,
    QuantumNetwork,
    HDQKD,
    QKDOptimizer
)

# Device-independent QKD
di_qkd = DeviceIndependentQKD(channel, key_length=100)
results = di_qkd.execute()

# Quantum key management
key_manager = QuantumKeyManager(channel)
key_id = key_manager.generate_key("secure_session", key_length=128)

# Quantum random number generation
qrng = QuantumRandomNumberGenerator(channel)
random_bits = qrng.generate_random_bits(100)

# Quantum network simulation
network = QuantumNetwork("Research Network")
network.add_node("Alice")
network.add_node("Bob")
network.add_connection("Alice", "Bob", channel)
key = network.establish_key_between_nodes("Alice", "Bob", 128)

# High-dimensional QKD
hd_qkd = HDQKD(channel, key_length=100, dimension=4)
hd_results = hd_qkd.execute()

# ML-based QKD optimization
optimizer = QKDOptimizer("BB84")
parameter_space = {
    "loss": (0.0, 0.5),
    "noise_level": (0.0, 0.1)
}
# optimization_results = optimizer.optimize_channel_parameters(
#     parameter_space,
#     lambda params: simulate_protocol_performance(params),
#     num_iterations=50
# )
```
