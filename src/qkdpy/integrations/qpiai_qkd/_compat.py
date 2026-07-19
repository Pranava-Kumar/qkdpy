"""Compatibility layer for the real QpiAI Quantum SDK.

This module is the *single* place that knows about the actual ``qpiai_quantum``
public API. The rest of the companion package stays clean and never pokes at SDK
quirks directly. It exists because the SDK differs from the API the original
integration was written against:

* ``Statevector(circuit)`` raises ``ValueError`` (not just ``TypeError``) when no
  ``API_KEY`` is set in the environment.
* ``DensityMatrix`` has **no** ``concurrence()`` method, so concurrence must be
  computed from first principles (Wootters formula).
* ``JobManager`` has **no** ``run_circuit``; real submission uses
  ``submit_and_wait_for_results_qasm`` / ``submit_circuit_job``.

We deliberately do NOT monkey-patch fake methods onto the SDK. The math is done
locally; the cloud path uses the real methods and surfaces real SDK errors
instead of masking them.
"""

from __future__ import annotations

import os
from typing import Any

import numpy as np

try:  # The optional QpiAI Quantum SDK — may be absent at import time.
    from qpiai_quantum import (
        Circuit,
        DensityMatrix,
        JobManager,
        Statevector,
    )

    _QPIAI_AVAILABLE = True
except Exception:  # pragma: no cover - import guard
    Circuit = Statevector = DensityMatrix = JobManager = None
    _QPIAI_AVAILABLE = False


class QpiAISDKError(RuntimeError):
    """Raised when a QpiAI SDK operation cannot be completed."""


def qpiai_available() -> bool:
    """Whether the QpiAI Quantum SDK is importable in this environment."""
    return _QPIAI_AVAILABLE


def _resolve_api_key(api_key: str | None) -> str | None:
    """Resolve the API key from the argument or the ``QPIAI_API_KEY`` env var."""
    if api_key:
        return api_key
    return os.getenv("QPIAI_API_KEY") or os.getenv("API_KEY")


class _SdkKeyContext:
    """Temporarily export the resolved key to ``API_KEY`` for the SDK.

    The QpiAI SDK reads its credential from the ``API_KEY`` environment
    variable (not ``QPIAI_API_KEY``). This makes a configured ``QPIAI_API_KEY``
    actually reach the SDK without permanently mutating the caller's env. If
    ``API_KEY`` is already set, it is left untouched.
    """

    def __init__(self, api_key: str | None) -> None:
        self._key = _resolve_api_key(api_key)
        self._set_here = False

    def __enter__(self) -> None:
        if self._key is not None and "API_KEY" not in os.environ:
            os.environ["API_KEY"] = self._key
            self._set_here = True

    def __exit__(self, *exc: object) -> None:
        if self._set_here:
            os.environ.pop("API_KEY", None)


def _with_sdk_key(api_key: str | None) -> _SdkKeyContext:
    return _SdkKeyContext(api_key)


def local_statevector(circuit: Any, shots: int = 1024) -> dict[str, Any]:
    """Run a circuit on the SDK's local statevector simulator.

    Requires an ``API_KEY``/``QPIAI_API_KEY`` in the environment (the SDK reads
    it itself). Raises :class:`QpiAISDKError` with a clear message if the key is
    missing or the SDK is unavailable, or if the SDK rejects the circuit.
    """
    if not _QPIAI_AVAILABLE:
        raise QpiAISDKError(
            "qpiai_quantum SDK is not installed. Install with `pip install qkdpy[qpiai]`."
        )
    key = _resolve_api_key(None)
    if not key:
        raise QpiAISDKError(
            "No QpiAI API key found. Set QPIAI_API_KEY (or API_KEY) to run the "
            "QpiAI local simulator / submit to the cloud."
        )
    with _with_sdk_key(None):
        try:
            sv = Statevector(circuit)
        except (ValueError, TypeError) as exc:  # E.g. missing API_KEY inside SDK.
            raise QpiAISDKError(f"QpiAI statevector simulation failed: {exc}") from exc

    amplitudes = np.asarray(sv.data, dtype=np.complex128)
    probs = np.abs(amplitudes) ** 2
    probs = probs / probs.sum()
    from qkdpy.core.secure_random import secure_randint

    rng = np.random.default_rng(secure_randint(0, 2**31))
    outcomes = rng.choice(len(probs), size=shots, p=probs)
    sampled = [format(int(o), f"0{sv.num_qubits}b") for o in outcomes]
    return {
        "simulation": "local_statevector",
        "statevector": sv.data,
        "probabilities": probs.tolist(),
        "num_qubits": sv.num_qubits,
        "shots": shots,
        "samples": sampled,
    }


def submit_to_cloud(
    circuit: Any,
    api_key: str | None = None,
    device_name: str = "QpiAI-QSV-Simulator",
    shots: int = 1024,
) -> dict[str, Any]:
    """Submit a circuit to the QpiAI cloud backend via the real SDK API.

    Uses ``JobManager().submit_and_wait_for_results_qasm(...)`` (the actual SDK
    method). Raises :class:`QpiAISDKError` when no key is set or when the SDK
    rejects the submission — we surface the real error rather than masking it.
    """
    if not _QPIAI_AVAILABLE:
        raise QpiAISDKError(
            "qpiai_quantum SDK is not installed. Install with `pip install qkdpy[qpiai]`."
        )
    key = _resolve_api_key(api_key)
    if not key:
        raise ValueError(
            "No QpiAI API key found. Set QPIAI_API_KEY (or API_KEY) to submit "
            "circuits to the cloud."
        )
    try:
        manager = JobManager()
        # The real SDK method name is submit_and_wait_for_results_qasm; circuit is
        # serialised to OpenQASM for submission. Export the key to API_KEY for the
        # SDK in case it reads the env var rather than the kwarg.
        qasm = getattr(circuit, "qasm", None)
        qasm_str = qasm() if callable(qasm) else str(circuit)
        with _with_sdk_key(api_key):
            result = manager.submit_and_wait_for_results_qasm(
                qasm_str,
                device_name=device_name,
                shots=shots,
                api_key=key,
            )
    except (ValueError, TypeError, AttributeError) as exc:
        raise QpiAISDKError(f"QpiAI cloud submission failed: {exc}") from exc
    return {
        "cloud": True,
        "device": device_name,
        "shots": shots,
        "result": result,
    }


def _as_density_matrix(state: Any) -> np.ndarray:
    """Coerce a statevector (1D) or density matrix (2D) into a 4x4 density matrix.

    Accepts:
      * a 1-D length-4 pure statevector (complex),
      * a 2-D 4x4 density matrix,
      * any object exposing ``.data`` (e.g. a qpiai/other Statevector).
    """
    arr = np.asarray(getattr(state, "data", state), dtype=np.complex128)
    if arr.ndim == 1:
        if arr.shape[0] != 4:
            raise ValueError(
                f"Concurrence requires a 2-qubit state (4 amplitudes), got shape {arr.shape}."
            )
        arr = np.outer(arr, np.conjugate(arr))
    elif arr.ndim == 2:
        if arr.shape != (4, 4):
            raise ValueError(
                f"Concurrence requires a 4x4 density matrix, got shape {arr.shape}."
            )
    else:
        raise ValueError(f"Unsupported state shape for concurrence: {arr.shape}.")
    # Normalise defensively (some inputs may be unnormalised).
    trace = np.trace(arr)
    if trace != 0:
        arr = arr / trace
    return arr


def concurrence(state: Any) -> float:
    """Wootters concurrence of a 2-qubit state.

    Implements the standard formula ``C = max(0, sqrt(lambda_1) - sqrt(lambda_2)
    - sqrt(lambda_3) - sqrt(lambda_4))`` where ``lambda_i`` are the eigenvalues of
    ``R = rho * (sigma_y ⊗ sigma_y) * rho^* * (sigma_y ⊗ sigma_y)`` in descending
    order. This replaces the SDK's missing ``DensityMatrix.concurrence()``.

    Returns 1.0 for a maximally entangled Bell state and 0.0 for a separable state.
    """
    rho = _as_density_matrix(state)
    sy = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    syy = np.kron(sy, sy)
    rho_tilde = syy @ rho.conj() @ syy
    r_mat = rho @ rho_tilde
    eigvals = np.linalg.eigvalsh(r_mat)
    eigvals = np.clip(np.real(eigvals), 0.0, None)
    sqrts = np.sqrt(eigvals)
    sqrts.sort()
    c = sqrts[-1] - sqrts[-2] - sqrts[-3] - sqrts[-4]
    return float(max(0.0, c))


def purity(state: Any) -> float:
    """Purity Tr(rho^2) of a 2-qubit state (1.0 = pure, < 1 = mixed)."""
    rho = _as_density_matrix(state)
    return float(np.real(np.trace(rho @ rho)))
