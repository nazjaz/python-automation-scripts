"""Sentiment analysis for customer reviews."""

import re
from typing import Dict, Tuple

from textblob import TextBlob


class SentimentAnalyzer:
    """Analyze sentiment of customer reviews."""

    def __init__(self, config: Dict):
        """Initialize sentiment analyzer.

        Args:
            config: Configuration dictionary with sentiment analysis settings.
        """
        self.config = config
        self.positive_threshold = config.get("positive_threshold", 0.1)
        self.negative_threshold = config.get("negative_threshold", -0.1)

    def analyze_sentiment(self, review_text: str, rating: int = None) -> Tuple[float, str]:
        """Analyze sentiment of review text.

        Args:
            review_text: Review text to analyze.
            rating: Optional rating (1-5) to influence sentiment.

        Returns:
            Tuple of (sentiment_score, sentiment_label).
            sentiment_score: Float between -1.0 (negative) and 1.0 (positive).
            sentiment_label: String label (positive, negative, neutral).
        """
        if not review_text or len(review_text.strip()) < 3:
            return 0.0, "neutral"

        cleaned_text = self._clean_text(review_text)
        blob = TextBlob(cleaned_text)
        polarity = blob.sentiment.polarity

        if rating is not None:
            rating_adjustment = self._rating_to_sentiment(rating)
            polarity = (polarity + rating_adjustment) / 2

        sentiment_label = self._classify_sentiment(polarity)

        return polarity, sentiment_label

    def _clean_text(self, text: str) -> str:
        """Clean text for sentiment analysis.

        Args:
            text: Text to clean.

        Returns:
            Cleaned text.
        """
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"http\S+", "", text)
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _rating_to_sentiment(self, rating: int) -> float:
        """Convert rating (1-5) to sentiment score.

        Args:
            rating: Rating value (1-5).

        Returns:
            Sentiment score between -1.0 and 1.0.
        """
        rating_map = {1: -0.8, 2: -0.4, 3: 0.0, 4: 0.4, 5: 0.8}
        return rating_map.get(rating, 0.0)

    def _classify_sentiment(self, polarity: float) -> str:
        """Classify sentiment based on polarity score.

        Args:
            polarity: Sentiment polarity score.

        Returns:
            Sentiment label (positive, negative, neutral).
        """
        if polarity > self.positive_threshold:
            return "positive"
        elif polarity < self.negative_threshold:
            return "negative"
        else:
            return "neutral"

    def calculate_average_sentiment(self, reviews: list) -> Dict[str, any]:
        """Calculate average sentiment across multiple reviews.

        Args:
            reviews: List of review dictionaries with sentiment_score.

        Returns:
            Dictionary with average sentiment metrics.
        """
        if not reviews:
            return {
                "average_score": 0.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "positive_percentage": 0.0,
                "negative_percentage": 0.0,
                "neutral_percentage": 0.0,
            }

        scores = [r.get("sentiment_score", 0.0) for r in reviews if r.get("sentiment_score") is not None]
        labels = [r.get("sentiment_label", "neutral") for r in reviews]

        positive_count = labels.count("positive")
        negative_count = labels.count("negative")
        neutral_count = labels.count("neutral")
        total_count = len(reviews)

        return {
            "average_score": sum(scores) / len(scores) if scores else 0.0,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "positive_percentage": (positive_count / total_count * 100) if total_count > 0 else 0.0,
            "negative_percentage": (negative_count / total_count * 100) if total_count > 0 else 0.0,
            "neutral_percentage": (neutral_count / total_count * 100) if total_count > 0 else 0.0,
        }
