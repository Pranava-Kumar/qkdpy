Enterprise Features
===================

QKDpy provides enterprise-grade features for production deployments of
Quantum Key Distribution systems. These features address compliance,
security auditing, and hardware integration requirements.

Hardware Security Module (HSM)
------------------------------

.. automodule:: qkdpy.enterprise.hsm_interface
   :members:
   :undoc-members:
   :noindex:

The HSM interface enables secure key storage and cryptographic operations
using PKCS#11-compatible hardware security modules. The :class:`~qkdpy.enterprise.hsm_interface.SoftwareHSM`
implementation provides a software fallback for development and testing.

Audit Logging
-------------

.. automodule:: qkdpy.enterprise.audit
   :members:
   :undoc-members:
   :noindex:

Comprehensive audit logging for compliance with regulatory requirements.
The :class:`~qkdpy.enterprise.audit.AuditLogger` tracks all key management
operations, protocol executions, and security events.

Compliance
----------

.. automodule:: qkdpy.enterprise.compliance
   :members:
   :undoc-members:
   :noindex:

Built-in compliance checking against industry standards including
FIPS 140-2/140-3, Common Criteria (CC), and ETSI QKD standards.

Usage Example
-------------

.. code-block:: python

   from qkdpy.enterprise import (
       HSMInterface,
       AuditLogger,
       ComplianceChecker,
       ComplianceStandard,
   )

   # Initialize enterprise components
   hsm = HSMInterface()
   logger = AuditLogger()
   compliance = ComplianceChecker()

   # Perform a compliance-checked key generation
   compliance.check(ComplianceStandard.FIPS_140_2)
   key_handle = hsm.generate_key()
   logger.log_key_generation(key_handle)
