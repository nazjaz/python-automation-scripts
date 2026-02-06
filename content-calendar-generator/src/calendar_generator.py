"""Content calendar generator module.

Generates personalized content calendars based on audience engagement,
optimal posting times, and content performance analysis.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.audience_analyzer import AudienceAnalyzer
from src.config import CalendarConfig, PlatformConfig, Settings
from src.performance_analyzer import PerformanceAnalyzer
from src.posting_time_analyzer import PostingTimeAnalyzer

logger = logging.getLogger(__name__)


class CalendarGenerator:
    """Generates personalized content calendars."""

    def __init__(self, settings: Settings) -> None:
        """Initialize calendar generator.

        Args:
            settings: Application settings.
        """
        self.settings = settings
        self.config: CalendarConfig = settings.calendar
        self.audience_analyzer = AudienceAnalyzer(settings)
        self.performance_analyzer = PerformanceAnalyzer(settings)
        self.posting_time_analyzer = PostingTimeAnalyzer(settings)

    def generate_calendar(
        self,
        platform: str,
        historical_data: Optional[List[Dict[str, Any]]] = None,
        start_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Generate content calendar for a platform.

        Args:
            platform: Platform name (e.g., 'facebook', 'twitter').
            historical_data: Historical post data for analysis.
            start_date: Start date for calendar. Defaults to today.

        Returns:
            List of scheduled content items with dates, times, and metadata.
        """
        if start_date is None:
            start_date = datetime.now()

        platform_config = self.settings.platforms.get(platform)
        if not platform_config or not platform_config.enabled:
            logger.warning(f"Platform {platform} is not enabled")
            return []

        optimal_times = {}
        optimal_content_types = self.config.content_types.copy()

        if historical_data:
            engagement_results = self.audience_analyzer.analyze_historical_engagement(
                historical_data
            )
            performance_results = self.performance_analyzer.analyze_performance(
                historical_data
            )
            optimal_times = (
                self.posting_time_analyzer.analyze_optimal_times(
                    historical_data
                )
            )

            best_types = self.performance_analyzer.get_best_content_types(
                performance_results
            )
            if best_types:
                optimal_content_types = best_types

        calendar = []
        end_date = start_date + timedelta(weeks=self.config.weeks_ahead)

        current_date = start_date
        while current_date < end_date:
            day_name = current_date.strftime("%A").lower()
            posts_for_day = self._generate_posts_for_day(
                current_date,
                day_name,
                platform,
                platform_config,
                optimal_times,
                optimal_content_types,
            )
            calendar.extend(posts_for_day)
            current_date += timedelta(days=1)

        logger.info(
            f"Generated calendar with {len(calendar)} posts for {platform}"
        )

        return calendar

    def _generate_posts_for_day(
        self,
        date: datetime,
        day_name: str,
        platform: str,
        platform_config: PlatformConfig,
        optimal_times: Dict[str, List[tuple]],
        optimal_content_types: List[str],
    ) -> List[Dict[str, Any]]:
        """Generate posts for a specific day.

        Args:
            date: Date for posts.
            day_name: Day name (e.g., 'monday').
            platform: Platform name.
            platform_config: Platform configuration.
            optimal_times: Optimal posting times by day.
            optimal_content_types: List of optimal content types.

        Returns:
            List of post dictionaries for the day.
        """
        posts = []
        posts_per_day = platform_config.posts_per_day

        optimal_hours = self._get_optimal_hours(
            day_name, platform_config, optimal_times
        )

        content_types = self._select_content_types(
            posts_per_day, optimal_content_types
        )

        for i in range(posts_per_day):
            hour = optimal_hours[i % len(optimal_hours)] if optimal_hours else 9 + i * 4
            post_time = date.replace(hour=hour, minute=0, second=0)

            content_type = content_types[i % len(content_types)]

            post = {
                "platform": platform,
                "scheduled_time": post_time.isoformat(),
                "date": date.strftime("%Y-%m-%d"),
                "time": post_time.strftime("%H:%M"),
                "content_type": content_type,
                "status": "pending",
                "title": f"{content_type.replace('_', ' ').title()} - {date.strftime('%B %d, %Y')}",
            }

            posts.append(post)

        return posts

    def _get_optimal_hours(
        self,
        day_name: str,
        platform_config: PlatformConfig,
        optimal_times: Dict[str, List[tuple]],
    ) -> List[int]:
        """Get optimal hours for posting on a specific day.

        Args:
            day_name: Day name.
            platform_config: Platform configuration.
            optimal_times: Analyzed optimal times.

        Returns:
            List of optimal hours.
        """
        if optimal_times and day_name in optimal_times:
            return [hour for hour, _ in optimal_times[day_name][:5]]

        for day_config in platform_config.optimal_times:
            if day_config.get("day", "").lower() == day_name:
                return day_config.get("hours", [9, 13, 17])

        return [9, 13, 17]

    def _select_content_types(
        self, count: int, optimal_types: List[str]
    ) -> List[str]:
        """Select content types based on mix configuration.

        Args:
            count: Number of content types needed.
            optimal_types: List of optimal content types.

        Returns:
            List of selected content types.
        """
        if not optimal_types:
            optimal_types = self.config.content_types.copy()

        if not optimal_types:
            return ["social_media"] * count

        content_mix = self.config.content_mix.copy()
        if not content_mix:
            return random.choices(optimal_types, k=count)

        selected = []
        total_weight = sum(content_mix.values())

        for _ in range(count):
            rand = random.uniform(0, total_weight)
            cumulative = 0
            for content_type, weight in content_mix.items():
                cumulative += weight
                if rand <= cumulative:
                    selected.append(content_type)
                    break
            else:
                selected.append(optimal_types[0])

        return selected

    def generate_multi_platform_calendar(
        self,
        platforms: List[str],
        historical_data: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        start_date: Optional[datetime] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate calendars for multiple platforms.

        Args:
            platforms: List of platform names.
            historical_data: Dictionary mapping platform names to historical
                data lists.
            start_date: Start date for calendars.

        Returns:
            Dictionary mapping platform names to their calendars.
        """
        calendars = {}

        for platform in platforms:
            platform_data = (
                historical_data.get(platform, []) if historical_data else None
            )
            calendar = self.generate_calendar(
                platform, platform_data, start_date
            )
            calendars[platform] = calendar

        logger.info(
            f"Generated calendars for {len(platforms)} platforms: "
            f"{', '.join(platforms)}"
        )

        return calendars
