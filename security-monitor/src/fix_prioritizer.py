"""Prioritize vulnerability fixes."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class FixPrioritizer:
    """Prioritize vulnerability fixes."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize fix prioritizer.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.severity_weights = config.get("severity_weights", {
            "critical": 10.0,
            "high": 7.0,
            "medium": 4.0,
            "low": 1.0,
        })
        self.cvss_thresholds = config.get("cvss_thresholds", {
            "critical": 9.0,
            "high": 7.0,
            "medium": 4.0,
            "low": 0.0,
        })

    def prioritize_fix(self, vulnerability_id: str) -> Dict[str, any]:
        """Prioritize fix for vulnerability.

        Args:
            vulnerability_id: Vulnerability identifier.

        Returns:
            Dictionary with prioritization results.
        """
        vulnerability = self.db_manager.get_vulnerability(vulnerability_id)

        if not vulnerability:
            return {"error": "Vulnerability not found"}

        priority_score = self._calculate_priority_score(vulnerability)
        priority_level = self._determine_priority_level(priority_score, vulnerability)

        fix = self.db_manager.add_fix(
            vulnerability_id=vulnerability.id,
            fix_type="patch",
            fix_description=f"Fix for {vulnerability.title}",
            priority=priority_level,
            estimated_effort_hours=self._estimate_effort(vulnerability),
        )

        return {
            "vulnerability_id": vulnerability_id,
            "priority_score": priority_score,
            "priority_level": priority_level,
            "fix_id": fix.id,
            "estimated_effort_hours": fix.estimated_effort_hours,
        }

    def _calculate_priority_score(self, vulnerability) -> float:
        """Calculate priority score for vulnerability.

        Args:
            vulnerability: Vulnerability object.

        Returns:
            Priority score (0.0 to 100.0).
        """
        base_score = self.severity_weights.get(vulnerability.severity, 1.0) * 10.0

        if vulnerability.cvss_score:
            cvss_contribution = vulnerability.cvss_score
            base_score += cvss_contribution

        days_open = 0
        if vulnerability.discovered_at:
            days_open = (datetime.utcnow() - vulnerability.discovered_at).days

        if days_open > 30:
            base_score += 5.0
        elif days_open > 14:
            base_score += 2.0

        if vulnerability.cve_id:
            base_score += 3.0

        return min(base_score, 100.0)

    def _determine_priority_level(self, priority_score: float, vulnerability) -> str:
        """Determine priority level.

        Args:
            priority_score: Priority score.
            vulnerability: Vulnerability object.

        Returns:
            Priority level (low, medium, high, urgent).
        """
        if vulnerability.severity == "critical" or priority_score >= 80:
            return "urgent"
        elif vulnerability.severity == "high" or priority_score >= 60:
            return "high"
        elif vulnerability.severity == "medium" or priority_score >= 40:
            return "medium"
        else:
            return "low"

    def _estimate_effort(self, vulnerability) -> float:
        """Estimate effort to fix vulnerability.

        Args:
            vulnerability: Vulnerability object.

        Returns:
            Estimated effort in hours.
        """
        base_effort = {
            "critical": 16.0,
            "high": 8.0,
            "medium": 4.0,
            "low": 2.0,
        }

        effort = base_effort.get(vulnerability.severity, 4.0)

        if vulnerability.cvss_score and vulnerability.cvss_score >= 9.0:
            effort *= 1.5

        return effort

    def get_prioritized_fixes(
        self, application_id: Optional[int] = None, limit: int = 20
    ) -> List[Dict[str, any]]:
        """Get prioritized list of fixes.

        Args:
            application_id: Optional application ID to filter by.
            limit: Maximum number of fixes to return.

        Returns:
            List of prioritized fix dictionaries.
        """
        open_vulnerabilities = self.db_manager.get_open_vulnerabilities(
            application_id=application_id, limit=100
        )

        prioritized = []

        for vulnerability in open_vulnerabilities:
            priority_score = self._calculate_priority_score(vulnerability)
            priority_level = self._determine_priority_level(priority_score, vulnerability)

            fixes = self.db_manager.get_vulnerability_fixes(vulnerability.id)
            latest_fix = fixes[0] if fixes else None

            prioritized.append({
                "vulnerability_id": vulnerability.vulnerability_id,
                "title": vulnerability.title,
                "severity": vulnerability.severity,
                "cvss_score": vulnerability.cvss_score,
                "priority_score": priority_score,
                "priority_level": priority_level,
                "estimated_effort_hours": latest_fix.estimated_effort_hours if latest_fix else self._estimate_effort(vulnerability),
            })

        prioritized.sort(key=lambda x: x["priority_score"], reverse=True)

        return prioritized[:limit]
