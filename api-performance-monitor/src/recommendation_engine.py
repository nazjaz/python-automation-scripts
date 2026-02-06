"""Generates optimization recommendations for API endpoints."""

import logging
from typing import Dict, List, Optional

from src.database import DatabaseManager, OptimizationRecommendation, APIRequest

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates optimization recommendations based on performance analysis."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize recommendation engine.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.optimization_config = config.get("optimization", {})

    def generate_recommendations(
        self,
        endpoint_id: int,
    ) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations for endpoint.

        Args:
            endpoint_id: Endpoint ID.

        Returns:
            List of OptimizationRecommendation objects.
        """
        if not self.optimization_config.get("generate_recommendations", True):
            return []

        requests = self.db_manager.get_requests(endpoint_id=endpoint_id, limit=100)
        endpoint = (
            self.db_manager.get_session()
            .query(self.db_manager.__class__.__module__)
            .first()
        )

        from src.database import APIEndpoint
        endpoint = (
            self.db_manager.get_session()
            .query(APIEndpoint)
            .filter(APIEndpoint.id == endpoint_id)
            .first()
        )

        if not endpoint:
            return []

        recommendations = []

        if self.optimization_config.get("check_caching", True):
            recommendations.extend(self._check_caching(endpoint, requests))

        if self.optimization_config.get("check_compression", True):
            recommendations.extend(self._check_compression(endpoint, requests))

        if self.optimization_config.get("check_pagination", True):
            recommendations.extend(self._check_pagination(endpoint, requests))

        if self.optimization_config.get("check_query_optimization", True):
            recommendations.extend(self._check_query_optimization(endpoint, requests))

        for rec in recommendations:
            self.db_manager.add_recommendation(
                endpoint_id=endpoint_id,
                recommendation_type=rec["type"],
                title=rec["title"],
                description=rec["description"],
                priority=rec["priority"],
                estimated_improvement=rec.get("estimated_improvement"),
            )

        logger.info(
            f"Generated {len(recommendations)} recommendations for endpoint {endpoint_id}",
            extra={"endpoint_id": endpoint_id, "recommendation_count": len(recommendations)},
        )

        return recommendations

    def _check_caching(
        self, endpoint, requests: List[APIRequest]
    ) -> List[Dict]:
        """Check for caching opportunities.

        Args:
            endpoint: APIEndpoint object.
            requests: List of APIRequest objects.

        Returns:
            List of recommendation dictionaries.
        """
        recommendations = []

        if endpoint.method == "GET" and len(requests) > 10:
            response_times = [r.response_time_ms for r in requests if r.response_time_ms]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                if avg_response_time > 500:
                    recommendations.append(
                        {
                            "type": "caching",
                            "title": "Implement Response Caching",
                            "description": f"GET endpoint with average response time {avg_response_time:.2f}ms. "
                            f"Consider implementing HTTP caching headers or application-level caching to reduce response times.",
                            "priority": "high",
                            "estimated_improvement": 50.0,
                        }
                    )

        return recommendations

    def _check_compression(
        self, endpoint, requests: List[APIRequest]
    ) -> List[Dict]:
        """Check for compression opportunities.

        Args:
            endpoint: APIEndpoint object.
            requests: List of APIRequest objects.

        Returns:
            List of recommendation dictionaries.
        """
        recommendations = []

        response_sizes = [r.response_size_bytes for r in requests if r.response_size_bytes]
        if response_sizes:
            avg_size = sum(response_sizes) / len(response_sizes)
            if avg_size > 10000:
                recommendations.append(
                    {
                        "type": "compression",
                        "title": "Enable Response Compression",
                        "description": f"Average response size {avg_size:.0f} bytes. "
                        f"Enable gzip or brotli compression to reduce bandwidth and improve response times.",
                        "priority": "medium",
                        "estimated_improvement": 30.0,
                    }
                )

        return recommendations

    def _check_pagination(
        self, endpoint, requests: List[APIRequest]
    ) -> List[Dict]:
        """Check for pagination opportunities.

        Args:
            endpoint: APIEndpoint object.
            requests: List of APIRequest objects.

        Returns:
            List of recommendation dictionaries.
        """
        recommendations = []

        response_sizes = [r.response_size_bytes for r in requests if r.response_size_bytes]
        if response_sizes:
            max_size = max(response_sizes)
            if max_size > 100000:
                recommendations.append(
                    {
                        "type": "pagination",
                        "title": "Implement Pagination",
                        "description": f"Large response size detected ({max_size:.0f} bytes). "
                        f"Consider implementing pagination to reduce response sizes and improve performance.",
                        "priority": "medium",
                        "estimated_improvement": 40.0,
                    }
                )

        return recommendations

    def _check_query_optimization(
        self, endpoint, requests: List[APIRequest]
    ) -> List[Dict]:
        """Check for query optimization opportunities.

        Args:
            endpoint: APIEndpoint object.
            requests: List of APIRequest objects.

        Returns:
            List of recommendation dictionaries.
        """
        recommendations = []

        response_times = [r.response_time_ms for r in requests if r.response_time_ms]
        if response_times:
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            if p95_response_time > 2000:
                recommendations.append(
                    {
                        "type": "query_optimization",
                        "title": "Optimize Database Queries",
                        "description": f"P95 response time {p95_response_time:.2f}ms suggests potential database query issues. "
                        f"Review and optimize database queries, add indexes, or implement query result caching.",
                        "priority": "high",
                        "estimated_improvement": 60.0,
                    }
                )

        return recommendations
