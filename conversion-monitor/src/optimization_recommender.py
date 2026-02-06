"""Generate optimization recommendations for improving conversions."""

from typing import Dict, List, Optional

from src.database import DatabaseManager


class OptimizationRecommender:
    """Generate optimization recommendations."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize optimization recommender.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.recommendation_templates = config.get("recommendation_templates", {})

    def generate_recommendations(
        self,
        website_id: int,
        conversion_goal_id: Optional[int] = None,
    ) -> List[Dict[str, any]]:
        """Generate optimization recommendations.

        Args:
            website_id: Website ID.
            conversion_goal_id: Optional conversion goal ID.

        Returns:
            List of recommendation dictionaries.
        """
        dropoffs = self.db_manager.get_dropoff_points(website_id=website_id)

        from src.conversion_monitor import ConversionMonitor

        monitor = ConversionMonitor(self.db_manager, self.config.get("monitoring", {}))
        conversion_stats = monitor.get_conversion_statistics(
            website_id=website_id, conversion_goal_id=conversion_goal_id
        )

        recommendations = []

        for dropoff in dropoffs:
            rec = self._generate_dropoff_recommendation(dropoff, conversion_stats)
            if rec:
                recommendation = self.db_manager.add_recommendation(
                    website_id=website_id,
                    recommendation_type=rec["type"],
                    title=rec["title"],
                    description=rec["description"],
                    priority=rec["priority"],
                    expected_impact=rec["expected_impact"],
                    dropoff_point_id=dropoff.id,
                )
                recommendations.append({
                    "id": recommendation.id,
                    "title": recommendation.title,
                    "description": recommendation.description,
                    "priority": recommendation.priority,
                    "expected_impact": recommendation.expected_impact,
                })

        general_recommendations = self._generate_general_recommendations(
            website_id, conversion_stats
        )
        for rec in general_recommendations:
            recommendation = self.db_manager.add_recommendation(
                website_id=website_id,
                recommendation_type=rec["type"],
                title=rec["title"],
                description=rec["description"],
                priority=rec["priority"],
                expected_impact=rec["expected_impact"],
            )
            recommendations.append({
                "id": recommendation.id,
                "title": recommendation.title,
                "description": recommendation.description,
                "priority": recommendation.priority,
                "expected_impact": recommendation.expected_impact,
            })

        return recommendations

    def _generate_dropoff_recommendation(
        self, dropoff, conversion_stats: Dict
    ) -> Optional[Dict[str, any]]:
        """Generate recommendation for drop-off point.

        Args:
            dropoff: DropOffPoint object.
            conversion_stats: Conversion statistics.

        Returns:
            Recommendation dictionary or None.
        """
        dropoff_rate = dropoff.dropoff_rate or 0.0

        if dropoff_rate < 0.2:
            return None

        priority = "high" if dropoff_rate > 0.5 else "medium"
        expected_impact = min(dropoff_rate * 1.5, 1.0)

        if dropoff.journey_step:
            step_name = dropoff.journey_step.step_name
            title = f"Optimize {step_name} to Reduce Drop-offs"
            description = (
                f"High drop-off rate ({dropoff_rate:.1%}) detected at '{step_name}'. "
                f"Consider improving page load time, simplifying form fields, "
                f"or enhancing user experience at this step."
            )
        else:
            title = "Reduce Drop-offs at Critical Point"
            description = (
                f"High drop-off rate ({dropoff_rate:.1%}) detected. "
                f"Review user experience, page performance, and content clarity "
                f"to improve conversion rates."
            )

        return {
            "type": "dropoff_optimization",
            "title": title,
            "description": description,
            "priority": priority,
            "expected_impact": expected_impact,
        }

    def _generate_general_recommendations(
        self, website_id: int, conversion_stats: Dict
    ) -> List[Dict[str, any]]:
        """Generate general optimization recommendations.

        Args:
            website_id: Website ID.
            conversion_stats: Conversion statistics.

        Returns:
            List of recommendation dictionaries.
        """
        recommendations = []

        conversion_rate = conversion_stats.get("conversion_rate", 0.0)
        avg_duration = conversion_stats.get("average_session_duration", 0.0)
        avg_page_views = conversion_stats.get("average_page_views", 0.0)

        if conversion_rate < 2.0:
            recommendations.append({
                "type": "conversion_optimization",
                "title": "URGENT: Improve Overall Conversion Rate",
                "description": (
                    f"Current conversion rate ({conversion_rate:.2f}%) is below industry average. "
                    f"Focus on improving value proposition, simplifying checkout process, "
                    f"and reducing friction in user journey."
                ),
                "priority": "urgent",
                "expected_impact": 0.8,
            })

        if avg_duration < 60:
            recommendations.append({
                "type": "engagement_optimization",
                "title": "Improve User Engagement",
                "description": (
                    f"Average session duration ({avg_duration:.0f}s) is low. "
                    f"Enhance content quality, improve page relevance, "
                    f"and provide clear calls-to-action to increase engagement."
                ),
                "priority": "medium",
                "expected_impact": 0.5,
            })

        if avg_page_views < 2:
            recommendations.append({
                "type": "navigation_optimization",
                "title": "Enhance Site Navigation",
                "description": (
                    f"Users view only {avg_page_views:.1f} pages on average. "
                    f"Improve internal linking, add related content suggestions, "
                    f"and optimize navigation structure."
                ),
                "priority": "medium",
                "expected_impact": 0.4,
            })

        if conversion_rate > 0 and conversion_rate < 5.0:
            recommendations.append({
                "type": "conversion_optimization",
                "title": "Optimize Conversion Funnel",
                "description": (
                    f"Conversion rate ({conversion_rate:.2f}%) has room for improvement. "
                    f"Test different value propositions, optimize landing pages, "
                    f"and implement A/B testing for key conversion points."
                ),
                "priority": "high",
                "expected_impact": 0.6,
            })

        return recommendations

    def get_recommendations_summary(
        self, website_id: int
    ) -> Dict[str, any]:
        """Get recommendations summary.

        Args:
            website_id: Website ID.

        Returns:
            Dictionary with recommendations summary.
        """
        recommendations = self.db_manager.get_recommendations(website_id=website_id)

        from collections import Counter

        priority_counts = Counter(r.priority for r in recommendations)
        type_counts = Counter(r.recommendation_type for r in recommendations)

        avg_impact = (
            sum(r.expected_impact for r in recommendations if r.expected_impact)
            / len(recommendations)
            if recommendations
            else 0.0
        )

        return {
            "total_recommendations": len(recommendations),
            "by_priority": dict(priority_counts),
            "by_type": dict(type_counts),
            "average_expected_impact": avg_impact,
        }
