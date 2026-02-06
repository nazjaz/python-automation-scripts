"""Gift recommendation engine."""

import logging
from typing import Dict, List, Optional

from src.database import DatabaseManager, GiftItem, Recipient
from src.occasion_handler import OccasionHandler
from src.preference_analyzer import PreferenceAnalyzer
from src.price_filter import PriceFilter
from src.purchase_analyzer import PurchaseAnalyzer

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates personalized gift recommendations."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize recommendation engine.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.recommendation_config = config.get("recommendations", {})

        self.preference_analyzer = PreferenceAnalyzer(db_manager)
        self.purchase_analyzer = PurchaseAnalyzer(db_manager)
        self.occasion_handler = OccasionHandler(config)
        self.price_filter = PriceFilter(config)

        self.preference_weight = self.recommendation_config.get(
            "preference_weight", 0.4
        )
        self.purchase_weight = self.recommendation_config.get(
            "purchase_history_weight", 0.3
        )
        self.occasion_weight = self.recommendation_config.get(
            "occasion_weight", 0.2
        )
        self.price_weight = self.recommendation_config.get(
            "price_weight", 0.1
        )

    def calculate_item_score(
        self,
        item: GiftItem,
        recipient_id: int,
        occasion: Optional[str] = None,
        target_price: Optional[float] = None,
        target_price_range: Optional[str] = None,
    ) -> float:
        """Calculate recommendation score for gift item.

        Args:
            item: Gift item to score.
            recipient_id: Recipient ID.
            occasion: Optional occasion type.
            target_price: Optional target price.
            target_price_range: Optional target price range category.

        Returns:
            Recommendation score (0.0 to 1.0).
        """
        preference_scores = self.preference_analyzer.get_preference_scores(
            recipient_id
        )
        preference_score = preference_scores.get(item.category, 0.0)

        purchase_scores = self.purchase_analyzer.get_category_scores(
            recipient_id
        )
        purchase_score = purchase_scores.get(item.category, 0.0)

        occasion_multiplier = self.occasion_handler.get_occasion_multiplier(
            occasion
        )

        price_score = self.price_filter.calculate_price_score(
            item.price, target_price, target_price_range
        )

        base_score = (
            preference_score * self.preference_weight
            + purchase_score * self.purchase_weight
            + price_score * self.price_weight
        )

        final_score = base_score * occasion_multiplier

        logger.debug(
            f"Calculated score for item {item.id}",
            extra={
                "item_id": item.id,
                "recipient_id": recipient_id,
                "final_score": final_score,
                "preference_score": preference_score,
                "purchase_score": purchase_score,
                "price_score": price_score,
            },
        )

        return min(1.0, final_score)

    def generate_recommendations(
        self,
        recipient_id: int,
        occasion: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        price_range: Optional[str] = None,
        categories: Optional[List[str]] = None,
        max_recommendations: Optional[int] = None,
    ) -> List[Dict]:
        """Generate gift recommendations for recipient.

        Args:
            recipient_id: Recipient ID.
            occasion: Optional occasion type.
            min_price: Optional minimum price filter.
            max_price: Optional maximum price filter.
            price_range: Optional price range category filter.
            categories: Optional list of category filters.
            max_recommendations: Optional maximum number of recommendations.

        Returns:
            List of recommendation dictionaries with item and score.
        """
        recipient = self.db_manager.get_recipient(recipient_id)
        if not recipient:
            logger.error(
                f"Recipient {recipient_id} not found",
                extra={"recipient_id": recipient_id},
            )
            return []

        if max_recommendations is None:
            max_recommendations = self.recommendation_config.get(
                "max_recommendations", 10
            )

        if price_range:
            bounds = self.price_filter.get_price_range_bounds(price_range)
            if bounds:
                range_min, range_max = bounds
                if min_price is None:
                    min_price = range_min
                if max_price is None:
                    max_price = range_max

        all_items = self.db_manager.get_gift_items(
            category=None, min_price=min_price, max_price=max_price
        )

        if categories:
            all_items = [item for item in all_items if item.category in categories]

        scored_items = []

        for item in all_items:
            score = self.calculate_item_score(
                item,
                recipient_id,
                occasion=occasion,
                target_price_range=price_range,
            )

            min_threshold = self.recommendation_config.get(
                "min_score_threshold", 0.3
            )

            if score >= min_threshold:
                price_category = self.price_filter.get_price_range_category(
                    item.price
                )

                reasoning = self._generate_reasoning(
                    item, recipient, score, occasion
                )

                scored_items.append(
                    {
                        "item": item,
                        "score": score,
                        "price_category": price_category,
                        "reasoning": reasoning,
                    }
                )

        scored_items.sort(key=lambda x: x["score"], reverse=True)

        recommendations = scored_items[:max_recommendations]

        diversity_factor = self.recommendation_config.get("diversity_factor", 0.3)
        if diversity_factor > 0:
            recommendations = self._apply_diversity(
                recommendations, diversity_factor
            )

        logger.info(
            f"Generated {len(recommendations)} recommendations for recipient {recipient_id}",
            extra={
                "recipient_id": recipient_id,
                "recommendation_count": len(recommendations),
                "occasion": occasion,
            },
        )

        return recommendations

    def _generate_reasoning(
        self,
        item: GiftItem,
        recipient: Recipient,
        score: float,
        occasion: Optional[str],
    ) -> str:
        """Generate reasoning text for recommendation.

        Args:
            item: Gift item.
            recipient: Recipient object.
            score: Recommendation score.
            occasion: Optional occasion type.

        Returns:
            Reasoning text.
        """
        reasons = []

        preference_scores = self.preference_analyzer.get_preference_scores(
            recipient.id
        )
        if preference_scores.get(item.category, 0) > 0.2:
            reasons.append(f"Matches {recipient.name}'s interest in {item.category}")

        purchase_scores = self.purchase_analyzer.get_category_scores(
            recipient.id
        )
        if purchase_scores.get(item.category, 0) > 0.2:
            reasons.append(
                f"Based on past purchases in {item.category} category"
            )

        if occasion:
            context = self.occasion_handler.get_occasion_context(occasion)
            if context:
                reasons.append(context.get("message", ""))

        if item.brand:
            reasons.append(f"From {item.brand}")

        if not reasons:
            reasons.append("A thoughtful gift choice")

        return ". ".join(reasons) + "."

    def _apply_diversity(
        self, recommendations: List[Dict], diversity_factor: float
    ) -> List[Dict]:
        """Apply diversity to recommendations to avoid too many similar items.

        Args:
            recommendations: List of recommendation dictionaries.
            diversity_factor: Diversity factor (0.0 to 1.0).

        Returns:
            Diversified list of recommendations.
        """
        if len(recommendations) <= 1:
            return recommendations

        diversified = [recommendations[0]]
        used_categories = {recommendations[0]["item"].category}

        for rec in recommendations[1:]:
            category = rec["item"].category

            if category not in used_categories:
                diversified.append(rec)
                used_categories.add(category)
            elif len(diversified) < len(recommendations) * (1 - diversity_factor):
                diversified.append(rec)

            if len(diversified) >= len(recommendations):
                break

        return diversified
