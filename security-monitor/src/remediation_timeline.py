"""Generate remediation timelines for vulnerabilities."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class RemediationTimeline:
    """Generate remediation timelines."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize remediation timeline generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.timeline_parameters = config.get("timeline_parameters", {
            "critical": {"days": 1, "buffer_days": 0},
            "high": {"days": 7, "buffer_days": 2},
            "medium": {"days": 30, "buffer_days": 5},
            "low": {"days": 90, "buffer_days": 10},
        })

    def generate_timeline(self, vulnerability_id: str) -> Dict[str, any]:
        """Generate remediation timeline for vulnerability.

        Args:
            vulnerability_id: Vulnerability identifier.

        Returns:
            Dictionary with timeline information.
        """
        vulnerability = self.db_manager.get_vulnerability(vulnerability_id)

        if not vulnerability:
            return {"error": "Vulnerability not found"}

        target_fix_date = self._calculate_target_fix_date(vulnerability)
        remediation_steps = self._generate_remediation_steps(vulnerability)

        timeline = self.db_manager.add_remediation_timeline(
            vulnerability_id=vulnerability.id,
            target_fix_date=target_fix_date,
            remediation_steps=remediation_steps,
            estimated_completion_date=target_fix_date,
        )

        days_until_target = (target_fix_date - datetime.utcnow()).days

        return {
            "vulnerability_id": vulnerability_id,
            "target_fix_date": target_fix_date,
            "estimated_completion_date": target_fix_date,
            "days_until_target": days_until_target,
            "remediation_steps": remediation_steps,
            "timeline_id": timeline.id,
        }

    def _calculate_target_fix_date(self, vulnerability) -> datetime:
        """Calculate target fix date based on severity.

        Args:
            vulnerability: Vulnerability object.

        Returns:
            Target fix date.
        """
        params = self.timeline_parameters.get(vulnerability.severity, {"days": 30, "buffer_days": 5})

        target_days = params["days"]
        if vulnerability.cvss_score and vulnerability.cvss_score >= 9.0:
            target_days = max(target_days - 2, 1)

        return datetime.utcnow() + timedelta(days=target_days)

    def _generate_remediation_steps(self, vulnerability) -> str:
        """Generate remediation steps.

        Args:
            vulnerability: Vulnerability object.

        Returns:
            Remediation steps as JSON string.
        """
        import json

        steps = []

        if vulnerability.cve_id:
            steps.append(f"Review CVE-{vulnerability.cve_id} details and patches")
        else:
            steps.append(f"Review vulnerability details: {vulnerability.title}")

        if vulnerability.component:
            steps.append(f"Identify affected component: {vulnerability.component}")

        if vulnerability.severity in ["critical", "high"]:
            steps.append("Apply security patch or update")
            steps.append("Test fix in staging environment")
        else:
            steps.append("Plan fix implementation")
            steps.append("Schedule fix deployment")

        steps.append("Deploy fix to production")
        steps.append("Verify fix and close vulnerability")

        return json.dumps(steps)

    def get_timeline_summary(
        self, application_id: Optional[int] = None
    ) -> Dict[str, any]:
        """Get summary of remediation timelines.

        Args:
            application_id: Optional application ID to filter by.

        Returns:
            Dictionary with timeline summary.
        """
        session = self.db_manager.get_session()
        try:
            from src.database import Vulnerability, RemediationTimeline

            query = (
                session.query(RemediationTimeline)
                .join(Vulnerability)
                .filter(Vulnerability.status == "open")
            )

            if application_id:
                query = query.filter(Vulnerability.application_id == application_id)

            timelines = query.all()

            if not timelines:
                return {
                    "total_timelines": 0,
                    "on_track": 0,
                    "at_risk": 0,
                    "overdue": 0,
                }

            on_track = 0
            at_risk = 0
            overdue = 0

            for timeline in timelines:
                days_until = (timeline.target_fix_date - datetime.utcnow()).days

                if days_until < 0:
                    overdue += 1
                elif days_until <= 3:
                    at_risk += 1
                else:
                    on_track += 1

            return {
                "total_timelines": len(timelines),
                "on_track": on_track,
                "at_risk": at_risk,
                "overdue": overdue,
            }
        finally:
            session.close()

    def get_upcoming_deadlines(
        self, days: int = 7, application_id: Optional[int] = None
    ) -> List[Dict[str, any]]:
        """Get vulnerabilities with upcoming fix deadlines.

        Args:
            days: Number of days to look ahead.
            application_id: Optional application ID to filter by.

        Returns:
            List of vulnerability dictionaries with upcoming deadlines.
        """
        session = self.db_manager.get_session()
        try:
            from src.database import Vulnerability, RemediationTimeline

            cutoff = datetime.utcnow() + timedelta(days=days)

            query = (
                session.query(RemediationTimeline)
                .join(Vulnerability)
                .filter(
                    Vulnerability.status == "open",
                    RemediationTimeline.target_fix_date <= cutoff,
                    RemediationTimeline.target_fix_date >= datetime.utcnow(),
                )
                .order_by(RemediationTimeline.target_fix_date.asc())
            )

            if application_id:
                query = query.filter(Vulnerability.application_id == application_id)

            timelines = query.all()

            upcoming = []
            for timeline in timelines:
                days_until = (timeline.target_fix_date - datetime.utcnow()).days
                upcoming.append({
                    "vulnerability_id": timeline.vulnerability.vulnerability_id,
                    "title": timeline.vulnerability.title,
                    "severity": timeline.vulnerability.severity,
                    "target_fix_date": timeline.target_fix_date,
                    "days_until": days_until,
                })

            return upcoming
        finally:
            session.close()
