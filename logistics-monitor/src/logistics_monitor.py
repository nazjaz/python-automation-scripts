"""Monitor supply chain logistics."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class LogisticsMonitor:
    """Monitor supply chain logistics."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize logistics monitor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def monitor_logistics(
        self, days: Optional[int] = None
    ) -> Dict[str, any]:
        """Monitor logistics performance.

        Args:
            days: Number of days to analyze.

        Returns:
            Dictionary with logistics monitoring results.
        """
        if days is None:
            days = 7

        cutoff = datetime.utcnow() - timedelta(days=days)
        session = self.db_manager.get_session()

        try:
            from src.database import Shipment

            shipments = (
                session.query(Shipment)
                .filter(Shipment.created_at >= cutoff)
                .all()
            )

            total_shipments = len(shipments)
            completed = [s for s in shipments if s.status == "delivered"]
            on_time = [
                s
                for s in completed
                if s.actual_delivery
                and s.estimated_delivery
                and s.actual_delivery <= s.estimated_delivery
            ]
            delayed = [
                s
                for s in completed
                if s.actual_delivery
                and s.estimated_delivery
                and s.actual_delivery > s.estimated_delivery
            ]

            delays = []
            for shipment in delayed:
                if shipment.actual_delivery and shipment.estimated_delivery:
                    delay_hours = (
                        shipment.actual_delivery - shipment.estimated_delivery
                    ).total_seconds() / 3600
                    delays.append(delay_hours)

            average_delay = sum(delays) / len(delays) if delays else 0.0

            on_time_percentage = (
                len(on_time) / len(completed) * 100 if completed else 0.0
            )

            self.db_manager.add_logistics_metric(
                time_window_start=cutoff,
                time_window_end=datetime.utcnow(),
                total_shipments=total_shipments,
                on_time_deliveries=len(on_time),
                delayed_deliveries=len(delayed),
                average_delay_hours=average_delay,
            )

            return {
                "days": days,
                "total_shipments": total_shipments,
                "completed_shipments": len(completed),
                "on_time_deliveries": len(on_time),
                "delayed_deliveries": len(delayed),
                "on_time_percentage": on_time_percentage,
                "average_delay_hours": average_delay,
            }
        finally:
            session.close()

    def get_logistics_trends(self, days: int = 30) -> Dict[str, any]:
        """Get logistics performance trends.

        Args:
            days: Number of days to analyze.

        Returns:
            Dictionary with logistics trends.
        """
        metrics = self.db_manager.get_recent_metrics(days=days)

        if not metrics:
            return {
                "days": days,
                "trend": "stable",
                "average_on_time_percentage": 0.0,
            }

        on_time_percentages = [
            m.on_time_percentage for m in metrics if m.on_time_percentage is not None
        ]

        if not on_time_percentages:
            return {
                "days": days,
                "trend": "stable",
                "average_on_time_percentage": 0.0,
            }

        average_on_time = sum(on_time_percentages) / len(on_time_percentages)

        trend = self._calculate_trend(on_time_percentages)

        return {
            "days": days,
            "trend": trend,
            "average_on_time_percentage": average_on_time,
            "min_on_time": min(on_time_percentages),
            "max_on_time": max(on_time_percentages),
        }

    def _calculate_trend(self, percentages: List[float]) -> str:
        """Calculate trend from percentages.

        Args:
            percentages: List of on-time percentages.

        Returns:
            Trend indicator (improving, declining, stable).
        """
        if len(percentages) < 2:
            return "stable"

        mid_point = len(percentages) // 2
        first_half_avg = sum(percentages[:mid_point]) / len(percentages[:mid_point])
        second_half_avg = sum(percentages[mid_point:]) / len(percentages[mid_point:])

        if second_half_avg > first_half_avg + 5:
            return "improving"
        elif second_half_avg < first_half_avg - 5:
            return "declining"
        else:
            return "stable"

    def get_supplier_performance(
        self, supplier_id: Optional[str] = None, days: int = 30
    ) -> Dict[str, any]:
        """Get supplier performance metrics.

        Args:
            supplier_id: Optional supplier ID to filter by.
            days: Number of days to analyze.

        Returns:
            Dictionary with supplier performance.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        session = self.db_manager.get_session()

        try:
            from src.database import Shipment, Supplier

            query = session.query(Shipment).filter(Shipment.created_at >= cutoff)

            if supplier_id:
                supplier = self.db_manager.get_supplier(supplier_id)
                if supplier:
                    query = query.filter(Shipment.supplier_id == supplier.id)

            shipments = query.all()

            total_shipments = len(shipments)
            completed = [s for s in shipments if s.status == "delivered"]
            on_time = [
                s
                for s in completed
                if s.actual_delivery
                and s.estimated_delivery
                and s.actual_delivery <= s.estimated_delivery
            ]

            return {
                "supplier_id": supplier_id,
                "days": days,
                "total_shipments": total_shipments,
                "completed_shipments": len(completed),
                "on_time_percentage": (
                    len(on_time) / len(completed) * 100 if completed else 0.0
                ),
            }
        finally:
            session.close()
