"""Generates study schedule reports."""

import csv
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, StudySession, Course, Exam

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates study schedule reports in various formats."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        output_dir: str = "reports",
    ) -> None:
        """Initialize report generator.

        Args:
            db_manager: Database manager instance.
            output_dir: Output directory for reports.
        """
        self.db_manager = db_manager
        self.output_dir = Path(output_dir)

    def generate_html_schedule(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        course_id: Optional[int] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate HTML study schedule report.

        Args:
            start_date: Optional start date filter.
            end_date: Optional end date filter.
            course_id: Optional course ID filter.
            output_path: Optional output file path.

        Returns:
            Path to generated HTML report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            course_suffix = f"_{course_id}" if course_id else ""
            filename = f"study_schedule{course_suffix}_{timestamp}.html"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = start_date + timedelta(days=30)

        sessions = self.db_manager.get_study_sessions(
            course_id=course_id, start_date=start_date, end_date=end_date
        )

        courses = self.db_manager.get_courses()
        exams = self.db_manager.get_exams(upcoming_only=True)

        from src.progress_tracker import ProgressTracker

        tracker = ProgressTracker(self.db_manager, {})

        schedule_data = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sessions": [],
            "courses": [{"id": c.id, "name": c.name, "code": c.code} for c in courses],
            "exams": [
                {
                    "name": e.name,
                    "course_name": next((c.name for c in courses if c.id == e.course_id), ""),
                    "exam_date": e.exam_date.isoformat(),
                    "days_until": (e.exam_date - date.today()).days,
                }
                for e in exams
            ],
            "weekly_progress": tracker.get_weekly_progress(course_id=course_id),
        }

        for session in sessions:
            course = next((c for c in courses if c.id == session.course_id), None)
            schedule_data["sessions"].append(
                {
                    "date": session.session_date.isoformat(),
                    "course_name": course.name if course else f"Course {session.course_id}",
                    "start_time": session.start_time or "",
                    "end_time": session.end_time or "",
                    "duration_minutes": session.duration_minutes or 0,
                    "topics": session.topics_covered or "",
                    "status": session.completion_status,
                }
            )

        template_path = Path(__file__).parent.parent / "templates" / "study_schedule.html"
        if not template_path.exists():
            html_content = self._get_default_html_template()
        else:
            with open(template_path, "r") as f:
                html_content = f.read()

        template = Template(html_content)
        rendered_html = template.render(**schedule_data)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        logger.info(
            f"Generated HTML schedule: {output_path}",
            extra={"output_path": str(output_path), "course_id": course_id},
        )

        return output_path

    def generate_csv_schedule(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        course_id: Optional[int] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate CSV study schedule report.

        Args:
            start_date: Optional start date filter.
            end_date: Optional end date filter.
            course_id: Optional course ID filter.
            output_path: Optional output file path.

        Returns:
            Path to generated CSV report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            course_suffix = f"_{course_id}" if course_id else ""
            filename = f"study_schedule{course_suffix}_{timestamp}.csv"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = start_date + timedelta(days=30)

        sessions = self.db_manager.get_study_sessions(
            course_id=course_id, start_date=start_date, end_date=end_date
        )

        courses = self.db_manager.get_courses()

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "date",
                "course_name",
                "course_code",
                "start_time",
                "end_time",
                "duration_minutes",
                "topics_covered",
                "completion_status",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for session in sessions:
                course = next((c for c in courses if c.id == session.course_id), None)
                writer.writerow(
                    {
                        "date": session.session_date.isoformat(),
                        "course_name": course.name if course else "",
                        "course_code": course.code if course else "",
                        "start_time": session.start_time or "",
                        "end_time": session.end_time or "",
                        "duration_minutes": session.duration_minutes or 0,
                        "topics_covered": session.topics_covered or "",
                        "completion_status": session.completion_status,
                    }
                )

        logger.info(
            f"Generated CSV schedule: {output_path}",
            extra={"output_path": str(output_path), "course_id": course_id},
        )

        return output_path

    def _get_default_html_template(self) -> str:
        """Get default HTML template for schedules.

        Returns:
            HTML template string.
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Study Schedule</title>
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
        }
        .status-completed {
            color: #28a745;
        }
        .status-partial {
            color: #ffc107;
        }
        .status-incomplete {
            color: #dc3545;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Study Schedule</h1>
        <p>Period: {{ start_date }} to {{ end_date }}</p>
        <p>Generated: {{ generated_at }}</p>
    </div>

    <h2>Upcoming Exams</h2>
    <table>
        <thead>
            <tr>
                <th>Exam</th>
                <th>Course</th>
                <th>Date</th>
                <th>Days Until</th>
            </tr>
        </thead>
        <tbody>
            {% for exam in exams %}
            <tr>
                <td>{{ exam.name }}</td>
                <td>{{ exam.course_name }}</td>
                <td>{{ exam.exam_date }}</td>
                <td>{{ exam.days_until }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <h2>Study Sessions</h2>
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Course</th>
                <th>Time</th>
                <th>Duration</th>
                <th>Topics</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for session in sessions %}
            <tr>
                <td>{{ session.date }}</td>
                <td>{{ session.course_name }}</td>
                <td>{{ session.start_time }} - {{ session.end_time }}</td>
                <td>{{ session.duration_minutes }} min</td>
                <td>{{ session.topics }}</td>
                <td class="status-{{ session.status }}">{{ session.status }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>"""
