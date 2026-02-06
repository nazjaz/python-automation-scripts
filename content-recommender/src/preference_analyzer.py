"""Analyze user preferences."""

from typing import Dict, List, Optional

from src.database import DatabaseManager


class PreferenceAnalyzer:
    """Analyze user preferences."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize preference analyzer.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def analyze_preferences(self, user_id: str) -> Dict[str, any]:
        """Analyze user preferences.

        Args:
            user_id: User identifier.

        Returns:
            Dictionary with preference analysis results.
        """
        user = self.db_manager.get_user(user_id)

        if not user:
            return {"error": "User not found"}

        preferences = self.db_manager.get_user_preferences(user.id)

        preference_summary = {}
        for pref in preferences:
            if pref.preference_type not in preference_summary:
                preference_summary[pref.preference_type] = []

            preference_summary[pref.preference_type].append({
                "value": pref.preference_value,
                "weight": pref.weight,
            })

        total_weight = sum(p.weight for p in preferences)
        average_weight = total_weight / len(preferences) if preferences else 0.0

        return {
            "user_id": user_id,
            "total_preferences": len(preferences),
            "preference_types": list(preference_summary.keys()),
            "preference_summary": preference_summary,
            "average_weight": average_weight,
        }

    def extract_preferences_from_history(
        self, user_id: str, min_views: int = 2
    ) -> Dict[str, any]:
        """Extract preferences from viewing history.

        Args:
            user_id: User identifier.
            min_views: Minimum number of views to consider a preference.

        Returns:
            Dictionary with extracted preferences.
        """
        user = self.db_manager.get_user(user_id)

        if not user:
            return {"error": "User not found"}

        history = self.db_manager.get_user_viewing_history(user.id)

        category_counts = {}
        content_type_counts = {}
        tag_counts = {}

        for entry in history:
            content = entry.content

            if content.category:
                category_counts[content.category] = category_counts.get(content.category, 0) + 1

            if content.content_type:
                content_type_counts[content.content_type] = (
                    content_type_counts.get(content.content_type, 0) + 1
                )

            if content.tags:
                tags = [t.strip() for t in content.tags.split(",")]
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        extracted_preferences = []

        for category, count in category_counts.items():
            if count >= min_views:
                weight = min(count / 10.0, 2.0)
                self.db_manager.add_user_preference(
                    user.id, "category", category, weight=weight
                )
                extracted_preferences.append({
                    "type": "category",
                    "value": category,
                    "weight": weight,
                })

        for content_type, count in content_type_counts.items():
            if count >= min_views:
                weight = min(count / 10.0, 2.0)
                self.db_manager.add_user_preference(
                    user.id, "content_type", content_type, weight=weight
                )
                extracted_preferences.append({
                    "type": "content_type",
                    "value": content_type,
                    "weight": weight,
                })

        for tag, count in tag_counts.items():
            if count >= min_views:
                weight = min(count / 10.0, 1.5)
                self.db_manager.add_user_preference(
                    user.id, "tag", tag, weight=weight
                )
                extracted_preferences.append({
                    "type": "tag",
                    "value": tag,
                    "weight": weight,
                })

        return {
            "user_id": user_id,
            "extracted_preferences": len(extracted_preferences),
            "preferences": extracted_preferences,
        }

    def get_preference_score(
        self, user_id: str, content_category: Optional[str], content_type: Optional[str], content_tags: Optional[str]
    ) -> float:
        """Calculate preference score for content.

        Args:
            user_id: User identifier.
            content_category: Content category.
            content_type: Content type.
            content_tags: Content tags as comma-separated string.

        Returns:
            Preference score (0.0 to 1.0).
        """
        user = self.db_manager.get_user(user_id)

        if not user:
            return 0.0

        preferences = self.db_manager.get_user_preferences(user.id)

        if not preferences:
            return 0.5

        score = 0.0
        total_weight = 0.0

        for pref in preferences:
            weight = pref.weight

            if pref.preference_type == "category" and content_category:
                if pref.preference_value.lower() == content_category.lower():
                    score += weight * 0.4
                    total_weight += weight * 0.4

            if pref.preference_type == "content_type" and content_type:
                if pref.preference_value.lower() == content_type.lower():
                    score += weight * 0.3
                    total_weight += weight * 0.3

            if pref.preference_type == "tag" and content_tags:
                tags = [t.strip().lower() for t in content_tags.split(",")]
                if pref.preference_value.lower() in tags:
                    score += weight * 0.3
                    total_weight += weight * 0.3

        if total_weight > 0:
            normalized_score = min(score / total_weight, 1.0)
        else:
            normalized_score = 0.0

        return normalized_score
