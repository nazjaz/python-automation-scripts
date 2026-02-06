"""Tracks accessibility improvement progress over time."""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, AccessibilityScan, ProgressMetric

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Tracks accessibility improvement progress over time."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize progress tracker.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.progress_config = config.get("progress_tracking", {})
        self.improvement_threshold = self.progress_config.get("improvement_threshold", 0.05)

    def record_daily_metrics(
        self,
        website_id: int,
        metric_date: Optional[date] = None,
    ) -> ProgressMetric:
        """Record daily progress metrics.

        Args:
            website_id: Website ID.
            metric_date: Optional metric date (defaults to today).

        Returns:
            ProgressMetric object.
        """
        if metric_date is None:
            metric_date = date.today()

        scans = self.db_manager.get_scans(
            website_id=website_id,
            start_date=datetime.combine(metric_date, datetime.min.time()),
            end_date=datetime.combine(metric_date, datetime.max.time()),
        )

        if not scans:
            logger.warning(
                f"No scans found for date {metric_date}",
                extra={"website_id": website_id, "metric_date": str(metric_date)},
            )
            return None

        total_violations = sum(s.total_violations for s in scans)
        critical_violations = sum(s.critical_violations for s in scans)
        high_violations = sum(s.high_violations for s in scans)
        medium_violations = sum(s.medium_violations for s in scans)
        low_violations = sum(s.low_violations for s in scans)

        avg_compliance = sum(s.compliance_score for s in scans if s.compliance_score) / len(scans) if scans else None

        metric = self.db_manager.add_progress_metric(
            website_id=website_id,
            metric_date=metric_date,
            compliance_score=avg_compliance,
            total_violations=total_violations,
            critical_violations=critical_violations,
            high_violations=high_violations,
            medium_violations=medium_violations,
            low_violations=low_violations,
            pages_scanned=len(scans),
        )

        logger.info(
            f"Recorded daily metrics for {metric_date}",
            extra={
                "website_id": website_id,
                "metric_date": str(metric_date),
                "compliance_score": avg_compliance,
            },
        )

        return metric

    def get_progress_trend(
        self,
        website_id: int,
        days: int = 30,
    ) -> Dict:
        """Get progress trend over time.

        Args:
            website_id: Website ID.
            days: Number of days to analyze.

        Returns:
            Dictionary with progress trend data.
        """
        start_date = date.today() - timedelta(days=days)

        metrics = (
            self.db_manager.get_session()
            .query(ProgressMetric)
            .filter(
                ProgressMetric.website_id == website_id,
                ProgressMetric.metric_date >= start_date,
            )
            .order_by(ProgressMetric.metric_date.asc())
            .all()
        )

        if len(metrics) < self.progress_config.get("min_scans_for_trend", 3):
            return {
                "trend": "insufficient_data",
                "message": f"Need at least {self.progress_config.get('min_scans_for_trend', 3)} scans for trend analysis",
            }

        compliance_scores = [m.compliance_score for m in metrics if m.compliance_score]
        total_violations = [m.total_violations for m in metrics]

        if len(compliance_scores) < 2:
            return {"trend": "insufficient_data"}

        first_score = compliance_scores[0]
        last_score = compliance_scores[-1]
        score_change = last_score - first_score

        first_violations = total_violations[0]
        last_violations = total_violations[-1]
        violation_change = first_violations - last_violations

        if score_change > self.improvement_threshold:
            trend = "improving"
        elif score_change < -self.improvement_threshold:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "score_change": score_change,
            "violation_change": violation_change,
            "first_score": first_score,
            "last_score": last_score,
            "first_violations": first_violations,
            "last_violations": last_violations,
            "data_points": len(metrics),
            "metrics": [
                {
                    "date": m.metric_date.isoformat(),
                    "compliance_score": m.compliance_score,
                    "total_violations": m.total_violations,
                }
                for m in metrics
            ],
        }

    def get_improvement_summary(
        self,
        website_id: int,
        days: int = 30,
    ) -> Dict:
        """Get improvement summary.

        Args:
            website_id: Website ID.
            days: Number of days to analyze.

        Returns:
            Dictionary with improvement summary.
        """
        trend = self.get_progress_trend(website_id, days=days)

        scans = self.db_manager.get_scans(website_id=website_id, limit=100)

        if not scans:
            return {"message": "No scans available"}

        latest_scan = scans[0]
        oldest_scan = scans[-1] if len(scans) > 1 else latest_scan

        score_improvement = None
        if latest_scan.compliance_score and oldest_scan.compliance_score:
            score_improvement = latest_scan.compliance_score - oldest_scan.compliance_score

        violation_reduction = oldest_scan.total_violations - latest_scan.total_violations

        return {
            "trend": trend.get("trend", "unknown"),
            "score_improvement": score_improvement,
            "violation_reduction": violation_reduction,
            "current_score": latest_scan.compliance_score,
            "current_violations": latest_scan.total_violations,
            "baseline_score": oldest_scan.compliance_score,
            "baseline_violations": oldest_scan.total_violations,
            "scans_analyzed": len(scans),
        }
