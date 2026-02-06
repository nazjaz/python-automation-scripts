"""Generate bug reports from error analysis."""

from datetime import datetime
from typing import Dict, List, Optional


class BugReportGenerator:
    """Generate bug reports with reproduction steps and priority rankings."""

    def __init__(self, db_manager, config: Dict):
        """Initialize bug report generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.priority_rules = config.get("priority_rules", {})
        self.reproduction_template = config.get("reproduction_template", {})

    def generate_bug_report(
        self,
        error_pattern: Dict[str, any],
        errors: List[Dict[str, any]],
        error_rate: Optional[float] = None,
    ) -> Dict[str, any]:
        """Generate bug report from error pattern and errors.

        Args:
            error_pattern: Error pattern dictionary.
            errors: List of errors matching the pattern.
            error_rate: Error rate percentage.

        Returns:
            Bug report dictionary.
        """
        title = self._generate_title(error_pattern, errors)
        description = self._generate_description(error_pattern, errors)
        reproduction_steps = self._generate_reproduction_steps(errors)
        priority = self._determine_priority(error_pattern, errors, error_rate)
        severity = self._determine_severity(error_pattern, errors)

        affected_users = len(set(e.get("user_id") for e in errors if e.get("user_id")))

        bug_report = self.db_manager.create_bug_report(
            title=title,
            description=description,
            priority=priority,
            severity=severity,
            reproduction_steps=reproduction_steps,
            category=error_pattern.get("error_type", ""),
            error_rate=error_rate,
            affected_users=affected_users,
        )

        for error in errors:
            if isinstance(error, dict) and "id" in error:
                self.db_manager.link_error_to_bug_report(error["id"], bug_report.id)
            elif hasattr(error, "id"):
                self.db_manager.link_error_to_bug_report(error.id, bug_report.id)

        return {
            "id": bug_report.id,
            "title": bug_report.title,
            "description": bug_report.description,
            "priority": bug_report.priority,
            "severity": bug_report.severity,
            "reproduction_steps": bug_report.reproduction_steps,
            "error_rate": bug_report.error_rate,
            "affected_users": bug_report.affected_users,
        }

    def _generate_title(self, error_pattern: Dict[str, any], errors: List[Dict[str, any]]) -> str:
        """Generate bug report title.

        Args:
            error_pattern: Error pattern dictionary.
            errors: List of errors.

        Returns:
            Bug report title.
        """
        error_type = error_pattern.get("error_type", "Error")
        frequency = error_pattern.get("frequency", len(errors))
        trend = error_pattern.get("trend", "stable")

        title = f"{error_type}: {frequency} occurrence(s)"
        if trend == "increasing":
            title += " (increasing trend)"
        elif trend == "decreasing":
            title += " (decreasing trend)"

        return title

    def _generate_description(
        self, error_pattern: Dict[str, any], errors: List[Dict[str, any]]
    ) -> str:
        """Generate bug report description.

        Args:
            error_pattern: Error pattern dictionary.
            errors: List of errors.

        Returns:
            Bug report description.
        """
        error_message = error_pattern.get("error_message", "")
        error_type = error_pattern.get("error_type", "")
        frequency = error_pattern.get("frequency", len(errors))
        first_seen = error_pattern.get("first_seen", datetime.utcnow())
        last_seen = error_pattern.get("last_seen", datetime.utcnow())

        description = f"Error Type: {error_type}\n\n"
        description += f"Error Message: {error_message}\n\n"
        description += f"Frequency: {frequency} occurrence(s)\n"
        description += f"First Seen: {first_seen}\n"
        description += f"Last Seen: {last_seen}\n\n"

        if errors:
            sample_error = errors[0]
            if isinstance(sample_error, dict):
                stack_trace = sample_error.get("stack_trace", "")
                if stack_trace:
                    description += f"Stack Trace:\n{stack_trace[:500]}\n"

        return description

    def _generate_reproduction_steps(self, errors: List[Dict[str, any]]) -> str:
        """Generate reproduction steps from errors.

        Args:
            errors: List of errors.

        Returns:
            Reproduction steps text.
        """
        if not errors:
            return "Unable to determine reproduction steps from available error data."

        steps = []
        steps.append("1. Review error logs and identify common patterns")
        steps.append("2. Check application state at time of error")
        steps.append("3. Attempt to reproduce using error context")

        sample_error = errors[0]
        if isinstance(sample_error, dict):
            user_id = sample_error.get("user_id")
            request_id = sample_error.get("request_id")
            environment = sample_error.get("environment")

            if user_id:
                steps.append(f"4. Check user context: user_id={user_id}")
            if request_id:
                steps.append(f"5. Review request details: request_id={request_id}")
            if environment:
                steps.append(f"6. Verify environment: {environment}")

        steps.append("7. Monitor error rate and pattern trends")
        steps.append("8. Review stack trace for root cause")

        return "\n".join(steps)

    def _determine_priority(
        self,
        error_pattern: Dict[str, any],
        errors: List[Dict[str, any]],
        error_rate: Optional[float],
    ) -> str:
        """Determine bug report priority.

        Args:
            error_pattern: Error pattern dictionary.
            errors: List of errors.
            error_rate: Error rate percentage.

        Returns:
            Priority level (low, medium, high, urgent).
        """
        frequency = error_pattern.get("frequency", len(errors))
        trend = error_pattern.get("trend", "stable")
        severity = error_pattern.get("severity", "medium")

        if error_rate and error_rate > 10.0:
            return "urgent"
        elif error_rate and error_rate > 5.0:
            return "high"
        elif frequency >= 100 or trend == "increasing":
            return "high"
        elif frequency >= 50:
            return "medium"
        elif severity == "critical":
            return "high"
        elif severity == "high":
            return "medium"
        else:
            return "low"

    def _determine_severity(
        self, error_pattern: Dict[str, any], errors: List[Dict[str, any]]
    ) -> str:
        """Determine bug report severity.

        Args:
            error_pattern: Error pattern dictionary.
            errors: List of errors.

        Returns:
            Severity level (low, medium, high, critical).
        """
        severity_counts = {}
        for error in errors:
            if isinstance(error, dict):
                severity = error.get("severity", "medium")
            else:
                severity = getattr(error, "severity", "medium") if hasattr(error, "severity") else "medium"

            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        if severity_counts.get("critical", 0) > 0:
            return "critical"
        elif severity_counts.get("high", 0) > len(errors) * 0.5:
            return "high"
        elif severity_counts.get("medium", 0) > 0:
            return "medium"
        else:
            return "low"

    def generate_reports_for_patterns(
        self, patterns: List[Dict[str, any]], error_rate: Optional[float] = None
    ) -> List[Dict[str, any]]:
        """Generate bug reports for multiple patterns.

        Args:
            patterns: List of error patterns.
            error_rate: Overall error rate.

        Returns:
            List of bug report dictionaries.
        """
        bug_reports = []

        for pattern in patterns:
            session = self.db_manager.get_session()
            try:
                from src.database import ErrorLog

                signature = pattern.get("error_signature")
                if signature:
                    errors = (
                        session.query(ErrorLog)
                        .filter(ErrorLog.pattern_id == pattern.get("id"))
                        .all()
                    )

                    error_dicts = [
                        {
                            "id": e.id,
                            "error_message": e.error_message,
                            "error_type": e.error_type,
                            "stack_trace": e.stack_trace,
                            "user_id": e.user_id,
                            "request_id": e.request_id,
                            "environment": e.environment,
                            "severity": e.severity,
                        }
                        for e in errors
                    ]

                    bug_report = self.generate_bug_report(pattern, error_dicts, error_rate)
                    bug_reports.append(bug_report)
            finally:
                session.close()

        return bug_reports
