"""Analyze user behavior patterns."""

from collections import Counter
from typing import Dict, List, Optional

from src.database import DatabaseManager


class BehaviorAnalyzer:
    """Analyze user behavior patterns."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize behavior analyzer.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def analyze_user_behavior(self, user_id: int) -> Dict[str, any]:
        """Analyze user behavior patterns.

        Args:
            user_id: User ID.

        Returns:
            Dictionary with behavior analysis results.
        """
        behaviors = self.db_manager.get_user_behaviors(user_id)

        if not behaviors:
            return {
                "user_id": user_id,
                "total_behaviors": 0,
                "behavior_types": {},
                "most_active_time": None,
            }

        behavior_types = Counter(b.behavior_type for b in behaviors)
        time_patterns = self._analyze_time_patterns(behaviors)
        category_preferences = self._analyze_category_preferences(user_id)

        return {
            "user_id": user_id,
            "total_behaviors": len(behaviors),
            "behavior_types": dict(behavior_types),
            "most_common_behavior": behavior_types.most_common(1)[0][0] if behavior_types else None,
            "most_active_time": time_patterns.get("most_active_hour"),
            "average_sessions_per_day": time_patterns.get("average_sessions_per_day", 0.0),
            "category_preferences": category_preferences,
        }

    def _analyze_time_patterns(self, behaviors: List) -> Dict[str, any]:
        """Analyze time patterns in behaviors.

        Args:
            behaviors: List of behavior objects.

        Returns:
            Dictionary with time pattern analysis.
        """
        hours = [b.timestamp.hour for b in behaviors if b.timestamp]
        hour_counts = Counter(hours)

        if not hour_counts:
            return {}

        most_active_hour = hour_counts.most_common(1)[0][0]

        unique_days = len(set(b.timestamp.date() for b in behaviors if b.timestamp))
        average_sessions_per_day = len(behaviors) / unique_days if unique_days > 0 else 0.0

        return {
            "most_active_hour": most_active_hour,
            "average_sessions_per_day": average_sessions_per_day,
            "hour_distribution": dict(hour_counts),
        }

    def _analyze_category_preferences(self, user_id: int) -> Dict[str, float]:
        """Analyze user category preferences.

        Args:
            user_id: User ID.

        Returns:
            Dictionary with category preferences.
        """
        enrollments = self.db_manager.get_user_enrollments(user_id)

        category_counts = Counter()
        for enrollment in enrollments:
            if enrollment.course and enrollment.course.category:
                category_counts[enrollment.course.category] += 1

        total = sum(category_counts.values())
        if total == 0:
            return {}

        preferences = {
            category: count / total
            for category, count in category_counts.items()
        }

        return preferences

    def get_learning_style(self, user_id: int) -> Dict[str, any]:
        """Determine user learning style.

        Args:
            user_id: User ID.

        Returns:
            Dictionary with learning style information.
        """
        behaviors = self.db_manager.get_user_behaviors(user_id)
        enrollments = self.db_manager.get_user_enrollments(user_id)

        view_count = len([b for b in behaviors if b.behavior_type == "view"])
        click_count = len([b for b in behaviors if b.behavior_type == "click"])
        search_count = len([b for b in behaviors if b.behavior_type == "search"])

        total_behaviors = len(behaviors)
        if total_behaviors == 0:
            return {
                "learning_style": "unknown",
                "confidence": 0.0,
            }

        view_ratio = view_count / total_behaviors
        click_ratio = click_count / total_behaviors
        search_ratio = search_count / total_behaviors

        avg_completion_rate = (
            sum(e.completion_rate for e in enrollments) / len(enrollments)
            if enrollments
            else 0.0
        )

        if search_ratio > 0.3:
            style = "exploratory"
        elif click_ratio > 0.4:
            style = "interactive"
        elif view_ratio > 0.6:
            style = "visual"
        elif avg_completion_rate > 0.8:
            style = "structured"
        else:
            style = "balanced"

        confidence = min(total_behaviors / 50.0, 1.0)

        return {
            "learning_style": style,
            "confidence": confidence,
            "view_ratio": view_ratio,
            "click_ratio": click_ratio,
            "search_ratio": search_ratio,
        }
