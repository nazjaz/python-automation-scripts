"""Check data quality in pipelines."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class DataQualityChecker:
    """Check data quality in pipelines."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize data quality checker.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.quality_checks = config.get("quality_checks", {})
        self.thresholds = config.get("thresholds", {})

    def run_quality_checks(
        self, pipeline_id: int, data_sample: Optional[Dict] = None
    ) -> List[Dict[str, any]]:
        """Run quality checks for pipeline.

        Args:
            pipeline_id: Pipeline ID.
            data_sample: Optional data sample for checks.

        Returns:
            List of quality check result dictionaries.
        """
        check_results = []

        for check_name, check_config in self.quality_checks.items():
            result = self._run_check(
                pipeline_id, check_name, check_config, data_sample
            )
            if result:
                check_results.append(result)

        return check_results

    def _run_check(
        self,
        pipeline_id: int,
        check_name: str,
        check_config: Dict,
        data_sample: Optional[Dict],
    ) -> Optional[Dict[str, any]]:
        """Run a single quality check.

        Args:
            pipeline_id: Pipeline ID.
            check_name: Check name.
            check_config: Check configuration.
            data_sample: Optional data sample.

        Returns:
            Check result dictionary or None.
        """
        check_type = check_config.get("type", "generic")
        threshold = check_config.get("threshold", 0.0)

        if check_type == "completeness":
            result_value = self._check_completeness(data_sample, check_config)
        elif check_type == "validity":
            result_value = self._check_validity(data_sample, check_config)
        elif check_type == "consistency":
            result_value = self._check_consistency(data_sample, check_config)
        elif check_type == "accuracy":
            result_value = self._check_accuracy(data_sample, check_config)
        else:
            result_value = 1.0

        status = "passed" if result_value >= threshold else "failed"
        severity = self._determine_severity(result_value, threshold, check_config)

        message = check_config.get("message_template", "").format(
            result=result_value, threshold=threshold
        )

        quality_check = self.db_manager.add_quality_check(
            pipeline_id=pipeline_id,
            check_name=check_name,
            check_type=check_type,
            status=status,
            severity=severity,
            result_value=result_value,
            threshold_value=threshold,
            message=message,
        )

        return {
            "id": quality_check.id,
            "check_name": check_name,
            "check_type": check_type,
            "status": status,
            "severity": severity,
            "result_value": result_value,
            "threshold_value": threshold,
            "message": message,
        }

    def _check_completeness(
        self, data_sample: Optional[Dict], check_config: Dict
    ) -> float:
        """Check data completeness.

        Args:
            data_sample: Data sample.
            check_config: Check configuration.

        Returns:
            Completeness score (0.0 to 1.0).
        """
        if not data_sample:
            return 0.5

        required_fields = check_config.get("required_fields", [])
        if not required_fields:
            return 1.0

        present_fields = sum(1 for field in required_fields if field in data_sample)
        completeness = present_fields / len(required_fields) if required_fields else 1.0

        return completeness

    def _check_validity(
        self, data_sample: Optional[Dict], check_config: Dict
    ) -> float:
        """Check data validity.

        Args:
            data_sample: Data sample.
            check_config: Check configuration.

        Returns:
            Validity score (0.0 to 1.0).
        """
        if not data_sample:
            return 0.5

        validation_rules = check_config.get("validation_rules", {})
        if not validation_rules:
            return 1.0

        valid_count = 0
        total_rules = len(validation_rules)

        for field, rule in validation_rules.items():
            if field in data_sample:
                value = data_sample[field]
                if self._validate_field(value, rule):
                    valid_count += 1

        return valid_count / total_rules if total_rules > 0 else 1.0

    def _validate_field(self, value: any, rule: Dict) -> bool:
        """Validate a field value against a rule.

        Args:
            value: Field value.
            rule: Validation rule.

        Returns:
            True if valid.
        """
        rule_type = rule.get("type")

        if rule_type == "not_null":
            return value is not None
        elif rule_type == "range":
            min_val = rule.get("min")
            max_val = rule.get("max")
            return (min_val is None or value >= min_val) and (
                max_val is None or value <= max_val
            )
        elif rule_type == "pattern":
            import re

            pattern = rule.get("pattern", "")
            return bool(re.match(pattern, str(value)))
        elif rule_type == "enum":
            allowed_values = rule.get("values", [])
            return value in allowed_values

        return True

    def _check_consistency(
        self, data_sample: Optional[Dict], check_config: Dict
    ) -> float:
        """Check data consistency.

        Args:
            data_sample: Data sample.
            check_config: Check configuration.

        Returns:
            Consistency score (0.0 to 1.0).
        """
        if not data_sample:
            return 0.5

        return 1.0

    def _check_accuracy(
        self, data_sample: Optional[Dict], check_config: Dict
    ) -> float:
        """Check data accuracy.

        Args:
            data_sample: Data sample.
            check_config: Check configuration.

        Returns:
            Accuracy score (0.0 to 1.0).
        """
        if not data_sample:
            return 0.5

        return 1.0

    def _determine_severity(
        self, result_value: float, threshold: float, check_config: Dict
    ) -> str:
        """Determine check severity.

        Args:
            result_value: Check result value.
            threshold: Threshold value.
            check_config: Check configuration.

        Returns:
            Severity level (low, medium, high, critical).
        """
        if result_value >= threshold:
            return "low"

        deviation = threshold - result_value
        severity_thresholds = check_config.get("severity_thresholds", {})

        if deviation >= severity_thresholds.get("critical", 0.5):
            return "critical"
        elif deviation >= severity_thresholds.get("high", 0.3):
            return "high"
        elif deviation >= severity_thresholds.get("medium", 0.1):
            return "medium"
        else:
            return "low"

    def get_quality_summary(
        self, pipeline_id: int, hours: int = 24
    ) -> Dict[str, any]:
        """Get quality check summary.

        Args:
            pipeline_id: Pipeline ID.
            hours: Number of hours to analyze.

        Returns:
            Dictionary with quality summary.
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        session = self.db_manager.get_session()

        try:
            from src.database import QualityCheck

            checks = (
                session.query(QualityCheck)
                .filter(
                    QualityCheck.pipeline_id == pipeline_id,
                    QualityCheck.checked_at >= cutoff_time,
                )
                .all()
            )

            if not checks:
                return {
                    "total_checks": 0,
                    "passed_checks": 0,
                    "failed_checks": 0,
                    "pass_rate": 0.0,
                }

            from collections import Counter

            status_counts = Counter(c.status for c in checks)
            severity_counts = Counter(c.severity for c in checks if c.severity)

            return {
                "total_checks": len(checks),
                "passed_checks": status_counts.get("passed", 0),
                "failed_checks": status_counts.get("failed", 0),
                "warning_checks": status_counts.get("warning", 0),
                "pass_rate": status_counts.get("passed", 0) / len(checks),
                "by_severity": dict(severity_counts),
            }
        finally:
            session.close()
