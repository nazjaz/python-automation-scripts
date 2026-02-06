"""Product issue identification from customer reviews."""

import re
from collections import Counter
from typing import Dict, List

from textblob import TextBlob


class IssueIdentifier:
    """Identify product issues from customer reviews."""

    def __init__(self, config: Dict):
        """Initialize issue identifier.

        Args:
            config: Configuration dictionary with issue identification settings.
        """
        self.config = config
        self.issue_keywords = config.get("issue_keywords", {})
        self.severity_keywords = config.get("severity_keywords", {})
        self.min_issue_length = config.get("min_issue_length", 10)

    def identify_issues(
        self, review_text: str, sentiment_score: float, sentiment_label: str
    ) -> List[Dict[str, any]]:
        """Identify product issues from review.

        Args:
            review_text: Review text to analyze.
            sentiment_score: Review sentiment score.
            sentiment_label: Review sentiment label.

        Returns:
            List of issue dictionaries with text, severity, and category.
        """
        if not review_text or len(review_text.strip()) < self.min_issue_length:
            return []

        if sentiment_label != "negative" and sentiment_score > -0.2:
            return []

        sentences = self._split_into_sentences(review_text)
        issues = []

        for sentence in sentences:
            issue_info = self._analyze_sentence_for_issues(sentence, sentiment_score)
            if issue_info:
                issues.append(issue_info)

        return issues

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences.

        Args:
            text: Text to split.

        Returns:
            List of sentences.
        """
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if len(s.strip()) >= self.min_issue_length]

    def _analyze_sentence_for_issues(
        self, sentence: str, sentiment_score: float
    ) -> Dict[str, any]:
        """Analyze sentence for product issues.

        Args:
            sentence: Sentence to analyze.
            sentiment_score: Overall sentiment score.

        Returns:
            Issue dictionary or None if no issue found.
        """
        sentence_lower = sentence.lower()

        issue_category = None
        severity = "medium"

        for category, keywords in self.issue_keywords.items():
            for keyword in keywords:
                if keyword.lower() in sentence_lower:
                    issue_category = category
                    break
            if issue_category:
                break

        if not issue_category:
            if any(
                word in sentence_lower
                for word in ["problem", "issue", "broken", "defect", "faulty", "error"]
            ):
                issue_category = "general"

        if issue_category:
            severity = self._determine_severity(sentence, sentiment_score)

            return {
                "issue_text": sentence.strip(),
                "severity": severity,
                "category": issue_category,
            }

        return None

    def _determine_severity(self, sentence: str, sentiment_score: float) -> str:
        """Determine issue severity.

        Args:
            sentence: Issue sentence.
            sentiment_score: Sentiment score.

        Returns:
            Severity level (low, medium, high, critical).
        """
        sentence_lower = sentence.lower()

        critical_keywords = self.severity_keywords.get("critical", [])
        high_keywords = self.severity_keywords.get("high", [])
        low_keywords = self.severity_keywords.get("low", [])

        if any(keyword in sentence_lower for keyword in critical_keywords):
            return "critical"

        if any(keyword in sentence_lower for keyword in high_keywords):
            return "high"

        if any(keyword in sentence_lower for keyword in low_keywords):
            return "low"

        if sentiment_score < -0.5:
            return "high"
        elif sentiment_score < -0.3:
            return "medium"
        else:
            return "low"

    def aggregate_issues(self, issues: List[Dict[str, any]]) -> Dict[str, any]:
        """Aggregate and summarize issues.

        Args:
            issues: List of issue dictionaries.

        Returns:
            Aggregated issue statistics.
        """
        if not issues:
            return {
                "total_issues": 0,
                "by_category": {},
                "by_severity": {},
                "most_common": [],
            }

        categories = [issue.get("category", "unknown") for issue in issues]
        severities = [issue.get("severity", "medium") for issue in issues]

        category_counts = Counter(categories)
        severity_counts = Counter(severities)

        issue_texts = [issue.get("issue_text", "") for issue in issues]
        common_issues = Counter(issue_texts).most_common(5)

        return {
            "total_issues": len(issues),
            "by_category": dict(category_counts),
            "by_severity": dict(severity_counts),
            "most_common": [{"text": text, "count": count} for text, count in common_issues],
        }
