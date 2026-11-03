.. _benchmarks:

Benchmarks
==========

Key Rate Comparison
-------------------

The following table compares key rates for different QKD protocols under
standard simulation conditions (50 km fiber channel, ideal detectors).

.. csv-table::
   :header: "Protocol", "Key Rate (bps)", "Max Distance (km)"
   :widths: 25, 20, 20

   "BB84", "1.2e5", "150"
   "DecoyStateBB84", "8.5e4", "180"
   "E91", "6.1e3", "100"
   "B92", "4.3e4", "80"
   "SARG04", "7.8e4", "120"
   "CVQKD", "2.2e4", "200"
   "EnhancedCVQKD", "3.1e4", "250"
   "HDQKD (d=4)", "9.6e4", "130"
   "DeviceIndependentQKD", "1.2e3", "70"
   "TwistedPairQKD", "5.4e3", "90"

.. note::

   These values are illustrative. Actual performance depends on hardware
   specifications, channel conditions, and implementation details.

Running Benchmarks
------------------

To generate benchmark results for your specific setup:

.. code-block:: python

   from qkdpy import QuantumChannel
   from qkdpy.protocols import BB84, CVQKD, DecoyStateBB84

   # Run a protocol simulation
   channel = QuantumChannel(distance=50.0, noise_level=0.02)
   bb84 = BB84(channel, key_length=10000)
   results = bb84.execute()

   print(f"QBER: {results['qber']:.4f}")
   print(f"Key rate: {bb84.get_key_rate():.2e} bps")
