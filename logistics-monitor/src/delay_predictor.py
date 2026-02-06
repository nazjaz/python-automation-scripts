"""Predict shipment delays."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class DelayPredictor:
    """Predict shipment delays."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize delay predictor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.delay_factors = config.get("delay_factors", {
            "weather": 0.3,
            "traffic": 0.2,
            "customs": 0.25,
            "mechanical": 0.15,
            "other": 0.1,
        })

    def predict_delay(
        self, shipment_id: str, delay_type: str, reason: Optional[str] = None
    ) -> Dict[str, any]:
        """Predict delay for shipment.

        Args:
            shipment_id: Shipment identifier.
            delay_type: Delay type (weather, traffic, customs, etc.).
            reason: Delay reason.

        Returns:
            Dictionary with delay prediction.
        """
        shipment = self.db_manager.get_shipment(shipment_id)

        if not shipment:
            return {"error": "Shipment not found"}

        base_delay = self._calculate_base_delay(shipment, delay_type)
        severity = self._determine_severity(base_delay, delay_type)

        delay = self.db_manager.add_delay(
            shipment_id=shipment.id,
            delay_type=delay_type,
            predicted_delay_hours=base_delay,
            reason=reason or f"{delay_type} delay",
            severity=severity,
        )

        adjusted_eta = None
        if shipment.estimated_delivery:
            adjusted_eta = shipment.estimated_delivery + timedelta(hours=base_delay)

        return {
            "shipment_id": shipment_id,
            "delay_type": delay_type,
            "predicted_delay_hours": base_delay,
            "severity": severity,
            "reason": reason,
            "original_eta": shipment.estimated_delivery,
            "adjusted_eta": adjusted_eta,
            "delay_id": delay.id,
        }

    def _calculate_base_delay(self, shipment, delay_type: str) -> float:
        """Calculate base delay hours.

        Args:
            shipment: Shipment object.
            delay_type: Delay type.

        Returns:
            Base delay in hours.
        """
        base_delays = {
            "weather": 4.0,
            "traffic": 2.0,
            "customs": 8.0,
            "mechanical": 6.0,
            "other": 3.0,
        }

        base_delay = base_delays.get(delay_type, 3.0)

        if shipment.priority == "urgent":
            base_delay *= 0.7
        elif shipment.priority == "high":
            base_delay *= 0.85

        distance_factor = self._get_distance_factor(shipment)
        base_delay *= distance_factor

        return base_delay

    def _get_distance_factor(self, shipment) -> float:
        """Get distance factor for delay calculation.

        Args:
            shipment: Shipment object.

        Returns:
            Distance factor.
        """
        routes = self.db_manager.get_shipment_routes(shipment.id)
        if routes:
            distance = routes[0].distance_km
            if distance > 5000:
                return 1.2
            elif distance > 2000:
                return 1.1
            elif distance < 500:
                return 0.9

        return 1.0

    def _determine_severity(self, delay_hours: float, delay_type: str) -> str:
        """Determine delay severity.

        Args:
            delay_hours: Delay in hours.
            delay_type: Delay type.

        Returns:
            Severity level (low, medium, high, critical).
        """
        if delay_hours >= 24:
            return "critical"
        elif delay_hours >= 12:
            return "high"
        elif delay_hours >= 6:
            return "medium"
        else:
            return "low"

    def analyze_delay_risk(self, shipment_id: str) -> Dict[str, any]:
        """Analyze delay risk for shipment.

        Args:
            shipment_id: Shipment identifier.

        Returns:
            Dictionary with delay risk analysis.
        """
        shipment = self.db_manager.get_shipment(shipment_id)

        if not shipment:
            return {"error": "Shipment not found"}

        risk_factors = []
        risk_score = 0.0

        if shipment.priority == "urgent":
            risk_score += 0.1

        routes = self.db_manager.get_shipment_routes(shipment.id)
        if routes:
            route = routes[0]
            if route.distance_km > 5000:
                risk_score += 0.2
                risk_factors.append("Long distance")
            if route.estimated_duration_hours > 48:
                risk_score += 0.15
                risk_factors.append("Long duration")

        existing_delays = self.db_manager.get_shipment_delays(shipment.id)
        if existing_delays:
            risk_score += 0.25
            risk_factors.append("Previous delays")

        if shipment.status == "in_transit":
            tracking_events = self.db_manager.get_shipment_tracking_events(shipment.id)
            if not tracking_events or len(tracking_events) < 2:
                risk_score += 0.1
                risk_factors.append("Limited tracking")

        risk_level = "low"
        if risk_score >= 0.5:
            risk_level = "high"
        elif risk_score >= 0.3:
            risk_level = "medium"

        return {
            "shipment_id": shipment_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
        }

    def get_delay_statistics(self, days: int = 30) -> Dict[str, any]:
        """Get delay statistics.

        Args:
            days: Number of days to analyze.

        Returns:
            Dictionary with delay statistics.
        """
        session = self.db_manager.get_session()
        try:
            from src.database import Delay, Shipment

            cutoff = datetime.utcnow() - timedelta(days=days)
            delays = (
                session.query(Delay)
                .filter(Delay.predicted_at >= cutoff)
                .all()
            )

            if not delays:
                return {
                    "total_delays": 0,
                    "average_delay_hours": 0.0,
                    "by_type": {},
                    "by_severity": {},
                }

            delay_types = {}
            severities = {}
            total_delay_hours = 0.0

            for delay in delays:
                delay_types[delay.delay_type] = delay_types.get(delay.delay_type, 0) + 1
                severities[delay.severity] = severities.get(delay.severity, 0) + 1
                total_delay_hours += delay.predicted_delay_hours

            return {
                "total_delays": len(delays),
                "average_delay_hours": total_delay_hours / len(delays),
                "by_type": delay_types,
                "by_severity": severities,
            }
        finally:
            session.close()
