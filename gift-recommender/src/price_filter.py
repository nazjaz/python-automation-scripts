"""Price range filtering for gift recommendations."""

import logging
from typing import Dict, List, Optional, Tuple

from src.database import GiftItem

logger = logging.getLogger(__name__)


class PriceFilter:
    """Filters and categorizes gift items by price range."""

    def __init__(self, config: Dict) -> None:
        """Initialize price filter.

        Args:
            config: Configuration dictionary with price range settings.
        """
        self.config = config
        self.price_ranges = config.get("price_ranges", {})
        self.budget = self.price_ranges.get("budget", 0.0)
        self.low = self.price_ranges.get("low", 25.0)
        self.medium = self.price_ranges.get("medium", 100.0)
        self.high = self.price_ranges.get("high", 500.0)
        self.premium = self.price_ranges.get("premium", 1000.0)

    def get_price_range_category(
        self, price: float
    ) -> str:
        """Get price range category for price.

        Args:
            price: Item price.

        Returns:
            Price range category name.
        """
        if price <= self.budget:
            return "budget"
        elif price <= self.low:
            return "low"
        elif price <= self.medium:
            return "medium"
        elif price <= self.high:
            return "high"
        elif price <= self.premium:
            return "premium"
        else:
            return "luxury"

    def filter_by_price_range(
        self,
        items: List[GiftItem],
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> List[GiftItem]:
        """Filter items by price range.

        Args:
            items: List of gift items.
            min_price: Optional minimum price.
            max_price: Optional maximum price.

        Returns:
            Filtered list of gift items.
        """
        filtered = []

        for item in items:
            if min_price is not None and item.price < min_price:
                continue
            if max_price is not None and item.price > max_price:
                continue
            filtered.append(item)

        logger.debug(
            f"Filtered items by price range",
            extra={
                "original_count": len(items),
                "filtered_count": len(filtered),
                "min_price": min_price,
                "max_price": max_price,
            },
        )

        return filtered

    def get_price_range_bounds(
        self, range_name: str
    ) -> Optional[Tuple[float, float]]:
        """Get price bounds for range category.

        Args:
            range_name: Price range category name.

        Returns:
            Tuple of (min_price, max_price) or None if invalid.
        """
        range_name_lower = range_name.lower()

        if range_name_lower == "budget":
            return (0.0, self.budget)
        elif range_name_lower == "low":
            return (self.budget, self.low)
        elif range_name_lower == "medium":
            return (self.low, self.medium)
        elif range_name_lower == "high":
            return (self.medium, self.high)
        elif range_name_lower == "premium":
            return (self.high, self.premium)
        elif range_name_lower == "luxury":
            return (self.premium, float("inf"))
        else:
            return None

    def calculate_price_score(
        self,
        item_price: float,
        target_price: Optional[float] = None,
        target_range: Optional[str] = None,
    ) -> float:
        """Calculate price match score.

        Args:
            item_price: Item price.
            target_price: Optional target price.
            target_range: Optional target price range category.

        Returns:
            Price score (0.0 to 1.0).
        """
        if target_price is not None:
            price_diff = abs(item_price - target_price)
            max_diff = max(item_price, target_price)
            if max_diff == 0:
                return 1.0
            score = 1.0 - (price_diff / max_diff)
            return max(0.0, min(1.0, score))

        if target_range:
            bounds = self.get_price_range_bounds(target_range)
            if bounds:
                min_price, max_price = bounds
                if min_price <= item_price <= max_price:
                    return 1.0
                elif item_price < min_price:
                    distance = min_price - item_price
                    return max(0.0, 1.0 - (distance / min_price))
                else:
                    distance = item_price - max_price
                    return max(0.0, 1.0 - (distance / max_price))

        return 0.5
