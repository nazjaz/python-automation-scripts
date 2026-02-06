"""Categorize errors by type and characteristics."""

import re
from typing import Dict, List, Optional


class ErrorCategorizer:
    """Categorize errors into predefined categories."""

    def __init__(self, config: Dict):
        """Initialize error categorizer.

        Args:
            config: Configuration dictionary with categorization settings.
        """
        self.config = config
        self.categories = config.get("categories", {})
        self.severity_rules = config.get("severity_rules", {})

    def categorize_error(
        self, error_message: str, error_type: Optional[str] = None, stack_trace: Optional[str] = None
    ) -> Dict[str, any]:
        """Categorize an error.

        Args:
            error_message: Error message text.
            error_type: Error type or exception class.
            stack_trace: Stack trace text.

        Returns:
            Dictionary with category name, description, and severity.
        """
        error_text = f"{error_message} {error_type or ''} {stack_trace or ''}".lower()

        best_match = None
        best_score = 0

        for category_name, category_config in self.categories.items():
            keywords = category_config.get("keywords", [])
            patterns = category_config.get("patterns", [])

            score = 0

            for keyword in keywords:
                if keyword.lower() in error_text:
                    score += 1

            for pattern in patterns:
                if re.search(pattern, error_text, re.IGNORECASE):
                    score += 2

            if score > best_score:
                best_score = score
                best_match = category_name

        if not best_match:
            best_match = "unknown"

        category_config = self.categories.get(best_match, {})
        severity = self._determine_severity(error_message, error_type, category_config)

        return {
            "category": best_match,
            "description": category_config.get("description", ""),
            "severity": severity,
            "confidence": min(best_score / 5.0, 1.0) if best_score > 0 else 0.0,
        }

    def _determine_severity(
        self, error_message: str, error_type: Optional[str], category_config: Dict
    ) -> str:
        """Determine error severity.

        Args:
            error_message: Error message.
            error_type: Error type.
            category_config: Category configuration.

        Returns:
            Severity level (low, medium, high, critical).
        """
        default_severity = category_config.get("default_severity", "medium")
        severity_keywords = self.severity_rules.get("keywords", {})

        error_text = f"{error_message} {error_type or ''}".lower()

        for severity, keywords in severity_keywords.items():
            if any(keyword.lower() in error_text for keyword in keywords):
                return severity

        return default_severity

    def get_category_keywords(self, category: str) -> List[str]:
        """Get keywords for a category.

        Args:
            category: Category name.

        Returns:
            List of keywords.
        """
        category_config = self.categories.get(category, {})
        return category_config.get("keywords", [])
