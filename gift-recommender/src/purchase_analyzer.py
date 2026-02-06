"""Analyzes purchase history for gift recommendations."""

import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, PurchaseHistory

logger = logging.getLogger(__name__)


class PurchaseAnalyzer:
    """Analyzes purchase history to inform gift recommendations."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        lookback_days: int = 365,
    ) -> None:
        """Initialize purchase analyzer.

        Args:
            db_manager: Database manager instance.
            lookback_days: Number of days to look back in purchase history.
        """
        self.db_manager = db_manager
        self.lookback_days = lookback_days

    def get_category_frequency(
        self, recipient_id: int
    ) -> Dict[str, int]:
        """Calculate frequency of purchases by category.

        Args:
            recipient_id: Recipient ID.

        Returns:
            Dictionary mapping category names to purchase counts.
        """
        purchases = self.db_manager.get_purchase_history(
            recipient_id, days=self.lookback_days
        )

        category_counts = Counter()
        for purchase in purchases:
            if purchase.category:
                category_counts[purchase.category] += 1

        logger.debug(
            f"Category frequency for recipient {recipient_id}",
            extra={
                "recipient_id": recipient_id,
                "categories": dict(category_counts),
            },
        )

        return dict(category_counts)

    def get_category_scores(
        self, recipient_id: int
    ) -> Dict[str, float]:
        """Calculate preference scores based on purchase history.

        Args:
            recipient_id: Recipient ID.

        Returns:
            Dictionary mapping category names to scores (0.0 to 1.0).
        """
        frequency = self.get_category_frequency(recipient_id)

        if not frequency:
            return {}

        total_purchases = sum(frequency.values())
        if total_purchases == 0:
            return {}

        scores = {
            category: count / float(total_purchases)
            for category, count in frequency.items()
        }

        logger.debug(
            f"Purchase-based scores for recipient {recipient_id}",
            extra={"recipient_id": recipient_id, "scores": scores},
        )

        return scores

    def get_average_price(
        self, recipient_id: int, category: Optional[str] = None
    ) -> Optional[float]:
        """Calculate average purchase price.

        Args:
            recipient_id: Recipient ID.
            category: Optional category filter.

        Returns:
            Average price or None if no purchases found.
        """
        purchases = self.db_manager.get_purchase_history(
            recipient_id, days=self.lookback_days
        )

        if category:
            purchases = [p for p in purchases if p.category == category]

        prices = [p.price for p in purchases if p.price is not None]

        if not prices:
            return None

        avg_price = sum(prices) / len(prices)

        logger.debug(
            f"Average price for recipient {recipient_id}",
            extra={
                "recipient_id": recipient_id,
                "category": category,
                "average_price": avg_price,
            },
        )

        return avg_price

    def get_price_range(
        self, recipient_id: int, category: Optional[str] = None
    ) -> Optional[Dict[str, float]]:
        """Get price range from purchase history.

        Args:
            recipient_id: Recipient ID.
            category: Optional category filter.

        Returns:
            Dictionary with 'min' and 'max' keys, or None if no purchases.
        """
        purchases = self.db_manager.get_purchase_history(
            recipient_id, days=self.lookback_days
        )

        if category:
            purchases = [p for p in purchases if p.category == category]

        prices = [p.price for p in purchases if p.price is not None]

        if not prices:
            return None

        return {
            "min": min(prices),
            "max": max(prices),
            "avg": sum(prices) / len(prices),
        }

    def get_highly_rated_categories(
        self, recipient_id: int, min_rating: int = 4
    ) -> List[str]:
        """Get categories with highly rated purchases.

        Args:
            recipient_id: Recipient ID.
            min_rating: Minimum rating threshold.

        Returns:
            List of category names with high ratings.
        """
        purchases = self.db_manager.get_purchase_history(
            recipient_id, days=self.lookback_days
        )

        rated_purchases = [
            p for p in purchases
            if p.rating is not None and p.rating >= min_rating and p.category
        ]

        categories = [p.category for p in rated_purchases]
        category_counts = Counter(categories)

        top_categories = [
            cat for cat, _ in category_counts.most_common(5)
        ]

        logger.debug(
            f"Highly rated categories for recipient {recipient_id}",
            extra={
                "recipient_id": recipient_id,
                "categories": top_categories,
            },
        )

        return top_categories

    def get_recent_purchases(
        self, recipient_id: int, limit: int = 10
    ) -> List[PurchaseHistory]:
        """Get recent purchases for recipient.

        Args:
            recipient_id: Recipient ID.
            limit: Maximum number of purchases to return.

        Returns:
            List of PurchaseHistory objects.
        """
        purchases = self.db_manager.get_purchase_history(
            recipient_id, limit=limit, days=self.lookback_days
        )

        return purchases
