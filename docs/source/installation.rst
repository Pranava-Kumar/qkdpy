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

   # Enterprise features (cryptography, PKCS#11)
   pip install qkdpy[enterprise]

   # All extras
   pip install qkdpy[all]

Verify installation
-------------------

.. code-block:: python

   import qkdpy
   print(qkdpy.__version__)
