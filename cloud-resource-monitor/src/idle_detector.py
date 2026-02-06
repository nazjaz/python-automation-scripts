"""Detects idle cloud resources."""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, CloudResource, ResourceMetric, IdleResource

logger = logging.getLogger(__name__)


class IdleDetector:
    """Detects idle cloud resources."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize idle detector.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.idle_config = config.get("idle_detection", {})
        self.thresholds = self.idle_config.get("idle_thresholds", {})
        self.idle_duration_hours = self.idle_config.get("idle_duration_hours", 24)
        self.min_samples = self.idle_config.get("min_samples_for_idle", 10)

    def detect_idle_resources(
        self,
        resource_id: Optional[int] = None,
    ) -> List[IdleResource]:
        """Detect idle resources.

        Args:
            resource_id: Optional resource ID filter.

        Returns:
            List of IdleResource objects.
        """
        if not self.idle_config.get("enabled", True):
            return []

        if resource_id:
            resources = [
                self.db_manager.get_session()
                .query(CloudResource)
                .filter(CloudResource.id == resource_id)
                .first()
            ]
            resources = [r for r in resources if r]
        else:
            resources = self.db_manager.get_resources(state="running")

        idle_resources = []

        for resource in resources:
            if self._is_idle(resource):
                idle_since, idle_metrics = self._calculate_idle_period(resource)

                if idle_since:
                    idle_duration = (datetime.utcnow() - idle_since).total_seconds() / 3600.0

                    if idle_duration >= self.idle_duration_hours:
                        idle_resource = self._create_idle_record(
                            resource.id,
                            idle_since,
                            idle_duration,
                            idle_metrics,
                        )
                        idle_resources.append(idle_resource)

        logger.info(
            f"Detected {len(idle_resources)} idle resources",
            extra={"idle_count": len(idle_resources)},
        )

        return idle_resources

    def _is_idle(self, resource: CloudResource) -> bool:
        """Check if resource is idle.

        Args:
            resource: CloudResource object.

        Returns:
            True if resource is idle, False otherwise.
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=self.idle_duration_hours)

        metrics = (
            self.db_manager.get_session()
            .query(ResourceMetric)
            .filter(
                ResourceMetric.resource_id == resource.id,
                ResourceMetric.metric_timestamp >= start_time,
                ResourceMetric.metric_timestamp <= end_time,
            )
            .all()
        )

        if len(metrics) < self.min_samples:
            return False

        check_all = self.idle_config.get("check_all_metrics", True)

        idle_metrics = []

        for metric_type, threshold in self.thresholds.items():
            type_metrics = [m for m in metrics if m.metric_type == metric_type]
            if type_metrics:
                avg_value = sum(m.metric_value for m in type_metrics) / len(type_metrics)
                if avg_value <= threshold:
                    idle_metrics.append(metric_type)
                elif check_all:
                    return False

        return len(idle_metrics) > 0

    def _calculate_idle_period(
        self,
        resource: CloudResource,
    ) -> tuple:
        """Calculate when resource became idle.

        Args:
            resource: CloudResource object.

        Returns:
            Tuple of (idle_since datetime, idle_metrics dict).
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=self.idle_duration_hours * 2)

        metrics = (
            self.db_manager.get_session()
            .query(ResourceMetric)
            .filter(
                ResourceMetric.resource_id == resource.id,
                ResourceMetric.metric_timestamp >= start_time,
                ResourceMetric.metric_timestamp <= end_time,
            )
            .order_by(ResourceMetric.metric_timestamp)
            .all()
        )

        idle_since = None
        idle_metrics = {}

        for metric_type, threshold in self.thresholds.items():
            type_metrics = [m for m in metrics if m.metric_type == metric_type]
            if type_metrics:
                for metric in type_metrics:
                    if metric.metric_value <= threshold:
                        if idle_since is None or metric.metric_timestamp < idle_since:
                            idle_since = metric.metric_timestamp
                        idle_metrics[metric_type] = metric.metric_value
                        break

        return idle_since, idle_metrics

    def _create_idle_record(
        self,
        resource_id: int,
        idle_since: datetime,
        idle_duration_hours: float,
        idle_metrics: Dict,
    ) -> IdleResource:
        """Create idle resource record.

        Args:
            resource_id: Resource ID.
            idle_since: When resource became idle.
            idle_duration_hours: Idle duration in hours.
            idle_metrics: Dictionary of idle metrics.

        Returns:
            IdleResource object.
        """
        session = self.db_manager.get_session()
        try:
            idle_resource = IdleResource(
                resource_id=resource_id,
                idle_since=idle_since,
                idle_duration_hours=idle_duration_hours,
                idle_metrics=json.dumps(idle_metrics),
            )
            session.add(idle_resource)
            session.commit()
            session.refresh(idle_resource)
            return idle_resource
        finally:
            session.close()
