"""Generate personalized content recommendations."""

from typing import Dict, List, Optional

from src.database import DatabaseManager
from src.preference_analyzer import PreferenceAnalyzer
from src.history_analyzer import HistoryAnalyzer
from src.engagement_analyzer import EngagementAnalyzer


class RecommendationGenerator:
    """Generate personalized content recommendations."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize recommendation generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.preference_analyzer = PreferenceAnalyzer(
            db_manager, config.get("preference_analysis", {})
        )
        self.history_analyzer = HistoryAnalyzer(
            db_manager, config.get("history_analysis", {})
        )
        self.engagement_analyzer = EngagementAnalyzer(
            db_manager, config.get("engagement_analysis", {})
        )

        self.preference_weight = config.get("recommendation_weights", {}).get(
            "preference", 0.3
        )
        self.history_weight = config.get("recommendation_weights", {}).get(
            "history", 0.4
        )
        self.engagement_weight = config.get("recommendation_weights", {}).get(
            "engagement", 0.3
        )

    def generate_recommendations(
        self, user_id: str, limit: int = 10, content_type: Optional[str] = None
    ) -> Dict[str, any]:
        """Generate personalized recommendations for user.

        Args:
            user_id: User identifier.
            limit: Maximum number of recommendations to generate.
            content_type: Optional content type to filter by.

        Returns:
            Dictionary with recommendation results.
        """
        user = self.db_manager.get_user(user_id)

        if not user:
            return {"error": "User not found"}

        session = self.db_manager.get_session()
        try:
            from src.database import Content

            query = session.query(Content)

            if content_type:
                query = query.filter(Content.content_type == content_type)

            all_content = query.all()

            if not all_content:
                return {"error": "No content available"}

            scored_content = []

            for content in all_content:
                preference_score = self.preference_analyzer.get_preference_score(
                    user_id,
                    content.category,
                    content.content_type,
                    content.tags,
                )

                history_score = self.history_analyzer.get_similar_content_score(
                    user_id, content.content_id
                )

                engagement_score = self.engagement_analyzer.calculate_engagement_score(
                    user_id, content.content_type or "unknown"
                )

                total_score = (
                    preference_score * self.preference_weight
                    + history_score * self.history_weight
                    + engagement_score * self.engagement_weight
                )

                scored_content.append({
                    "content": content,
                    "score": total_score,
                    "preference_score": preference_score,
                    "history_score": history_score,
                    "engagement_score": engagement_score,
                })

            scored_content.sort(key=lambda x: x["score"], reverse=True)

            recommendations_created = []

            for item in scored_content[:limit]:
                content = item["content"]
                score = item["score"]

                reason_parts = []
                if item["preference_score"] > 0.5:
                    reason_parts.append("matches your preferences")
                if item["history_score"] > 0.5:
                    reason_parts.append("similar to content you've viewed")
                if item["engagement_score"] > 0.5:
                    reason_parts.append("high engagement with this type")

                reason = ", ".join(reason_parts) if reason_parts else "recommended for you"

                recommendation = self.db_manager.add_recommendation(
                    user_id=user.id,
                    content_id=content.id,
                    recommendation_score=score,
                    recommendation_reason=reason,
                    recommendation_type="hybrid",
                )

                recommendations_created.append({
                    "recommendation_id": recommendation.id,
                    "content_id": content.content_id,
                    "title": content.title,
                    "score": score,
                    "reason": reason,
                })

            return {
                "success": True,
                "user_id": user_id,
                "recommendations_created": len(recommendations_created),
                "recommendations": recommendations_created,
            }
        finally:
            session.close()

    def get_recommendations(
        self, user_id: str, limit: int = 10, shown_only: bool = False
    ) -> List[Dict[str, any]]:
        """Get recommendations for user.

        Args:
            user_id: User identifier.
            limit: Maximum number of recommendations to return.
            shown_only: Only return shown recommendations.

        Returns:
            List of recommendation dictionaries.
        """
        user = self.db_manager.get_user(user_id)

        if not user:
            return []

        recommendations = self.db_manager.get_user_recommendations(
            user.id, limit=limit, shown_only=shown_only
        )

        return [
            {
                "recommendation_id": r.id,
                "content_id": r.content.content_id,
                "title": r.content.title,
                "content_type": r.content.content_type,
                "category": r.content.category,
                "score": r.recommendation_score,
                "reason": r.recommendation_reason,
                "generated_at": r.generated_at,
                "shown_at": r.shown_at,
                "clicked_at": r.clicked_at,
            }
            for r in recommendations
        ]

    def get_recommendation_statistics(
        self, user_id: str
    ) -> Dict[str, any]:
        """Get recommendation statistics for user.

        Args:
            user_id: User identifier.

        Returns:
            Dictionary with recommendation statistics.
        """
        user = self.db_manager.get_user(user_id)

        if not user:
            return {"error": "User not found"}

        recommendations = self.db_manager.get_user_recommendations(user.id)

        total = len(recommendations)
        shown = len([r for r in recommendations if r.shown_at])
        clicked = len([r for r in recommendations if r.clicked_at])
        converted = len([r for r in recommendations if r.converted_at])

        click_through_rate = (clicked / shown * 100) if shown > 0 else 0.0
        conversion_rate = (converted / clicked * 100) if clicked > 0 else 0.0

        average_score = (
            sum(r.recommendation_score for r in recommendations) / total
            if total > 0
            else 0.0
        )

        return {
            "user_id": user_id,
            "total_recommendations": total,
            "shown_recommendations": shown,
            "clicked_recommendations": clicked,
            "converted_recommendations": converted,
            "click_through_rate": click_through_rate,
            "conversion_rate": conversion_rate,
            "average_score": average_score,
        }
