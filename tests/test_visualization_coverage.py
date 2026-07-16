"""Coverage tests for qkdpy.utils.visualization (was ~13%).

Exercises the public plotting / analysis API with small real data so the
module is actually executed, not just imported.
"""

import importlib

import matplotlib

# Use a non-interactive backend so plots build in CI / headless envs.
matplotlib.use("Agg")


from qkdpy.core import Qubit
from qkdpy.utils.visualization import (
    BlochSphere,
    KeyRateAnalyzer,
    ProtocolVisualizer,
)

# matplotlib.figure.Figure is what the plot* methods return.
Figure = matplotlib.figure.Figure


# --------------------------------------------------------------------------- #
#  BlochSphere
# --------------------------------------------------------------------------- #


def test_bloch_sphere_plots_qubit() -> None:
    sphere = BlochSphere()
    # plot_qubit accepts a Qubit instance, not a raw list.
    qubit = Qubit(0.6 + 0j, 0.8 + 0j)
    ax = sphere.plot_qubit(qubit)
    # Returns a 3D Axes, not a Figure; verify it has the expected attributes.
    assert hasattr(ax, "plot_surface")


def test_bloch_sphere_multiple_qubits() -> None:
    sphere = BlochSphere()
    states = [Qubit(1.0, 0.0), Qubit(0.0, 1.0), Qubit(0.707, 0.707)]
    fig = sphere.plot_multiple_qubits(states)
    assert isinstance(fig, Figure)


# --------------------------------------------------------------------------- #
#  ProtocolVisualizer  — all methods accept flat lists, NOT a protocol result
# --------------------------------------------------------------------------- #


def test_protocol_visualizer_bb84() -> None:
    viz = ProtocolVisualizer()
    fig = viz.plot_bb84_protocol(
        alice_bits=[0, 1, 0, 1],
        alice_bases=["computational", "hadamard", "computational", "hadamard"],
        bob_bases=["computational", "hadamard", "hadamard", "computational"],
        bob_results=[0, 1, 1, 0],
    )
    assert isinstance(fig, Figure)


def test_protocol_visualizer_e91() -> None:
    viz = ProtocolVisualizer()
    fig = viz.plot_e91_protocol(
        alice_choices=[0, 1, 2, 0],
        alice_results=[0, 1, 0, 1],
        bob_choices=[1, 2, 0, 1],
        bob_results=[1, 0, 0, 1],
    )
    assert isinstance(fig, Figure)


def test_protocol_visualizer_sarg04() -> None:
    viz = ProtocolVisualizer()
    fig = viz.plot_sarg04_protocol(
        alice_bits=[0, 1, 0],
        alice_bases=["computational", "hadamard", "computational"],
        bob_bases=["computational", "computational", "hadamard"],
        bob_results=[0, 0, 0],
        bob_guesses=[0, 1, 0],
    )
    assert isinstance(fig, Figure)


# --------------------------------------------------------------------------- #
#  KeyRateAnalyzer
# --------------------------------------------------------------------------- #


def test_key_rate_analyzer_vs_qber() -> None:
    analyzer = KeyRateAnalyzer()
    qber_vals = [0.0, 0.02, 0.05, 0.08, 0.11]
    key_rates = [1.0, 0.9, 0.7, 0.4, 0.0]
    fig = analyzer.plot_key_rate_vs_qber(qber_vals, key_rates)
    assert isinstance(fig, Figure)


def test_key_rate_analyzer_vs_distance() -> None:
    analyzer = KeyRateAnalyzer()
    distances = [0, 10, 20, 50, 100]
    key_rates = [1.0, 0.8, 0.6, 0.3, 0.05]
    fig = analyzer.plot_key_rate_vs_distance(distances, key_rates)
    assert isinstance(fig, Figure)


def test_key_rate_analyzer_compare_protocols() -> None:
    analyzer = KeyRateAnalyzer()
    protocol_data: dict[str, tuple[list[float], list[float]]] = {
        "BB84": ([0.0, 0.05, 0.1], [1.0, 0.5, 0.0]),
        "E91": ([0.0, 0.05, 0.1], [0.9, 0.4, 0.0]),
    }
    fig = analyzer.compare_protocols(protocol_data)
    assert isinstance(fig, Figure)


# --------------------------------------------------------------------------- #
#  Module import guard
# --------------------------------------------------------------------------- #


def test_visualization_module_importable() -> None:
    # guards against the module being moved / renamed
    mod = importlib.import_module("qkdpy.utils.visualization")
    assert hasattr(mod, "BlochSphere")
