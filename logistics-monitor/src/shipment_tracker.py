"""Track shipments and update status."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class ShipmentTracker:
    """Track shipments and update status."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize shipment tracker.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def track_shipment(self, shipment_id: str) -> Dict[str, any]:
        """Track shipment status and events.

        Args:
            shipment_id: Shipment identifier.

        Returns:
            Dictionary with shipment tracking information.
        """
        shipment = self.db_manager.get_shipment(shipment_id)

        if not shipment:
            return {"error": "Shipment not found"}

        tracking_events = self.db_manager.get_shipment_tracking_events(shipment.id)
        routes = self.db_manager.get_shipment_routes(shipment.id)
        delays = self.db_manager.get_shipment_delays(shipment.id)

        current_location = None
        if tracking_events:
            latest_event = tracking_events[-1]
            current_location = latest_event.location

        estimated_arrival = shipment.estimated_delivery
        if delays:
            latest_delay = delays[0]
            if estimated_arrival:
                estimated_arrival = estimated_arrival + timedelta(
                    hours=latest_delay.predicted_delay_hours
                )

        return {
            "shipment_id": shipment.shipment_id,
            "status": shipment.status,
            "origin": shipment.origin,
            "destination": shipment.destination,
            "current_location": current_location,
            "estimated_delivery": shipment.estimated_delivery,
            "adjusted_estimated_delivery": estimated_arrival,
            "actual_delivery": shipment.actual_delivery,
            "total_events": len(tracking_events),
            "total_routes": len(routes),
            "active_delays": len([d for d in delays if not d.occurred_at]),
        }

    def update_shipment_location(
        self,
        shipment_id: str,
        location: str,
        event_type: str = "in_transit",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Dict[str, any]:
        """Update shipment location.

        Args:
            shipment_id: Shipment identifier.
            location: Current location.
            event_type: Event type.
            latitude: Latitude coordinate.
            longitude: Longitude coordinate.

        Returns:
            Dictionary with update results.
        """
        shipment = self.db_manager.get_shipment(shipment_id)

        if not shipment:
            return {"success": False, "error": "Shipment not found"}

        event = self.db_manager.add_tracking_event(
            shipment_id=shipment.id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            location=location,
            description=f"Shipment at {location}",
            latitude=latitude,
            longitude=longitude,
        )

        if event_type == "departed":
            self.db_manager.update_shipment_status(
                shipment_id, "in_transit", shipped_at=datetime.utcnow()
            )
        elif event_type == "arrived":
            self.db_manager.update_shipment_status(
                shipment_id, "delivered", actual_delivery=datetime.utcnow()
            )

        return {
            "success": True,
            "event_id": event.id,
            "location": location,
            "status": shipment.status,
        }

    def get_shipment_timeline(self, shipment_id: str) -> List[Dict[str, any]]:
        """Get shipment timeline with all events.

        Args:
            shipment_id: Shipment identifier.

        Returns:
            List of timeline event dictionaries.
        """
        shipment = self.db_manager.get_shipment(shipment_id)

        if not shipment:
            return []

        tracking_events = self.db_manager.get_shipment_tracking_events(shipment.id)
        delays = self.db_manager.get_shipment_delays(shipment.id)

        timeline = []

        timeline.append({
            "timestamp": shipment.created_at,
            "event_type": "created",
            "description": f"Shipment created: {shipment.origin} to {shipment.destination}",
        })

        for event in tracking_events:
            timeline.append({
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "location": event.location,
                "description": event.description,
            })

        for delay in delays:
            timeline.append({
                "timestamp": delay.predicted_at,
                "event_type": "delay_predicted",
                "description": f"Delay predicted: {delay.predicted_delay_hours} hours - {delay.reason}",
            })

        if shipment.actual_delivery:
            timeline.append({
                "timestamp": shipment.actual_delivery,
                "event_type": "delivered",
                "description": f"Shipment delivered to {shipment.destination}",
            })

        timeline.sort(key=lambda x: x["timestamp"])

        return timeline

    def get_active_shipments_summary(self) -> Dict[str, any]:
        """Get summary of active shipments.

        Returns:
            Dictionary with active shipments summary.
        """
        active_shipments = self.db_manager.get_active_shipments()

        status_counts = {}
        for shipment in active_shipments:
            status_counts[shipment.status] = status_counts.get(shipment.status, 0) + 1

        return {
            "total_active": len(active_shipments),
            "by_status": status_counts,
            "shipments": [
                {
                    "shipment_id": s.shipment_id,
                    "status": s.status,
                    "origin": s.origin,
                    "destination": s.destination,
                }
                for s in active_shipments[:10]
            ],
        }
