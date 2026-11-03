Installation
============

QKDpy requires Python 3.11 or later.

Install from PyPI
-----------------

The easiest way to install QKDpy is via pip:

.. code-block:: bash

   pip install qkdpy

Install from source
-------------------

To install the latest development version directly from the repository:

.. code-block:: bash

   git clone https://github.com/Pranava-Kumar/qkdpy.git
   cd qkdpy
   pip install .

Install with extras
-------------------

QKDpy provides several optional dependency groups for extended functionality:

.. code-block:: bash

   # Development tools (testing, linting, documentation)
   pip install qkdpy[dev]

   # Machine learning components (scikit-learn, pandas)
   pip install qkdpy[ml]

   # Documentation dependencies
   pip install qkdpy[docs]

   # Visualization extras (seaborn)
   pip install qkdpy[viz]

   # Enterprise features (compliance, audit, software-simulation HSM)
   pip install "qkdpy[enterprise]"

   # Cirq quantum computing framework integration
   pip install "qkdpy[cirq]"

   # PennyLane quantum computing framework integration
   pip install "qkdpy[pennylane]"

   # Qiskit integration
   pip install "qkdpy[qiskit]"

   # QpiAI Quantum SDK integration
   pip install "qkdpy[qpiai]"

   # Common optional features (no external quantum SDKs)
   pip install "qkdpy[ml,viz,enterprise]"

Product Tiers
-------------

QKDpy uses a cumulative three-tier licensing model:

- **FREE** (default) — All protocols, satellite simulation, ML, visualization
- **ENTERPRISE** — Adds compliance reporting, HSM, audit logging, attack detection, key escrow
- **PREMIUM** — Adds quantum-safe migration toolkit, crypto inventory, priority support

Set the active tier programmatically. Non-FREE tiers require a license key
(any non-empty string in demo mode):

.. code-block:: python

   from qkdpy import QKDConfig, set_config

   config = QKDConfig()
   config.enterprise.product_tier = "enterprise"
   config.enterprise.license_key = "demo-key"
   set_config(config)

You can also set ``QKDPY_PRODUCT_TIER`` / ``QKDPY_LICENSE_KEY`` in the
environment and then call ``set_config(get_config())`` to apply them.

Verify installation
-------------------

.. code-block:: python

   import qkdpy
   print(qkdpy.__version__)
