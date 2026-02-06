"""Identifies top-performing content across platforms."""

import logging
from typing import Dict, List, Optional

from src.database import DatabaseManager, ContentAnalysis, ContentPost

logger = logging.getLogger(__name__)


class TopContentIdentifier:
    """Identifies and ranks top-performing content."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        top_count: int = 10,
    ) -> None:
        """Initialize top content identifier.

        Args:
            db_manager: Database manager instance.
            top_count: Number of top content items to identify.
        """
        self.db_manager = db_manager
        self.top_count = top_count

    def get_top_content(
        self,
        platform: Optional[str] = None,
        days: Optional[int] = None,
    ) -> List[Dict]:
        """Get top-performing content.

        Args:
            platform: Optional platform filter.
            days: Optional number of days to look back.

        Returns:
            List of dictionaries with top content information.
        """
        analyses = self.db_manager.get_top_content(
            platform=platform, limit=self.top_count, days=days
        )

        top_content = []
        session = self.db_manager.get_session()
        try:
            for analysis in analyses:
                post = (
                    session.query(ContentPost)
                    .filter(ContentPost.id == analysis.content_post_id)
                    .first()
                )

                if post:
                metrics = self.db_manager.get_metrics_for_post(post.id)
                top_content.append(
                    {
                        "content_post_id": post.id,
                        "platform": post.platform,
                        "content_id": post.content_id,
                        "title": post.title,
                        "content_type": post.content_type,
                        "posted_at": post.posted_at.isoformat() if post.posted_at else None,
                        "overall_score": analysis.overall_score,
                        "engagement_score": analysis.engagement_score,
                        "reach_score": analysis.reach_score,
                        "views_score": analysis.views_score,
                        "metrics": metrics,
                    }
                )
        finally:
            session.close()

        logger.info(
            f"Identified {len(top_content)} top content items",
            extra={
                "count": len(top_content),
                "platform": platform,
                "days": days,
            },
        )

        return top_content

    def get_top_content_by_platform(
        self, days: Optional[int] = None
    ) -> Dict[str, List[Dict]]:
        """Get top content grouped by platform.

        Args:
            days: Optional number of days to look back.

        Returns:
            Dictionary mapping platform names to lists of top content.
        """
        platforms = ["facebook", "twitter", "instagram", "linkedin", "youtube"]
        top_by_platform = {}

        for platform in platforms:
            top_content = self.get_top_content(platform=platform, days=days)
            if top_content:
                top_by_platform[platform] = top_content

        return top_by_platform

    def get_top_content_by_type(
        self,
        content_type: str,
        platform: Optional[str] = None,
        days: Optional[int] = None,
    ) -> List[Dict]:
        """Get top content filtered by content type.

        Args:
            content_type: Type of content (e.g., 'video', 'image', 'text').
            platform: Optional platform filter.
            days: Optional number of days to look back.

        Returns:
            List of top content items of specified type.
        """
        all_top = self.get_top_content(platform=platform, days=days)
        filtered = [
            item for item in all_top if item.get("content_type") == content_type
        ]

        logger.info(
            f"Identified {len(filtered)} top {content_type} content items",
            extra={
                "content_type": content_type,
                "count": len(filtered),
                "platform": platform,
            },
        )

        return filtered
