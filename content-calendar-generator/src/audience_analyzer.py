"""Audience engagement analyzer module.

Analyzes audience engagement patterns from historical post data to identify
trends and optimize content calendar generation.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.config import EngagementConfig, Settings

logger = logging.getLogger(__name__)


class AudienceAnalyzer:
    """Analyzes audience engagement patterns."""

    def __init__(self, settings: Settings) -> None:
        """Initialize audience analyzer.

        Args:
            settings: Application settings containing engagement config.
        """
        self.settings = settings
        self.config: EngagementConfig = settings.engagement

    def calculate_engagement_score(
        self, metrics: Dict[str, float]
    ) -> float:
        """Calculate weighted engagement score from metrics.

        Args:
            metrics: Dictionary of engagement metrics and their values.

        Returns:
            Weighted engagement score.
        """
        score = 0.0
        weights = self.config.metric_weights

        for metric, value in metrics.items():
            if metric in weights:
                score += value * weights[metric]

        return score

    def analyze_historical_engagement(
        self, historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze historical engagement data.

        Args:
            historical_data: List of post data dictionaries with engagement
                metrics and timestamps.

        Returns:
            Dictionary containing:
                - average_engagement: Average engagement score
                - top_performing_content_types: List of best content types
                - engagement_by_day: Engagement by day of week
                - engagement_by_hour: Engagement by hour of day
                - trending_topics: List of trending topics
        """
        if not historical_data:
            logger.warning("No historical data provided for analysis")
            return {
                "average_engagement": 0.0,
                "top_performing_content_types": [],
                "engagement_by_day": {},
                "engagement_by_hour": {},
                "trending_topics": [],
            }

        engagement_scores = []
        content_type_engagement = defaultdict(list)
        day_engagement = defaultdict(list)
        hour_engagement = defaultdict(list)
        topic_engagement = defaultdict(list)

        cutoff_date = datetime.now() - timedelta(
            days=self.config.analysis_period_days
        )

        for post in historical_data:
            post_date = self._parse_date(post.get("timestamp"))
            if post_date and post_date < cutoff_date:
                continue

            metrics = {
                "likes": post.get("likes", 0),
                "comments": post.get("comments", 0),
                "shares": post.get("shares", 0),
                "clicks": post.get("clicks", 0),
                "impressions": post.get("impressions", 0),
                "reach": post.get("reach", 0),
            }

            score = self.calculate_engagement_score(metrics)
            engagement_scores.append(score)

            content_type = post.get("content_type", "unknown")
            content_type_engagement[content_type].append(score)

            if post_date:
                day_engagement[post_date.strftime("%A")].append(score)
                hour_engagement[post_date.hour].append(score)

            topics = post.get("topics", [])
            for topic in topics:
                topic_engagement[topic].append(score)

        avg_engagement = (
            sum(engagement_scores) / len(engagement_scores)
            if engagement_scores
            else 0.0
        )

        content_type_avg = {
            ct: sum(scores) / len(scores)
            for ct, scores in content_type_engagement.items()
            if scores
        }
        top_content_types = sorted(
            content_type_avg.items(), key=lambda x: x[1], reverse=True
        )[:5]

        day_avg = {
            day: sum(scores) / len(scores)
            for day, scores in day_engagement.items()
            if scores
        }

        hour_avg = {
            hour: sum(scores) / len(scores)
            for hour, scores in hour_engagement.items()
            if scores
        }

        topic_avg = {
            topic: sum(scores) / len(scores)
            for topic, scores in topic_engagement.items()
            if scores
        }
        trending_topics = sorted(
            topic_avg.items(), key=lambda x: x[1], reverse=True
        )[:10]

        logger.info(
            f"Analyzed {len(historical_data)} posts, "
            f"average engagement: {avg_engagement:.2f}"
        )

        return {
            "average_engagement": avg_engagement,
            "top_performing_content_types": [
                ct for ct, _ in top_content_types
            ],
            "engagement_by_day": day_avg,
            "engagement_by_hour": hour_avg,
            "trending_topics": [topic for topic, _ in trending_topics],
        }

    def get_optimal_content_types(
        self, analysis_results: Dict[str, Any]
    ) -> List[str]:
        """Get optimal content types based on engagement analysis.

        Args:
            analysis_results: Results from analyze_historical_engagement.

        Returns:
            List of content types ordered by performance.
        """
        return analysis_results.get("top_performing_content_types", [])

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
