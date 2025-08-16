from qkdpy import (  # Import individual gate classes
    BB84,
    PauliX,
    QuantumChannel,
    Qubit,
)

# Create a quantum channel with some noise
channel = QuantumChannel(loss=0.1, noise_model="depolarizing", noise_level=0.05)

# Create a BB84 protocol instance
bb84 = BB84(channel, key_length=100)

# Execute the protocol
results = bb84.execute()

# Print the results
print(f"Generated key: {results['final_key']}")
print(f"QBER: {results['qber']:.4f}")
print(f"Is secure: {results['is_secure']}")

# Example of flexible qubit measurement and collapse
q = Qubit.plus()  # Qubit in superposition
print(f"Qubit state before measurement: {q.state}")
measurement_result = q.measure("hadamard")  # Measure without collapsing internal state
print(f"Measurement result: {measurement_result}")
print(f"Qubit state after measurement (still in superposition): {q.state}")
q.collapse_state(measurement_result, "hadamard")  # Explicitly collapse the state
print(f"Qubit state after explicit collapse: {q.state}")

# Example of applying a gate
q_zero = Qubit.zero()
print(f"Qubit state before X gate: {q_zero.state}")
q_zero.apply_gate(PauliX().matrix)  # Apply Pauli-X gate
print(f"Qubit state after X gate: {q_zero.state}")
