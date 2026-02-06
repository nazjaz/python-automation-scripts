"""Categorize customer complaints by issue type."""

from typing import Dict, List, Optional

from src.database import DatabaseManager


class IssueCategorizer:
    """Categorize customer complaints by issue type."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize issue categorizer.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.category_keywords = config.get("category_keywords", {
            "product_quality": ["defective", "broken", "damaged", "quality", "faulty"],
            "billing": ["charge", "billing", "invoice", "payment", "refund", "overcharge"],
            "shipping": ["delivery", "shipping", "late", "missing", "package", "tracking"],
            "customer_service": ["service", "support", "representative", "help", "assistance"],
            "technical": ["error", "bug", "technical", "system", "website", "app", "login"],
            "account": ["account", "password", "access", "login", "registration"],
        })

    def categorize_complaint(self, complaint_text: str) -> Dict[str, any]:
        """Categorize complaint based on text.

        Args:
            complaint_text: Complaint text.

        Returns:
            Dictionary with categorization results.
        """
        complaint_lower = complaint_text.lower()

        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in complaint_lower)
            if score > 0:
                category_scores[category] = score

        if not category_scores:
            category = "general"
            subcategory = "other"
            confidence = 0.3
        else:
            category = max(category_scores, key=category_scores.get)
            max_score = category_scores[category]
            total_keywords = len(self.category_keywords.get(category, []))
            confidence = min(max_score / total_keywords, 1.0) if total_keywords > 0 else 0.5
            subcategory = self._determine_subcategory(category, complaint_lower)

        priority = self._determine_priority(complaint_text, category)

        return {
            "category": category,
            "subcategory": subcategory,
            "confidence": confidence,
            "priority": priority,
        }

    def _determine_subcategory(self, category: str, complaint_text: str) -> str:
        """Determine subcategory for complaint.

        Args:
            category: Main category.
            subcategory_keywords: Subcategory keywords dictionary.

        Returns:
            Subcategory string.
        """
        subcategory_keywords = self.config.get("subcategory_keywords", {})

        if category in subcategory_keywords:
            for subcat, keywords in subcategory_keywords[category].items():
                if any(keyword in complaint_text for keyword in keywords):
                    return subcat

        return "general"

    def _determine_priority(self, complaint_text: str, category: str) -> str:
        """Determine priority for complaint.

        Args:
            complaint_text: Complaint text.
            category: Complaint category.

        Returns:
            Priority level (low, medium, high, urgent).
        """
        urgent_keywords = ["urgent", "critical", "emergency", "immediately", "asap"]
        high_keywords = ["important", "serious", "unacceptable", "terrible", "awful"]

        complaint_lower = complaint_text.lower()

        if any(keyword in complaint_lower for keyword in urgent_keywords):
            return "urgent"
        elif any(keyword in complaint_lower for keyword in high_keywords):
            return "high"
        elif category in ["billing", "technical", "account"]:
            return "high"
        else:
            return "medium"

    def get_category_statistics(self) -> Dict[str, any]:
        """Get statistics by category.

        Returns:
            Dictionary with category statistics.
        """
        session = self.db_manager.get_session()
        try:
            from src.database import Complaint
            from collections import Counter

            complaints = session.query(Complaint).all()

            category_counts = Counter(c.category for c in complaints if c.category)
            status_counts = Counter(c.status for c in complaints if c.status)

            return {
                "total_complaints": len(complaints),
                "by_category": dict(category_counts),
                "by_status": dict(status_counts),
            }
        finally:
            session.close()
