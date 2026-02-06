"""Handles special occasions for gift recommendations."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class OccasionHandler:
    """Handles special occasions and their impact on gift recommendations."""

    def __init__(self, config: Dict) -> None:
        """Initialize occasion handler.

        Args:
            config: Configuration dictionary with occasion settings.
        """
        self.config = config
        self.occasion_config = config.get("occasions", {})
        self.occasion_types = self.occasion_config.get("types", [])
        self.multipliers = self.occasion_config.get("occasion_multipliers", {})

    def get_occasion_multiplier(
        self, occasion: Optional[str]
    ) -> float:
        """Get score multiplier for occasion type.

        Args:
            occasion: Occasion type name.

        Returns:
            Multiplier value (default: 1.0).
        """
        if not occasion:
            return 1.0

        multiplier = self.multipliers.get(occasion.lower(), 1.0)

        logger.debug(
            f"Occasion multiplier for {occasion}",
            extra={"occasion": occasion, "multiplier": multiplier},
        )

        return multiplier

    def is_valid_occasion(self, occasion: str) -> bool:
        """Check if occasion type is valid.

        Args:
            occasion: Occasion type name.

        Returns:
            True if valid, False otherwise.
        """
        return occasion.lower() in [o.lower() for o in self.occasion_types]

    def get_occasion_suggestions(
        self, date: Optional[datetime] = None
    ) -> List[str]:
        """Get suggested occasions based on date.

        Args:
            date: Optional date to check. Defaults to today.

        Returns:
            List of suggested occasion types.
        """
        if date is None:
            date = datetime.now()

        suggestions = []

        month = date.month
        day = date.day

        if month == 12 and day >= 20:
            suggestions.append("holiday")

        if month == 2 and day == 14:
            suggestions.append("anniversary")

        if month == 5 and day == 14:
            suggestions.append("thank_you")

        logger.debug(
            f"Occasion suggestions for date",
            extra={"date": date.isoformat(), "suggestions": suggestions},
        )

        return suggestions

    def get_occasion_context(
        self, occasion: Optional[str]
    ) -> Dict[str, str]:
        """Get context information for occasion.

        Args:
            occasion: Occasion type name.

        Returns:
            Dictionary with occasion context information.
        """
        if not occasion:
            return {}

        context_map = {
            "birthday": {
                "message": "Perfect for celebrating another year",
                "priority": "high",
            },
            "anniversary": {
                "message": "Ideal for commemorating special moments",
                "priority": "high",
            },
            "wedding": {
                "message": "Thoughtful gift for the happy couple",
                "priority": "high",
            },
            "graduation": {
                "message": "Celebrate this achievement",
                "priority": "medium",
            },
            "holiday": {
                "message": "Seasonal gift for the holidays",
                "priority": "medium",
            },
            "thank_you": {
                "message": "Show your appreciation",
                "priority": "low",
            },
            "congratulations": {
                "message": "Celebrate their success",
                "priority": "medium",
            },
            "get_well": {
                "message": "Wishing them a speedy recovery",
                "priority": "medium",
            },
        }

        return context_map.get(occasion.lower(), {})
