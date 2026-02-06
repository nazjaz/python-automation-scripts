"""Monitor application error rates and metrics."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class ErrorMonitor:
    """Monitor application error rates and metrics."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize error monitor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.time_window_minutes = config.get("time_window_minutes", 60)
        self.error_rate_threshold = config.get("error_rate_threshold", 1.0)

    def calculate_error_rate(
        self,
        application: Optional[str] = None,
        environment: Optional[str] = None,
        hours: int = 1,
    ) -> Dict[str, any]:
        """Calculate error rate for time period.

        Args:
            application: Filter by application.
            environment: Filter by environment.
            hours: Number of hours to analyze.

        Returns:
            Dictionary with error rate metrics.
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        session = self.db_manager.get_session()

        try:
            from src.database import ErrorLog

            query = session.query(ErrorLog).filter(ErrorLog.timestamp >= cutoff_time)

            if application:
                query = query.filter(ErrorLog.application == application)
            if environment:
                query = query.filter(ErrorLog.environment == environment)

            errors = query.all()
            error_count = len(errors)

            total_requests = self._estimate_total_requests(
                application, environment, hours, error_count
            )

            error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0.0

            time_window_start = cutoff_time
            time_window_end = datetime.utcnow()

            self.db_manager.add_error_rate(
                application or "unknown",
                environment or "unknown",
                error_count,
                total_requests,
                time_window_start,
                time_window_end,
            )

            return {
                "error_count": error_count,
                "total_requests": total_requests,
                "error_rate": error_rate,
                "time_window_start": time_window_start,
                "time_window_end": time_window_end,
                "application": application,
                "environment": environment,
                "threshold_exceeded": error_rate > self.error_rate_threshold,
            }
        finally:
            session.close()

    def _estimate_total_requests(
        self,
        application: Optional[str],
        environment: Optional[str],
        hours: int,
        error_count: int,
    ) -> int:
        """Estimate total requests based on error count and rate.

        Args:
            application: Application name.
            environment: Environment name.
            hours: Number of hours.
            error_count: Number of errors.

        Returns:
            Estimated total requests.
        """
        if error_count == 0:
            return 1000

        estimated_error_rate = self.error_rate_threshold
        estimated_requests = int(error_count / (estimated_error_rate / 100))

        return max(estimated_requests, error_count * 10)

    def get_error_statistics(
        self,
        application: Optional[str] = None,
        environment: Optional[str] = None,
        hours: int = 24,
    ) -> Dict[str, any]:
        """Get comprehensive error statistics.

        Args:
            application: Filter by application.
            environment: Filter by environment.
            hours: Number of hours to analyze.

        Returns:
            Dictionary with error statistics.
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        session = self.db_manager.get_session()

        try:
            from src.database import ErrorLog

            query = session.query(ErrorLog).filter(ErrorLog.timestamp >= cutoff_time)

            if application:
                query = query.filter(ErrorLog.application == application)
            if environment:
                query = query.filter(ErrorLog.environment == environment)

            errors = query.all()

            severity_counts = {}
            category_counts = {}
            error_types = {}

            for error in errors:
                if error.severity:
                    severity_counts[error.severity] = severity_counts.get(error.severity, 0) + 1

                if error.category:
                    category_name = error.category.name
                    category_counts[category_name] = category_counts.get(category_name, 0) + 1

                if error.error_type:
                    error_types[error.error_type] = error_types.get(error.error_type, 0) + 1

            return {
                "total_errors": len(errors),
                "severity_breakdown": severity_counts,
                "category_breakdown": category_counts,
                "error_types": error_types,
                "time_period_hours": hours,
                "application": application,
                "environment": environment,
            }
        finally:
            session.close()

    def check_error_rate_threshold(
        self,
        application: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> bool:
        """Check if error rate exceeds threshold.

        Args:
            application: Filter by application.
            environment: Filter by environment.

        Returns:
            True if threshold exceeded.
        """
        error_rate = self.calculate_error_rate(application, environment, hours=1)
        return error_rate.get("threshold_exceeded", False)
