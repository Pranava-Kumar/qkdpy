# QKDpy Examples

This directory contains example scripts and notebooks demonstrating how to use QKDpy for quantum key distribution simulations and research.

## Table of Contents

1. [Jupyter Notebook Tutorial](#jupyter-notebook-tutorial)
2. [Educational Demo](#educational-demo)
3. [Protocol Comparisons](#protocol-comparisons)
4. [Network Simulations](#network-simulations)
5. [Machine Learning Examples](#machine-learning-examples)
6. [Cryptography & Security](#cryptography--security)
7. [Key Management](#key-management)
8. [Enterprise, Core & Visualization](#enterprise-core--visualization)

## Jupyter Notebook Tutorial

[`qkdpy_tutorial.ipynb`](qkdpy_tutorial.ipynb) - A comprehensive interactive tutorial covering:

- Introduction to QKD concepts
- Basic protocol usage (BB84, E91, etc.)
- Quantum network simulation
- Visualization tools
- Machine learning integration

To run the tutorial:
```bash
jupyter notebook qkdpy_tutorial.ipynb
```

## Educational Demo

[`educational_demo.py`](educational_demo.py) - A Python script demonstrating fundamental QKD concepts:

- Step-by-step explanation of BB84 protocol
- Quantum state visualization
- Protocol comparisons
- Security feature demonstrations

To run the demo:
```bash
python educational_demo.py
```

## Protocol Comparisons

Examples comparing different QKD protocols under various channel conditions:

- [`protocol_comparison.py`](protocol_comparison.py) - Compare BB84, E91, SARG04, CV-QKD, etc.
- [`protocols_example.py`](protocols_example.py) - Walk through the shipped protocol classes
- [`bb84_example.py`](bb84_example.py) - Standard BB84 walkthrough
- [`b92_example.py`](b92_example.py) - B92 protocol example
- [`hd_qkd_example.py`](hd_qkd_example.py) - High-dimensional QKD
- [`advanced_protocols_example.py`](advanced_protocols_example.py) - Decoy-state, MDI, and DI-QKD

## Network Simulations

Examples of multi-node quantum networks:

- [`network_simulation.py`](network_simulation.py) - Basic quantum network setup
- [`quantum_network_example.py`](quantum_network_example.py) - Network topology and routing
- [`satellite_qkd_demo.py`](satellite_qkd_demo.py) - Satellite-to-ground QKD pass
- [`full_qkd_scenario.py`](full_qkd_scenario.py) - End-to-end QKD scenario

## Machine Learning Examples

Examples integrating machine learning with QKD:

- [`ml_integration.py`](ml_integration.py) - Parameter optimization and anomaly detection

## Cryptography & Security

- [`encryption_example.py`](encryption_example.py) - One-time-pad encryption with QKD keys
- [`enhanced_security_example.py`](enhanced_security_example.py) - Side-channel and attack analysis
- [`quantum_cryptography_example.py`](quantum_cryptography_example.py) - Quantum authentication and RNG

## Key Management

- [`key_management_example.py`](key_management_example.py) - Key lifecycle basics
- [`advanced_key_management_example.py`](advanced_key_management_example.py) - Error correction and privacy amplification

## Enterprise, Core & Visualization

- [`enterprise_demo.py`](enterprise_demo.py) - Config audit, HSM simulation, and licensing
- [`core_features_example.py`](core_features_example.py) - Density matrices and circuits
- [`v080_features_showcase.py`](v080_features_showcase.py) - v0.8.0 feature tour
- [`advanced_visualization_example.py`](advanced_visualization_example.py) - Plotting helpers

## Getting Started

To run these examples, first install QKDpy:

```bash
pip install qkdpy

# Or, from a clone of this repository
pip install -e .
```

Then navigate to this examples directory and run any of the example scripts:

```bash
cd examples
python educational_demo.py
```

For Jupyter notebooks, make sure you have Jupyter installed:

```bash
pip install jupyter
jupyter notebook
```

## Prerequisites

- Python 3.11+
- QKDpy library
- Jupyter (for notebooks)
- Matplotlib (for visualizations)
- NumPy
- SciPy

Install optional dependencies explicitly; the examples do not install packages
at runtime. Visualization examples may also need `seaborn`
(`pip install "qkdpy[viz]"`), and ML examples need `scikit-learn` and `pandas`
(`pip install "qkdpy[ml]"`).
