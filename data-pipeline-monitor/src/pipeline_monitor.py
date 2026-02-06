"""Monitor data pipeline health and metrics."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class PipelineMonitor:
    """Monitor data pipeline health and metrics."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize pipeline monitor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.health_check_interval = config.get("health_check_interval_minutes", 5)
        self.degraded_threshold = config.get("degraded_threshold", 0.8)
        self.unhealthy_threshold = config.get("unhealthy_threshold", 0.5)

    def check_pipeline_health(
        self, pipeline_id: int, hours: int = 1
    ) -> Dict[str, any]:
        """Check pipeline health.

        Args:
            pipeline_id: Pipeline ID.
            hours: Number of hours to analyze.

        Returns:
            Dictionary with health status and metrics.
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        session = self.db_manager.get_session()

        try:
            from src.database import PipelineRun

            runs = (
                session.query(PipelineRun)
                .filter(
                    PipelineRun.pipeline_id == pipeline_id,
                    PipelineRun.start_time >= cutoff_time,
                )
                .all()
            )

            if not runs:
                return {
                    "pipeline_id": pipeline_id,
                    "health_status": "unknown",
                    "success_rate": 0.0,
                    "total_runs": 0,
                    "successful_runs": 0,
                    "failed_runs": 0,
                }

            total_runs = len(runs)
            successful_runs = len([r for r in runs if r.status == "success"])
            failed_runs = total_runs - successful_runs
            success_rate = successful_runs / total_runs if total_runs > 0 else 0.0

            if success_rate >= self.degraded_threshold:
                health_status = "healthy"
            elif success_rate >= self.unhealthy_threshold:
                health_status = "degraded"
            else:
                health_status = "unhealthy"

            self.db_manager.update_pipeline_health(pipeline_id, health_status)

            avg_duration = (
                sum(r.duration_seconds for r in runs if r.duration_seconds) / total_runs
                if total_runs > 0
                else 0.0
            )

            total_records = sum(r.records_processed for r in runs)
            total_failed_records = sum(r.records_failed for r in runs)

            return {
                "pipeline_id": pipeline_id,
                "health_status": health_status,
                "success_rate": success_rate,
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "average_duration_seconds": avg_duration,
                "total_records_processed": total_records,
                "total_records_failed": total_failed_records,
            }
        finally:
            session.close()

    def monitor_all_pipelines(self) -> List[Dict[str, any]]:
        """Monitor all active pipelines.

        Returns:
            List of health status dictionaries.
        """
        pipelines = self.db_manager.get_all_pipelines(status="active")
        health_statuses = []

        for pipeline in pipelines:
            health = self.check_pipeline_health(pipeline.id)
            health["pipeline_name"] = pipeline.name
            health_statuses.append(health)

        return health_statuses

    def get_pipeline_metrics(
        self, pipeline_id: int, hours: int = 24
    ) -> Dict[str, any]:
        """Get pipeline metrics.

        Args:
            pipeline_id: Pipeline ID.
            hours: Number of hours to analyze.

        Returns:
            Dictionary with pipeline metrics.
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        session = self.db_manager.get_session()

        try:
            from src.database import PipelineRun, QualityCheck

            runs = (
                session.query(PipelineRun)
                .filter(
                    PipelineRun.pipeline_id == pipeline_id,
                    PipelineRun.start_time >= cutoff_time,
                )
                .all()
            )

            quality_checks = (
                session.query(QualityCheck)
                .filter(
                    QualityCheck.pipeline_id == pipeline_id,
                    QualityCheck.checked_at >= cutoff_time,
                )
                .all()
            )

            total_runs = len(runs)
            successful_runs = len([r for r in runs if r.status == "success"])
            failed_runs = total_runs - successful_runs

            passed_checks = len([c for c in quality_checks if c.status == "passed"])
            failed_checks = len([c for c in quality_checks if c.status == "failed"])

            return {
                "pipeline_id": pipeline_id,
                "time_period_hours": hours,
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "success_rate": successful_runs / total_runs if total_runs > 0 else 0.0,
                "total_quality_checks": len(quality_checks),
                "passed_checks": passed_checks,
                "failed_checks": failed_checks,
                "quality_pass_rate": (
                    passed_checks / len(quality_checks) if quality_checks else 0.0
                ),
            }
        finally:
            session.close()
