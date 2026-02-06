"""Identify drop-off points in user journeys."""

from typing import Dict, List, Optional

from src.database import DatabaseManager


class DropOffIdentifier:
    """Identify drop-off points in user journeys."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize drop-off identifier.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.min_dropoff_rate = config.get("min_dropoff_rate", 0.1)

    def identify_dropoffs(
        self, website_id: int, conversion_goal_id: Optional[int] = None
    ) -> List[Dict[str, any]]:
        """Identify drop-off points in user journeys.

        Args:
            website_id: Website ID.
            conversion_goal_id: Optional conversion goal ID to filter by.

        Returns:
            List of drop-off point dictionaries.
        """
        journey_steps = self.db_manager.get_journey_steps(website_id)
        sessions = self.db_manager.get_recent_sessions(website_id=website_id, limit=1000)

        if conversion_goal_id:
            sessions = [s for s in sessions if s.conversion_goal_id == conversion_goal_id]

        if not journey_steps:
            dropoffs = self._identify_dropoffs_from_events(website_id, sessions)
        else:
            dropoffs = self._identify_dropoffs_from_steps(website_id, journey_steps, sessions)

        for dropoff in dropoffs:
            if dropoff["dropoff_rate"] >= self.min_dropoff_rate:
                self.db_manager.add_dropoff_point(
                    website_id=website_id,
                    dropoff_rate=dropoff["dropoff_rate"],
                    sessions_entered=dropoff["sessions_entered"],
                    sessions_exited=dropoff["sessions_exited"],
                    journey_step_id=dropoff.get("journey_step_id"),
                )

        return dropoffs

    def _identify_dropoffs_from_steps(
        self, website_id: int, journey_steps: List, sessions: List
    ) -> List[Dict[str, any]]:
        """Identify drop-offs using defined journey steps.

        Args:
            website_id: Website ID.
            journey_steps: List of journey step objects.
            sessions: List of session objects.

        Returns:
            List of drop-off dictionaries.
        """
        dropoffs = []

        for i, step in enumerate(journey_steps):
            sessions_reached = 0
            sessions_exited = 0

            for session in sessions:
                events = self.db_manager.get_session_events(session.id)
                reached_step = False

                for event in events:
                    if step.page_url and event.page_url:
                        if step.page_url in event.page_url:
                            reached_step = True
                            break
                    elif step.event_type and event.event_type:
                        if step.event_type == event.event_type:
                            reached_step = True
                            break

                if reached_step:
                    sessions_reached += 1

                    if i < len(journey_steps) - 1:
                        next_step = journey_steps[i + 1]
                        reached_next = False

                        for event in events:
                            if next_step.page_url and event.page_url:
                                if next_step.page_url in event.page_url:
                                    reached_next = True
                                    break
                            elif next_step.event_type and event.event_type:
                                if next_step.event_type == event.event_type:
                                    reached_next = True
                                    break

                        if not reached_next:
                            sessions_exited += 1

            if sessions_reached > 0:
                dropoff_rate = sessions_exited / sessions_reached
                dropoffs.append({
                    "journey_step_id": step.id,
                    "step_name": step.step_name,
                    "dropoff_rate": dropoff_rate,
                    "sessions_entered": sessions_reached,
                    "sessions_exited": sessions_exited,
                })

        return dropoffs

    def _identify_dropoffs_from_events(
        self, website_id: int, sessions: List
    ) -> List[Dict[str, any]]:
        """Identify drop-offs by analyzing event patterns.

        Args:
            website_id: Website ID.
            sessions: List of session objects.

        Returns:
            List of drop-off dictionaries.
        """
        dropoffs = []

        page_visits = {}
        for session in sessions:
            events = self.db_manager.get_session_events(session.id)
            pages_visited = set()

            for event in events:
                if event.page_url:
                    pages_visited.add(event.page_url)

            for page_url in pages_visited:
                if page_url not in page_visits:
                    page_visits[page_url] = {"entered": 0, "exited": 0}
                page_visits[page_url]["entered"] += 1

            if len(events) > 0:
                last_event = events[-1]
                if last_event.page_url:
                    page_visits[last_event.page_url]["exited"] += 1

        for page_url, stats in page_visits.items():
            if stats["entered"] > 0:
                dropoff_rate = stats["exited"] / stats["entered"]
                if dropoff_rate >= self.min_dropoff_rate:
                    dropoffs.append({
                        "page_url": page_url,
                        "dropoff_rate": dropoff_rate,
                        "sessions_entered": stats["entered"],
                        "sessions_exited": stats["exited"],
                    })

        return sorted(dropoffs, key=lambda x: x["dropoff_rate"], reverse=True)

    def get_dropoff_statistics(
        self, website_id: int
    ) -> Dict[str, any]:
        """Get drop-off statistics.

        Args:
            website_id: Website ID.

        Returns:
            Dictionary with drop-off statistics.
        """
        dropoffs = self.db_manager.get_dropoff_points(website_id=website_id)

        if not dropoffs:
            return {
                "total_dropoff_points": 0,
                "average_dropoff_rate": 0.0,
                "highest_dropoff_rate": 0.0,
            }

        dropoff_rates = [d.dropoff_rate for d in dropoffs if d.dropoff_rate is not None]

        return {
            "total_dropoff_points": len(dropoffs),
            "average_dropoff_rate": (
                sum(dropoff_rates) / len(dropoff_rates) if dropoff_rates else 0.0
            ),
            "highest_dropoff_rate": max(dropoff_rates) if dropoff_rates else 0.0,
            "total_sessions_affected": sum(d.sessions_exited for d in dropoffs),
        }
