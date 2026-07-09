Protocols
=========

QKDpy implements a comprehensive suite of Quantum Key Distribution protocols.
Below is a comparison of the available protocols and their key characteristics.

Protocol Comparison
-------------------

.. list-table::
   :header-rows: 1
   :widths: 15 20 25 40

   * - Protocol
     - Type
     - Key Feature
     - Best For
   * - :mod:`qkdpy.protocols.bb84`
     - Prepare-and-Measure
     - Original QKD protocol using four polarization states
     - General-purpose QKD, educational use
   * - :mod:`qkdpy.protocols.e91`
     - Entanglement-Based
     - Uses entangled photon pairs (Ekert protocol)
     - Entanglement-based networks, device-independent QKD
   * - :mod:`qkdpy.protocols.b92`
     - Prepare-and-Measure
     - Two-state protocol (simplified BB84)
     - Resource-constrained environments
   * - :mod:`qkdpy.protocols.sarg04`
     - Prepare-and-Measure
     - BB84 variant with same states but different encoding
     - Improved security against PNS attacks
   * - :mod:`qkdpy.protocols.decoy_state_bb84`
     - Prepare-and-Measure
     - Decoy state method for practical security
     - Practical implementations with weak coherent sources
   * - :mod:`qkdpy.protocols.cv_qkd`
     - Continuous-Variable
     - Uses amplitude and phase quadratures
     - Metropolitan area networks, interoperability with classical systems
   * - :mod:`qkdpy.protocols.enhanced_cv_qkd`
     - Continuous-Variable
     - Enhanced CV-QKD with improved noise tolerance
     - Higher loss budget, longer distance CV-QKD
   * - :mod:`qkdpy.protocols.hd_qkd`
     - High-Dimensional
     - Uses qudits (d-level quantum systems)
     - Higher key rates, noise resilience
   * - :mod:`qkdpy.protocols.di_qkd`
     - Device-Independent
     - Security based on Bell inequality violation
     - Untrusted device scenarios, maximum security
   * - :mod:`qkdpy.protocols.twisted_pair`
     - Entanglement-Based
     - Twisted photon pairs for enhanced entanglement distribution
     - Real-world deployments, atmospheric channels

For a detailed protocol comparison with key rate analysis, run the
:ref:`Protocol Comparison <benchmarks>` use case.
