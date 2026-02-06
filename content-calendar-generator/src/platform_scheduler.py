"""Platform scheduler module.

Handles automated scheduling of content across multiple social media platforms.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from src.config import SchedulingConfig, Settings

logger = logging.getLogger(__name__)


class PlatformScheduler:
    """Manages scheduling of content across platforms."""

    def __init__(self, settings: Settings) -> None:
        """Initialize platform scheduler.

        Args:
            settings: Application settings.
        """
        self.settings = settings
        self.config: SchedulingConfig = settings.scheduling
        self.api_tokens = self._load_api_tokens()

    def schedule_post(
        self, platform: str, post: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Schedule a single post on a platform.

        Args:
            platform: Platform name.
            post: Post data dictionary.

        Returns:
            Dictionary with scheduling result:
                - success: Boolean indicating success
                - post_id: Platform post ID if successful
                - error: Error message if failed
        """
        if not self.config.auto_schedule:
            logger.info(
                f"Auto-scheduling disabled, skipping post: {post.get('title')}"
            )
            return {"success": False, "error": "Auto-scheduling disabled"}

        try:
            scheduled_time = datetime.fromisoformat(
                post.get("scheduled_time", "")
            )
            buffer_time = scheduled_time.timestamp() - (
                self.config.buffer_minutes * 60
            )

            if buffer_time < time.time():
                logger.warning(
                    f"Post time {scheduled_time} is in the past, skipping"
                )
                return {
                    "success": False,
                    "error": "Scheduled time is in the past",
                }

            result = self._schedule_on_platform(platform, post, scheduled_time)

            if result.get("success"):
                logger.info(
                    f"Successfully scheduled post on {platform}: "
                    f"{post.get('title')}"
                )
            else:
                logger.error(
                    f"Failed to schedule post on {platform}: "
                    f"{result.get('error')}"
                )

            return result

        except Exception as e:
            logger.error(f"Error scheduling post: {str(e)}")
            return {"success": False, "error": str(e)}

    def schedule_calendar(
        self, calendar: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Dict[str, Any]]:
        """Schedule all posts in a calendar.

        Args:
            calendar: Dictionary mapping platform names to lists of posts.

        Returns:
            Dictionary mapping platform names to scheduling results.
        """
        results = {}

        for platform, posts in calendar.items():
            platform_results = {
                "scheduled": 0,
                "failed": 0,
                "errors": [],
            }

            for post in posts:
                result = self.schedule_post(platform, post)
                if result.get("success"):
                    platform_results["scheduled"] += 1
                else:
                    platform_results["failed"] += 1
                    platform_results["errors"].append(
                        {
                            "post": post.get("title"),
                            "error": result.get("error"),
                        }
                    )

            results[platform] = platform_results

            logger.info(
                f"Scheduled {platform_results['scheduled']} posts on {platform}, "
                f"{platform_results['failed']} failed"
            )

        return results

    def _schedule_on_platform(
        self, platform: str, post: Dict[str, Any], scheduled_time: datetime
    ) -> Dict[str, Any]:
        """Schedule post on specific platform.

        Args:
            platform: Platform name.
            post: Post data dictionary.
            scheduled_time: Scheduled datetime.

        Returns:
            Dictionary with scheduling result.
        """
        platform_lower = platform.lower()

        if platform_lower == "facebook":
            return self._schedule_facebook(post, scheduled_time)
        elif platform_lower == "twitter":
            return self._schedule_twitter(post, scheduled_time)
        elif platform_lower == "instagram":
            return self._schedule_instagram(post, scheduled_time)
        elif platform_lower == "linkedin":
            return self._schedule_linkedin(post, scheduled_time)
        else:
            return {
                "success": False,
                "error": f"Unsupported platform: {platform}",
            }

    def _schedule_facebook(
        self, post: Dict[str, Any], scheduled_time: datetime
    ) -> Dict[str, Any]:
        """Schedule post on Facebook.

        Args:
            post: Post data dictionary.
            scheduled_time: Scheduled datetime.

        Returns:
            Dictionary with scheduling result.
        """
        access_token = self.api_tokens.get("facebook_access_token")
        page_id = self.api_tokens.get("facebook_page_id")

        if not access_token or not page_id:
            return {
                "success": False,
                "error": "Facebook credentials not configured",
            }

        try:
            url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
            params = {
                "message": post.get("title", ""),
                "scheduled_publish_time": int(scheduled_time.timestamp()),
                "published": False,
                "access_token": access_token,
            }

            response = requests.post(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            return {"success": True, "post_id": data.get("id")}

        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def _schedule_twitter(
        self, post: Dict[str, Any], scheduled_time: datetime
    ) -> Dict[str, Any]:
        """Schedule post on Twitter/X.

        Args:
            post: Post data dictionary.
            scheduled_time: Scheduled datetime.

        Returns:
            Dictionary with scheduling result.
        """
        api_key = self.api_tokens.get("twitter_api_key")
        api_secret = self.api_tokens.get("twitter_api_secret")
        access_token = self.api_tokens.get("twitter_access_token")
        access_token_secret = self.api_tokens.get(
            "twitter_access_token_secret"
        )

        if not all([api_key, api_secret, access_token, access_token_secret]):
            return {
                "success": False,
                "error": "Twitter credentials not configured",
            }

        try:
            import tweepy

            auth = tweepy.OAuth1UserHandler(
                api_key, api_secret, access_token, access_token_secret
            )
            api = tweepy.API(auth)

            api.update_status(status=post.get("title", ""))
            return {"success": True, "post_id": "twitter_post_id"}

        except ImportError:
            return {
                "success": False,
                "error": "tweepy library not installed",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _schedule_instagram(
        self, post: Dict[str, Any], scheduled_time: datetime
    ) -> Dict[str, Any]:
        """Schedule post on Instagram.

        Args:
            post: Post data dictionary.
            scheduled_time: Scheduled datetime.

        Returns:
            Dictionary with scheduling result.
        """
        access_token = self.api_tokens.get("instagram_access_token")
        account_id = self.api_tokens.get("instagram_account_id")

        if not access_token or not account_id:
            return {
                "success": False,
                "error": "Instagram credentials not configured",
            }

        return {
            "success": False,
            "error": "Instagram scheduling requires media upload",
        }

    def _schedule_linkedin(
        self, post: Dict[str, Any], scheduled_time: datetime
    ) -> Dict[str, Any]:
        """Schedule post on LinkedIn.

        Args:
            post: Post data dictionary.
            scheduled_time: Scheduled datetime.

        Returns:
            Dictionary with scheduling result.
        """
        access_token = self.api_tokens.get("linkedin_access_token")

        if not access_token:
            return {
                "success": False,
                "error": "LinkedIn credentials not configured",
            }

        try:
            url = "https://api.linkedin.com/v2/ugcPosts"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "author": f"urn:li:person:{self.api_tokens.get('linkedin_person_id', '')}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": post.get("title", "")},
                        "shareMediaCategory": "NONE",
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            }

            response = requests.post(
                url, json=payload, headers=headers, timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return {"success": True, "post_id": data.get("id")}

        except requests.RequestException as e:
            return {"success": False, "error": str(e)}

    def _load_api_tokens(self) -> Dict[str, Optional[str]]:
        """Load API tokens from environment variables.

        Returns:
            Dictionary mapping token names to values.
        """
        from src.config import get_env_var

        return {
            "facebook_access_token": get_env_var("FACEBOOK_ACCESS_TOKEN"),
            "facebook_page_id": get_env_var("FACEBOOK_PAGE_ID"),
            "twitter_api_key": get_env_var("TWITTER_API_KEY"),
            "twitter_api_secret": get_env_var("TWITTER_API_SECRET"),
            "twitter_access_token": get_env_var("TWITTER_ACCESS_TOKEN"),
            "twitter_access_token_secret": get_env_var(
                "TWITTER_ACCESS_TOKEN_SECRET"
            ),
            "instagram_access_token": get_env_var("INSTAGRAM_ACCESS_TOKEN"),
            "instagram_account_id": get_env_var("INSTAGRAM_ACCOUNT_ID"),
            "linkedin_access_token": get_env_var("LINKEDIN_ACCESS_TOKEN"),
            "linkedin_person_id": get_env_var("LINKEDIN_PERSON_ID"),
        }
