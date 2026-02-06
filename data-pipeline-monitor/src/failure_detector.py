"""Detect pipeline failures."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class FailureDetector:
    """Detect pipeline failures."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize failure detector.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.failure_patterns = config.get("failure_patterns", {})
        self.severity_rules = config.get("severity_rules", {})

    def detect_failures(
        self, pipeline_id: Optional[int] = None, hours: int = 1
    ) -> List[Dict[str, any]]:
        """Detect failures in pipeline runs.

        Args:
            pipeline_id: Optional pipeline ID to filter by.
            hours: Number of hours to check.

        Returns:
            List of detected failure dictionaries.
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        session = self.db_manager.get_session()

        try:
            from src.database import PipelineRun

            query = session.query(PipelineRun).filter(
                PipelineRun.status == "failed",
                PipelineRun.start_time >= cutoff_time,
            )

            if pipeline_id:
                query = query.filter(PipelineRun.pipeline_id == pipeline_id)

            failed_runs = query.all()

            detected_failures = []
            for run in failed_runs:
                failure_info = self._analyze_failure(run)
                if failure_info:
                    failure = self.db_manager.add_failure(
                        pipeline_id=run.pipeline_id,
                        failure_type=failure_info["failure_type"],
                        severity=failure_info["severity"],
                        error_message=failure_info["error_message"],
                        run_id=run.run_id,
                    )
                    detected_failures.append({
                        "id": failure.id,
                        "pipeline_id": failure.pipeline_id,
                        "failure_type": failure.failure_type,
                        "severity": failure.severity,
                        "error_message": failure.error_message,
                        "detected_at": failure.detected_at,
                    })

            return detected_failures
        finally:
            session.close()

    def _analyze_failure(self, run) -> Optional[Dict[str, any]]:
        """Analyze a failed run to determine failure type and severity.

        Args:
            run: PipelineRun object.

        Returns:
            Dictionary with failure information or None.
        """
        error_message = run.error_message or "Unknown error"
        error_lower = error_message.lower()

        failure_type = "unknown"
        severity = "medium"

        for pattern_type, patterns in self.failure_patterns.items():
            for pattern in patterns:
                if pattern.lower() in error_lower:
                    failure_type = pattern_type
                    break
            if failure_type != "unknown":
                break

        if failure_type == "unknown":
            if "timeout" in error_lower:
                failure_type = "timeout"
            elif "connection" in error_lower:
                failure_type = "connection"
            elif "validation" in error_lower:
                failure_type = "validation"
            elif "data" in error_lower:
                failure_type = "data_error"

        severity = self._determine_severity(failure_type, run)

        return {
            "failure_type": failure_type,
            "severity": severity,
            "error_message": error_message,
        }

    def _determine_severity(self, failure_type: str, run) -> str:
        """Determine failure severity.

        Args:
            failure_type: Failure type.
            run: PipelineRun object.

        Returns:
            Severity level (low, medium, high, critical).
        """
        severity_map = self.severity_rules.get("failure_types", {})

        if failure_type in severity_map:
            return severity_map[failure_type]

        if run.records_failed and run.records_processed:
            failure_rate = run.records_failed / run.records_processed
            if failure_rate > 0.5:
                return "critical"
            elif failure_rate > 0.2:
                return "high"
            elif failure_rate > 0.1:
                return "medium"
            else:
                return "low"

        return "medium"

    def get_failure_statistics(
        self, pipeline_id: Optional[int] = None, days: int = 7
    ) -> Dict[str, any]:
        """Get failure statistics.

        Args:
            pipeline_id: Optional pipeline ID to filter by.
            days: Number of days to analyze.

        Returns:
            Dictionary with failure statistics.
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        session = self.db_manager.get_session()

        try:
            from src.database import Failure

            query = session.query(Failure).filter(Failure.detected_at >= cutoff_time)

            if pipeline_id:
                query = query.filter(Failure.pipeline_id == pipeline_id)

            failures = query.all()

            from collections import Counter

            failure_types = Counter(f.failure_type for f in failures)
            severities = Counter(f.severity for f in failures)

            open_failures = len([f for f in failures if f.resolution_status == "open"])

            return {
                "total_failures": len(failures),
                "open_failures": open_failures,
                "resolved_failures": len(failures) - open_failures,
                "by_type": dict(failure_types),
                "by_severity": dict(severities),
                "days_analyzed": days,
            }
        finally:
            session.close()
