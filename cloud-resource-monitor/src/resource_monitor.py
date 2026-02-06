"""Monitors cloud resource utilization."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np

from src.database import DatabaseManager, CloudResource, ResourceMetric

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitors cloud resource utilization."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize resource monitor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.monitoring_config = config.get("monitoring", {})
        self.metrics = self.monitoring_config.get("metrics", [])

    def collect_metrics(
        self,
        resource_id: int,
        metrics: Dict[str, float],
        metric_timestamp: Optional[datetime] = None,
    ) -> List[ResourceMetric]:
        """Collect metrics for a resource.

        Args:
            resource_id: Resource ID.
            metrics: Dictionary mapping metric types to values.
            metric_timestamp: Optional metric timestamp.

        Returns:
            List of ResourceMetric objects.
        """
        if metric_timestamp is None:
            metric_timestamp = datetime.utcnow()

        collected_metrics = []

        for metric_type, metric_value in metrics.items():
            metric = self.db_manager.add_metric(
                resource_id=resource_id,
                metric_type=metric_type,
                metric_value=metric_value,
                metric_timestamp=metric_timestamp,
            )
            collected_metrics.append(metric)

        logger.info(
            f"Collected {len(collected_metrics)} metrics for resource {resource_id}",
            extra={"resource_id": resource_id, "metric_count": len(collected_metrics)},
        )

        return collected_metrics

    def get_utilization_summary(
        self,
        resource_id: int,
        hours: int = 24,
    ) -> Dict:
        """Get utilization summary for resource.

        Args:
            resource_id: Resource ID.
            hours: Number of hours to analyze.

        Returns:
            Dictionary with utilization summary.
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        metrics = (
            self.db_manager.get_session()
            .query(ResourceMetric)
            .filter(
                ResourceMetric.resource_id == resource_id,
                ResourceMetric.metric_timestamp >= start_time,
                ResourceMetric.metric_timestamp <= end_time,
            )
            .all()
        )

        summary = {
            "resource_id": resource_id,
            "period_start": start_time,
            "period_end": end_time,
            "total_metrics": len(metrics),
            "utilization_by_metric": {},
        }

        for metric_type in self.metrics:
            type_metrics = [m for m in metrics if m.metric_type == metric_type]
            if type_metrics:
                values = [m.metric_value for m in type_metrics]
                summary["utilization_by_metric"][metric_type] = {
                    "avg": float(np.mean(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "p95": float(np.percentile(values, 95)),
                    "p99": float(np.percentile(values, 99)),
                }

        logger.info(
            f"Generated utilization summary for resource {resource_id}",
            extra={"resource_id": resource_id, "metric_count": len(metrics)},
        )

        return summary

    def get_current_utilization(
        self,
        resource_id: int,
    ) -> Dict:
        """Get current utilization for resource.

        Args:
            resource_id: Resource ID.

        Returns:
            Dictionary with current utilization metrics.
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=15)

        metrics = (
            self.db_manager.get_session()
            .query(ResourceMetric)
            .filter(
                ResourceMetric.resource_id == resource_id,
                ResourceMetric.metric_timestamp >= start_time,
                ResourceMetric.metric_timestamp <= end_time,
            )
            .order_by(ResourceMetric.metric_timestamp.desc())
            .all()
        )

        current_utilization = {}

        for metric_type in self.metrics:
            type_metrics = [m for m in metrics if m.metric_type == metric_type]
            if type_metrics:
                latest = type_metrics[0]
                current_utilization[metric_type] = latest.metric_value

        return current_utilization
