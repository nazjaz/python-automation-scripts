"""Generates cloud resource monitoring reports."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates cloud resource monitoring reports in various formats."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
        output_dir: str = "reports",
    ) -> None:
        """Initialize report generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
            output_dir: Output directory for reports.
        """
        self.db_manager = db_manager
        self.config = config
        self.reporting_config = config.get("reporting", {})
        self.output_dir = Path(output_dir)

    def generate_html_report(
        self,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate HTML resource monitoring report.

        Args:
            output_path: Optional output file path.

        Returns:
            Path to generated HTML report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resource_report_{timestamp}.html"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        from src.idle_detector import IdleDetector
        from src.right_sizing_analyzer import RightSizingAnalyzer
        from src.database import CloudResource, IdleResource

        detector = IdleDetector(self.db_manager, self.config)
        analyzer = RightSizingAnalyzer(self.db_manager, self.config)

        resources = self.db_manager.get_resources(state="running")
        idle_resources = detector.detect_idle_resources()
        recommendations = self.db_manager.get_unimplemented_recommendations(limit=20)

        report_data = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_resources": len(resources),
            "idle_resources": [
                {
                    "resource_id": ir.resource_id,
                    "idle_duration_hours": ir.idle_duration_hours,
                    "idle_since": ir.idle_since.strftime("%Y-%m-%d %H:%M:%S") if ir.idle_since else "",
                }
                for ir in idle_resources[:10]
            ],
            "recommendations": [
                {
                    "resource_id": r.resource_id,
                    "recommendation_type": r.recommendation_type,
                    "current_instance_type": r.current_instance_type,
                    "recommended_instance_type": r.recommended_instance_type,
                    "estimated_cost_savings": r.estimated_cost_savings,
                    "priority": r.priority,
                }
                for r in recommendations
            ],
        }

        template_path = Path(__file__).parent.parent / "templates" / "resource_report.html"
        if not template_path.exists():
            html_content = self._get_default_html_template()
        else:
            with open(template_path, "r") as f:
                html_content = f.read()

        template = Template(html_content)
        rendered_html = template.render(**report_data)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        logger.info(
            f"Generated HTML report: {output_path}",
            extra={"output_path": str(output_path)},
        )

        return output_path

    def _get_default_html_template(self) -> str:
        """Get default HTML template for reports.

        Returns:
            HTML template string.
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Cloud Resource Report</title>
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
    </style>
</head>
<body>
    <div class="header">
        <h1>Cloud Resource Report</h1>
        <p>Generated: {{ generated_at }}</p>
    </div>

    <h2>Summary</h2>
    <p>Total Resources: {{ total_resources }}</p>
    <p>Idle Resources: {{ idle_resources|length }}</p>
    <p>Recommendations: {{ recommendations|length }}</p>
</body>
</html>"""
