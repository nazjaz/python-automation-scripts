"""Optimize shipment routes."""

from typing import Dict, List, Optional

from src.database import DatabaseManager


class RouteOptimizer:
    """Optimize shipment routes."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize route optimizer.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.optimization_factors = config.get("optimization_factors", {
            "distance": 0.4,
            "time": 0.4,
            "cost": 0.2,
        })

    def optimize_route(
        self, shipment_id: str, waypoints: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """Optimize route for shipment.

        Args:
            shipment_id: Shipment identifier.
            waypoints: Optional list of waypoints.

        Returns:
            Dictionary with route optimization results.
        """
        shipment = self.db_manager.get_shipment(shipment_id)

        if not shipment:
            return {"error": "Shipment not found"}

        existing_routes = self.db_manager.get_shipment_routes(shipment.id)
        current_route = existing_routes[0] if existing_routes else None

        optimized_route = self._calculate_optimized_route(
            shipment, waypoints, current_route
        )

        route = self.db_manager.add_route(
            shipment_id=shipment.id,
            origin=shipment.origin,
            destination=shipment.destination,
            distance_km=optimized_route["distance_km"],
            estimated_duration_hours=optimized_route["duration_hours"],
            cost=optimized_route.get("cost"),
            waypoints=optimized_route.get("waypoints_json"),
            is_optimized="true",
        )

        savings = {}
        if current_route:
            savings = {
                "time_savings_hours": (
                    current_route.estimated_duration_hours
                    - optimized_route["duration_hours"]
                ),
                "distance_savings_km": (
                    current_route.distance_km - optimized_route["distance_km"]
                ),
                "cost_savings": (
                    (current_route.cost or 0) - (optimized_route.get("cost") or 0)
                ),
            }

            recommendation = self.db_manager.add_optimization_recommendation(
                shipment_id=shipment.id,
                recommendation_type="route_optimization",
                title=f"Optimized Route for {shipment_id}",
                description=(
                    f"Optimized route reduces travel time by {savings['time_savings_hours']:.1f} hours "
                    f"and distance by {savings['distance_savings_km']:.1f} km"
                ),
                expected_savings_hours=savings["time_savings_hours"],
                expected_savings_cost=savings["cost_savings"],
                current_route_id=current_route.id,
                recommended_route_id=route.id,
                priority="high" if savings["time_savings_hours"] > 4 else "medium",
            )

        return {
            "shipment_id": shipment_id,
            "optimized_route_id": route.id,
            "distance_km": optimized_route["distance_km"],
            "duration_hours": optimized_route["duration_hours"],
            "savings": savings,
        }

    def _calculate_optimized_route(
        self, shipment, waypoints: Optional[List[str]], current_route: Optional
    ) -> Dict[str, any]:
        """Calculate optimized route.

        Args:
            shipment: Shipment object.
            waypoints: Optional waypoints.
            current_route: Current route object.

        Returns:
            Dictionary with optimized route details.
        """
        base_distance = self._estimate_distance(shipment.origin, shipment.destination)
        base_duration = base_distance / 60.0

        if waypoints:
            optimized_distance = self._calculate_waypoint_distance(
                shipment.origin, shipment.destination, waypoints
            )
            optimized_duration = optimized_distance / 60.0
        else:
            optimized_distance = base_distance * 0.95
            optimized_duration = base_duration * 0.95

        if current_route:
            if current_route.distance_km < optimized_distance:
                optimized_distance = current_route.distance_km * 0.92
            if current_route.estimated_duration_hours < optimized_duration:
                optimized_duration = current_route.estimated_duration_hours * 0.92

        waypoints_json = None
        if waypoints:
            import json

            waypoints_json = json.dumps(waypoints)

        cost = optimized_distance * 0.5

        return {
            "distance_km": optimized_distance,
            "duration_hours": optimized_duration,
            "cost": cost,
            "waypoints_json": waypoints_json,
        }

    def _estimate_distance(self, origin: str, destination: str) -> float:
        """Estimate distance between locations.

        Args:
            origin: Origin location.
            destination: Destination location.

        Returns:
            Estimated distance in kilometers.
        """
        base_distances = {
            ("New York", "Los Angeles"): 3944,
            ("London", "Paris"): 344,
            ("Tokyo", "Shanghai"): 1777,
        }

        for (loc1, loc2), distance in base_distances.items():
            if (loc1 in origin and loc2 in destination) or (
                loc2 in origin and loc1 in destination
            ):
                return distance

        return 1000.0

    def _calculate_waypoint_distance(
        self, origin: str, destination: str, waypoints: List[str]
    ) -> float:
        """Calculate distance with waypoints.

        Args:
            origin: Origin location.
            destination: Destination location.
            waypoints: List of waypoint locations.

        Returns:
            Total distance in kilometers.
        """
        total_distance = self._estimate_distance(origin, waypoints[0])

        for i in range(len(waypoints) - 1):
            total_distance += self._estimate_distance(waypoints[i], waypoints[i + 1])

        total_distance += self._estimate_distance(waypoints[-1], destination)

        return total_distance

    def generate_optimization_recommendations(
        self, limit: int = 10
    ) -> List[Dict[str, any]]:
        """Generate route optimization recommendations.

        Args:
            limit: Maximum number of recommendations.

        Returns:
            List of recommendation dictionaries.
        """
        active_shipments = self.db_manager.get_active_shipments(limit=50)

        recommendations = []

        for shipment in active_shipments:
            routes = self.db_manager.get_shipment_routes(shipment.id)
            if not routes or routes[0].is_optimized == "true":
                continue

            current_route = routes[0]
            optimized = self._calculate_optimized_route(shipment, None, current_route)

            time_savings = (
                current_route.estimated_duration_hours - optimized["duration_hours"]
            )
            distance_savings = current_route.distance_km - optimized["distance_km"]

            if time_savings > 2.0 or distance_savings > 100:
                recommendation = self.db_manager.add_optimization_recommendation(
                    shipment_id=shipment.id,
                    recommendation_type="route_optimization",
                    title=f"Optimize Route for {shipment.shipment_id}",
                    description=(
                        f"Potential savings: {time_savings:.1f} hours, "
                        f"{distance_savings:.1f} km"
                    ),
                    expected_savings_hours=time_savings,
                    expected_savings_cost=distance_savings * 0.5,
                    current_route_id=current_route.id,
                    priority="high" if time_savings > 4 else "medium",
                )

                recommendations.append({
                    "id": recommendation.id,
                    "shipment_id": shipment.shipment_id,
                    "time_savings": time_savings,
                    "distance_savings": distance_savings,
                })

        return recommendations[:limit]
