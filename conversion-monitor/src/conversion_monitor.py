"""Monitor website conversion rates."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class ConversionMonitor:
    """Monitor website conversion rates."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize conversion monitor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.time_window_hours = config.get("time_window_hours", 24)

    def calculate_conversion_rate(
        self,
        website_id: int,
        conversion_goal_id: Optional[int] = None,
        hours: Optional[int] = None,
    ) -> Dict[str, any]:
        """Calculate conversion rate for time period.

        Args:
            website_id: Website ID.
            conversion_goal_id: Optional conversion goal ID to filter by.
            hours: Number of hours to analyze.

        Returns:
            Dictionary with conversion rate metrics.
        """
        if hours is None:
            hours = self.time_window_hours

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        session = self.db_manager.get_session()

        try:
            from src.database import Session

            query = session.query(Session).filter(
                Session.website_id == website_id,
                Session.started_at >= cutoff_time,
            )

            if conversion_goal_id:
                query = query.filter(Session.conversion_goal_id == conversion_goal_id)

            sessions = query.all()

            total_sessions = len(sessions)
            converted_sessions = len([s for s in sessions if s.converted == "true"])

            conversion_rate = (
                converted_sessions / total_sessions * 100 if total_sessions > 0 else 0.0
            )

            time_window_start = cutoff_time
            time_window_end = datetime.utcnow()

            self.db_manager.add_conversion_rate(
                website_id=website_id,
                time_window_start=time_window_start,
                time_window_end=time_window_end,
                total_sessions=total_sessions,
                converted_sessions=converted_sessions,
                conversion_goal_id=conversion_goal_id,
            )

            return {
                "website_id": website_id,
                "conversion_goal_id": conversion_goal_id,
                "time_window_hours": hours,
                "total_sessions": total_sessions,
                "converted_sessions": converted_sessions,
                "conversion_rate": conversion_rate,
                "time_window_start": time_window_start,
                "time_window_end": time_window_end,
            }
        finally:
            session.close()

    def get_conversion_trends(
        self,
        website_id: int,
        conversion_goal_id: Optional[int] = None,
        days: int = 7,
    ) -> Dict[str, any]:
        """Get conversion rate trends over time.

        Args:
            website_id: Website ID.
            conversion_goal_id: Optional conversion goal ID to filter by.
            days: Number of days to analyze.

        Returns:
            Dictionary with conversion trends.
        """
        conversion_rates = self.db_manager.get_conversion_rates(
            website_id=website_id,
            conversion_goal_id=conversion_goal_id,
            hours=days * 24,
        )

        if not conversion_rates:
            return {
                "website_id": website_id,
                "days": days,
                "average_rate": 0.0,
                "trend": "stable",
                "rates": [],
            }

        rates = [cr.conversion_rate for cr in conversion_rates if cr.conversion_rate is not None]
        average_rate = sum(rates) / len(rates) if rates else 0.0

        trend = self._calculate_trend(rates)

        return {
            "website_id": website_id,
            "days": days,
            "average_rate": average_rate,
            "min_rate": min(rates) if rates else 0.0,
            "max_rate": max(rates) if rates else 0.0,
            "trend": trend,
            "rates": [
                {
                    "rate": cr.conversion_rate,
                    "start": cr.time_window_start,
                    "end": cr.time_window_end,
                }
                for cr in conversion_rates
            ],
        }

    def _calculate_trend(self, rates: List[float]) -> str:
        """Calculate trend from rates.

        Args:
            rates: List of conversion rates.

        Returns:
            Trend indicator (increasing, decreasing, stable).
        """
        if len(rates) < 2:
            return "stable"

        mid_point = len(rates) // 2
        first_half_avg = sum(rates[:mid_point]) / len(rates[:mid_point])
        second_half_avg = sum(rates[mid_point:]) / len(rates[mid_point:])

        if second_half_avg > first_half_avg * 1.05:
            return "increasing"
        elif second_half_avg < first_half_avg * 0.95:
            return "decreasing"
        else:
            return "stable"

    def get_conversion_statistics(
        self,
        website_id: int,
        conversion_goal_id: Optional[int] = None,
        days: int = 30,
    ) -> Dict[str, any]:
        """Get comprehensive conversion statistics.

        Args:
            website_id: Website ID.
            conversion_goal_id: Optional conversion goal ID to filter by.
            days: Number of days to analyze.

        Returns:
            Dictionary with conversion statistics.
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        session = self.db_manager.get_session()

        try:
            from src.database import Session

            query = session.query(Session).filter(
                Session.website_id == website_id,
                Session.started_at >= cutoff_time,
            )

            if conversion_goal_id:
                query = query.filter(Session.conversion_goal_id == conversion_goal_id)

            sessions = query.all()

            total_sessions = len(sessions)
            converted_sessions = len([s for s in sessions if s.converted == "true"])

            avg_duration = (
                sum(s.duration_seconds for s in sessions if s.duration_seconds) / total_sessions
                if total_sessions > 0
                else 0.0
            )

            avg_page_views = (
                sum(s.page_views for s in sessions) / total_sessions
                if total_sessions > 0
                else 0.0
            )

            return {
                "website_id": website_id,
                "conversion_goal_id": conversion_goal_id,
                "days": days,
                "total_sessions": total_sessions,
                "converted_sessions": converted_sessions,
                "conversion_rate": (
                    converted_sessions / total_sessions * 100 if total_sessions > 0 else 0.0
                ),
                "average_session_duration": avg_duration,
                "average_page_views": avg_page_views,
            }
        finally:
            session.close()
