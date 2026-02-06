"""Track user journeys through website."""

from collections import Counter
from typing import Dict, List, Optional

from src.database import DatabaseManager


class JourneyTracker:
    """Track user journeys through website."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize journey tracker.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def track_journey(self, session_id: int) -> Dict[str, any]:
        """Track user journey for a session.

        Args:
            session_id: Session ID.

        Returns:
            Dictionary with journey information.
        """
        session = self.db_manager.get_session()
        try:
            from src.database import Session, Event

            db_session = session.query(Session).filter(Session.id == session_id).first()
            if not db_session:
                return {}

            events = (
                session.query(Event)
                .filter(Event.session_id == session_id)
                .order_by(Event.timestamp.asc())
                .all()
            )

            journey_steps = []
            for event in events:
                step = {
                    "step_order": len(journey_steps) + 1,
                    "event_type": event.event_type,
                    "event_name": event.event_name,
                    "page_url": event.page_url,
                    "page_title": event.page_title,
                    "timestamp": event.timestamp,
                }
                journey_steps.append(step)

            return {
                "session_id": session_id,
                "website_id": db_session.website_id,
                "user_id": db_session.user_id,
                "started_at": db_session.started_at,
                "ended_at": db_session.ended_at,
                "converted": db_session.converted == "true",
                "total_steps": len(journey_steps),
                "journey_steps": journey_steps,
            }
        finally:
            session.close()

    def get_common_journeys(
        self, website_id: int, limit: int = 10
    ) -> List[Dict[str, any]]:
        """Get most common user journeys.

        Args:
            website_id: Website ID.
            limit: Maximum number of journeys to return.

        Returns:
            List of common journey dictionaries.
        """
        sessions = self.db_manager.get_recent_sessions(website_id=website_id, limit=1000)

        journey_patterns = {}
        for db_session in sessions:
            journey = self.track_journey(db_session.id)
            if journey and journey.get("journey_steps"):
                pattern = self._create_journey_pattern(journey["journey_steps"])
                if pattern not in journey_patterns:
                    journey_patterns[pattern] = {
                        "pattern": pattern,
                        "count": 0,
                        "conversion_count": 0,
                        "sample_journey": journey,
                    }
                journey_patterns[pattern]["count"] += 1
                if journey.get("converted"):
                    journey_patterns[pattern]["conversion_count"] += 1

        sorted_patterns = sorted(
            journey_patterns.values(), key=lambda x: x["count"], reverse=True
        )

        return sorted_patterns[:limit]

    def _create_journey_pattern(self, journey_steps: List[Dict]) -> str:
        """Create journey pattern string.

        Args:
            journey_steps: List of journey step dictionaries.

        Returns:
            Journey pattern string.
        """
        pattern_parts = []
        for step in journey_steps[:10]:
            if step.get("page_url"):
                url_parts = step["page_url"].split("/")
                page_name = url_parts[-1] if url_parts else "home"
                pattern_parts.append(page_name)
            elif step.get("event_name"):
                pattern_parts.append(step["event_name"])
            else:
                pattern_parts.append(step.get("event_type", "unknown"))

        return " -> ".join(pattern_parts)

    def get_journey_statistics(
        self, website_id: int, days: int = 7
    ) -> Dict[str, any]:
        """Get journey statistics.

        Args:
            website_id: Website ID.
            days: Number of days to analyze.

        Returns:
            Dictionary with journey statistics.
        """
        from datetime import timedelta

        sessions = self.db_manager.get_recent_sessions(
            website_id=website_id, hours=days * 24
        )

        total_journeys = len(sessions)
        converted_journeys = len([s for s in sessions if s.converted == "true"])

        journey_lengths = []
        for session in sessions:
            events = self.db_manager.get_session_events(session.id)
            journey_lengths.append(len(events))

        avg_journey_length = (
            sum(journey_lengths) / len(journey_lengths) if journey_lengths else 0.0
        )

        return {
            "website_id": website_id,
            "days": days,
            "total_journeys": total_journeys,
            "converted_journeys": converted_journeys,
            "average_journey_length": avg_journey_length,
            "min_journey_length": min(journey_lengths) if journey_lengths else 0,
            "max_journey_length": max(journey_lengths) if journey_lengths else 0,
        }

    def define_journey_steps(
        self, website_id: int, steps: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """Define journey steps for website.

        Args:
            website_id: Website ID.
            steps: List of step dictionaries with name, order, page_url, event_type.

        Returns:
            List of created journey step dictionaries.
        """
        created_steps = []
        for step in steps:
            journey_step = self.db_manager.add_journey_step(
                website_id=website_id,
                step_name=step.get("name", ""),
                step_order=step.get("order", 0),
                page_url=step.get("page_url"),
                event_type=step.get("event_type"),
            )
            created_steps.append({
                "id": journey_step.id,
                "step_name": journey_step.step_name,
                "step_order": journey_step.step_order,
            })

        return created_steps
