# QKDpy Examples

This directory contains example scripts and notebooks demonstrating how to use QKDpy for quantum key distribution simulations and research.

## Table of Contents

1. [Jupyter Notebook Tutorial](#jupyter-notebook-tutorial)
2. [Educational Demo](#educational-demo)
3. [Protocol Comparisons](#protocol-comparisons)
4. [Network Simulations](#network-simulations)
5. [Machine Learning Examples](#machine-learning-examples)

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
- [`performance_analysis.py`](performance_analysis.py) - Analyze key rates vs. channel loss/noise

## Network Simulations

Examples of multi-node quantum networks:

- [`network_demo.py`](network_demo.py) - Basic quantum network setup
- [`multi_party_qkd.py`](multi_party_qkd.py) - Multi-party key distribution
- [`trusted_relay.py`](trusted_relay.py) - Trusted relay networks

## Machine Learning Examples

Examples integrating machine learning with QKD:

- [`ml_optimization.py`](ml_optimization.py) - Protocol parameter optimization
- [`anomaly_detection.py`](anomaly_detection.py) - Anomaly detection in QKD systems
- [`reinforcement_learning.py`](reinforcement_learning.py) - Adaptive protocol selection

## Getting Started

To run these examples, first install QKDpy:

```bash
# Using uv (recommended)
uv pip install qkdpy

# Or using pip
pip install qkdpy
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

- Python 3.10+
- QKDpy library
- Jupyter (for notebooks)
- Matplotlib (for visualizations)
- NumPy
- SciPy

Most examples will automatically install missing dependencies when run.
