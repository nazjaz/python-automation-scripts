"""Personalizes newsletter content for subscribers."""

import json
import logging
from typing import Dict, List, Optional

from src.database import DatabaseManager, Subscriber, Article, Newsletter

logger = logging.getLogger(__name__)


class PersonalizationEngine:
    """Personalizes newsletter content for subscribers."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize personalization engine.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.personalization_config = config.get("personalization", {})

    def personalize_articles(
        self,
        subscriber_id: int,
        articles: List[Article],
    ) -> List[Article]:
        """Personalize article selection for subscriber.

        Args:
            subscriber_id: Subscriber ID.
            articles: List of Article objects.

        Returns:
            Personalized list of Article objects.
        """
        if not self.personalization_config.get("enabled", True):
            return articles

        subscriber = (
            self.db_manager.get_session()
            .query(Subscriber)
            .filter(Subscriber.id == subscriber_id)
            .first()
        )

        if not subscriber:
            return articles

        personalized = self._rank_for_subscriber(subscriber, articles)

        logger.info(
            f"Personalized {len(personalized)} articles for subscriber {subscriber_id}",
            extra={"subscriber_id": subscriber_id, "article_count": len(personalized)},
        )

        return personalized

    def _rank_for_subscriber(
        self,
        subscriber: Subscriber,
        articles: List[Article],
    ) -> List[Article]:
        """Rank articles for subscriber based on preferences and history.

        Args:
            subscriber: Subscriber object.
            articles: List of Article objects.

        Returns:
            Ranked list of Article objects.
        """
        scored_articles = []

        preferences = {}
        if subscriber.preferences:
            try:
                preferences = json.loads(subscriber.preferences)
            except (json.JSONDecodeError, TypeError):
                pass

        reading_history = subscriber.reading_history
        read_article_ids = {rh.article_id for rh in reading_history}

        for article in articles:
            score = 0.0

            if self.personalization_config.get("use_reading_history", True):
                if article.id not in read_article_ids:
                    score += 0.3
                else:
                    score -= 0.2

            if self.personalization_config.get("use_subscriber_preferences", True):
                preferred_categories = preferences.get("categories", [])
                if article.category in preferred_categories:
                    score += 0.4

                preferred_tags = preferences.get("tags", [])
                if article.tags:
                    article_tags = article.tags.split(",")
                    matching_tags = len(set(article_tags) & set(preferred_tags))
                    if matching_tags > 0:
                        score += 0.2 * matching_tags

            if self.personalization_config.get("use_demographics", True):
                demographics = {}
                if subscriber.demographics:
                    try:
                        demographics = json.loads(subscriber.demographics)
                    except (json.JSONDecodeError, TypeError):
                        pass

            if article.quality_score:
                score += article.quality_score * 0.2

            if article.relevance_score:
                score += article.relevance_score * 0.1

            scored_articles.append((score, article))

        scored_articles.sort(key=lambda x: x[0], reverse=True)

        return [article for _, article in scored_articles]

    def personalize_greeting(
        self,
        subscriber: Subscriber,
    ) -> str:
        """Generate personalized greeting.

        Args:
            subscriber: Subscriber object.

        Returns:
            Personalized greeting string.
        """
        if subscriber.name:
            return f"Hello {subscriber.name},"
        else:
            return "Hello,"

    def personalize_sections(
        self,
        newsletter: Newsletter,
        subscriber: Subscriber,
    ) -> Dict:
        """Personalize newsletter sections.

        Args:
            newsletter: Newsletter object.
            subscriber: Subscriber object.

        Returns:
            Dictionary with personalized sections.
        """
        personalized = {
            "greeting": self.personalize_greeting(subscriber),
            "recommended_articles": [],
        }

        if self.personalization_config.get("personalize_sections", []):
            articles = [
                item.article for item in newsletter.items
                if item.article
            ]

            personalized_articles = self.personalize_articles(subscriber.id, articles)
            personalized["recommended_articles"] = personalized_articles[:3]

        logger.info(
            f"Personalized sections for subscriber {subscriber.id}",
            extra={"subscriber_id": subscriber.id},
        )

        return personalized
