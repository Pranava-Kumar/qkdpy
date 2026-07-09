"""Compliance checking and reporting for QKDpy.

This module provides automated compliance checks against security
standards and generates compliance reports.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from ..config import QKDConfig, SecurityMode, get_config
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ComplianceStandard(Enum):
    """Supported compliance standards."""

    ETSI_GS_QKD_014 = "ETSI GS QKD 014"
    ETSI_GS_QKD_016 = "ETSI GS QKD 016"
    ISO_IEC_23837_1 = "ISO/IEC 23837-1"
    ISO_IEC_23837_2 = "ISO/IEC 23837-2"
    NIST_SP_800_57 = "NIST SP 800-57"
    NIST_SP_800_90 = "NIST SP 800-90"
    COMMON_CRITERIA = "Common Criteria"
    FIPS_140_2 = "FIPS 140-2"
    FIPS_140_3 = "FIPS 140-3"
    ISO_27001 = "ISO 27001"


@dataclass
class ComplianceCheck:
    """Result of a single compliance check."""

    check_id: str
    standard: ComplianceStandard
    requirement: str
    description: str
    passed: bool
    severity: str
    details: str | None = None
    recommendation: str | None = None


@dataclass
class ComplianceReport:
    """Comprehensive compliance report."""

    report_id: str
    generated_at: datetime
    standards_checked: list[ComplianceStandard]
    total_checks: int
    passed_checks: int
    failed_checks: int
    checks: list[ComplianceCheck]
    overall_compliant: bool

    def get_summary(self) -> dict[str, Any]:
        """Get summary of the report."""
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "standards": [s.value for s in self.standards_checked],
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "compliance_rate": (
                self.passed_checks / self.total_checks if self.total_checks > 0 else 0
            ),
            "overall_compliant": self.overall_compliant,
        }

    def get_failed_checks(self) -> list[ComplianceCheck]:
        """Get list of failed checks."""
        return [c for c in self.checks if not c.passed]

    def export_markdown(self) -> str:
        """Export report as Markdown."""
        lines = [
            "# Compliance Report",
            "",
            f"**Report ID:** {self.report_id}",
            f"**Generated:** {self.generated_at.isoformat()}",
            f"**Standards:** {', '.join(s.value for s in self.standards_checked)}",
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Checks | {self.total_checks} |",
            f"| Passed | {self.passed_checks} |",
            f"| Failed | {self.failed_checks} |",
            f"| Compliance Rate | {self.passed_checks / self.total_checks * 100:.1f}% |",
            f"| Overall Compliant | {'✅ Yes' if self.overall_compliant else '❌ No'} |",
            "",
        ]

        if self.failed_checks > 0:
            lines.extend(
                [
                    "## Failed Checks",
                    "",
                ]
            )
            for check in self.get_failed_checks():
                lines.extend(
                    [
                        f"### {check.check_id}: {check.requirement}",
                        "",
                        f"**Standard:** {check.standard.value}",
                        f"**Severity:** {check.severity}",
                        "",
                        f"{check.description}",
                        "",
                    ]
                )
                if check.details:
                    lines.append(f"**Details:** {check.details}")
                    lines.append("")
                if check.recommendation:
                    lines.append(f"**Recommendation:** {check.recommendation}")
                    lines.append("")

        return "\n".join(lines)


class ComplianceChecker:
    """Checks QKD system configuration against compliance standards."""

    def __init__(
        self,
        standards: list[ComplianceStandard] | None = None,
        config: QKDConfig | None = None,
    ) -> None:
        """Initialize compliance checker.

        Args:
            standards: Standards to check (default: ETSI GS QKD 014)
            config: QKD config to check against. Uses global config if None.
        """
        self.standards = (
            standards if standards is not None else [ComplianceStandard.ETSI_GS_QKD_014]
        )
        self._config = config

    def check_compliance(self) -> ComplianceReport:
        """Run all compliance checks.

        Returns:
            Compliance report
        """
        import secrets

        checks: list[ComplianceCheck] = []

        for standard in self.standards:
            if standard == ComplianceStandard.NIST_SP_800_57:
                checks.extend(self._check_nist_800_57())
            elif standard == ComplianceStandard.FIPS_140_2:
                checks.extend(self._check_fips_140_2())
            elif standard == ComplianceStandard.ISO_27001:
                checks.extend(self._check_iso_27001())
            elif standard == ComplianceStandard.ETSI_GS_QKD_014:
                checks.extend(self._check_etsi_qkd_014())
            elif standard == ComplianceStandard.ETSI_GS_QKD_016:
                checks.extend(self._check_etsi_qkd_016())
            elif standard in (
                ComplianceStandard.ISO_IEC_23837_1,
                ComplianceStandard.ISO_IEC_23837_2,
            ):
                checks.extend(self._check_iso_23837())

        passed = sum(1 for c in checks if c.passed)
        failed = len(checks) - passed

        # Overall compliant if no critical/high severity failures
        critical_failures = [
            c for c in checks if not c.passed and c.severity in ("critical", "high")
        ]
        overall_compliant = len(critical_failures) == 0

        report = ComplianceReport(
            report_id=secrets.token_hex(8),
            generated_at=datetime.now(UTC),
            standards_checked=self.standards,
            total_checks=len(checks),
            passed_checks=passed,
            failed_checks=failed,
            checks=checks,
            overall_compliant=overall_compliant,
        )

        logger.info(
            "Compliance check completed",
            total=len(checks),
            passed=passed,
            failed=failed,
            overall_compliant=overall_compliant,
        )

        return report

    def _check_nist_800_57(self) -> list[ComplianceCheck]:
        """Check NIST SP 800-57 compliance."""
        checks: list[ComplianceCheck] = []
        config = self._config if self._config is not None else get_config()

        # Key length requirements
        checks.append(
            ComplianceCheck(
                check_id="NIST-57-001",
                standard=ComplianceStandard.NIST_SP_800_57,
                requirement="Minimum symmetric key length",
                description="Symmetric keys must be at least 128 bits for security through 2030",
                passed=config.security.min_key_length >= 128,
                severity="critical",
                details=f"Current minimum: {config.security.min_key_length} bits",
                recommendation="Set min_key_length to at least 128 bits",
            )
        )

        # Key rotation
        checks.append(
            ComplianceCheck(
                check_id="NIST-57-002",
                standard=ComplianceStandard.NIST_SP_800_57,
                requirement="Key rotation policy",
                description="Keys should be rotated periodically to limit exposure",
                passed=config.security.enable_key_rotation,
                severity="high",
                details=f"Key rotation enabled: {config.security.enable_key_rotation}",
                recommendation="Enable automatic key rotation",
            )
        )

        # Audit logging
        checks.append(
            ComplianceCheck(
                check_id="NIST-57-003",
                standard=ComplianceStandard.NIST_SP_800_57,
                requirement="Audit logging",
                description="All key management operations must be logged",
                passed=config.security.enable_audit_logging,
                severity="high",
                details=f"Audit logging enabled: {config.security.enable_audit_logging}",
                recommendation="Enable audit logging for compliance",
            )
        )

        # Production mode security
        checks.append(
            ComplianceCheck(
                check_id="NIST-57-004",
                standard=ComplianceStandard.NIST_SP_800_57,
                requirement="Production security mode",
                description="Production deployments should use production security mode",
                passed=config.security.mode == SecurityMode.PRODUCTION,
                severity="medium",
                details=f"Current mode: {config.security.mode.value}",
                recommendation="Set security mode to 'production' for deployment",
            )
        )

        # Secret redaction in logs
        checks.append(
            ComplianceCheck(
                check_id="NIST-57-005",
                standard=ComplianceStandard.NIST_SP_800_57,
                requirement="Log sanitization",
                description="Secret data must be redacted from logs",
                passed=config.logging.redact_secrets,
                severity="critical",
                details=f"Redaction enabled: {config.logging.redact_secrets}",
                recommendation="Enable secret redaction in logging configuration",
            )
        )

        return checks

    def _check_fips_140_2(self) -> list[ComplianceCheck]:
        """Check FIPS 140-2 compliance."""
        checks: list[ComplianceCheck] = []
        config = self._config if self._config is not None else get_config()

        # HSM requirement
        checks.append(
            ComplianceCheck(
                check_id="FIPS-140-001",
                standard=ComplianceStandard.FIPS_140_2,
                requirement="Hardware security module",
                description="FIPS 140-2 Level 2+ requires HSM for key storage",
                passed=config.enterprise.enable_hsm,
                severity="critical",
                details=f"HSM enabled: {config.enterprise.enable_hsm}",
                recommendation="Enable HSM integration for FIPS compliance",
            )
        )

        # Authentication requirement
        checks.append(
            ComplianceCheck(
                check_id="FIPS-140-002",
                standard=ComplianceStandard.FIPS_140_2,
                requirement="Authentication",
                description="Role-based authentication is required",
                passed=config.security.require_authentication,
                severity="critical",
                details=f"Authentication required: {config.security.require_authentication}",
                recommendation="Enable authentication requirement",
            )
        )

        return checks

    def _check_iso_27001(self) -> list[ComplianceCheck]:
        """Check ISO 27001 compliance."""
        checks: list[ComplianceCheck] = []
        config = self._config if self._config is not None else get_config()

        # Access control
        checks.append(
            ComplianceCheck(
                check_id="ISO-27001-001",
                standard=ComplianceStandard.ISO_27001,
                requirement="Access Control (A.9)",
                description="Access to systems and data must be controlled",
                passed=config.security.require_authentication,
                severity="high",
                details=f"Authentication enabled: {config.security.require_authentication}",
                recommendation="Implement access control mechanisms",
            )
        )

        # Cryptographic controls
        checks.append(
            ComplianceCheck(
                check_id="ISO-27001-002",
                standard=ComplianceStandard.ISO_27001,
                requirement="Cryptographic Controls (A.10)",
                description="Cryptographic controls must be properly implemented",
                passed=config.security.min_key_length >= 128,
                severity="high",
                details=f"Key length: {config.security.min_key_length} bits",
                recommendation="Ensure minimum 128-bit key length",
            )
        )

        # Logging and monitoring
        checks.append(
            ComplianceCheck(
                check_id="ISO-27001-003",
                standard=ComplianceStandard.ISO_27001,
                requirement="Logging and Monitoring (A.12.4)",
                description="Event logging must be enabled and protected",
                passed=config.security.enable_audit_logging
                and config.logging.redact_secrets,
                severity="medium",
                details="Audit logging and log protection",
                recommendation="Enable audit logging with secret redaction",
            )
        )

        return checks

    def _check_etsi_qkd_014(self) -> list[ComplianceCheck]:
        """Check ETSI GS QKD 014 (KME-SA Interface) compliance."""
        checks: list[ComplianceCheck] = []
        config = self._config if self._config is not None else get_config()

        # KME-SA interface defined and HSM enabled
        hsm_available = config.enterprise.enable_hsm
        checks.append(
            ComplianceCheck(
                check_id="ETSI-014-001",
                standard=ComplianceStandard.ETSI_GS_QKD_014,
                requirement="KME-SA interface compliance",
                description=(
                    "Key Management Entity (KME) interface must be defined and HSM "
                    "enabled to conform to ETSI GS QKD 014 key delivery specification"
                ),
                passed=hsm_available,
                severity="critical",
                details=f"HSM enabled: {hsm_available}",
                recommendation="Enable HSM integration to provide a KME interface",
            )
        )

        # Key format compliance (hex-encoded, proper length)
        key_len_ok = config.security.min_key_length >= 128
        checks.append(
            ComplianceCheck(
                check_id="ETSI-014-002",
                standard=ComplianceStandard.ETSI_GS_QKD_014,
                requirement="Key format compliance",
                description=(
                    "Keys must be delivered in hex-encoded format with a minimum "
                    "length of 128 bits as specified by ETSI 014"
                ),
                passed=key_len_ok,
                severity="critical",
                details=f"Minimum key length: {config.security.min_key_length} bits "
                f"(requires >= 128)",
                recommendation="Set min_key_length to at least 128 bits for ETSI 014 compliance",
            )
        )

        # Identity authentication (mutual authentication between KME and SA)
        auth_ok = config.security.require_authentication
        checks.append(
            ComplianceCheck(
                check_id="ETSI-014-003",
                standard=ComplianceStandard.ETSI_GS_QKD_014,
                requirement="Identity authentication",
                description=(
                    "Mutual authentication between Key Management Entity (KME) and "
                    "Security Application (SA) must be enforced"
                ),
                passed=auth_ok,
                severity="high",
                details=f"Authentication required: {auth_ok}",
                recommendation="Enable authentication to enforce mutual KME-SA identity verification",
            )
        )

        # Key churn (key refresh/rotation)
        rotation_ok = (
            config.security.enable_key_rotation
            and config.security.key_rotation_interval_seconds <= 3600
        )
        checks.append(
            ComplianceCheck(
                check_id="ETSI-014-004",
                standard=ComplianceStandard.ETSI_GS_QKD_014,
                requirement="Key churn",
                description=(
                    "Key refresh or rotation must be enabled with a reasonable "
                    "interval (<= 1 hour) to satisfy key churn requirements"
                ),
                passed=rotation_ok,
                severity="high",
                details=f"Key rotation enabled: {config.security.enable_key_rotation}, "
                f"Interval: {config.security.key_rotation_interval_seconds}s",
                recommendation=(
                    "Enable key rotation with an interval of 3600 seconds or less"
                ),
            )
        )

        return checks

    def _check_etsi_qkd_016(self) -> list[ComplianceCheck]:
        """Check ETSI GS QKD 016 (Common Criteria Protection Profile) compliance."""
        checks: list[ComplianceCheck] = []
        config = self._config if self._config is not None else get_config()

        # Security target — production mode required
        mode_ok = config.security.mode == SecurityMode.PRODUCTION
        checks.append(
            ComplianceCheck(
                check_id="ETSI-016-001",
                standard=ComplianceStandard.ETSI_GS_QKD_016,
                requirement="Security target compliance",
                description=(
                    "System must meet Common Criteria security target requirements "
                    "by operating in PRODUCTION security mode"
                ),
                passed=mode_ok,
                severity="critical",
                details=f"Current security mode: {config.security.mode.value}",
                recommendation="Set security mode to 'production' for Common Criteria compliance",
            )
        )

        # Authentication mechanisms
        checks.append(
            ComplianceCheck(
                check_id="ETSI-016-002",
                standard=ComplianceStandard.ETSI_GS_QKD_016,
                requirement="Authentication mechanisms",
                description=(
                    "Authentication mechanisms must be in place to satisfy "
                    "Common Criteria security functional requirements"
                ),
                passed=config.security.require_authentication,
                severity="critical",
                details=f"Authentication required: {config.security.require_authentication}",
                recommendation="Enable authentication for Common Criteria compliance",
            )
        )

        # Audit logging
        checks.append(
            ComplianceCheck(
                check_id="ETSI-016-003",
                standard=ComplianceStandard.ETSI_GS_QKD_016,
                requirement="Audit logging",
                description=(
                    "Audit logging must be enabled to meet Common Criteria "
                    "audit functional requirements"
                ),
                passed=config.security.enable_audit_logging,
                severity="high",
                details=f"Audit logging enabled: {config.security.enable_audit_logging}",
                recommendation="Enable audit logging for Common Criteria compliance",
            )
        )

        return checks

    def _check_iso_23837(self) -> list[ComplianceCheck]:
        """Check ISO/IEC 23837 (QKD Security Requirements) compliance."""
        checks: list[ComplianceCheck] = []
        config = self._config if self._config is not None else get_config()

        # Security requirements — key length
        key_len_ok = config.security.min_key_length >= 128
        checks.append(
            ComplianceCheck(
                check_id="ISO-23837-001",
                standard=ComplianceStandard.ISO_IEC_23837_1,
                requirement="Security requirements definition",
                description=(
                    "Key length must meet or exceed the minimum security "
                    "requirements defined in ISO/IEC 23837 (128 bits)"
                ),
                passed=key_len_ok,
                severity="critical",
                details=f"Minimum key length: {config.security.min_key_length} bits",
                recommendation="Ensure min_key_length is at least 128 bits",
            )
        )

        # QBER threshold
        qber_ok = config.security.max_qber_threshold <= 0.11
        checks.append(
            ComplianceCheck(
                check_id="ISO-23837-002",
                standard=ComplianceStandard.ISO_IEC_23837_2,
                requirement="QBER threshold",
                description=(
                    "Quantum Bit Error Rate (QBER) threshold must be within the "
                    "acceptable range (<= 0.11) defined by ISO/IEC 23837"
                ),
                passed=qber_ok,
                severity="critical",
                details=f"Max QBER threshold: {config.security.max_qber_threshold}",
                recommendation="Set max_qber_threshold to 0.11 or lower",
            )
        )

        # Key distillation parameters
        distillation_ok = (
            config.security.enable_key_rotation and config.security.enable_audit_logging
        )
        checks.append(
            ComplianceCheck(
                check_id="ISO-23837-003",
                standard=ComplianceStandard.ISO_IEC_23837_2,
                requirement="Key distillation parameters",
                description=(
                    "Key rotation and audit logging must both be enabled for "
                    "proper key distillation as required by ISO/IEC 23837"
                ),
                passed=distillation_ok,
                severity="high",
                details=f"Key rotation: {config.security.enable_key_rotation}, "
                f"Audit logging: {config.security.enable_audit_logging}",
                recommendation="Enable both key rotation and audit logging",
            )
        )

        return checks
