"""Backwards-compatible entry point for the qpiai-qkd companion.

This thin module preserves the historical import path
``from qkdpy.integrations.qpiai_integration import QpiAIIntegration`` while the
real, hardened implementation lives in the :mod:`qkdpy.integrations.qpiai_qkd`
subpackage (a standalone companion installable via ``pip install qkdpy[qpiai]``).

All logic and the real QpiAI Quantum SDK handling is in ``qpiai_qkd``; this file
only re-exports so existing callers and tests keep working.
"""

from .qpiai_qkd import QpiAIIntegration

__all__ = ["QpiAIIntegration"]
