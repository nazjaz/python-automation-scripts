"""Generate security compliance reports."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class ComplianceReporter:
    """Generate security compliance reports."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize compliance reporter.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.compliance_thresholds = config.get("compliance_thresholds", {
            "critical": 0,
            "high": 5,
            "medium": 20,
            "low": 50,
        })

    def generate_compliance_report(
        self, application_id: int, report_type: str = "security"
    ) -> Dict[str, any]:
        """Generate compliance report for application.

        Args:
            application_id: Application ID.
            report_type: Report type (security, compliance, audit).

        Returns:
            Dictionary with compliance report information.
        """
        session = self.db_manager.get_session()
        try:
            from src.database import Vulnerability

            vulnerabilities = (
                session.query(Vulnerability)
                .filter(Vulnerability.application_id == application_id)
                .all()
            )

            open_vulnerabilities = [v for v in vulnerabilities if v.status == "open"]

            critical_count = len([v for v in open_vulnerabilities if v.severity == "critical"])
            high_count = len([v for v in open_vulnerabilities if v.severity == "high"])
            medium_count = len([v for v in open_vulnerabilities if v.severity == "medium"])
            low_count = len([v for v in open_vulnerabilities if v.severity == "low"])

            compliance_status, compliance_score = self._calculate_compliance(
                critical_count, high_count, medium_count, low_count
            )

            from src.database import Application

            application = session.query(Application).filter(Application.id == application_id).first()

            report_id = f"COMP-{application_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            report = self.db_manager.add_compliance_report(
                report_id=report_id,
                application_id=application_id,
                report_type=report_type,
                compliance_status=compliance_status,
                total_vulnerabilities=len(open_vulnerabilities),
                critical_vulnerabilities=critical_count,
                high_vulnerabilities=high_count,
                medium_vulnerabilities=medium_count,
                low_vulnerabilities=low_count,
                compliance_score=compliance_score,
            )

            return {
                "report_id": report_id,
                "application_id": application_id,
                "compliance_status": compliance_status,
                "compliance_score": compliance_score,
                "total_vulnerabilities": len(open_vulnerabilities),
                "critical_vulnerabilities": critical_count,
                "high_vulnerabilities": high_count,
                "medium_vulnerabilities": medium_count,
                "low_vulnerabilities": low_count,
            }
        finally:
            session.close()

    def _calculate_compliance(
        self, critical: int, high: int, medium: int, low: int
    ) -> tuple:
        """Calculate compliance status and score.

        Args:
            critical: Number of critical vulnerabilities.
            high: Number of high severity vulnerabilities.
            medium: Number of medium severity vulnerabilities.
            low: Number of low severity vulnerabilities.

        Returns:
            Tuple of (compliance_status, compliance_score).
        """
        if critical > self.compliance_thresholds["critical"]:
            return ("non_compliant", 0.0)

        if high > self.compliance_thresholds["high"]:
            return ("at_risk", 40.0)

        if medium > self.compliance_thresholds["medium"]:
            return ("at_risk", 60.0)

        if low > self.compliance_thresholds["low"]:
            return ("at_risk", 80.0)

        base_score = 100.0
        score_deduction = (
            critical * 20.0
            + high * 10.0
            + medium * 2.0
            + low * 0.5
        )

        compliance_score = max(base_score - score_deduction, 0.0)

        if compliance_score >= 90:
            status = "compliant"
        elif compliance_score >= 70:
            status = "at_risk"
        else:
            status = "non_compliant"

        return (status, compliance_score)

    def get_compliance_trends(
        self, application_id: int, days: int = 30
    ) -> Dict[str, any]:
        """Get compliance trends over time.

        Args:
            application_id: Application ID.
            days: Number of days to analyze.

        Returns:
            Dictionary with compliance trends.
        """
        reports = self.db_manager.get_recent_compliance_reports(
            application_id=application_id, limit=100
        )

        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_reports = [r for r in reports if r.generated_at >= cutoff]

        if not recent_reports:
            return {
                "days": days,
                "trend": "stable",
                "average_score": 0.0,
            }

        scores = [r.compliance_score for r in recent_reports if r.compliance_score is not None]
        average_score = sum(scores) / len(scores) if scores else 0.0

        trend = self._calculate_trend(scores)

        return {
            "days": days,
            "trend": trend,
            "average_score": average_score,
            "min_score": min(scores) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
        }

    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate trend from scores.

        Args:
            scores: List of compliance scores.

        Returns:
            Trend indicator (improving, declining, stable).
        """
        if len(scores) < 2:
            return "stable"

        mid_point = len(scores) // 2
        first_half_avg = sum(scores[:mid_point]) / len(scores[:mid_point])
        second_half_avg = sum(scores[mid_point:]) / len(scores[mid_point:])

        if second_half_avg > first_half_avg + 5:
            return "improving"
        elif second_half_avg < first_half_avg - 5:
            return "declining"
        else:
            return "stable"
