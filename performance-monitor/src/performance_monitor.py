"""Monitors employee performance metrics."""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import numpy as np

from src.database import DatabaseManager, Employee, PerformanceMetric

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitors employee performance metrics."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize performance monitor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.performance_config = config.get("performance", {})
        self.metrics = self.performance_config.get("metrics", [])
        self.thresholds = self.performance_config.get("performance_thresholds", {})

    def calculate_performance_score(
        self,
        employee_id: int,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
    ) -> Dict:
        """Calculate overall performance score for employee.

        Args:
            employee_id: Employee ID.
            period_start: Optional period start date.
            period_end: Optional period end date.

        Returns:
            Dictionary with performance score and breakdown.
        """
        if period_end is None:
            period_end = date.today()

        if period_start is None:
            evaluation_period = self.performance_config.get("evaluation_period_days", 90)
            period_start = period_end - timedelta(days=evaluation_period)

        metrics = (
            self.db_manager.get_session()
            .query(PerformanceMetric)
            .filter(
                PerformanceMetric.employee_id == employee_id,
                PerformanceMetric.metric_date >= period_start,
                PerformanceMetric.metric_date <= period_end,
            )
            .all()
        )

        if not metrics:
            return {
                "employee_id": employee_id,
                "overall_score": 0.0,
                "rating": "insufficient_data",
                "metrics_count": 0,
            }

        metric_scores = {}
        for metric_type in self.metrics:
            type_metrics = [m for m in metrics if m.metric_type == metric_type]
            if type_metrics:
                if type_metrics[0].target_value:
                    scores = [
                        min(m.value / m.target_value, 1.0) if m.target_value > 0 else 0.0
                        for m in type_metrics
                    ]
                    metric_scores[metric_type] = np.mean(scores)
                else:
                    metric_scores[metric_type] = np.mean([m.value for m in type_metrics]) / 100.0

        if not metric_scores:
            return {
                "employee_id": employee_id,
                "overall_score": 0.0,
                "rating": "insufficient_data",
                "metrics_count": len(metrics),
            }

        overall_score = np.mean(list(metric_scores.values()))

        if overall_score >= self.thresholds.get("excellent", 0.90):
            rating = "excellent"
        elif overall_score >= self.thresholds.get("good", 0.75):
            rating = "good"
        elif overall_score >= self.thresholds.get("satisfactory", 0.60):
            rating = "satisfactory"
        elif overall_score >= self.thresholds.get("needs_improvement", 0.40):
            rating = "needs_improvement"
        else:
            rating = "poor"

        logger.info(
            f"Calculated performance score for employee {employee_id}",
            extra={
                "employee_id": employee_id,
                "overall_score": overall_score,
                "rating": rating,
            },
        )

        return {
            "employee_id": employee_id,
            "overall_score": float(overall_score),
            "rating": rating,
            "metric_scores": metric_scores,
            "metrics_count": len(metrics),
            "period_start": period_start,
            "period_end": period_end,
        }

    def get_performance_summary(
        self,
        employee_id: int,
        period_days: int = 90,
    ) -> Dict:
        """Get performance summary for employee.

        Args:
            employee_id: Employee ID.
            period_days: Number of days to analyze.

        Returns:
            Dictionary with performance summary.
        """
        period_end = date.today()
        period_start = period_end - timedelta(days=period_days)

        metrics = (
            self.db_manager.get_session()
            .query(PerformanceMetric)
            .filter(
                PerformanceMetric.employee_id == employee_id,
                PerformanceMetric.metric_date >= period_start,
                PerformanceMetric.metric_date <= period_end,
            )
            .all()
        )

        summary = {
            "employee_id": employee_id,
            "period_start": period_start,
            "period_end": period_end,
            "total_metrics": len(metrics),
            "metrics_by_type": {},
            "average_values": {},
        }

        for metric_type in self.metrics:
            type_metrics = [m for m in metrics if m.metric_type == metric_type]
            if type_metrics:
                summary["metrics_by_type"][metric_type] = len(type_metrics)
                summary["average_values"][metric_type] = float(np.mean([m.value for m in type_metrics]))

        return summary
