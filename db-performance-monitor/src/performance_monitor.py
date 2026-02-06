"""Monitor database performance."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class PerformanceMonitor:
    """Monitor database performance."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize performance monitor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def monitor_performance(self, database_id: str) -> Dict[str, any]:
        """Monitor database performance.

        Args:
            database_id: Database identifier.

        Returns:
            Dictionary with performance monitoring information.
        """
        database = self.db_manager.get_database(database_id)

        if not database:
            return {"error": "Database not found"}

        recent_metrics = self.db_manager.get_recent_metrics(database.id, limit=100)

        metrics_summary = {}
        for metric in recent_metrics:
            if metric.metric_type not in metrics_summary:
                metrics_summary[metric.metric_type] = []

            metrics_summary[metric.metric_type].append({
                "value": metric.metric_value,
                "unit": metric.metric_unit,
                "collected_at": metric.collected_at,
            })

        return {
            "database_id": database_id,
            "database_name": database.database_name,
            "database_type": database.database_type,
            "metrics_count": len(recent_metrics),
            "metrics_summary": metrics_summary,
        }

    def collect_metrics(
        self,
        database_id: str,
        metrics: List[Dict[str, any]],
    ) -> Dict[str, any]:
        """Collect performance metrics.

        Args:
            database_id: Database identifier.
            metrics: List of metric dictionaries with type, value, and unit.

        Returns:
            Dictionary with collection results.
        """
        database = self.db_manager.get_database(database_id)

        if not database:
            return {"error": "Database not found"}

        collected = []

        for metric_data in metrics:
            metric = self.db_manager.add_performance_metric(
                database_id=database.id,
                metric_type=metric_data.get("type"),
                metric_value=metric_data.get("value", 0.0),
                metric_unit=metric_data.get("unit"),
            )
            collected.append(metric.id)

        return {
            "success": True,
            "database_id": database_id,
            "metrics_collected": len(collected),
        }

    def get_performance_statistics(
        self, database_id: str, days: int = 7
    ) -> Dict[str, any]:
        """Get performance statistics.

        Args:
            database_id: Database identifier.
            days: Number of days to analyze.

        Returns:
            Dictionary with performance statistics.
        """
        database = self.db_manager.get_database(database_id)

        if not database:
            return {"error": "Database not found"}

        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_metrics = self.db_manager.get_recent_metrics(database.id, limit=1000)

        filtered_metrics = [m for m in recent_metrics if m.collected_at >= cutoff]

        if not filtered_metrics:
            return {
                "database_id": database_id,
                "days": days,
                "total_metrics": 0,
            }

        metric_stats = {}
        for metric in filtered_metrics:
            if metric.metric_type not in metric_stats:
                metric_stats[metric.metric_type] = {
                    "values": [],
                    "unit": metric.metric_unit,
                }

            metric_stats[metric.metric_type]["values"].append(metric.metric_value)

        for metric_type, stats in metric_stats.items():
            values = stats["values"]
            stats["count"] = len(values)
            stats["average"] = sum(values) / len(values) if values else 0.0
            stats["min"] = min(values) if values else 0.0
            stats["max"] = max(values) if values else 0.0

        return {
            "database_id": database_id,
            "days": days,
            "total_metrics": len(filtered_metrics),
            "metric_statistics": metric_stats,
        }
