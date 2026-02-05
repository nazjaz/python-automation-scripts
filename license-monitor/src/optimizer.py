"""License optimization and cost reduction recommendations."""

import logging
from typing import Optional

from src.database import (
    DatabaseManager,
    License,
    OptimizationRecommendation,
)

logger = logging.getLogger(__name__)


class LicenseOptimizer:
    """Generates optimization recommendations for license cost reduction."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        license_types_config: list[dict],
        cost_savings_threshold: float = 100.00,
    ):
        """Initialize license optimizer.

        Args:
            db_manager: Database manager instance.
            license_types_config: License type configurations with costs.
            cost_savings_threshold: Minimum cost savings to report.
        """
        self.db_manager = db_manager
        self.license_types_config = {
            lt["name"]: lt for lt in license_types_config
        }
        self.cost_savings_threshold = cost_savings_threshold

    def identify_unused_licenses(
        self, threshold_days: int = 90
    ) -> list[OptimizationRecommendation]:
        """Identify unused licenses and create recommendations.

        Args:
            threshold_days: Days of inactivity to consider unused.

        Returns:
            List of OptimizationRecommendation objects.
        """
        unused_licenses = self.db_manager.get_unused_licenses(threshold_days)
        recommendations = []

        license_groups = {}
        for license_obj in unused_licenses:
            if license_obj.license_type not in license_groups:
                license_groups[license_obj.license_type] = []
            license_groups[license_obj.license_type].append(license_obj)

        for license_type, licenses in license_groups.items():
            license_config = self.license_types_config.get(license_type, {})
            cost_per_license = license_config.get("cost_per_license", 0.0)
            total_savings = len(licenses) * cost_per_license

            if total_savings >= self.cost_savings_threshold:
                recommendation = self._create_recommendation(
                    license_type=license_type,
                    recommendation_type="unused_licenses",
                    description=(
                        f"Found {len(licenses)} unused {license_type} licenses "
                        f"unused for {threshold_days}+ days. Consider revoking "
                        f"these licenses to save ${total_savings:.2f} annually."
                    ),
                    estimated_savings=total_savings,
                    priority="high" if total_savings > 1000 else "medium",
                )
                recommendations.append(recommendation)

        logger.info(f"Identified {len(recommendations)} unused license recommendations")
        return recommendations

    def identify_over_licensed_scenarios(
        self,
    ) -> list[OptimizationRecommendation]:
        """Identify scenarios where too many licenses are purchased.

        Returns:
            List of OptimizationRecommendation objects.
        """
        recommendations = []

        with self.db_manager.get_session() as session:
            for license_type, license_config in self.license_types_config.items():
                licenses = self.db_manager.get_licenses_by_type(license_type)
                total_licenses = len(licenses)
                assigned_licenses = sum(1 for l in licenses if l.assigned_to)

                if total_licenses > 0:
                    utilization_rate = assigned_licenses / total_licenses

                    if utilization_rate < 0.7 and total_licenses > 10:
                        cost_per_license = license_config.get("cost_per_license", 0.0)
                        excess_licenses = int(total_licenses * 0.3)
                        potential_savings = excess_licenses * cost_per_license

                        if potential_savings >= self.cost_savings_threshold:
                            recommendation = self._create_recommendation(
                                license_type=license_type,
                                recommendation_type="over_licensed",
                                description=(
                                    f"{license_type} has {utilization_rate:.1%} "
                                    f"utilization rate. Consider reducing licenses "
                                    f"by {excess_licenses} to save "
                                    f"${potential_savings:.2f} annually."
                                ),
                                estimated_savings=potential_savings,
                                priority="medium",
                            )
                            recommendations.append(recommendation)

        logger.info(
            f"Identified {len(recommendations)} over-licensed recommendations"
        )
        return recommendations

    def _create_recommendation(
        self,
        license_type: str,
        recommendation_type: str,
        description: str,
        estimated_savings: float,
        priority: str = "medium",
    ) -> OptimizationRecommendation:
        """Create an optimization recommendation.

        Args:
            license_type: License type name.
            recommendation_type: Type of recommendation.
            description: Recommendation description.
            estimated_savings: Estimated annual savings.
            priority: Priority level (high, medium, low).

        Returns:
            Created OptimizationRecommendation object.
        """
        with self.db_manager.get_session() as session:
            recommendation = OptimizationRecommendation(
                license_type=license_type,
                recommendation_type=recommendation_type,
                description=description,
                estimated_savings=estimated_savings,
                priority=priority,
            )
            session.add(recommendation)
            session.commit()
            session.refresh(recommendation)

        return recommendation

    def generate_all_recommendations(
        self, threshold_days: int = 90
    ) -> list[OptimizationRecommendation]:
        """Generate all optimization recommendations.

        Args:
            threshold_days: Days of inactivity for unused license detection.

        Returns:
            List of all OptimizationRecommendation objects.
        """
        recommendations = []

        recommendations.extend(self.identify_unused_licenses(threshold_days))
        recommendations.extend(self.identify_over_licensed_scenarios())

        total_savings = sum(r.estimated_savings for r in recommendations)
        logger.info(
            f"Generated {len(recommendations)} recommendations with total "
            f"potential savings: ${total_savings:.2f}"
        )

        return recommendations
