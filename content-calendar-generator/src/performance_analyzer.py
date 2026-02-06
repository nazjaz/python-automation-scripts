"""Content performance analyzer module.

Analyzes content performance metrics to identify high-performing content
patterns and optimize future content calendar generation.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.config import PerformanceConfig, Settings

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """Analyzes content performance metrics."""

    def __init__(self, settings: Settings) -> None:
        """Initialize performance analyzer.

        Args:
            settings: Application settings containing performance config.
        """
        self.settings = settings
        self.config: PerformanceConfig = settings.performance

    def analyze_performance(
        self, historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze content performance from historical data.

        Args:
            historical_data: List of post data dictionaries with performance
                metrics.

        Returns:
            Dictionary containing:
                - average_engagement_rate: Average engagement rate
                - average_ctr: Average click-through rate
                - high_performing_content: List of high-performing content IDs
                - performance_by_type: Performance metrics by content type
                - performance_trends: Performance trends over time
        """
        if not historical_data:
            logger.warning("No historical data provided for performance analysis")
            return {
                "average_engagement_rate": 0.0,
                "average_ctr": 0.0,
                "high_performing_content": [],
                "performance_by_type": {},
                "performance_trends": {},
            }

        engagement_rates = []
        ctrs = []
        content_type_performance = defaultdict(list)
        high_performers = []
        cutoff_date = datetime.now() - timedelta(
            days=self.config.analysis_period_days
        )

        for post in historical_data:
            post_date = self._parse_date(post.get("timestamp"))
            if post_date and post_date < cutoff_date:
                continue

            impressions = post.get("impressions", 0)
            if impressions == 0:
                continue

            engagement = (
                post.get("likes", 0)
                + post.get("comments", 0)
                + post.get("shares", 0)
            )
            engagement_rate = engagement / impressions
            engagement_rates.append(engagement_rate)

            clicks = post.get("clicks", 0)
            ctr = clicks / impressions
            ctrs.append(ctr)

            content_type = post.get("content_type", "unknown")
            content_type_performance[content_type].append(
                {"engagement_rate": engagement_rate, "ctr": ctr}
            )

            if engagement_rate >= self.config.thresholds.get(
                "high_performance", 0.05
            ):
                high_performers.append(post.get("id", "unknown"))

        avg_engagement_rate = (
            sum(engagement_rates) / len(engagement_rates)
            if engagement_rates
            else 0.0
        )
        avg_ctr = sum(ctrs) / len(ctrs) if ctrs else 0.0

        performance_by_type = {}
        for content_type, metrics_list in content_type_performance.items():
            if metrics_list:
                avg_er = sum(m["engagement_rate"] for m in metrics_list) / len(
                    metrics_list
                )
                avg_ctr_type = sum(m["ctr"] for m in metrics_list) / len(
                    metrics_list
                )
                performance_by_type[content_type] = {
                    "engagement_rate": avg_er,
                    "ctr": avg_ctr_type,
                }

        logger.info(
            f"Analyzed performance for {len(historical_data)} posts, "
            f"avg engagement rate: {avg_engagement_rate:.4f}, "
            f"avg CTR: {avg_ctr:.4f}"
        )

        return {
            "average_engagement_rate": avg_engagement_rate,
            "average_ctr": avg_ctr,
            "high_performing_content": high_performers,
            "performance_by_type": performance_by_type,
            "performance_trends": {},
        }

    def get_best_content_types(
        self, performance_results: Dict[str, Any]
    ) -> List[str]:
        """Get best performing content types.

        Args:
            performance_results: Results from analyze_performance.

        Returns:
            List of content types ordered by performance.
        """
        performance_by_type = performance_results.get(
            "performance_by_type", {}
        )

        sorted_types = sorted(
            performance_by_type.items(),
            key=lambda x: x[1].get("engagement_rate", 0),
            reverse=True,
        )

        return [content_type for content_type, _ in sorted_types]

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object.

        Args:
            date_str: Date string in various formats.

        Returns:
            Datetime object or None if parsing fails.
        """
        if not date_str:
            return None

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S%z",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except (ValueError, TypeError):
                continue

        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            logger.warning(f"Could not parse date: {date_str}")
            return None
