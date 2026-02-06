"""Generate reports from pipeline monitoring data."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, Pipeline, PipelineRun, Failure, QualityCheck


class ReportGenerator:
    """Generate HTML and CSV reports from pipeline monitoring data."""

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
        self, pipeline_id: Optional[int] = None
    ) -> Dict[str, Path]:
        """Generate all reports.

        Args:
            pipeline_id: Optional pipeline ID to filter by.

        Returns:
            Dictionary mapping report types to file paths.
        """
        reports = {}

        if self.config.get("generate_html", True):
            html_path = self.generate_html_report(pipeline_id)
            if html_path:
                reports["html"] = html_path

        if self.config.get("generate_csv", True):
            csv_path = self.generate_csv_report(pipeline_id)
            if csv_path:
                reports["csv"] = csv_path

        return reports

    def generate_html_report(
        self, pipeline_id: Optional[int] = None
    ) -> Optional[Path]:
        """Generate HTML report.

        Args:
            pipeline_id: Optional pipeline ID to filter by.

        Returns:
            Path to generated HTML file.
        """
        session = self.db_manager.get_session()
        try:
            pipelines = self.db_manager.get_all_pipelines()
            if pipeline_id:
                pipelines = [p for p in pipelines if p.id == pipeline_id]

            if not pipelines:
                return None

            recent_runs = self.db_manager.get_recent_runs(pipeline_id=pipeline_id, limit=50)
            open_failures = self.db_manager.get_open_failures(pipeline_id=pipeline_id)
            recent_alerts = self.db_manager.get_recent_alerts(pipeline_id=pipeline_id, limit=20)

            stats = self._calculate_statistics(pipelines, recent_runs, open_failures)

            template_path = Path(__file__).parent.parent / "templates" / "pipeline_report.html"
            if template_path.exists():
                with open(template_path, "r") as f:
                    template_content = f.read()
            else:
                template_content = self._get_default_html_template()

            template = Template(template_content)

            html_content = template.render(
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                total_pipelines=len(pipelines),
                stats=stats,
                open_failures=open_failures[:10],
                recent_alerts=recent_alerts[:10],
                recent_runs=recent_runs[:20],
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"pipeline_report_{timestamp}.html"

            with open(output_path, "w") as f:
                f.write(html_content)

            return output_path
        finally:
            session.close()

    def generate_csv_report(
        self, pipeline_id: Optional[int] = None
    ) -> Optional[Path]:
        """Generate CSV report.

        Args:
            pipeline_id: Optional pipeline ID to filter by.

        Returns:
            Path to generated CSV file.
        """
        session = self.db_manager.get_session()
        try:
            pipelines = self.db_manager.get_all_pipelines()
            if pipeline_id:
                pipelines = [p for p in pipelines if p.id == pipeline_id]

            if not pipelines:
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"pipeline_report_{timestamp}.csv"

            with open(output_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Pipeline ID",
                    "Pipeline Name",
                    "Status",
                    "Health Status",
                    "Recent Runs",
                    "Open Failures",
                ])

                for pipeline in pipelines:
                    recent_runs = self.db_manager.get_recent_runs(
                        pipeline_id=pipeline.id, limit=10
                    )
                    open_failures = self.db_manager.get_open_failures(
                        pipeline_id=pipeline.id
                    )

                    writer.writerow([
                        pipeline.id,
                        pipeline.name,
                        pipeline.status,
                        pipeline.health_status,
                        len(recent_runs),
                        len(open_failures),
                    ])

            return output_path
        finally:
            session.close()

    def _calculate_statistics(
        self, pipelines: List[Pipeline], runs: List[PipelineRun], failures: List[Failure]
    ) -> Dict[str, any]:
        """Calculate statistics.

        Args:
            pipelines: List of pipelines.
            runs: List of pipeline runs.
            failures: List of failures.

        Returns:
            Statistics dictionary.
        """
        from collections import Counter

        health_statuses = Counter(p.health_status for p in pipelines if p.health_status)
        run_statuses = Counter(r.status for r in runs if r.status)
        failure_types = Counter(f.failure_type for f in failures if f.failure_type)

        successful_runs = len([r for r in runs if r.status == "success"])
        success_rate = successful_runs / len(runs) if runs else 0.0

        return {
            "total_pipelines": len(pipelines),
            "total_runs": len(runs),
            "successful_runs": successful_runs,
            "failed_runs": len(runs) - successful_runs,
            "success_rate": success_rate,
            "total_failures": len(failures),
            "open_failures": len([f for f in failures if f.resolution_status == "open"]),
            "health_statuses": dict(health_statuses),
            "run_statuses": dict(run_statuses),
            "failure_types": dict(failure_types),
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
    <title>Pipeline Monitoring Report</title>
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
    <h1>Pipeline Monitoring Report</h1>
    <p>Generated at: {{ generated_at }}</p>
    
    <h2>Summary</h2>
    <div class="stat-box">
        <strong>Total Pipelines:</strong> {{ total_pipelines }}
    </div>
    
    <h2>Open Failures</h2>
    <table>
        <tr>
            <th>Pipeline ID</th>
            <th>Failure Type</th>
            <th>Severity</th>
            <th>Detected At</th>
        </tr>
        {% for failure in open_failures %}
        <tr>
            <td>{{ failure.pipeline_id }}</td>
            <td>{{ failure.failure_type }}</td>
            <td>{{ failure.severity }}</td>
            <td>{{ failure.detected_at }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""
