"""Generates content strategy recommendations based on performance analysis."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd

from src.database import DatabaseManager
from src.top_content_identifier import TopContentIdentifier

logger = logging.getLogger(__name__)


class StrategyRecommender:
    """Generates content strategy recommendations."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        top_content_identifier: TopContentIdentifier,
        config: Dict,
    ) -> None:
        """Initialize strategy recommender.

        Args:
            db_manager: Database manager instance.
            top_content_identifier: Top content identifier instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.top_content_identifier = top_content_identifier
        self.config = config
        self.strategy_config = config.get("strategy", {})

    def analyze_content_trends(
        self, platform: Optional[str] = None, days: int = 7
    ) -> Dict:
        """Analyze content performance trends.

        Args:
            platform: Optional platform filter.
            days: Number of days to analyze.

        Returns:
            Dictionary with trend analysis results.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        posts = self.db_manager.get_content_posts(platform=platform)
        recent_posts = [p for p in posts if p.posted_at >= cutoff_date]

        if not recent_posts:
            return {
                "total_posts": 0,
                "avg_engagement": 0.0,
                "top_content_type": None,
                "best_posting_day": None,
                "best_posting_hour": None,
            }

        engagement_scores = []
        content_types = {}
        posting_days = {}
        posting_hours = {}

        for post in recent_posts:
            metrics = self.db_manager.get_metrics_for_post(post.id)
            if metrics:
                views = metrics.get("views", 0) or metrics.get("impressions", 0)
                likes = metrics.get("likes", 0)
                comments = metrics.get("comments", 0) or metrics.get("replies", 0)
                shares = (
                    metrics.get("shares", 0)
                    or metrics.get("retweets", 0)
                    or metrics.get("saves", 0)
                )

                if views > 0:
                    engagement = (likes + comments + shares) / float(views)
                    engagement_scores.append(engagement)

                if post.content_type:
                    content_types[post.content_type] = (
                        content_types.get(post.content_type, 0) + 1
                    )

                if post.posted_at:
                    posting_days[post.posted_at.weekday()] = (
                        posting_days.get(post.posted_at.weekday(), 0) + 1
                    )
                    posting_hours[post.posted_at.hour] = (
                        posting_hours.get(post.posted_at.hour, 0) + 1
                    )

        avg_engagement = (
            sum(engagement_scores) / len(engagement_scores)
            if engagement_scores
            else 0.0
        )

        top_content_type = (
            max(content_types.items(), key=lambda x: x[1])[0]
            if content_types
            else None
        )

        best_posting_day = (
            max(posting_days.items(), key=lambda x: x[1])[0]
            if posting_days
            else None
        )

        best_posting_hour = (
            max(posting_hours.items(), key=lambda x: x[1])[0]
            if posting_hours
            else None
        )

        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        return {
            "total_posts": len(recent_posts),
            "avg_engagement": round(avg_engagement, 4),
            "top_content_type": top_content_type,
            "best_posting_day": day_names[best_posting_day]
            if best_posting_day is not None
            else None,
            "best_posting_hour": best_posting_hour,
        }

    def generate_recommendations(
        self, platform: Optional[str] = None
    ) -> List[Dict]:
        """Generate content strategy recommendations.

        Args:
            platform: Optional platform filter.

        Returns:
            List of recommendation dictionaries.
        """
        recommendations = []

        top_content = self.top_content_identifier.get_top_content(
            platform=platform, days=30
        )

        if not top_content:
            recommendations.append(
                {
                    "type": "info",
                    "priority": "medium",
                    "title": "Insufficient Data",
                    "description": "Not enough content data available for analysis. "
                    "Collect more content performance data to generate recommendations.",
                }
            )
            return recommendations

        trends = self.analyze_content_trends(platform=platform, days=7)

        top_content_types = {}
        for item in top_content[:10]:
            content_type = item.get("content_type", "unknown")
            top_content_types[content_type] = (
                top_content_types.get(content_type, 0) + 1
            )

        if top_content_types:
            best_type = max(top_content_types.items(), key=lambda x: x[1])[0]
            recommendations.append(
                {
                    "type": "content_type",
                    "priority": "high",
                    "title": f"Focus on {best_type.title()} Content",
                    "description": f"Your top-performing content is primarily {best_type} type. "
                    f"Consider creating more {best_type} content to maximize engagement.",
                }
            )

        if trends["best_posting_day"]:
            recommendations.append(
                {
                    "type": "timing",
                    "priority": "high",
                    "title": f"Post on {trends['best_posting_day']}s",
                    "description": f"Your content performs best when posted on {trends['best_posting_day']}s. "
                    f"Schedule more content for this day of the week.",
                }
            )

        if trends["best_posting_hour"] is not None:
            hour_str = f"{trends['best_posting_hour']:02d}:00"
            recommendations.append(
                {
                    "type": "timing",
                    "priority": "medium",
                    "title": f"Optimal Posting Time: {hour_str}",
                    "description": f"Content posted around {hour_str} tends to perform better. "
                    f"Consider scheduling content for this time slot.",
                }
            )

        avg_engagement = trends["avg_engagement"]
        if avg_engagement < 0.05:
            recommendations.append(
                {
                    "type": "engagement",
                    "priority": "high",
                    "title": "Improve Engagement Rates",
                    "description": f"Current average engagement rate is {avg_engagement:.2%}, "
                    f"which is below optimal. Focus on creating more engaging content, "
                    f"asking questions, and responding to comments.",
                }
            )

        top_item = top_content[0] if top_content else None
        if top_item:
            recommendations.append(
                {
                    "type": "content_analysis",
                    "priority": "medium",
                    "title": "Analyze Top-Performing Content",
                    "description": f"Your top content '{top_item.get('title', 'N/A')[:50]}...' "
                    f"scored {top_item.get('overall_score', 0):.2%}. "
                    f"Analyze what made it successful and replicate those elements.",
                }
            )

        platform_specific = self._get_platform_specific_recommendations(
            platform, top_content
        )
        recommendations.extend(platform_specific)

        recommendation_count = self.strategy_config.get("recommendation_count", 5)
        recommendations = recommendations[:recommendation_count]

        logger.info(
            f"Generated {len(recommendations)} recommendations",
            extra={
                "count": len(recommendations),
                "platform": platform,
            },
        )

        return recommendations

    def _get_platform_specific_recommendations(
        self, platform: Optional[str], top_content: List[Dict]
    ) -> List[Dict]:
        """Get platform-specific recommendations.

        Args:
            platform: Platform name.
            top_content: List of top content items.

        Returns:
            List of platform-specific recommendations.
        """
        recommendations = []

        if not platform:
            return recommendations

        platform_lower = platform.lower()

        if platform_lower == "youtube":
            watch_times = [
                item.get("metrics", {}).get("watch_time", 0)
                for item in top_content
                if item.get("metrics", {}).get("watch_time", 0) > 0
            ]
            if watch_times:
                avg_watch_time = sum(watch_times) / len(watch_times)
                recommendations.append(
                    {
                        "type": "platform_specific",
                        "priority": "medium",
                        "title": "Optimize Video Length",
                        "description": f"Average watch time is {avg_watch_time:.0f} seconds. "
                        f"Consider creating videos that match this optimal length.",
                    }
                )

        elif platform_lower in ["facebook", "instagram"]:
            shares = [
                item.get("metrics", {}).get("shares", 0)
                for item in top_content
                if item.get("metrics", {}).get("shares", 0) > 0
            ]
            if shares:
                recommendations.append(
                    {
                        "type": "platform_specific",
                        "priority": "medium",
                        "title": "Increase Shareability",
                        "description": "Your top content gets shared frequently. "
                        "Create more shareable content with compelling visuals and clear value propositions.",
                    }
                )

        elif platform_lower == "twitter":
            retweets = [
                item.get("metrics", {}).get("retweets", 0)
                for item in top_content
                if item.get("metrics", {}).get("retweets", 0) > 0
            ]
            if retweets:
                recommendations.append(
                    {
                        "type": "platform_specific",
                        "priority": "medium",
                        "title": "Leverage Retweets",
                        "description": "Your top content gets retweeted. "
                        "Use trending hashtags and timely topics to increase retweet potential.",
                    }
                )

        return recommendations
