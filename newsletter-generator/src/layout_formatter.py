"""Formats newsletter layouts."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, Newsletter, Article

logger = logging.getLogger(__name__)


class LayoutFormatter:
    """Formats newsletter layouts."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize layout formatter.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.layout_config = config.get("layout", {})
        self.template_path = Path(self.layout_config.get("template", "templates/newsletter_template.html"))

    def format_newsletter(
        self,
        newsletter: Newsletter,
        articles: List[Article],
        subscriber_name: Optional[str] = None,
        personalized: Optional[Dict] = None,
    ) -> str:
        """Format newsletter HTML content.

        Args:
            newsletter: Newsletter object.
            articles: List of Article objects.
            subscriber_name: Optional subscriber name for personalization.
            personalized: Optional personalized sections dictionary.

        Returns:
            Formatted HTML content.
        """
        if self.template_path.exists():
            with open(self.template_path, "r") as f:
                template_content = f.read()
        else:
            template_content = self._get_default_template()

        template = Template(template_content)

        styling = self.layout_config.get("styling", {})
        sections = self.layout_config.get("sections", [])

        featured_article = next((a for a in articles if a), None)
        other_articles = [a for a in articles if a != featured_article]

        html_content = template.render(
            newsletter=newsletter,
            subscriber_name=subscriber_name or "Subscriber",
            featured_article=featured_article,
            articles=other_articles,
            styling=styling,
            sections=sections,
            personalized=personalized or {},
        )

        logger.info(
            f"Formatted newsletter: {newsletter.newsletter_id}",
            extra={"newsletter_id": newsletter.newsletter_id, "article_count": len(articles)},
        )

        return html_content

    def format_text_version(
        self,
        newsletter: Newsletter,
        articles: List[Article],
    ) -> str:
        """Format newsletter text version.

        Args:
            newsletter: Newsletter object.
            articles: List of Article objects.

        Returns:
            Formatted text content.
        """
        text_lines = [
            newsletter.title,
            "=" * len(newsletter.title),
            "",
        ]

        for article in articles:
            text_lines.append(f"{article.title}")
            if article.summary:
                text_lines.append(f"\n{article.summary}\n")
            if article.source_url:
                text_lines.append(f"Read more: {article.source_url}\n")
            text_lines.append("-" * 50)
            text_lines.append("")

        return "\n".join(text_lines)

    def _get_default_template(self) -> str:
        """Get default newsletter template.

        Returns:
            Default HTML template string.
        """
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ newsletter.title }}</title>
    <style>
        body { font-family: {{ styling.font_family }}; font-size: {{ styling.font_size }}; }
        .header { background: {{ styling.primary_color }}; color: white; padding: 20px; }
        .article { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ newsletter.title }}</h1>
    </div>
    {% if featured_article %}
    <div class="article">
        <h2>{{ featured_article.title }}</h2>
        <p>{{ featured_article.summary }}</p>
    </div>
    {% endif %}
    {% for article in articles %}
    <div class="article">
        <h3>{{ article.title }}</h3>
        <p>{{ article.summary }}</p>
    </div>
    {% endfor %}
</body>
</html>"""
