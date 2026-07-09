"""Compliance checking and reporting for QKDpy.

This module provides automated compliance checks against security
standards and generates compliance reports.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from ..config import SecurityMode, get_config
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ComplianceStandard(Enum):
    """Supported compliance standards."""

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
    ) -> None:
        """Initialize compliance checker.

        Args:
            standards: Standards to check (default: NIST SP 800-57)
        """
        self.standards = standards or [ComplianceStandard.NIST_SP_800_57]

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
        config = get_config()

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
        config = get_config()

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
        config = get_config()

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
