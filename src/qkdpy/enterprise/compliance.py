"""Config auditing and reporting for QKDpy.

This module provides automated configuration audits against security
standards and generates audit reports.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from html import escape
from typing import Any

from ..config import (
    QKDConfig,
    SecurityMode,
    get_config,
)
from ..utils.logging_config import get_logger
from .hsm_interface import HSMProvider, _hsm_is_hardware_backed

logger = get_logger(__name__)


# Truthfulness guard for HSM-backed compliance checks.
#
# ``config.enterprise.enable_hsm`` only records that the operator *requested* HSM
# support. It does NOT tell us whether a real, hardware-backed HSM is actually in
# use: in this build the only available provider is ``HSMProvider.SOFTWARE`` — an
# in-memory simulation that is explicitly NOT production-grade. We therefore must
# not auto-mark "FIPS/HSM compliant" from the config flag alone. A compliant
# FIPS/ETSI result requires a hardware-backed provider, which does not exist here.
#
# ``_hsm_is_hardware_backed`` lives in ``hsm_interface`` and performs a real
# capability check (it inspects the active provider). This wrapper keeps the
# config-aware signature used by the checks below.
def _hsm_is_hardware_backed_for_config(config: QKDConfig) -> bool:
    """Whether the configured HSM is actually hardware-backed."""
    return _hsm_is_hardware_backed(HSMProvider.SOFTWARE if config.enterprise.enable_hsm else None)


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

    def export_html(self) -> str:
        """Export report as a self-contained HTML page."""
        rate = (
            self.passed_checks / self.total_checks * 100
            if self.total_checks > 0
            else 0.0
        )
        status_colour = "#22c55e" if self.overall_compliant else "#ef4444"
        standards_str = ", ".join(escape(s.value) for s in self.standards_checked)
        severity_colours = {
            "critical": "#dc2626",
            "high": "#ea580c",
            "medium": "#ca8a04",
            "low": "#2563eb",
        }

        rows_html = ""
        for c in self.checks:
            badge = "&#9989;" if c.passed else "&#10060;"
            colour = severity_colours.get(c.severity, "#2563eb")
            rows_html += f"""
            <tr>
                <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;font-family:monospace;font-size:13px">{escape(c.check_id)}</td>
                <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb">{escape(c.requirement)}</td>
                <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb">{badge}</td>
                <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb"><span style="background:{colour};color:#fff;padding:2px 8px;border-radius:9999px;font-size:12px">{escape(c.severity)}</span></td>
            </tr>"""

        failed_html = ""
        for c in self.get_failed_checks():
            details_html = ""
            if c.details:
                details_html = f'<p style="margin:4px 0;font-size:13px"><strong>Details:</strong> {escape(c.details)}</p>'
            rec_html = ""
            if c.recommendation:
                rec_html = f'<p style="margin:4px 0;font-size:13px"><strong>Recommendation:</strong> {escape(c.recommendation)}</p>'
            failed_html += f"""
            <div style="margin-bottom:16px;padding:16px;background:#fef2f2;border-left:4px solid #ef4444;border-radius:6px">
                <h3 style="margin:0 0 4px;font-size:15px;font-weight:600">[{escape(c.check_id)}] {escape(c.requirement)}</h3>
                <p style="margin:4px 0;color:#6b7280;font-size:13px">{escape(c.description)}</p>
                {details_html}
                {rec_html}
            </div>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Compliance Report — {escape(self.report_id)}</title>
</head>
<body style="margin:0;padding:24px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f9fafb;color:#111827">
<div style="max-width:960px;margin:0 auto;background:#fff;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.1);padding:32px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px">
        <h1 style="margin:0;font-size:24px;font-weight:700">Compliance Report</h1>
        <span style="background:{status_colour};color:#fff;padding:6px 16px;border-radius:9999px;font-size:14px;font-weight:600">{"COMPLIANT" if self.overall_compliant else "NON-COMPLIANT"}</span>
    </div>
    <table style="width:100%;font-size:14px;margin-bottom:24px">
        <tr><td style="padding:4px 0;color:#6b7280">Report ID</td><td style="padding:4px 0;font-family:monospace">{escape(self.report_id)}</td></tr>
        <tr><td style="padding:4px 0;color:#6b7280">Generated</td><td style="padding:4px 0">{self.generated_at.isoformat()}</td></tr>
        <tr><td style="padding:4px 0;color:#6b7280">Standards</td><td style="padding:4px 0">{standards_str}</td></tr>
    </table>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:32px">
        <div style="background:#f3f4f6;border-radius:8px;padding:16px;text-align:center"><div style="font-size:28px;font-weight:700">{self.total_checks}</div><div style="font-size:12px;color:#6b7280">Total</div></div>
        <div style="background:#f0fdf4;border-radius:8px;padding:16px;text-align:center"><div style="font-size:28px;font-weight:700;color:#16a34a">{self.passed_checks}</div><div style="font-size:12px;color:#6b7280">Passed</div></div>
        <div style="background:#fef2f2;border-radius:8px;padding:16px;text-align:center"><div style="font-size:28px;font-weight:700;color:#dc2626">{self.failed_checks}</div><div style="font-size:12px;color:#6b7280">Failed</div></div>
        <div style="background:#eff6ff;border-radius:8px;padding:16px;text-align:center"><div style="font-size:28px;font-weight:700;color:#2563eb">{rate:.1f}%</div><div style="font-size:12px;color:#6b7280">Rate</div></div>
    </div>
    <h2 style="font-size:18px;font-weight:600;margin:0 0 12px">All Checks</h2>
    <table style="width:100%;border-collapse:collapse;margin-bottom:32px">
        <thead>
            <tr style="background:#f9fafb;text-align:left">
                <th style="padding:8px 12px;font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase">ID</th>
                <th style="padding:8px 12px;font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase">Requirement</th>
                <th style="padding:8px 12px;font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase">Status</th>
                <th style="padding:8px 12px;font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase">Severity</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    {failed_html if self.failed_checks > 0 else ""}
    <p style="font-size:12px;color:#9ca3af;margin:32px 0 0;text-align:center">Generated by QKDpy Enterprise Compliance Suite</p>
</div>
</body>
</html>"""


class ConfigAudit:
    """Audits QKD system configuration against named standards.

    This is a *config audit*, not a third-party compliance certification. It
    checks the local configuration against best-practice standards (ETSI,
    NIST, ISO, FIPS) and reports findings. It does not certify compliance with
    any external body, and it fails closed on capabilities it cannot prove
    (e.g. hardware-backed HSM).
    """

    def __init__(
        self,
        standards: list[ComplianceStandard] | None = None,
        config: QKDConfig | None = None,
    ) -> None:
        """Initialize config audit.

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

        # HSM requirement — must be a *hardware-backed* HSM, not just requested.
        hsm_enabled = config.enterprise.enable_hsm
        hsm_hardware_backed = _hsm_is_hardware_backed_for_config(config)
        checks.append(
            ComplianceCheck(
                check_id="FIPS-140-001",
                standard=ComplianceStandard.FIPS_140_2,
                requirement="Hardware security module",
                description="FIPS 140-2 Level 2+ requires a hardware-backed HSM for key storage",
                passed=hsm_hardware_backed,
                severity="critical",
                details=(
                    f"HSM requested: {hsm_enabled}, "
                    f"hardware-backed: {hsm_hardware_backed}"
                ),
                recommendation=(
                    "Configure a hardware-backed HSM (e.g. PKCS#11 / cloud HSM). "
                    "Software simulation does not satisfy FIPS 140-2 Level 2+."
                ),
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

        # KME-SA interface defined and backed by a *hardware* HSM
        hsm_enabled = config.enterprise.enable_hsm
        hsm_hardware_backed = _hsm_is_hardware_backed_for_config(config)
        checks.append(
            ComplianceCheck(
                check_id="ETSI-014-001",
                standard=ComplianceStandard.ETSI_GS_QKD_014,
                requirement="KME-SA interface compliance",
                description=(
                    "Key Management Entity (KME) interface must be defined and backed "
                    "by a hardware-backed HSM to conform to ETSI GS QKD 014 key "
                    "delivery specification"
                ),
                passed=hsm_hardware_backed,
                severity="critical",
                details=(
                    f"HSM requested: {hsm_enabled}, "
                    f"hardware-backed: {hsm_hardware_backed}"
                ),
                recommendation=(
                    "Configure a hardware-backed HSM to provide a QKD-certified KME "
                    "interface. Software simulation is insufficient."
                ),
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
