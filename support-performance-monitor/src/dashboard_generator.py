"""Generates performance dashboards for management."""

import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """Generates performance dashboards in various formats."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
        output_dir: str = "dashboards",
    ) -> None:
        """Initialize dashboard generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
            output_dir: Output directory for dashboards.
        """
        self.db_manager = db_manager
        self.config = config
        self.dashboard_config = config.get("dashboard", {})
        self.output_dir = Path(output_dir)

    def generate_html_dashboard(
        self,
        days: int = 30,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate HTML performance dashboard.

        Args:
            days: Number of days to analyze.
            output_path: Optional output file path.

        Returns:
            Path to generated HTML dashboard.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"support_dashboard_{days}days_{timestamp}.html"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        from src.response_time_tracker import ResponseTimeTracker
        from src.resolution_rate_analyzer import ResolutionRateAnalyzer
        from src.bottleneck_identifier import BottleneckIdentifier

        response_tracker = ResponseTimeTracker(self.db_manager, self.config)
        analyzer = ResolutionRateAnalyzer(self.db_manager, self.config)
        bottleneck_id = BottleneckIdentifier(self.db_manager, self.config)

        overall_resolution = analyzer.calculate_resolution_rate(days=days)
        overall_response_time = response_tracker.get_average_response_time(days=days)
        overall_sla = response_tracker.get_sla_compliance_rate(days=days)

        resolution_by_category = analyzer.get_resolution_rate_by_category(days=days)
        resolution_by_agent = analyzer.get_resolution_rate_by_agent(days=days)

        bottlenecks = self.db_manager.get_unresolved_bottlenecks(limit=10)

        tickets = self.db_manager.get_tickets(days=days)
        ticket_volume_by_status = {}
        for ticket in tickets:
            ticket_volume_by_status[ticket.status] = (
                ticket_volume_by_status.get(ticket.status, 0) + 1
            )

        dashboard_data = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "period_days": days,
            "overall_metrics": {
                "total_tickets": overall_resolution["total_tickets"],
                "resolved_tickets": overall_resolution["resolved_tickets"],
                "resolution_rate": overall_resolution["resolution_rate"],
                "average_response_time_minutes": overall_response_time,
                "average_resolution_time_hours": overall_resolution.get(
                    "average_resolution_time_hours"
                ),
                "sla_compliance_percentage": overall_sla * 100.0 if overall_sla else None,
            },
            "resolution_by_category": [
                {"category": cat, "rate": rate}
                for cat, rate in resolution_by_category.items()
            ],
            "resolution_by_agent": [
                {"agent": agent, "rate": rate}
                for agent, rate in resolution_by_agent.items()
            ],
            "bottlenecks": [
                {
                    "type": b.bottleneck_type,
                    "identifier": b.identifier,
                    "severity": b.severity,
                    "description": b.description,
                    "impact_percentage": b.impact_percentage,
                    "ticket_count": b.ticket_count,
                }
                for b in bottlenecks
            ],
            "ticket_volume_by_status": ticket_volume_by_status,
        }

        template_path = Path(__file__).parent.parent / "templates" / "dashboard.html"
        if not template_path.exists():
            html_content = self._get_default_dashboard_template()
        else:
            with open(template_path, "r") as f:
                html_content = f.read()

        template = Template(html_content)
        rendered_html = template.render(**dashboard_data)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        logger.info(
            f"Generated HTML dashboard: {output_path}",
            extra={"output_path": str(output_path), "days": days},
        )

        return output_path

    def generate_csv_dashboard(
        self,
        days: int = 30,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate CSV performance dashboard.

        Args:
            days: Number of days to analyze.
            output_path: Optional output file path.

        Returns:
            Path to generated CSV dashboard.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"support_dashboard_{days}days_{timestamp}.csv"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        from src.response_time_tracker import ResponseTimeTracker
        from src.resolution_rate_analyzer import ResolutionRateAnalyzer

        response_tracker = ResponseTimeTracker(self.db_manager, self.config)
        analyzer = ResolutionRateAnalyzer(self.db_manager, self.config)

        overall_resolution = analyzer.calculate_resolution_rate(days=days)
        overall_response_time = response_tracker.get_average_response_time(days=days)
        overall_sla = response_tracker.get_sla_compliance_rate(days=days)

        resolution_by_category = analyzer.get_resolution_rate_by_category(days=days)
        resolution_by_agent = analyzer.get_resolution_rate_by_agent(days=days)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow(["Support Performance Dashboard"])
            writer.writerow([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
            writer.writerow([f"Period: Last {days} days"])
            writer.writerow([])

            writer.writerow(["Overall Metrics"])
            writer.writerow(
                [
                    "Metric",
                    "Value",
                ]
            )
            writer.writerow(
                [
                    "Total Tickets",
                    overall_resolution["total_tickets"],
                ]
            )
            writer.writerow(
                [
                    "Resolved Tickets",
                    overall_resolution["resolved_tickets"],
                ]
            )
            writer.writerow(
                [
                    "Resolution Rate",
                    f"{overall_resolution['resolution_rate']:.2%}",
                ]
            )
            if overall_response_time:
                writer.writerow(
                    [
                        "Average Response Time (minutes)",
                        f"{overall_response_time:.2f}",
                    ]
                )
            if overall_sla:
                writer.writerow(
                    [
                        "SLA Compliance",
                        f"{overall_sla * 100.0:.2f}%",
                    ]
                )
            writer.writerow([])

            writer.writerow(["Resolution Rate by Category"])
            writer.writerow(["Category", "Resolution Rate"])
            for category, rate in resolution_by_category.items():
                writer.writerow([category, f"{rate:.2%}"])

            writer.writerow([])

            writer.writerow(["Resolution Rate by Agent"])
            writer.writerow(["Agent", "Resolution Rate"])
            for agent, rate in resolution_by_agent.items():
                writer.writerow([agent, f"{rate:.2%}"])

        logger.info(
            f"Generated CSV dashboard: {output_path}",
            extra={"output_path": str(output_path), "days": days},
        )

        return output_path

    def _get_default_dashboard_template(self) -> str:
        """Get default HTML dashboard template.

        Returns:
            HTML template string.
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Support Performance Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 2em;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .section {
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .section h2 {
            color: #667eea;
            margin-top: 0;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
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
        .bottleneck {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 4px;
        }
        .bottleneck.critical {
            background: #f8d7da;
            border-left-color: #dc3545;
        }
        .bottleneck.high {
            background: #ffeaa7;
            border-left-color: #f39c12;
        }
        .severity-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .severity-critical {
            background: #dc3545;
            color: white;
        }
        .severity-high {
            background: #f39c12;
            color: white;
        }
        .severity-medium {
            background: #ffc107;
            color: #333;
        }
        .severity-low {
            background: #28a745;
            color: white;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Support Performance Dashboard</h1>
        <p>Generated on {{ generated_at }} - Last {{ period_days }} days</p>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">Total Tickets</div>
            <div class="metric-value">{{ overall_metrics.total_tickets }}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Resolved Tickets</div>
            <div class="metric-value">{{ overall_metrics.resolved_tickets }}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Resolution Rate</div>
            <div class="metric-value">{{ "%.1f"|format(overall_metrics.resolution_rate * 100) }}%</div>
        </div>
        {% if overall_metrics.average_response_time_minutes %}
        <div class="metric-card">
            <div class="metric-label">Avg Response Time</div>
            <div class="metric-value">{{ "%.1f"|format(overall_metrics.average_response_time_minutes) }} min</div>
        </div>
        {% endif %}
        {% if overall_metrics.sla_compliance_percentage %}
        <div class="metric-card">
            <div class="metric-label">SLA Compliance</div>
            <div class="metric-value">{{ "%.1f"|format(overall_metrics.sla_compliance_percentage) }}%</div>
        </div>
        {% endif %}
    </div>

    <div class="section">
        <h2>Resolution Rate by Category</h2>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Resolution Rate</th>
                </tr>
            </thead>
            <tbody>
                {% for item in resolution_by_category %}
                <tr>
                    <td>{{ item.category }}</td>
                    <td>{{ "%.1f"|format(item.rate * 100) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>Resolution Rate by Agent</h2>
        <table>
            <thead>
                <tr>
                    <th>Agent</th>
                    <th>Resolution Rate</th>
                </tr>
            </thead>
            <tbody>
                {% for item in resolution_by_agent %}
                <tr>
                    <td>{{ item.agent }}</td>
                    <td>{{ "%.1f"|format(item.rate * 100) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    {% if bottlenecks %}
    <div class="section">
        <h2>Identified Bottlenecks</h2>
        {% for bottleneck in bottlenecks %}
        <div class="bottleneck {{ bottleneck.severity }}">
            <strong>{{ bottleneck.type|title }}: {{ bottleneck.identifier }}</strong>
            <span class="severity-badge severity-{{ bottleneck.severity }}">{{ bottleneck.severity|upper }}</span>
            <p>{{ bottleneck.description }}</p>
            <p><small>Impact: {{ "%.1f"|format(bottleneck.impact_percentage) }}% | Affected Tickets: {{ bottleneck.ticket_count }}</small></p>
        </div>
        {% endfor %}
    </div>
    {% endif %}
</body>
</html>"""
