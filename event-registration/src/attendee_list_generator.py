"""Generates attendee lists for events."""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, Registration, Event

logger = logging.getLogger(__name__)


class AttendeeListGenerator:
    """Generates attendee lists in various formats."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        output_dir: str = "reports",
    ) -> None:
        """Initialize attendee list generator.

        Args:
            db_manager: Database manager instance.
            output_dir: Output directory for lists.
        """
        self.db_manager = db_manager
        self.output_dir = Path(output_dir)

    def generate_csv_list(
        self,
        event_id: int,
        include_waitlist: bool = False,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate CSV attendee list.

        Args:
            event_id: Event ID.
            include_waitlist: Whether to include waitlist registrations.
            output_path: Optional output file path.

        Returns:
            Path to generated CSV file.
        """
        if output_path is None:
            event = self.db_manager.get_event(event_id)
            event_name_safe = event.name.replace(" ", "_") if event else f"event_{event_id}"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"attendee_list_{event_name_safe}_{timestamp}.csv"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        registrations = self.db_manager.get_registrations(
            event_id=event_id,
            status="confirmed",
            is_waitlist=False,
        )

        if include_waitlist:
            waitlist_regs = self.db_manager.get_registrations(
                event_id=event_id,
                status="pending",
                is_waitlist=True,
            )
            registrations.extend(waitlist_regs)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "name",
                "email",
                "company",
                "phone",
                "ticket_type",
                "dietary_restrictions",
                "special_requests",
                "status",
                "is_waitlist",
                "waitlist_position",
                "registered_at",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for reg in registrations:
                writer.writerow(
                    {
                        "name": reg.name,
                        "email": reg.email,
                        "company": reg.company or "",
                        "phone": reg.phone or "",
                        "ticket_type": reg.ticket_type or "",
                        "dietary_restrictions": reg.dietary_restrictions or "",
                        "special_requests": reg.special_requests or "",
                        "status": reg.status,
                        "is_waitlist": "Yes" if reg.is_waitlist else "No",
                        "waitlist_position": reg.waitlist_position or "",
                        "registered_at": reg.registered_at.isoformat() if reg.registered_at else "",
                    }
                )

        logger.info(
            f"Generated CSV attendee list: {output_path}",
            extra={"event_id": event_id, "output_path": str(output_path)},
        )

        return output_path

    def generate_html_list(
        self,
        event_id: int,
        include_waitlist: bool = False,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate HTML attendee list.

        Args:
            event_id: Event ID.
            include_waitlist: Whether to include waitlist registrations.
            output_path: Optional output file path.

        Returns:
            Path to generated HTML file.
        """
        if output_path is None:
            event = self.db_manager.get_event(event_id)
            event_name_safe = event.name.replace(" ", "_") if event else f"event_{event_id}"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"attendee_list_{event_name_safe}_{timestamp}.html"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        event = self.db_manager.get_event(event_id)

        registrations = self.db_manager.get_registrations(
            event_id=event_id,
            status="confirmed",
            is_waitlist=False,
        )

        waitlist_regs = []
        if include_waitlist:
            waitlist_regs = self.db_manager.get_registrations(
                event_id=event_id,
                status="pending",
                is_waitlist=True,
            )

        template_path = Path(__file__).parent.parent / "templates" / "attendee_list.html"
        if not template_path.exists():
            html_content = self._get_default_html_template()
        else:
            with open(template_path, "r") as f:
                html_content = f.read()

        template = Template(html_content)

        report_data = {
            "event_name": event.name if event else f"Event {event_id}",
            "event_date": event.event_date.strftime("%Y-%m-%d %H:%M") if event and event.event_date else "",
            "event_location": event.location if event else "",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "attendees": [
                {
                    "name": reg.name,
                    "email": reg.email,
                    "company": reg.company or "",
                    "phone": reg.phone or "",
                    "ticket_type": reg.ticket_type or "",
                }
                for reg in registrations
            ],
            "waitlist": [
                {
                    "name": reg.name,
                    "email": reg.email,
                    "company": reg.company or "",
                    "position": reg.waitlist_position or 0,
                }
                for reg in waitlist_regs
            ],
            "total_attendees": len(registrations),
            "total_waitlist": len(waitlist_regs),
        }

        rendered_html = template.render(**report_data)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        logger.info(
            f"Generated HTML attendee list: {output_path}",
            extra={"event_id": event_id, "output_path": str(output_path)},
        )

        return output_path

    def _get_default_html_template(self) -> str:
        """Get default HTML template for attendee lists.

        Returns:
            HTML template string.
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Attendee List - {{ event_name }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: #667eea;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #f5f5f5;
            font-weight: bold;
        }
        .waitlist {
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ event_name }}</h1>
        <p>Date: {{ event_date }} | Location: {{ event_location }}</p>
        <p>Generated: {{ generated_at }}</p>
    </div>

    <h2>Confirmed Attendees ({{ total_attendees }})</h2>
    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Company</th>
                <th>Phone</th>
                <th>Ticket Type</th>
            </tr>
        </thead>
        <tbody>
            {% for attendee in attendees %}
            <tr>
                <td>{{ attendee.name }}</td>
                <td>{{ attendee.email }}</td>
                <td>{{ attendee.company }}</td>
                <td>{{ attendee.phone }}</td>
                <td>{{ attendee.ticket_type }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    {% if waitlist %}
    <div class="waitlist">
        <h2>Waitlist ({{ total_waitlist }})</h2>
        <table>
            <thead>
                <tr>
                    <th>Position</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Company</th>
                </tr>
            </thead>
            <tbody>
                {% for person in waitlist %}
                <tr>
                    <td>{{ person.position }}</td>
                    <td>{{ person.name }}</td>
                    <td>{{ person.email }}</td>
                    <td>{{ person.company }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endif %}
</body>
</html>"""
