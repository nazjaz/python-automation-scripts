"""Generates name badges for event attendees."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, Registration, Event

logger = logging.getLogger(__name__)


class BadgeGenerator:
    """Generates name badges for event attendees."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize badge generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.badge_config = config.get("badges", {})
        self.output_dir = Path(self.badge_config.get("output_directory", "badges"))
        self.template_path = Path(self.badge_config.get("template", "templates/badge_template.html"))

    def generate_badge(
        self, registration_id: int
    ) -> Optional[Path]:
        """Generate badge for a registration.

        Args:
            registration_id: Registration ID.

        Returns:
            Path to generated badge file or None if error.
        """
        registration = (
            self.db_manager.get_session()
            .query(Registration)
            .filter(Registration.id == registration_id)
            .first()
        )

        if not registration:
            logger.error(
                f"Registration {registration_id} not found",
                extra={"registration_id": registration_id},
            )
            return None

        if registration.status != "confirmed":
            logger.warning(
                f"Registration {registration_id} is not confirmed",
                extra={"registration_id": registration_id, "status": registration.status},
            )
            return None

        event = self.db_manager.get_event(registration.event_id)

        if not event:
            return None

        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.template_path.is_absolute():
            template_path = Path(__file__).parent.parent / self.template_path
        else:
            template_path = self.template_path

        try:
            if template_path.exists():
                with open(template_path, "r") as f:
                    template_content = f.read()
            else:
                template_content = self._get_default_badge_template()

            template = Template(template_content)

            badge_data = {
                "name": registration.name,
                "company": registration.company or "",
                "ticket_type": registration.ticket_type or "",
                "event_name": event.name,
                "event_date": event.event_date.strftime("%Y-%m-%d") if event.event_date else "",
                "registration_id": registration.id,
            }

            html_content = template.render(**badge_data)

            badge_filename = f"badge_{registration_id}_{registration.name.replace(' ', '_')}.html"
            badge_path = self.output_dir / badge_filename

            with open(badge_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            registration.badge_generated = True
            session = self.db_manager.get_session()
            try:
                session.merge(registration)
                session.commit()
            finally:
                session.close()

            logger.info(
                f"Badge generated for registration {registration_id}",
                extra={"registration_id": registration_id, "badge_path": str(badge_path)},
            )

            return badge_path

        except Exception as e:
            logger.error(
                f"Error generating badge: {e}",
                extra={"registration_id": registration_id, "error": str(e)},
            )
            return None

    def generate_badges_for_event(
        self, event_id: int, only_confirmed: bool = True
    ) -> List[Path]:
        """Generate badges for all registrations in an event.

        Args:
            event_id: Event ID.
            only_confirmed: Whether to generate only for confirmed registrations.

        Returns:
            List of generated badge file paths.
        """
        status_filter = "confirmed" if only_confirmed else None

        registrations = self.db_manager.get_registrations(
            event_id=event_id,
            status=status_filter,
            is_waitlist=False,
        )

        generated_badges = []

        for registration in registrations:
            badge_path = self.generate_badge(registration.id)
            if badge_path:
                generated_badges.append(badge_path)

        logger.info(
            f"Generated {len(generated_badges)} badges for event {event_id}",
            extra={"event_id": event_id, "badge_count": len(generated_badges)},
        )

        return generated_badges

    def _get_default_badge_template(self) -> str:
        """Get default badge template.

        Returns:
            HTML template string.
        """
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @media print {
            @page { size: 3.375in 2.125in; margin: 0; }
            body { margin: 0; }
        }
        body {
            font-family: Arial, sans-serif;
            width: 3.375in;
            height: 2.125in;
            margin: 0;
            padding: 15px;
            box-sizing: border-box;
            border: 2px solid #667eea;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
        }
        .name {
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }
        .company {
            font-size: 16px;
            color: #666;
            margin-bottom: 5px;
        }
        .ticket-type {
            font-size: 12px;
            color: #667eea;
            font-weight: bold;
            margin-top: 5px;
        }
        .event-name {
            font-size: 10px;
            color: #999;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="name">{{ name }}</div>
    {% if company %}
    <div class="company">{{ company }}</div>
    {% endif %}
    {% if ticket_type %}
    <div class="ticket-type">{{ ticket_type }}</div>
    {% endif %}
    <div class="event-name">{{ event_name }}</div>
</body>
</html>"""
