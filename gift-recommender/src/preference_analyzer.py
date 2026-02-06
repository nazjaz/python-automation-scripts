"""Analyzes recipient preferences for gift recommendations."""

import logging
from typing import Dict, List, Optional

from src.database import DatabaseManager, Preference

logger = logging.getLogger(__name__)


class PreferenceAnalyzer:
    """Analyzes recipient preferences to inform gift recommendations."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initialize preference analyzer.

        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager

    def get_preference_scores(
        self, recipient_id: int
    ) -> Dict[str, float]:
        """Calculate preference scores by category.

        Args:
            recipient_id: Recipient ID.

        Returns:
            Dictionary mapping category names to preference scores (0.0 to 1.0).
        """
        preferences = self.db_manager.get_preferences(recipient_id)

        if not preferences:
            logger.debug(
                f"No preferences found for recipient {recipient_id}",
                extra={"recipient_id": recipient_id},
            )
            return {}

        category_scores = {}
        total_priority = 0.0

        for pref in preferences:
            priority = float(pref.priority or 1)
            total_priority += priority

            if pref.category not in category_scores:
                category_scores[pref.category] = 0.0

            category_scores[pref.category] += priority

        if total_priority > 0:
            for category in category_scores:
                category_scores[category] = category_scores[category] / total_priority

        logger.debug(
            f"Calculated preference scores for recipient {recipient_id}",
            extra={
                "recipient_id": recipient_id,
                "categories": list(category_scores.keys()),
            },
        )

        return category_scores

    def get_top_categories(
        self, recipient_id: int, limit: int = 5
    ) -> List[str]:
        """Get top preferred categories for recipient.

        Args:
            recipient_id: Recipient ID.
            limit: Number of top categories to return.

        Returns:
            List of category names ordered by preference score.
        """
        scores = self.get_preference_scores(recipient_id)

        sorted_categories = sorted(
            scores.items(), key=lambda x: x[1], reverse=True
        )

        top_categories = [cat for cat, _ in sorted_categories[:limit]]

        logger.debug(
            f"Top categories for recipient {recipient_id}",
            extra={
                "recipient_id": recipient_id,
                "top_categories": top_categories,
            },
        )

        return top_categories

    def matches_preference(
        self,
        recipient_id: int,
        category: str,
        min_score: float = 0.1,
    ) -> bool:
        """Check if category matches recipient preferences.

        Args:
            recipient_id: Recipient ID.
            category: Category to check.
            min_score: Minimum preference score threshold.

        Returns:
            True if category matches preferences, False otherwise.
        """
        scores = self.get_preference_scores(recipient_id)
        score = scores.get(category, 0.0)

        return score >= min_score

    def get_interests(self, recipient_id: int) -> List[str]:
        """Get list of recipient interests.

        Args:
            recipient_id: Recipient ID.

        Returns:
            List of interest strings.
        """
        preferences = self.db_manager.get_preferences(recipient_id)
        interests = [
            pref.interest
            for pref in preferences
            if pref.interest
        ]

        return interests
