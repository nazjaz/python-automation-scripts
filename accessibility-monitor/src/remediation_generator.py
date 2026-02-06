"""Generates remediation reports and tasks."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from src.database import DatabaseManager, Violation, RemediationTask

logger = logging.getLogger(__name__)


class RemediationGenerator:
    """Generates remediation reports and tasks from violations."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize remediation generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.remediation_config = config.get("remediation", {})

    def generate_remediation_tasks(
        self,
        scan_id: Optional[int] = None,
        website_id: Optional[int] = None,
        severity: Optional[str] = None,
    ) -> List[RemediationTask]:
        """Generate remediation tasks from violations.

        Args:
            scan_id: Optional scan ID filter.
            website_id: Optional website ID filter.
            severity: Optional severity filter.

        Returns:
            List of RemediationTask objects.
        """
        violations = self.db_manager.get_violations(
            scan_id=scan_id, severity=severity
        )

        if website_id:
            scans = self.db_manager.get_scans(website_id=website_id)
            scan_ids = [s.id for s in scans]
            violations = [v for v in violations if v.scan_id in scan_ids]

        tasks = []

        for violation in violations:
            existing_task = (
                self.db_manager.get_session()
                .query(RemediationTask)
                .filter(RemediationTask.violation_id == violation.id)
                .first()
            )

            if existing_task:
                continue

            task_description = self._generate_task_description(violation)
            priority = self._determine_priority(violation.severity)

            task = self.db_manager.add_remediation_task(
                violation_id=violation.id,
                task_description=task_description,
                priority=priority,
            )

            tasks.append(task)

        logger.info(
            f"Generated {len(tasks)} remediation tasks",
            extra={"task_count": len(tasks), "scan_id": scan_id, "website_id": website_id},
        )

        return tasks

    def _generate_task_description(self, violation: Violation) -> str:
        """Generate task description from violation.

        Args:
            violation: Violation object.

        Returns:
            Task description string.
        """
        description = f"Fix {violation.violation_type}: {violation.description}"

        if violation.element_selector:
            description += f" (Element: {violation.element_selector})"

        if violation.recommendation:
            description += f" - {violation.recommendation}"

        return description

    def _determine_priority(self, severity: str) -> str:
        """Determine task priority from severity.

        Args:
            severity: Violation severity.

        Returns:
            Priority level string.
        """
        priority_map = {
            "critical": "high",
            "high": "high",
            "medium": "medium",
            "low": "low",
        }

        return priority_map.get(severity, "medium")

    def get_remediation_summary(
        self,
        website_id: Optional[int] = None,
        scan_id: Optional[int] = None,
    ) -> Dict:
        """Get remediation summary.

        Args:
            website_id: Optional website ID filter.
            scan_id: Optional scan ID filter.

        Returns:
            Dictionary with remediation summary.
        """
        if scan_id:
            violations = self.db_manager.get_violations(scan_id=scan_id)
        elif website_id:
            scans = self.db_manager.get_scans(website_id=website_id)
            violations = []
            for scan in scans:
                violations.extend(self.db_manager.get_violations(scan_id=scan.id))
        else:
            violations = self.db_manager.get_violations()

        tasks = (
            self.db_manager.get_session()
            .query(RemediationTask)
            .all()
        )

        if website_id or scan_id:
            violation_ids = [v.id for v in violations]
            tasks = [t for t in tasks if t.violation_id in violation_ids]

        by_severity = {}
        by_status = {"pending": 0, "in_progress": 0, "completed": 0}

        for violation in violations:
            severity = violation.severity
            by_severity[severity] = by_severity.get(severity, 0) + 1

        for task in tasks:
            status = task.status
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total_violations": len(violations),
            "violations_by_severity": by_severity,
            "total_tasks": len(tasks),
            "tasks_by_status": by_status,
            "tasks_by_priority": self._group_tasks_by_priority(tasks),
        }

    def _group_tasks_by_priority(self, tasks: List[RemediationTask]) -> Dict:
        """Group tasks by priority.

        Args:
            tasks: List of RemediationTask objects.

        Returns:
            Dictionary mapping priority to count.
        """
        by_priority = {"high": 0, "medium": 0, "low": 0}

        for task in tasks:
            priority = task.priority
            by_priority[priority] = by_priority.get(priority, 0) + 1

        return by_priority
