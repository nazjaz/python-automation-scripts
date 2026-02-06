"""Automatically scales resources based on demand patterns."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np

from src.database import DatabaseManager, CloudResource, ResourceMetric, ScalingAction, DemandPattern

logger = logging.getLogger(__name__)


class AutoScaler:
    """Automatically scales resources based on demand patterns."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize auto-scaler.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.scaling_config = config.get("auto_scaling", {})
        self.scale_up_threshold = self.scaling_config.get("scale_up_threshold", 75.0)
        self.scale_down_threshold = self.scaling_config.get("scale_down_threshold", 25.0)
        self.cooldown_minutes = self.scaling_config.get("cooldown_period_minutes", 15)
        self.min_instances = self.scaling_config.get("min_instances", 1)
        self.max_instances = self.scaling_config.get("max_instances", 10)

    def check_scaling_needed(
        self,
        resource_id: int,
    ) -> Optional[ScalingAction]:
        """Check if resource needs scaling.

        Args:
            resource_id: Resource ID.

        Returns:
            ScalingAction object if scaling needed, None otherwise.
        """
        if not self.scaling_config.get("enabled", False):
            return None

        resource = (
            self.db_manager.get_session()
            .query(CloudResource)
            .filter(CloudResource.id == resource_id)
            .first()
        )

        if not resource or resource.state != "running":
            return None

        if self._in_cooldown_period(resource_id):
            return None

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
            .all()
        )

        if not metrics:
            return None

        policies = self.scaling_config.get("scaling_policies", [])

        for policy in policies:
            action = self._evaluate_policy(resource, metrics, policy)
            if action:
                return action

        return None

    def _evaluate_policy(
        self,
        resource: CloudResource,
        metrics: List[ResourceMetric],
        policy: str,
    ) -> Optional[ScalingAction]:
        """Evaluate scaling policy.

        Args:
            resource: CloudResource object.
            metrics: List of recent ResourceMetric objects.
            policy: Policy name.

        Returns:
            ScalingAction object if action needed, None otherwise.
        """
        if policy == "cpu_based":
            cpu_metrics = [m for m in metrics if m.metric_type == "cpu_utilization"]
            if cpu_metrics:
                avg_cpu = np.mean([m.metric_value for m in cpu_metrics])
                return self._create_scaling_action(resource, avg_cpu, "cpu_utilization", "cpu_based")

        elif policy == "memory_based":
            memory_metrics = [m for m in metrics if m.metric_type == "memory_utilization"]
            if memory_metrics:
                avg_memory = np.mean([m.metric_value for m in memory_metrics])
                return self._create_scaling_action(resource, avg_memory, "memory_utilization", "memory_based")

        elif policy == "request_based":
            request_metrics = [m for m in metrics if m.metric_type == "request_count"]
            if request_metrics:
                avg_requests = np.mean([m.metric_value for m in request_metrics])
                threshold = self.scale_up_threshold
                if avg_requests > threshold:
                    return self._create_scaling_action(resource, avg_requests, "request_count", "request_based")

        return None

    def _create_scaling_action(
        self,
        resource: CloudResource,
        metric_value: float,
        metric_type: str,
        policy: str,
    ) -> Optional[ScalingAction]:
        """Create scaling action if thresholds are met.

        Args:
            resource: CloudResource object.
            metric_value: Current metric value.
            metric_type: Metric type.
            policy: Policy name.

        Returns:
            ScalingAction object if action needed, None otherwise.
        """
        action_type = None
        scaling_reason = ""

        if metric_value >= self.scale_up_threshold:
            action_type = "scale_up"
            scaling_reason = f"{metric_type} at {metric_value:.1f}% exceeds scale-up threshold {self.scale_up_threshold}%"
        elif metric_value <= self.scale_down_threshold:
            action_type = "scale_down"
            scaling_reason = f"{metric_type} at {metric_value:.1f}% below scale-down threshold {self.scale_down_threshold}%"

        if not action_type:
            return None

        current_capacity = self._get_current_capacity(resource)
        if current_capacity is None:
            return None

        if action_type == "scale_up":
            target_capacity = min(current_capacity + self.scaling_config.get("scale_up_increment", 1), self.max_instances)
            if target_capacity == current_capacity:
                return None
        else:
            target_capacity = max(current_capacity - self.scaling_config.get("scale_down_increment", 1), self.min_instances)
            if target_capacity == current_capacity:
                return None

        action = self.db_manager.add_scaling_action(
            resource_id=resource.id,
            action_type=action_type,
            scaling_reason=scaling_reason,
            current_capacity=current_capacity,
            target_capacity=target_capacity,
            triggered_by_metric=metric_type,
            metric_value=metric_value,
        )

        logger.info(
            f"Created scaling action for resource {resource.resource_id}",
            extra={
                "resource_id": resource.id,
                "action_type": action_type,
                "current_capacity": current_capacity,
                "target_capacity": target_capacity,
            },
        )

        return action

    def _get_current_capacity(self, resource: CloudResource) -> Optional[int]:
        """Get current capacity for resource.

        Args:
            resource: CloudResource object.

        Returns:
            Current capacity or None.
        """
        return 1

    def _in_cooldown_period(self, resource_id: int) -> bool:
        """Check if resource is in cooldown period.

        Args:
            resource_id: Resource ID.

        Returns:
            True if in cooldown, False otherwise.
        """
        cooldown_time = datetime.utcnow() - timedelta(minutes=self.cooldown_minutes)

        recent_action = (
            self.db_manager.get_session()
            .query(ScalingAction)
            .filter(
                ScalingAction.resource_id == resource_id,
                ScalingAction.executed_at.isnot(None),
                ScalingAction.executed_at >= cooldown_time,
            )
            .first()
        )

        return recent_action is not None

    def analyze_demand_patterns(
        self,
        resource_id: int,
    ) -> Optional[DemandPattern]:
        """Analyze demand patterns for resource.

        Args:
            resource_id: Resource ID.

        Returns:
            DemandPattern object or None.
        """
        if not self.config.get("demand_patterns", {}).get("analysis_enabled", True):
            return None

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)

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

        min_data_points = self.config.get("demand_patterns", {}).get("min_data_points", 100)
        if len(metrics) < min_data_points:
            return None

        cpu_metrics = [m for m in metrics if m.metric_type == "cpu_utilization"]
        if not cpu_metrics:
            return None

        hourly_averages = {}
        for metric in cpu_metrics:
            hour = metric.metric_timestamp.hour
            if hour not in hourly_averages:
                hourly_averages[hour] = []
            hourly_averages[hour].append(metric.metric_value)

        if hourly_averages:
            peak_hour = max(hourly_averages.keys(), key=lambda h: np.mean(hourly_averages[h]))
            low_hour = min(hourly_averages.keys(), key=lambda h: np.mean(hourly_averages[h]))

            pattern_type = "daily_cycles"
            pattern_description = f"Peak utilization at hour {peak_hour}, low at hour {low_hour}"

            session = self.db_manager.get_session()
            try:
                pattern = DemandPattern(
                    resource_id=resource_id,
                    pattern_type=pattern_type,
                    pattern_description=pattern_description,
                    peak_hours=str([peak_hour]),
                    low_hours=str([low_hour]),
                    predicted_demand=np.mean([m.metric_value for m in cpu_metrics]),
                    confidence_score=0.7,
                )
                session.add(pattern)
                session.commit()
                session.refresh(pattern)
                return pattern
            finally:
                session.close()

        return None
