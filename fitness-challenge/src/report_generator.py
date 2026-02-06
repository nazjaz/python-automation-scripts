"""Generate reports from fitness challenge data."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, Participant, Challenge, Goal


class ReportGenerator:
    """Generate HTML and CSV reports from fitness challenge data."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize report generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.output_dir = Path(config.get("output_directory", "reports"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_reports(
        self, participant_id: Optional[int] = None, challenge_id: Optional[int] = None
    ) -> Dict[str, Path]:
        """Generate all reports.

        Args:
            participant_id: Optional participant ID to filter by.
            challenge_id: Optional challenge ID to filter by.

        Returns:
            Dictionary mapping report types to file paths.
        """
        reports = {}

        if self.config.get("generate_html", True):
            html_path = self.generate_html_report(participant_id, challenge_id)
            if html_path:
                reports["html"] = html_path

        if self.config.get("generate_csv", True):
            csv_path = self.generate_csv_report(participant_id, challenge_id)
            if csv_path:
                reports["csv"] = csv_path

        return reports

    def generate_html_report(
        self, participant_id: Optional[int] = None, challenge_id: Optional[int] = None
    ) -> Optional[Path]:
        """Generate HTML report.

        Args:
            participant_id: Optional participant ID to filter by.
            challenge_id: Optional challenge ID to filter by.

        Returns:
            Path to generated HTML file.
        """
        session = self.db_manager.get_session()
        try:
            participants = self.db_manager.get_all_participants()
            if participant_id:
                participants = [p for p in participants if p.id == participant_id]

            challenges = self.db_manager.get_active_challenges()
            if challenge_id:
                challenges = [c for c in challenges if c.id == challenge_id]

            goals = self.db_manager.get_active_goals()
            if participant_id:
                goals = [g for g in goals if g.participant_id == participant_id]

            leaderboard = self.db_manager.get_leaderboard(challenge_id=challenge_id, limit=10)

            stats = self._calculate_statistics(participants, challenges, goals)

            template_path = Path(__file__).parent.parent / "templates" / "fitness_report.html"
            if template_path.exists():
                with open(template_path, "r") as f:
                    template_content = f.read()
            else:
                template_content = self._get_default_html_template()

            template = Template(template_content)

            html_content = template.render(
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                total_participants=len(participants),
                total_challenges=len(challenges),
                total_goals=len(goals),
                stats=stats,
                top_leaderboard=leaderboard[:10],
                recent_challenges=challenges[:10],
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"fitness_report_{timestamp}.html"

            with open(output_path, "w") as f:
                f.write(html_content)

            return output_path
        finally:
            session.close()

    def generate_csv_report(
        self, participant_id: Optional[int] = None, challenge_id: Optional[int] = None
    ) -> Optional[Path]:
        """Generate CSV report.

        Args:
            participant_id: Optional participant ID to filter by.
            challenge_id: Optional challenge ID to filter by.

        Returns:
            Path to generated CSV file.
        """
        session = self.db_manager.get_session()
        try:
            participants = self.db_manager.get_all_participants()
            if participant_id:
                participants = [p for p in participants if p.id == participant_id]

            if not participants:
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"fitness_report_{timestamp}.csv"

            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Participant ID",
                    "Name",
                    "Email",
                    "Fitness Level",
                    "Active Challenges",
                    "Active Goals",
                    "Total Progress (7 days)",
                ])

                for participant in participants:
                    challenges = self.db_manager.get_active_challenges(
                        participant_id=participant.id
                    )
                    goals = self.db_manager.get_active_goals(participant_id=participant.id)
                    progress_entries = self.db_manager.get_progress_entries(
                        participant_id=participant.id, days=7
                    )
                    total_progress = sum(pe.value for pe in progress_entries)

                    writer.writerow([
                        participant.id,
                        participant.name,
                        participant.email,
                        participant.fitness_level or "N/A",
                        len(challenges),
                        len(goals),
                        total_progress,
                    ])

            return output_path
        finally:
            session.close()

    def _calculate_statistics(
        self, participants: List[Participant], challenges: List[Challenge], goals: List[Goal]
    ) -> Dict[str, any]:
        """Calculate statistics.

        Args:
            participants: List of participants.
            challenges: List of challenges.
            goals: List of goals.

        Returns:
            Statistics dictionary.
        """
        from collections import Counter

        fitness_levels = Counter(p.fitness_level for p in participants if p.fitness_level)
        challenge_types = Counter(c.challenge_type for c in challenges if c.challenge_type)
        goal_types = Counter(g.goal_type for g in goals if g.goal_type)

        completed_goals = len([g for g in goals if g.status == "completed"])

        return {
            "total_participants": len(participants),
            "total_challenges": len(challenges),
            "total_goals": len(goals),
            "completed_goals": completed_goals,
            "fitness_levels": dict(fitness_levels),
            "challenge_types": dict(challenge_types),
            "goal_types": dict(goal_types),
        }

    def _get_default_html_template(self) -> str:
        """Get default HTML template.

        Returns:
            Default HTML template string.
        """
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Fitness Challenge Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1, h2 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        .stat-box { display: inline-block; margin: 10px; padding: 15px; background: #f0f0f0; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Fitness Challenge Report</h1>
    <p>Generated at: {{ generated_at }}</p>
    
    <h2>Summary</h2>
    <div class="stat-box">
        <strong>Total Participants:</strong> {{ total_participants }}
    </div>
    <div class="stat-box">
        <strong>Active Challenges:</strong> {{ total_challenges }}
    </div>
    <div class="stat-box">
        <strong>Active Goals:</strong> {{ total_goals }}
    </div>
    
    <h2>Top Leaderboard</h2>
    <table>
        <tr>
            <th>Rank</th>
            <th>Participant</th>
            <th>Score</th>
        </tr>
        {% for entry in top_leaderboard %}
        <tr>
            <td>{{ entry.rank }}</td>
            <td>{{ entry.participant.name if entry.participant else 'N/A' }}</td>
            <td>{{ entry.score }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""
