"""Example of using the core features of QKDpy."""

import sys

import matplotlib.pyplot as plt

from qkdpy.core import Measurement, QuantumChannel, QuantumGate, Qubit
from qkdpy.utils import BlochSphere


def core_features_example() -> None:
    """Demonstrates the core functionalities of QKDpy."""
    sys.stdout.reconfigure(encoding="utf-8")
    print("QKDpy Core Features Example")
    print("===========================")

    # 1. Creating Qubits
    print("\n1. Creating Qubits")
    q0 = Qubit.zero()
    q1 = Qubit.one()
    q_plus = Qubit.plus()
    q_minus = Qubit.minus()
    print(f"Qubit 0 state: alpha={q0.state[0]:.3f}, beta={q0.state[1]:.3f}")
    print(f"Qubit 1 state: alpha={q1.state[0]:.3f}, beta={q1.state[1]:.3f}")
    print(f"Qubit plus state: alpha={q_plus.state[0]:.3f}, beta={q_plus.state[1]:.3f}")
    print(
        f"Qubit minus state: alpha={q_minus.state[0]:.3f}, beta={q_minus.state[1]:.3f}"
    )

    # 2. Applying Quantum Gates
    print("\n2. Applying Quantum Gates")
    q = Qubit.zero()
    print(f"Initial qubit state: {q.state}")
    q.apply_gate(QuantumGate.H())
    print(f"After Hadamard gate: {q.state}")
    q.apply_gate(QuantumGate.X())
    print(f"After X gate: {q.state}")
    q.apply_gate(QuantumGate.Z())
    print(f"After Z gate: {q.state}")

    # 3. Using a Quantum Channel
    print("\n3. Using a Quantum Channel")
    channel = QuantumChannel(loss=0.5, noise_model="bit_flip", noise_level=0.5)
    q_in = Qubit.zero()
    print(f"Qubit before channel: {q_in.state}")
    q_out = channel.transmit(q_in)
    if q_out is not None:
        print(f"Qubit after channel: {q_out.state}")
    else:
        print("Qubit was lost in the channel.")

    # 4. Measuring Qubits
    print("\n4. Measuring Qubits")
    q_to_measure = Qubit.plus()
    print(f"Measuring qubit: {q_to_measure.state}")
    result_comp = Measurement.measure_in_basis(q_to_measure, "computational")
    print(f"Measurement in computational basis: {result_comp}")
    # Recreate the qubit as measurement changes its state
    q_to_measure = Qubit.plus()
    result_had = Measurement.measure_in_basis(q_to_measure, "hadamard")
    print(f"Measurement in Hadamard basis: {result_had}")

    # 5. Visualizing a Qubit
    print("\n5. Visualizing a Qubit on the Bloch Sphere")
    q_to_plot = Qubit(alpha=0.6, beta=0.8j)
    BlochSphere.plot_qubit(
        q_to_plot,
        title=f"State of Qubit(alpha={q_to_plot.state[0]:.3f}, beta={q_to_plot.state[1]:.3f})",
    )
    plt.show()


if __name__ == "__main__":
    core_features_example()
