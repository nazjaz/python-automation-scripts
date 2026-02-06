"""Analyzes resources and recommends right-sizing."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np

from src.database import DatabaseManager, CloudResource, ResourceMetric, RightSizingRecommendation

logger = logging.getLogger(__name__)


class RightSizingAnalyzer:
    """Analyzes resources and recommends right-sizing."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize right-sizing analyzer.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.right_sizing_config = config.get("right_sizing", {})
        self.analysis_window = self.right_sizing_config.get("analysis_window_days", 7)
        self.underutilized_threshold = self.right_sizing_config.get("utilization_thresholds", {}).get("underutilized", 30.0)
        self.overutilized_threshold = self.right_sizing_config.get("utilization_thresholds", {}).get("overutilized", 80.0)
        self.min_samples = self.right_sizing_config.get("min_samples_for_recommendation", 20)

    def analyze_resource(
        self,
        resource_id: int,
    ) -> Optional[RightSizingRecommendation]:
        """Analyze resource and generate right-sizing recommendation.

        Args:
            resource_id: Resource ID.

        Returns:
            RightSizingRecommendation object or None.
        """
        if not self.right_sizing_config.get("enabled", True):
            return None

        resource = (
            self.db_manager.get_session()
            .query(CloudResource)
            .filter(CloudResource.id == resource_id)
            .first()
        )

        if not resource:
            return None

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=self.analysis_window)

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

        if len(metrics) < self.min_samples:
            logger.debug(
                f"Insufficient metrics for right-sizing analysis: {len(metrics)} < {self.min_samples}",
                extra={"resource_id": resource_id, "metric_count": len(metrics)},
            )
            return None

        cpu_metrics = [m for m in metrics if m.metric_type == "cpu_utilization"]
        memory_metrics = [m for m in metrics if m.metric_type == "memory_utilization"]

        if not cpu_metrics and not memory_metrics:
            return None

        avg_cpu = np.mean([m.metric_value for m in cpu_metrics]) if cpu_metrics else 0.0
        avg_memory = np.mean([m.metric_value for m in memory_metrics]) if memory_metrics else 0.0
        max_utilization = max(avg_cpu, avg_memory)
        p95_utilization = max(
            np.percentile([m.metric_value for m in cpu_metrics], 95) if cpu_metrics else 0.0,
            np.percentile([m.metric_value for m in memory_metrics], 95) if memory_metrics else 0.0,
        )

        recommendation_type = None
        priority = "medium"
        estimated_savings = None
        estimated_increase = None

        if max_utilization < self.underutilized_threshold:
            recommendation_type = "downsize"
            priority = "high" if max_utilization < 15.0 else "medium"
            if self.right_sizing_config.get("cost_aware", True) and resource.cost_per_hour:
                estimated_savings = resource.cost_per_hour * 0.3

        elif p95_utilization > self.overutilized_threshold:
            recommendation_type = "upsize"
            priority = "high" if p95_utilization > 90.0 else "medium"
            if self.right_sizing_config.get("cost_aware", True) and resource.cost_per_hour:
                estimated_increase = resource.cost_per_hour * 0.5

        if not recommendation_type:
            return None

        utilization_analysis = (
            f"Average CPU: {avg_cpu:.1f}%, Average Memory: {avg_memory:.1f}%, "
            f"P95 Utilization: {p95_utilization:.1f}%"
        )

        recommendation = self.db_manager.add_recommendation(
            resource_id=resource_id,
            recommendation_type=recommendation_type,
            current_instance_type=resource.instance_type,
            estimated_cost_savings=estimated_savings,
            estimated_cost_increase=estimated_increase,
            utilization_analysis=utilization_analysis,
            priority=priority,
        )

        logger.info(
            f"Generated right-sizing recommendation for resource {resource_id}",
            extra={
                "resource_id": resource_id,
                "recommendation_type": recommendation_type,
                "priority": priority,
            },
        )

        return recommendation

    def analyze_all_resources(
        self,
        resource_type: Optional[str] = None,
    ) -> List[RightSizingRecommendation]:
        """Analyze all resources and generate recommendations.

        Args:
            resource_type: Optional resource type filter.

        Returns:
            List of RightSizingRecommendation objects.
        """
        resources = self.db_manager.get_resources(
            resource_type=resource_type,
            state="running",
        )

        recommendations = []

        for resource in resources:
            recommendation = self.analyze_resource(resource.id)
            if recommendation:
                recommendations.append(recommendation)

        logger.info(
            f"Analyzed {len(resources)} resources: {len(recommendations)} recommendations",
            extra={"resource_count": len(resources), "recommendation_count": len(recommendations)},
        )

        return recommendations
