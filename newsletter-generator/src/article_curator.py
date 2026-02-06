"""Curates articles for newsletters."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np

from src.database import DatabaseManager, Article

logger = logging.getLogger(__name__)


class ArticleCurator:
    """Curates articles for newsletters."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize article curator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.curation_config = config.get("content_curation", {})
        self.min_quality = self.curation_config.get("min_quality_score", 0.6)
        self.max_age_days = self.curation_config.get("max_article_age_days", 30)

    def curate_articles(
        self,
        count: Optional[int] = None,
        category: Optional[str] = None,
        min_quality_score: Optional[float] = None,
    ) -> List[Article]:
        """Curate articles for newsletter.

        Args:
            count: Optional number of articles to curate.
            category: Optional category filter.
            min_quality_score: Optional minimum quality score.

        Returns:
            List of curated Article objects.
        """
        if count is None:
            newsletter_config = self.config.get("newsletter", {})
            count = newsletter_config.get("max_articles_per_newsletter", 10)

        min_quality = min_quality_score or self.min_quality

        articles = self.db_manager.get_articles(
            category=category,
            min_quality_score=min_quality,
            limit=count * 2,
        )

        cutoff_date = datetime.utcnow() - timedelta(days=self.max_age_days)
        recent_articles = [
            a for a in articles
            if a.published_date and a.published_date >= cutoff_date
        ]

        if not recent_articles:
            recent_articles = articles

        curated = self._rank_articles(recent_articles)

        curated = curated[:count]

        logger.info(
            f"Curated {len(curated)} articles",
            extra={"article_count": len(curated), "category": category},
        )

        return curated

    def _rank_articles(self, articles: List[Article]) -> List[Article]:
        """Rank articles by curation criteria.

        Args:
            articles: List of Article objects.

        Returns:
            Ranked list of Article objects.
        """
        criteria = self.curation_config.get("curation_criteria", [])

        scored_articles = []

        for article in articles:
            score = 0.0
            factors = []

            if "relevance" in criteria:
                relevance = article.relevance_score or 0.5
                score += relevance * 0.3
                factors.append(f"relevance: {relevance:.2f}")

            if "recency" in criteria:
                if article.published_date:
                    days_old = (datetime.utcnow() - article.published_date).days
                    recency = max(0.0, 1.0 - (days_old / self.max_age_days))
                    score += recency * 0.3
                    factors.append(f"recency: {recency:.2f}")

            if "quality_score" in criteria:
                quality = article.quality_score or 0.5
                score += quality * 0.4
                factors.append(f"quality: {quality:.2f}")

            scored_articles.append((score, article, factors))

        scored_articles.sort(key=lambda x: x[0], reverse=True)

        return [article for _, article, _ in scored_articles]

    def curate_for_segment(
        self,
        segment: str,
        count: Optional[int] = None,
    ) -> List[Article]:
        """Curate articles for specific subscriber segment.

        Args:
            segment: Subscriber segment.
            count: Optional number of articles.

        Returns:
            List of curated Article objects.
        """
        if count is None:
            newsletter_config = self.config.get("newsletter", {})
            count = newsletter_config.get("max_articles_per_newsletter", 10)

        articles = self.db_manager.get_articles(limit=count * 3)

        segment_articles = self._filter_by_segment(articles, segment)

        curated = self._rank_articles(segment_articles)

        return curated[:count]

    def _filter_by_segment(
        self,
        articles: List[Article],
        segment: str,
    ) -> List[Article]:
        """Filter articles by segment preferences.

        Args:
            articles: List of Article objects.
            segment: Subscriber segment.

        Returns:
            Filtered list of Article objects.
        """
        if segment == "all":
            return articles

        segment_keywords = self.config.get("segments", {}).get("segment_keywords", {})
        keywords = segment_keywords.get(segment, [])

        if not keywords:
            return articles

        filtered = []
        for article in articles:
            article_text = f"{article.title} {article.summary or ''} {article.tags or ''}".lower()
            if any(keyword.lower() in article_text for keyword in keywords):
                filtered.append(article)

        return filtered if filtered else articles
