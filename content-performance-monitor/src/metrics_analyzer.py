"""Engagement metrics analysis for content performance."""

import logging
from typing import Dict, Optional

import numpy as np

from src.database import DatabaseManager

logger = logging.getLogger(__name__)


class MetricsAnalyzer:
    """Analyzes engagement metrics and calculates performance scores."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        platform_configs: list,
    ) -> None:
        """Initialize metrics analyzer.

        Args:
            db_manager: Database manager instance.
            platform_configs: List of platform configuration dictionaries.
        """
        self.db_manager = db_manager
        self.platform_configs = {
            config["name"].lower(): config for config in platform_configs
        }

    def calculate_engagement_score(
        self, metrics: Dict, platform: str
    ) -> float:
        """Calculate engagement score for content.

        Args:
            metrics: Dictionary of metric names to values.
            platform: Platform name.

        Returns:
            Engagement score (0.0 to 1.0).
        """
        platform_config = self.platform_configs.get(platform.lower(), {})
        platform_metrics = platform_config.get("metrics", [])

        engagement_metrics = []
        for metric_name in platform_metrics:
            if metric_name in ["likes", "comments", "shares", "retweets", "replies", "saves"]:
                value = metrics.get(metric_name, 0)
                engagement_metrics.append(float(value))

        if not engagement_metrics:
            return 0.0

        total_engagement = sum(engagement_metrics)
        if total_engagement == 0:
            return 0.0

        views = metrics.get("views", 0) or metrics.get("impressions", 0) or 1
        engagement_rate = total_engagement / float(views)

        normalized_score = min(engagement_rate * 10, 1.0)
        return round(normalized_score, 4)

    def calculate_reach_score(
        self, metrics: Dict, platform: str
    ) -> Optional[float]:
        """Calculate reach score for content.

        Args:
            metrics: Dictionary of metric names to values.
            platform: Platform name.

        Returns:
            Reach score (0.0 to 1.0) or None if not applicable.
        """
        reach = metrics.get("reach", 0) or metrics.get("impressions", 0)
        if reach == 0:
            return None

        views = metrics.get("views", 0) or 1
        reach_rate = float(reach) / float(views)
        normalized_score = min(reach_rate, 1.0)
        return round(normalized_score, 4)

    def calculate_views_score(
        self, metrics: Dict, platform: str, threshold: int = 1000
    ) -> float:
        """Calculate views score for content.

        Args:
            metrics: Dictionary of metric names to values.
            platform: Platform name.
            threshold: Views threshold for normalization.

        Returns:
            Views score (0.0 to 1.0).
        """
        views = metrics.get("views", 0) or metrics.get("impressions", 0)
        if views == 0:
            return 0.0

        normalized_score = min(float(views) / float(threshold), 1.0)
        return round(normalized_score, 4)

    def calculate_overall_score(
        self,
        engagement_score: float,
        platform: str,
        reach_score: Optional[float] = None,
        views_score: Optional[float] = None,
    ) -> float:
        """Calculate overall performance score.

        Args:
            engagement_score: Engagement score.
            platform: Platform name.
            reach_score: Optional reach score.
            views_score: Optional views score.

        Returns:
            Overall score (0.0 to 1.0).
        """
        platform_config = self.platform_configs.get(platform.lower(), {})
        weights = platform_config.get("weight", {})

        engagement_weight = weights.get("engagement", 0.4)
        reach_weight = weights.get("reach", 0.3)
        views_weight = weights.get("views", 0.3)

        overall = engagement_score * engagement_weight

        if reach_score is not None:
            overall += reach_score * reach_weight
        else:
            overall += views_score * views_weight if views_score else 0

        if views_score is not None:
            overall += views_score * views_weight
        else:
            overall += reach_score * reach_weight if reach_score else 0

        return round(min(overall, 1.0), 4)

    def analyze_content(
        self, content_post_id: int, platform: str
    ) -> Dict:
        """Analyze content performance and calculate scores.

        Args:
            content_post_id: ID of the content post.
            platform: Platform name.

        Returns:
            Dictionary with analysis results including scores.
        """
        metrics = self.db_manager.get_metrics_for_post(content_post_id)

        if not metrics:
            logger.warning(
                f"No metrics found for content post {content_post_id}",
                extra={"content_post_id": content_post_id, "platform": platform},
            )
            return {
                "engagement_score": 0.0,
                "reach_score": None,
                "views_score": 0.0,
                "overall_score": 0.0,
            }

        engagement_score = self.calculate_engagement_score(metrics, platform)
        reach_score = self.calculate_reach_score(metrics, platform)
        views_score = self.calculate_views_score(metrics, platform)

        overall_score = self.calculate_overall_score(
            engagement_score, platform, reach_score, views_score
        )

        return {
            "engagement_score": engagement_score,
            "reach_score": reach_score,
            "views_score": views_score,
            "overall_score": overall_score,
            "metrics": metrics,
        }

    def analyze_all_content(
        self,
        platform: Optional[str] = None,
        days: Optional[int] = None,
    ) -> int:
        """Analyze all content posts and save results.

        Args:
            platform: Optional platform filter.
            days: Optional number of days to look back.

        Returns:
            Number of content items analyzed.
        """
        posts = self.db_manager.get_content_posts(platform=platform)

        if days:
            from datetime import datetime, timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=days)
            posts = [p for p in posts if p.posted_at >= cutoff_date]

        analyzed_count = 0
        for post in posts:
            try:
                analysis = self.analyze_content(post.id, post.platform)

                self.db_manager.save_analysis(
                    content_post_id=post.id,
                    platform=post.platform,
                    engagement_score=analysis["engagement_score"],
                    overall_score=analysis["overall_score"],
                    reach_score=analysis["reach_score"],
                    views_score=analysis["views_score"],
                )

                analyzed_count += 1
                logger.debug(
                    f"Analyzed content {post.id}",
                    extra={
                        "content_post_id": post.id,
                        "platform": post.platform,
                        "overall_score": analysis["overall_score"],
                    },
                )
            except Exception as e:
                logger.error(
                    f"Error analyzing content {post.id}: {e}",
                    extra={
                        "content_post_id": post.id,
                        "platform": post.platform,
                        "error": str(e),
                    },
                )

        logger.info(
            f"Analyzed {analyzed_count} content items",
            extra={"analyzed_count": analyzed_count, "platform": platform},
        )

        return analyzed_count
