"""Analyze user viewing history."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class HistoryAnalyzer:
    """Analyze user viewing history."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize history analyzer.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def analyze_history(self, user_id: str, days: int = 30) -> Dict[str, any]:
        """Analyze user viewing history.

        Args:
            user_id: User identifier.
            days: Number of days to analyze.

        Returns:
            Dictionary with history analysis results.
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
                "total_views": 0,
                "recent_views": 0,
                "average_rating": 0.0,
                "average_completion": 0.0,
            }

        total_watch_time = sum(
            h.watch_duration_minutes or 0 for h in recent_history
        )
        ratings = [h.rating for h in recent_history if h.rating]
        completions = [
            h.completion_percentage for h in recent_history if h.completion_percentage
        ]

        category_counts = {}
        content_type_counts = {}

        for entry in recent_history:
            content = entry.content

            if content.category:
                category_counts[content.category] = (
                    category_counts.get(content.category, 0) + 1
                )

            if content.content_type:
                content_type_counts[content.content_type] = (
                    content_type_counts.get(content.content_type, 0) + 1
                )

        return {
            "user_id": user_id,
            "total_views": len(history),
            "recent_views": len(recent_history),
            "total_watch_time_minutes": total_watch_time,
            "average_rating": sum(ratings) / len(ratings) if ratings else 0.0,
            "average_completion": (
                sum(completions) / len(completions) if completions else 0.0
            ),
            "top_categories": dict(
                sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ),
            "top_content_types": dict(
                sorted(
                    content_type_counts.items(), key=lambda x: x[1], reverse=True
                )[:5]
            ),
        }

    def get_similar_content_score(
        self, user_id: str, content_id: str
    ) -> float:
        """Calculate similarity score based on viewing history.

        Args:
            user_id: User identifier.
            content_id: Content identifier.

        Returns:
            Similarity score (0.0 to 1.0).
        """
        user = self.db_manager.get_user(user_id)
        content = self.db_manager.get_content(content_id)

        if not user or not content:
            return 0.0

        history = self.db_manager.get_user_viewing_history(user.id, limit=50)

        if not history:
            return 0.0

        score = 0.0
        matches = 0

        for entry in history:
            hist_content = entry.content

            if hist_content.category and content.category:
                if hist_content.category.lower() == content.category.lower():
                    score += 0.3
                    matches += 1

            if hist_content.content_type and content.content_type:
                if hist_content.content_type.lower() == content.content_type.lower():
                    score += 0.4
                    matches += 1

            if hist_content.tags and content.tags:
                hist_tags = [t.strip().lower() for t in hist_content.tags.split(",")]
                content_tags = [t.strip().lower() for t in content.tags.split(",")]
                common_tags = set(hist_tags) & set(content_tags)
                if common_tags:
                    score += 0.3 * (len(common_tags) / max(len(hist_tags), len(content_tags)))
                    matches += 1

            if entry.rating and entry.rating >= 4.0:
                score += 0.1

        if matches > 0:
            normalized_score = min(score / matches, 1.0)
        else:
            normalized_score = 0.0

        return normalized_score

    def get_recently_viewed_content(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, any]]:
        """Get recently viewed content.

        Args:
            user_id: User identifier.
            limit: Maximum number of items to return.

        Returns:
            List of recently viewed content dictionaries.
        """
        user = self.db_manager.get_user(user_id)

        if not user:
            return []

        history = self.db_manager.get_user_viewing_history(user.id, limit=limit)

        return [
            {
                "content_id": entry.content.content_id,
                "title": entry.content.title,
                "content_type": entry.content.content_type,
                "category": entry.content.category,
                "viewed_at": entry.viewed_at,
                "rating": entry.rating,
                "completion_percentage": entry.completion_percentage,
            }
            for entry in history
        ]
