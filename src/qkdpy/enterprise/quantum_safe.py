"""Quantum-safe migration toolkit (PREMIUM tier).

Helps enterprise security teams inventory their classical crypto assets,
assess QKD vs PQC fit, and generate a phased migration roadmap.

This module is gated behind ``Feature.QUANTUM_SAFE_MIGRATION`` and
``Feature.CRYPTO_INVENTORY`` in the PREMIUM tier.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from ..config import QKDConfig, get_config
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Crypto inventory
# ---------------------------------------------------------------------------


class CryptoAlgorithmType(str, Enum):
    """Category of a cryptographic algorithm found in an inventory scan."""

    SYMMETRIC = "symmetric"
    ASYMMETRIC = "asymmetric"
    HASH = "hash"
    KEY_EXCHANGE = "key_exchange"
    SIGNATURE = "signature"
    RANDOM = "random"


class QuantumResistance(str, Enum):
    """How resistant an algorithm is known to be against quantum attacks."""

    VULNERABLE = "vulnerable"  # e.g., RSA, ECDSA, Diffie-Hellman
    MIGRATE_SOON = "migrate_soon"  # e.g., 128-bit AES (Grover's halves security)
    SAFE = "safe"  # e.g., 256-bit AES, SHA-3
    PQC_READY = "pqc_ready"  # already using a standardised PQC algorithm


@dataclass
class CryptoAsset:
    """A single cryptographic asset found in the system."""

    name: str
    algorithm_type: CryptoAlgorithmType
    key_size_bits: int
    resistance: QuantumResistance
    location: str  # e.g. "TLS cert for api.example.com", "code-signing key"
    notes: str = ""


@dataclass
class CryptoInventoryReport:
    """Complete inventory of cryptographic assets in a system."""

    scanned_at: datetime
    assets: list[CryptoAsset]
    system_description: str = ""

    @property
    def total_assets(self) -> int:
        return len(self.assets)

    @property
    def vulnerable_count(self) -> int:
        return sum(
            1
            for a in self.assets
            if a.resistance in (QuantumResistance.VULNERABLE, QuantumResistance.MIGRATE_SOON)
        )

    @property
    def risk_score(self) -> float:
        """Normalised risk score 0.0 – 1.0 based on vulnerable asset ratio."""
        if not self.assets:
            return 0.0
        weights = {
            QuantumResistance.VULNERABLE: 1.0,
            QuantumResistance.MIGRATE_SOON: 0.5,
            QuantumResistance.SAFE: 0.0,
            QuantumResistance.PQC_READY: 0.0,
        }
        return sum(weights[a.resistance] for a in self.assets) / len(self.assets)

    def get_summary(self) -> dict[str, Any]:
        """Return a JSON-serialisable summary dict."""
        return {
            "scanned_at": self.scanned_at.isoformat(),
            "total_assets": self.total_assets,
            "vulnerable_count": self.vulnerable_count,
            "risk_score": round(self.risk_score, 3),
            "system_description": self.system_description,
        }


# ---------------------------------------------------------------------------
# Pre-built inventory presets
# ---------------------------------------------------------------------------

# Common enterprise crypto profiles — used when no real scan is available.


def classic_enterprise_profile() -> CryptoInventoryReport:
    """Return a representative crypto inventory for a typical enterprise."""
    now = datetime.now(UTC)
    return CryptoInventoryReport(
        scanned_at=now,
        system_description="Typical enterprise with web services, code-signing, and internal PKI",
        assets=[
            CryptoAsset(
                name="RSA-2048",
                algorithm_type=CryptoAlgorithmType.ASYMMETRIC,
                key_size_bits=2048,
                resistance=QuantumResistance.VULNERABLE,
                location="TLS server certificates (Nginx / reverse-proxy)",
                notes="Most widely deployed certificate key type",
            ),
            CryptoAsset(
                name="RSA-4096",
                algorithm_type=CryptoAlgorithmType.ASYMMETRIC,
                key_size_bits=4096,
                resistance=QuantumResistance.VULNERABLE,
                location="Code-signing certificate (internal PKI)",
                notes="Long-lived — hardest to rotate",
            ),
            CryptoAsset(
                name="ECDSA-P256",
                algorithm_type=CryptoAlgorithmType.SIGNATURE,
                key_size_bits=256,
                resistance=QuantumResistance.VULNERABLE,
                location="SSH host keys, JWT signing",
            ),
            CryptoAsset(
                name="AES-128-GCM",
                algorithm_type=CryptoAlgorithmType.SYMMETRIC,
                key_size_bits=128,
                resistance=QuantumResistance.MIGRATE_SOON,
                location="TLS session encryption, VPN (WireGuard / IPsec)",
                notes="Grover's algorithm halves effective security to 64 bits",
            ),
            CryptoAsset(
                name="AES-256-GCM",
                algorithm_type=CryptoAlgorithmType.SYMMETRIC,
                key_size_bits=256,
                resistance=QuantumResistance.SAFE,
                location="Vault / HSM storage encryption",
                notes="Comfortably post-quantum secure at 256 bits",
            ),
            CryptoAsset(
                name="SHA-256",
                algorithm_type=CryptoAlgorithmType.HASH,
                key_size_bits=256,
                resistance=QuantumResistance.SAFE,
                location="Certificate signatures, integrity checks",
                notes="Hash functions are relatively resistant to quantum attacks",
            ),
            CryptoAsset(
                name="Diffie-Hellman (2048-bit)",
                algorithm_type=CryptoAlgorithmType.KEY_EXCHANGE,
                key_size_bits=2048,
                resistance=QuantumResistance.VULNERABLE,
                location="TLS key agreement, legacy VPN",
                notes="Shor's algorithm completely breaks finite-field DH",
            ),
            CryptoAsset(
                name="HMAC-SHA256",
                algorithm_type=CryptoAlgorithmType.SYMMETRIC,
                key_size_bits=256,
                resistance=QuantumResistance.SAFE,
                location="API authentication tokens, webhooks",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Migration roadmap
# ---------------------------------------------------------------------------


class MigrationPhase(str, Enum):
    """Phases of a quantum-safe migration."""

    ASSESS = "assess"
    PLAN = "plan"
    PILOT = "pilot"
    MIGRATE = "migrate"
    VERIFY = "verify"


@dataclass
class MigrationStep:
    """A single action item in a migration roadmap."""

    phase: MigrationPhase
    priority: int  # 1 = highest
    title: str
    description: str
    estimated_effort: str  # e.g. "2 weeks", "3 months"
    depends_on: list[str] = field(default_factory=list)


@dataclass
class MigrationRoadmap:
    """Full quantum-safe migration roadmap for an organisation."""

    generated_at: datetime
    inventory: CryptoInventoryReport
    steps: list[MigrationStep]
    target_completion: str  # e.g. "Q4 2028"

    def get_summary(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "target_completion": self.target_completion,
            "total_steps": len(self.steps),
            "risk_score": self.inventory.risk_score,
            "vulnerable_assets": self.inventory.vulnerable_count,
        }


def generate_roadmap(
    inventory: CryptoInventoryReport | None = None,
    *,
    config: QKDConfig | None = None,
) -> MigrationRoadmap:
    """Generate a quantum-safe migration roadmap based on the crypto inventory.

    If no inventory is provided a representative enterprise profile is used so
    the function is useful for demonstration and pre-sales.
    """
    inv = inventory if inventory is not None else classic_enterprise_profile()
    now = datetime.now(UTC)
    _ = config  # reserved for future target-compliance-year injection

    steps: list[MigrationStep] = []

    # Phase 1: Assess
    steps.append(
        MigrationStep(
            phase=MigrationPhase.ASSESS,
            priority=1,
            title="Complete crypto inventory",
            description=(
                f"Catalog all {inv.total_assets} cryptographic assets across "
                f"the organisation — TLS certs, code-signing keys, SSH keys, "
                f"document signatures. {inv.vulnerable_count} assets are "
                f"quantum-vulnerable."
            ),
            estimated_effort="4–6 weeks",
        )
    )
    steps.append(
        MigrationStep(
            phase=MigrationPhase.ASSESS,
            priority=2,
            title="Identify high-risk assets",
            description="Prioritise long-lived certificates (code-signing, CA) and "
            "externally-facing TLS endpoints for earliest migration.",
            estimated_effort="2 weeks",
            depends_on=["Complete crypto inventory"],
        )
    )

    # Phase 2: Plan
    steps.append(
        MigrationStep(
            phase=MigrationPhase.PLAN,
            priority=3,
            title="Select replacement algorithms",
            description="Evaluate ML-KEM (FIPS 203) for key exchange, ML-DSA (FIPS 204) "
            "for signatures, and SLH-DSA (FIPS 205) for stateless hash-based "
            "signatures alongside QKD for symmetric key distribution.",
            estimated_effort="4 weeks",
            depends_on=["Identify high-risk assets"],
        )
    )
    steps.append(
        MigrationStep(
            phase=MigrationPhase.PLAN,
            priority=4,
            title="Define hybrid deployment strategy",
            description="Plan hybrid PQC + classical cipher suites (e.g., X25519+ML-KEM "
            "for TLS 1.3) to maintain interoperability during transition.",
            estimated_effort="2 weeks",
            depends_on=["Select replacement algorithms"],
        )
    )

    # Phase 3: Pilot
    steps.append(
        MigrationStep(
            phase=MigrationPhase.PILOT,
            priority=5,
            title="Enable QKD simulation for key distribution",
            description="Deploy QKDpy simulation to model QKD-based key distribution "
            "for select high-security links. Validate key rate and distance "
            "parameters match operational requirements.",
            estimated_effort="6–8 weeks",
            depends_on=["Define hybrid deployment strategy"],
        )
    )
    steps.append(
        MigrationStep(
            phase=MigrationPhase.PILOT,
            priority=6,
            title="PQC pilot on non-critical services",
            description="Enable ML-KEM / ML-DSA on internal staging services. "
            "Monitor performance impact, interoperability, and certificate "
            "management overhead.",
            estimated_effort="4 weeks",
            depends_on=["Define hybrid deployment strategy"],
        )
    )

    # Phase 4: Migrate
    steps.append(
        MigrationStep(
            phase=MigrationPhase.MIGRATE,
            priority=7,
            title="Migrate external-facing TLS",
            description="Roll out hybrid PQC cipher suites on public-facing endpoints. "
            "Requires CDN / load-balancer support.",
            estimated_effort="4–8 weeks",
            depends_on=["PQC pilot on non-critical services"],
        )
    )
    steps.append(
        MigrationStep(
            phase=MigrationPhase.MIGRATE,
            priority=8,
            title="Rotate long-lived signing keys",
            description="Replace code-signing and CA certificates with PQC equivalents. "
            "Coordinate with hardware vendors for HSM firmware updates.",
            estimated_effort="8–12 weeks",
            depends_on=["PQC pilot on non-critical services"],
        )
    )

    # Phase 5: Verify
    steps.append(
        MigrationStep(
            phase=MigrationPhase.VERIFY,
            priority=9,
            title="Continuous compliance monitoring",
            description="Use QKDpy Enterprise compliance suite to continuously monitor "
            "crypto hygiene. Alert on any new vulnerable asset deployments.",
            estimated_effort="Ongoing",
            depends_on=["Migrate external-facing TLS", "Rotate long-lived signing keys"],
        )
    )

    return MigrationRoadmap(
        generated_at=now,
        inventory=inv,
        steps=steps,
        target_completion="Q4 2028",
    )


# ---------------------------------------------------------------------------
# Assessment report
# ---------------------------------------------------------------------------


@dataclass
class QuantumSafeAssessment:
    """Full assessment combining inventory, roadmap, and recommendations."""

    inventory: CryptoInventoryReport
    roadmap: MigrationRoadmap
    assessed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Full assessment as a serialisable dict."""
        return {
            "assessed_at": self.assessed_at.isoformat(),
            "inventory": self.inventory.get_summary(),
            "roadmap": self.roadmap.get_summary(),
            "recommendations": self._recommendations(),
        }

    def _recommendations(self) -> list[str]:
        """Generate plain-english recommendations based on the inventory."""
        recs: list[str] = []
        vuln = self.inventory.vulnerable_count

        if vuln > 0:
            recs.append(
                f"Start quantum-safe migration planning immediately — "
                f"{vuln} of {self.inventory.total_assets} crypto assets are "
                f"quantum-vulnerable."
            )
        else:
            recs.append("No quantum-vulnerable crypto assets detected.")

        if any(a.key_size_bits == 128 and a.algorithm_type == CryptoAlgorithmType.SYMMETRIC for a in self.inventory.assets):
            recs.append(
                "Upgrade 128-bit AES deployments to 256-bit to maintain "
                "128-bit post-quantum security margin."
            )

        recs.append(
            "Use QKDpy's compliance suite to establish a baseline and "
            "track migration progress against ETSI / NIST timelines."
        )
        return recs


__all__ = [
    "CryptoAlgorithmType",
    "CryptoAsset",
    "CryptoInventoryReport",
    "MigrationPhase",
    "MigrationRoadmap",
    "MigrationStep",
    "QuantumResistance",
    "QuantumSafeAssessment",
    "classic_enterprise_profile",
    "generate_roadmap",
]
