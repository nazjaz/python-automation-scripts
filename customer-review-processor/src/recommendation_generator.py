"""Generate improvement recommendations from review analysis."""

from typing import Dict, List


class RecommendationGenerator:
    """Generate improvement recommendations based on review analysis."""

    def __init__(self, config: Dict):
        """Initialize recommendation generator.

        Args:
            config: Configuration dictionary with recommendation settings.
        """
        self.config = config
        self.recommendation_templates = config.get("recommendation_templates", {})
        self.priority_weights = config.get("priority_weights", {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.5,
            "low": 0.3,
        })

    def generate_recommendations(
        self, issues: List[Dict[str, any]], aggregated_issues: Dict[str, any]
    ) -> List[Dict[str, any]]:
        """Generate improvement recommendations from issues.

        Args:
            issues: List of identified issues.
            aggregated_issues: Aggregated issue statistics.

        Returns:
            List of recommendation dictionaries.
        """
        if not issues:
            return []

        recommendations = []
        processed_categories = set()

        for issue in issues:
            category = issue.get("category", "general")
            severity = issue.get("severity", "medium")

            if category not in processed_categories:
                recommendation = self._create_recommendation(issue, category, severity)
                if recommendation:
                    recommendations.append(recommendation)
                    processed_categories.add(category)

        recommendations.sort(key=lambda x: x.get("impact_score", 0), reverse=True)

        return recommendations

    def _create_recommendation(
        self, issue: Dict[str, any], category: str, severity: str
    ) -> Dict[str, any]:
        """Create recommendation for an issue.

        Args:
            issue: Issue dictionary.
            category: Issue category.
            severity: Issue severity.

        Returns:
            Recommendation dictionary.
        """
        template = self.recommendation_templates.get(category, {}).get(
            severity, self._get_default_recommendation(category, severity)
        )

        priority = self._determine_priority(severity)
        impact_score = self._calculate_impact_score(severity, category)

        return {
            "recommendation_text": template,
            "priority": priority,
            "category": category,
            "impact_score": impact_score,
        }

    def _get_default_recommendation(self, category: str, severity: str) -> str:
        """Get default recommendation text.

        Args:
            category: Issue category.
            severity: Issue severity.

        Returns:
            Default recommendation text.
        """
        base_recommendations = {
            "quality": "Improve product quality control and testing processes to address quality issues.",
            "performance": "Optimize product performance and address performance bottlenecks.",
            "design": "Review and improve product design based on customer feedback.",
            "customer_service": "Enhance customer service processes and response times.",
            "shipping": "Improve shipping and delivery processes to reduce delays and issues.",
            "pricing": "Review pricing strategy and consider value adjustments.",
            "general": "Address customer concerns and improve overall product experience.",
        }

        recommendation = base_recommendations.get(category, base_recommendations["general"])

        if severity in ["critical", "high"]:
            recommendation = f"URGENT: {recommendation}"

        return recommendation

    def _determine_priority(self, severity: str) -> str:
        """Determine recommendation priority from severity.

        Args:
            severity: Issue severity.

        Returns:
            Priority level (low, medium, high, urgent).
        """
        priority_map = {
            "critical": "urgent",
            "high": "high",
            "medium": "medium",
            "low": "low",
        }
        return priority_map.get(severity, "medium")

    def _calculate_impact_score(self, severity: str, category: str) -> float:
        """Calculate impact score for recommendation.

        Args:
            severity: Issue severity.
            category: Issue category.

        Returns:
            Impact score (0.0 to 1.0).
        """
        base_score = self.priority_weights.get(severity, 0.5)

        category_weights = {
            "quality": 1.0,
            "performance": 0.9,
            "customer_service": 0.8,
            "design": 0.7,
            "shipping": 0.6,
            "pricing": 0.5,
            "general": 0.4,
        }

        category_multiplier = category_weights.get(category, 0.5)
        impact_score = base_score * category_multiplier

        return min(impact_score, 1.0)

    def generate_category_recommendations(
        self, aggregated_issues: Dict[str, any]
    ) -> List[Dict[str, any]]:
        """Generate recommendations by category.

        Args:
            aggregated_issues: Aggregated issue statistics.

        Returns:
            List of category-based recommendations.
        """
        recommendations = []
        category_counts = aggregated_issues.get("by_category", {})

        for category, count in sorted(
            category_counts.items(), key=lambda x: x[1], reverse=True
        ):
            if count > 0:
                recommendation = {
                    "recommendation_text": f"Focus on addressing {category} issues. "
                    f"{count} issue(s) identified in this category.",
                    "priority": "high" if count >= 5 else "medium",
                    "category": category,
                    "impact_score": min(count / 10.0, 1.0),
                }
                recommendations.append(recommendation)

        return recommendations
