"""Process user events and sessions."""

from datetime import datetime
from typing import Dict, List, Optional

from src.database import DatabaseManager


class EventProcessor:
    """Process user events and sessions."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize event processor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def process_event(
        self,
        website_id: int,
        session_id: str,
        event_type: str,
        timestamp: datetime,
        event_name: Optional[str] = None,
        page_url: Optional[str] = None,
        page_title: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, any]:
        """Process a user event.

        Args:
            website_id: Website ID.
            session_id: Session identifier.
            event_type: Event type (pageview, click, form_submit, etc.).
            timestamp: Event timestamp.
            event_name: Event name.
            page_url: Page URL.
            page_title: Page title.
            user_id: User identifier.
            metadata: Additional metadata dictionary.

        Returns:
            Dictionary with event processing results.
        """
        session = self.db_manager.get_session(session_id)

        if not session:
            session = self.db_manager.add_session(
                website_id=website_id,
                session_id=session_id,
                started_at=timestamp,
                user_id=user_id,
            )

        metadata_str = None
        if metadata:
            import json

            metadata_str = json.dumps(metadata)

        event = self.db_manager.add_event(
            session_id=session.id,
            event_type=event_type,
            timestamp=timestamp,
            event_name=event_name,
            page_url=page_url,
            page_title=page_title,
            metadata=metadata_str,
        )

        self._check_conversion(session, event)

        return {
            "success": True,
            "event_id": event.id,
            "session_id": session.id,
        }

    def _check_conversion(self, session, event) -> None:
        """Check if event indicates conversion.

        Args:
            session: Session object.
            event: Event object.
        """
        goals = self.db_manager.get_website_goals(session.website_id)

        for goal in goals:
            if goal.target_url and event.page_url:
                if goal.target_url in event.page_url:
                    self.db_manager.update_session(
                        session.session_id,
                        converted="true",
                        conversion_goal_id=goal.id,
                    )
                    break
            elif goal.target_event and event.event_name:
                if goal.target_event == event.event_name:
                    self.db_manager.update_session(
                        session.session_id,
                        converted="true",
                        conversion_goal_id=goal.id,
                    )
                    break

    def end_session(
        self, session_id: str, ended_at: Optional[datetime] = None
    ) -> Dict[str, any]:
        """End a session.

        Args:
            session_id: Session identifier.
            ended_at: Session end time.

        Returns:
            Dictionary with session end results.
        """
        if ended_at is None:
            ended_at = datetime.utcnow()

        self.db_manager.update_session(session_id, ended_at=ended_at)

        return {"success": True, "session_id": session_id}

    def import_events_from_file(
        self, website_id: int, file_path: str, file_format: str = "json"
    ) -> Dict[str, any]:
        """Import events from file.

        Args:
            website_id: Website ID.
            file_path: Path to events file.
            file_format: File format (json or csv).

        Returns:
            Dictionary with import results.
        """
        from pathlib import Path

        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"Events file not found: {file_path}")

        imported_count = 0

        if file_format.lower() == "json":
            imported_count = self._import_events_from_json(website_id, file_path_obj)
        else:
            imported_count = self._import_events_from_csv(website_id, file_path_obj)

        return {
            "success": True,
            "imported_count": imported_count,
            "file_path": file_path,
        }

    def _import_events_from_json(
        self, website_id: int, file_path: Path
    ) -> int:
        """Import events from JSON file.

        Args:
            website_id: Website ID.
            file_path: Path to JSON file.

        Returns:
            Number of events imported.
        """
        import json

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            events_data = data
        elif isinstance(data, dict) and "events" in data:
            events_data = data["events"]
        else:
            events_data = [data]

        imported_count = 0
        for event_data in events_data:
            try:
                session_id = event_data.get("session_id", "")
                event_type = event_data.get("event_type", "pageview")
                timestamp_str = event_data.get("timestamp", "")
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

                result = self.process_event(
                    website_id=website_id,
                    session_id=session_id,
                    event_type=event_type,
                    timestamp=timestamp,
                    event_name=event_data.get("event_name"),
                    page_url=event_data.get("page_url"),
                    page_title=event_data.get("page_title"),
                    user_id=event_data.get("user_id"),
                    metadata=event_data.get("metadata"),
                )
                if result.get("success"):
                    imported_count += 1
            except Exception:
                continue

        return imported_count

    def _import_events_from_csv(self, website_id: int, file_path: Path) -> int:
        """Import events from CSV file.

        Args:
            website_id: Website ID.
            file_path: Path to CSV file.

        Returns:
            Number of events imported.
        """
        import csv

        imported_count = 0

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    session_id = row.get("session_id", "")
                    event_type = row.get("event_type", "pageview")
                    timestamp_str = row.get("timestamp", "")
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

                    result = self.process_event(
                        website_id=website_id,
                        session_id=session_id,
                        event_type=event_type,
                        timestamp=timestamp,
                        event_name=row.get("event_name"),
                        page_url=row.get("page_url"),
                        page_title=row.get("page_title"),
                        user_id=row.get("user_id"),
                    )
                    if result.get("success"):
                        imported_count += 1
                except Exception:
                    continue

        return imported_count
