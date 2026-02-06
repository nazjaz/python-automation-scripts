"""Analyze user engagement patterns."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class EngagementAnalyzer:
    """Analyze user engagement patterns."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize engagement analyzer.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def analyze_engagement(self, user_id: str, days: int = 30) -> Dict[str, any]:
        """Analyze user engagement patterns.

        Args:
            user_id: User identifier.
            days: Number of days to analyze.

        Returns:
            Dictionary with engagement analysis results.
        """
        user = self.db_manager.get_user(user_id)

        if not user:
            return {"error": "User not found"}

        history = self.db_manager.get_user_viewing_history(user.id)

        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_history = [h for h in history if h.viewed_at >= cutoff]

        if not recent_history:
            return {
                "user_id": user_id,
                "total_engagement": 0.0,
                "engagement_by_type": {},
            }

        engagement_by_type = {}
        total_engagement = 0.0

        for entry in recent_history:
            content_type = entry.content.content_type or "unknown"

            if content_type not in engagement_by_type:
                engagement_by_type[content_type] = {
                    "views": 0,
                    "total_watch_time": 0,
                    "total_rating": 0.0,
                    "rating_count": 0,
                    "total_completion": 0.0,
                    "completion_count": 0,
                }

            type_data = engagement_by_type[content_type]
            type_data["views"] += 1

            if entry.watch_duration_minutes:
                type_data["total_watch_time"] += entry.watch_duration_minutes
                total_engagement += entry.watch_duration_minutes * 0.1

            if entry.rating:
                type_data["total_rating"] += entry.rating
                type_data["rating_count"] += 1
                total_engagement += entry.rating * 0.2

            if entry.completion_percentage:
                type_data["total_completion"] += entry.completion_percentage
                type_data["completion_count"] += 1
                total_engagement += entry.completion_percentage * 0.1

        for content_type, data in engagement_by_type.items():
            if data["rating_count"] > 0:
                data["average_rating"] = data["total_rating"] / data["rating_count"]
            else:
                data["average_rating"] = 0.0

            if data["completion_count"] > 0:
                data["average_completion"] = (
                    data["total_completion"] / data["completion_count"]
                )
            else:
                data["average_completion"] = 0.0

        return {
            "user_id": user_id,
            "total_engagement": total_engagement,
            "engagement_by_type": engagement_by_type,
        }

    def calculate_engagement_score(
        self, user_id: str, content_type: str
    ) -> float:
        """Calculate engagement score for content type.

        Args:
            user_id: User identifier.
            content_type: Content type.

        Returns:
            Engagement score (0.0 to 1.0).
        """
        user = self.db_manager.get_user(user_id)

        if not user:
            return 0.0

        patterns = self.db_manager.get_user_engagement_patterns(
            user.id, content_type=content_type
        )

        if not patterns:
            return 0.5

        recent_patterns = [
            p
            for p in patterns
            if p.time_window_end >= datetime.utcnow() - timedelta(days=30)
        ]

        if not recent_patterns:
            return 0.5

        total_score = 0.0
        total_weight = 0.0

        for pattern in recent_patterns:
            if pattern.engagement_metric == "views":
                weight = 0.2
                score = min(pattern.metric_value / 100.0, 1.0)
            elif pattern.engagement_metric == "watch_time":
                weight = 0.3
                score = min(pattern.metric_value / 1000.0, 1.0)
            elif pattern.engagement_metric == "completion_rate":
                weight = 0.3
                score = pattern.metric_value / 100.0
            elif pattern.engagement_metric == "rating":
                weight = 0.2
                score = pattern.metric_value / 5.0
            else:
                weight = 0.1
                score = min(pattern.metric_value / 100.0, 1.0)

            total_score += score * weight
            total_weight += weight

        if total_weight > 0:
            normalized_score = total_score / total_weight
        else:
            normalized_score = 0.5

        return normalized_score

    def update_engagement_patterns(self, user_id: str) -> Dict[str, any]:
        """Update engagement patterns from viewing history.

        Args:
            user_id: User identifier.

        Returns:
            Dictionary with update results.
        """
        user = self.db_manager.get_user(user_id)

        if not user:
            return {"error": "User not found"}

        history = self.db_manager.get_user_viewing_history(user.id)

        if not history:
            return {"user_id": user_id, "patterns_updated": 0}

        cutoff = datetime.utcnow() - timedelta(days=30)
        recent_history = [h for h in history if h.viewed_at >= cutoff]

        content_type_counts = {}
        content_type_watch_time = {}
        content_type_ratings = []
        content_type_completions = []

        for entry in recent_history:
            content_type = entry.content.content_type or "unknown"

            if content_type not in content_type_counts:
                content_type_counts[content_type] = 0
                content_type_watch_time[content_type] = 0
                content_type_ratings.append([])
                content_type_completions.append([])

            content_type_counts[content_type] += 1

            if entry.watch_duration_minutes:
                content_type_watch_time[content_type] += entry.watch_duration_minutes

            if entry.rating:
                content_type_ratings[-1].append(entry.rating)

            if entry.completion_percentage:
                content_type_completions[-1].append(entry.completion_percentage)

        patterns_created = 0
        time_window_end = datetime.utcnow()
        time_window_start = cutoff

        for content_type, count in content_type_counts.items():
            self.db_manager.add_engagement_pattern(
                user.id,
                content_type,
                "views",
                float(count),
                time_window_start,
                time_window_end,
            )
            patterns_created += 1

            if content_type in content_type_watch_time:
                self.db_manager.add_engagement_pattern(
                    user.id,
                    content_type,
                    "watch_time",
                    float(content_type_watch_time[content_type]),
                    time_window_start,
                    time_window_end,
                )
                patterns_created += 1

        return {
            "user_id": user_id,
            "patterns_updated": patterns_created,
        }
