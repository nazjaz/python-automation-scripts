"""Platform connectors for collecting content performance data."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from src.database import DatabaseManager

logger = logging.getLogger(__name__)


class PlatformConnector:
    """Base class for platform-specific content data connectors."""

    def __init__(
        self,
        platform_name: str,
        db_manager: DatabaseManager,
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize platform connector.

        Args:
            platform_name: Name of the platform (e.g., 'facebook', 'twitter').
            db_manager: Database manager instance.
            api_key: Optional API key for platform API access.
        """
        self.platform_name = platform_name
        self.db_manager = db_manager
        self.api_key = api_key

    def fetch_content_data(
        self, limit: int = 100, days: int = 30
    ) -> List[Dict]:
        """Fetch content data from platform.

        This is a base implementation that returns mock data.
        Subclasses should override this to integrate with actual platform APIs.

        Args:
            limit: Maximum number of content items to fetch.
            days: Number of days to look back.

        Returns:
            List of dictionaries containing content data.
        """
        logger.warning(
            f"Using mock data for {self.platform_name}. "
            "Override fetch_content_data() for real API integration."
        )
        return []

    def normalize_metrics(self, raw_data: Dict) -> Dict:
        """Normalize platform-specific metrics to standard format.

        Args:
            raw_data: Raw data from platform API.

        Returns:
            Dictionary with normalized metric names and values.
        """
        return {}


class FacebookConnector(PlatformConnector):
    """Facebook content data connector."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize Facebook connector."""
        super().__init__("facebook", db_manager, api_key)

    def normalize_metrics(self, raw_data: Dict) -> Dict:
        """Normalize Facebook metrics to standard format.

        Args:
            raw_data: Raw Facebook API data.

        Returns:
            Dictionary with normalized metrics.
        """
        return {
            "likes": raw_data.get("likes", 0),
            "comments": raw_data.get("comments", 0),
            "shares": raw_data.get("shares", 0),
            "views": raw_data.get("views", 0),
            "reach": raw_data.get("reach", 0),
        }


class TwitterConnector(PlatformConnector):
    """Twitter/X content data connector."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize Twitter connector."""
        super().__init__("twitter", db_manager, api_key)

    def normalize_metrics(self, raw_data: Dict) -> Dict:
        """Normalize Twitter metrics to standard format.

        Args:
            raw_data: Raw Twitter API data.

        Returns:
            Dictionary with normalized metrics.
        """
        return {
            "likes": raw_data.get("like_count", 0),
            "retweets": raw_data.get("retweet_count", 0),
            "replies": raw_data.get("reply_count", 0),
            "views": raw_data.get("view_count", 0),
            "impressions": raw_data.get("impression_count", 0),
        }


class InstagramConnector(PlatformConnector):
    """Instagram content data connector."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize Instagram connector."""
        super().__init__("instagram", db_manager, api_key)

    def normalize_metrics(self, raw_data: Dict) -> Dict:
        """Normalize Instagram metrics to standard format.

        Args:
            raw_data: Raw Instagram API data.

        Returns:
            Dictionary with normalized metrics.
        """
        return {
            "likes": raw_data.get("like_count", 0),
            "comments": raw_data.get("comment_count", 0),
            "saves": raw_data.get("saved_count", 0),
            "views": raw_data.get("view_count", 0),
            "reach": raw_data.get("reach", 0),
        }


class LinkedInConnector(PlatformConnector):
    """LinkedIn content data connector."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize LinkedIn connector."""
        super().__init__("linkedin", db_manager, api_key)

    def normalize_metrics(self, raw_data: Dict) -> Dict:
        """Normalize LinkedIn metrics to standard format.

        Args:
            raw_data: Raw LinkedIn API data.

        Returns:
            Dictionary with normalized metrics.
        """
        return {
            "likes": raw_data.get("like_count", 0),
            "comments": raw_data.get("comment_count", 0),
            "shares": raw_data.get("share_count", 0),
            "views": raw_data.get("view_count", 0),
            "impressions": raw_data.get("impression_count", 0),
        }


class YouTubeConnector(PlatformConnector):
    """YouTube content data connector."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize YouTube connector."""
        super().__init__("youtube", db_manager, api_key)

    def normalize_metrics(self, raw_data: Dict) -> Dict:
        """Normalize YouTube metrics to standard format.

        Args:
            raw_data: Raw YouTube API data.

        Returns:
            Dictionary with normalized metrics.
        """
        return {
            "likes": raw_data.get("like_count", 0),
            "comments": raw_data.get("comment_count", 0),
            "views": raw_data.get("view_count", 0),
            "watch_time": raw_data.get("watch_time_seconds", 0),
            "subscribers_gained": raw_data.get("subscriber_gain", 0),
        }


class PlatformManager:
    """Manages multiple platform connectors."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        platform_configs: List[Dict],
    ) -> None:
        """Initialize platform manager.

        Args:
            db_manager: Database manager instance.
            platform_configs: List of platform configuration dictionaries.
        """
        self.db_manager = db_manager
        self.connectors = {}

        connector_classes = {
            "facebook": FacebookConnector,
            "twitter": TwitterConnector,
            "instagram": InstagramConnector,
            "linkedin": LinkedInConnector,
            "youtube": YouTubeConnector,
        }

        for config in platform_configs:
            platform_name = config.get("name", "").lower()
            if config.get("enabled", False) and platform_name in connector_classes:
                connector_class = connector_classes[platform_name]
                api_key = None
                self.connectors[platform_name] = connector_class(
                    db_manager, api_key
                )

    def collect_content_data(
        self, limit: int = 100, days: int = 30
    ) -> Dict[str, List[Dict]]:
        """Collect content data from all enabled platforms.

        Args:
            limit: Maximum number of content items per platform.
            days: Number of days to look back.

        Returns:
            Dictionary mapping platform names to lists of content data.
        """
        all_data = {}
        for platform_name, connector in self.connectors.items():
            try:
                data = connector.fetch_content_data(limit=limit, days=days)
                all_data[platform_name] = data
                logger.info(
                    f"Collected {len(data)} content items from {platform_name}",
                    extra={"platform": platform_name, "count": len(data)},
                )
            except Exception as e:
                logger.error(
                    f"Error collecting data from {platform_name}: {e}",
                    extra={"platform": platform_name, "error": str(e)},
                )
                all_data[platform_name] = []

        return all_data

    def store_content_data(self, platform_data: Dict[str, List[Dict]]) -> None:
        """Store collected content data in database.

        Args:
            platform_data: Dictionary mapping platform names to content data lists.
        """
        for platform_name, content_list in platform_data.items():
            connector = self.connectors.get(platform_name)
            if not connector:
                continue

            for content_item in content_list:
                try:
                    content_id = content_item.get("id", "")
                    title = content_item.get("title", "")
                    content_type = content_item.get("type", "")
                    posted_at_str = content_item.get("posted_at", "")
                    posted_at = None

                    if posted_at_str:
                        try:
                            posted_at = datetime.fromisoformat(
                                posted_at_str.replace("Z", "+00:00")
                            )
                        except (ValueError, AttributeError):
                            posted_at = datetime.utcnow()

                    post = self.db_manager.add_content_post(
                        platform=platform_name,
                        content_id=content_id,
                        title=title,
                        content_type=content_type,
                        posted_at=posted_at or datetime.utcnow(),
                    )

                    raw_metrics = content_item.get("metrics", {})
                    normalized_metrics = connector.normalize_metrics(raw_metrics)
                    self.db_manager.add_metrics(
                        content_post_id=post.id,
                        platform=platform_name,
                        metrics=normalized_metrics,
                    )

                    logger.debug(
                        f"Stored content {content_id} from {platform_name}",
                        extra={
                            "platform": platform_name,
                            "content_id": content_id,
                            "post_id": post.id,
                        },
                    )
                except Exception as e:
                    logger.error(
                        f"Error storing content from {platform_name}: {e}",
                        extra={
                            "platform": platform_name,
                            "content_id": content_item.get("id", ""),
                            "error": str(e),
                        },
                    )
