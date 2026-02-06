"""Optimal posting time analyzer module.

Analyzes historical post data to determine optimal posting times based on
audience engagement patterns.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from src.config import PostingTimesConfig, Settings

logger = logging.getLogger(__name__)


class PostingTimeAnalyzer:
    """Analyzes optimal posting times from historical data."""

    def __init__(self, settings: Settings) -> None:
        """Initialize posting time analyzer.

        Args:
            settings: Application settings containing posting times config.
        """
        self.settings = settings
        self.config: PostingTimesConfig = settings.posting_times

    def analyze_optimal_times(
        self, historical_data: List[Dict[str, Any]]
    ) -> Dict[str, List[Tuple[int, float]]]:
        """Analyze optimal posting times by day of week.

        Args:
            historical_data: List of post data dictionaries with timestamps
                and engagement metrics.

        Returns:
            Dictionary mapping day names to list of (hour, score) tuples
            sorted by score descending.
        """
        if not historical_data:
            logger.warning("No historical data provided for time analysis")
            return {}

        day_hour_engagement = defaultdict(lambda: defaultdict(list))
        cutoff_date = datetime.now() - timedelta(
            days=self.config.analysis_period_days
        )

        for post in historical_data:
            post_date = self._parse_date(post.get("timestamp"))
            if not post_date or post_date < cutoff_date:
                continue

            day_name = post_date.strftime("%A").lower()
            hour = post_date.hour

            engagement_score = self._calculate_post_engagement(post)
            day_hour_engagement[day_name][hour].append(engagement_score)

        optimal_times = {}

        for day_name, hour_data in day_hour_engagement.items():
            hour_scores = []
            for hour, scores in hour_data.items():
                if len(scores) >= self.config.min_posts_per_slot:
                    avg_score = sum(scores) / len(scores)
                    hour_scores.append((hour, avg_score))

            hour_scores.sort(key=lambda x: x[1], reverse=True)
            optimal_times[day_name] = hour_scores[:5]

        logger.info(
            f"Analyzed posting times for {len(historical_data)} posts"
        )

        return optimal_times

    def get_optimal_hours_for_day(
        self, optimal_times: Dict[str, List[Tuple[int, float]]], day: str
    ) -> List[int]:
        """Get optimal hours for a specific day.

        Args:
            optimal_times: Results from analyze_optimal_times.
            day: Day name (e.g., 'monday', 'tuesday').

        Returns:
            List of optimal hours for the day.
        """
        day_lower = day.lower()
        if day_lower not in optimal_times:
            return []

        return [hour for hour, _ in optimal_times[day_lower]]

    def get_best_time_slots(
        self, optimal_times: Dict[str, List[Tuple[int, float]]]
    ) -> Dict[str, List[int]]:
        """Get best time slots across all days.

        Args:
            optimal_times: Results from analyze_optimal_times.

        Returns:
            Dictionary mapping day names to list of optimal hours.
        """
        return {
            day: [hour for hour, _ in times]
            for day, times in optimal_times.items()
        }

    def _calculate_post_engagement(self, post: Dict[str, Any]) -> float:
        """Calculate engagement score for a single post.

        Args:
            post: Post data dictionary.

        Returns:
            Engagement score.
        """
        likes = post.get("likes", 0)
        comments = post.get("comments", 0)
        shares = post.get("shares", 0)
        clicks = post.get("clicks", 0)

        return (likes * 1.0) + (comments * 2.0) + (shares * 3.0) + (
            clicks * 1.5
        )

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
