"""Generates API performance reports."""

import csv
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates API performance reports in various formats."""

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
        endpoint_id: Optional[int] = None,
        hours: int = 24,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate HTML performance report.

        Args:
            endpoint_id: Optional endpoint ID filter.
            hours: Number of hours to analyze.
            output_path: Optional output file path.

        Returns:
            Path to generated HTML report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = f"_endpoint{endpoint_id}" if endpoint_id else ""
            filename = f"api_performance_report{suffix}_{timestamp}.html"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        from src.response_time_tracker import ResponseTimeTracker
        from src.bottleneck_analyzer import BottleneckAnalyzer
        from src.recommendation_engine import RecommendationEngine
        from src.database import APIEndpoint

        tracker = ResponseTimeTracker(self.db_manager, self.config)
        analyzer = BottleneckAnalyzer(self.db_manager, self.config)
        recommender = RecommendationEngine(self.db_manager, self.config)

        if endpoint_id:
            endpoints = [
                self.db_manager.get_session()
                .query(APIEndpoint)
                .filter(APIEndpoint.id == endpoint_id)
                .first()
            ]
        else:
            endpoints = self.db_manager.get_endpoints(active_only=True)

        endpoints = [e for e in endpoints if e]

        slow_endpoints = tracker.identify_slow_endpoints()

        report_data = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "analysis_window_hours": hours,
            "endpoints": [],
            "slow_endpoints": slow_endpoints,
            "bottlenecks": [],
            "recommendations": [],
        }

        for endpoint in endpoints:
            metrics = tracker.calculate_metrics(endpoint.id)
            bottlenecks = analyzer.analyze_endpoint(endpoint.id, hours=hours)
            recommendations = recommender.generate_recommendations(endpoint.id)

            endpoint_data = {
                "id": endpoint.id,
                "full_url": endpoint.full_url,
                "method": endpoint.method,
                "description": endpoint.description or "",
            }

            if metrics:
                endpoint_data["metrics"] = {
                    "avg_response_time_ms": metrics.avg_response_time_ms,
                    "p95_response_time_ms": metrics.p95_response_time_ms,
                    "p99_response_time_ms": metrics.p99_response_time_ms,
                    "request_count": metrics.request_count,
                    "error_rate": metrics.error_rate,
                    "throughput_per_second": metrics.throughput_per_second,
                }

            report_data["endpoints"].append(endpoint_data)
            report_data["bottlenecks"].extend(
                [
                    {
                        "type": b.bottleneck_type,
                        "severity": b.severity,
                        "description": b.description,
                    }
                    for b in bottlenecks
                ]
            )
            report_data["recommendations"].extend(
                [
                    {
                        "type": r.recommendation_type,
                        "title": r.title,
                        "description": r.description,
                        "priority": r.priority,
                    }
                    for r in recommendations
                ]
            )

        template_path = Path(__file__).parent.parent / "templates" / "performance_report.html"
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
            extra={"output_path": str(output_path), "endpoint_id": endpoint_id},
        )

        return output_path

    def generate_csv_report(
        self,
        endpoint_id: Optional[int] = None,
        hours: int = 24,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate CSV performance report.

        Args:
            endpoint_id: Optional endpoint ID filter.
            hours: Number of hours to analyze.
            output_path: Optional output file path.

        Returns:
            Path to generated CSV report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = f"_endpoint{endpoint_id}" if endpoint_id else ""
            filename = f"api_performance_report{suffix}_{timestamp}.csv"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        from src.response_time_tracker import ResponseTimeTracker
        from src.database import APIEndpoint

        tracker = ResponseTimeTracker(self.db_manager, self.config)

        if endpoint_id:
            endpoints = [
                self.db_manager.get_session()
                .query(APIEndpoint)
                .filter(APIEndpoint.id == endpoint_id)
                .first()
            ]
        else:
            endpoints = self.db_manager.get_endpoints(active_only=True)

        endpoints = [e for e in endpoints if e]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "endpoint_id",
                "full_url",
                "method",
                "avg_response_time_ms",
                "p95_response_time_ms",
                "p99_response_time_ms",
                "request_count",
                "error_rate",
                "throughput_per_second",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for endpoint in endpoints:
                metrics = tracker.calculate_metrics(endpoint.id)
                if metrics:
                    writer.writerow(
                        {
                            "endpoint_id": endpoint.id,
                            "full_url": endpoint.full_url,
                            "method": endpoint.method,
                            "avg_response_time_ms": f"{metrics.avg_response_time_ms:.2f}" if metrics.avg_response_time_ms else "",
                            "p95_response_time_ms": f"{metrics.p95_response_time_ms:.2f}" if metrics.p95_response_time_ms else "",
                            "p99_response_time_ms": f"{metrics.p99_response_time_ms:.2f}" if metrics.p99_response_time_ms else "",
                            "request_count": metrics.request_count,
                            "error_rate": f"{metrics.error_rate:.4f}" if metrics.error_rate else "",
                            "throughput_per_second": f"{metrics.throughput_per_second:.2f}" if metrics.throughput_per_second else "",
                        }
                    )

        logger.info(
            f"Generated CSV report: {output_path}",
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
    <title>API Performance Report</title>
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
        .severity-critical { color: #dc3545; font-weight: bold; }
        .severity-high { color: #f39c12; font-weight: bold; }
        .severity-medium { color: #ffc107; }
    </style>
</head>
<body>
    <div class="header">
        <h1>API Performance Report</h1>
        <p>Generated: {{ generated_at }}</p>
    </div>

    <h2>Endpoints</h2>
    <table>
        <thead>
            <tr>
                <th>Endpoint</th>
                <th>Method</th>
                <th>Avg Response Time</th>
                <th>P95 Response Time</th>
                <th>Error Rate</th>
            </tr>
        </thead>
        <tbody>
            {% for endpoint in endpoints %}
            <tr>
                <td>{{ endpoint.full_url }}</td>
                <td>{{ endpoint.method }}</td>
                <td>{{ "%.2f"|format(endpoint.metrics.avg_response_time_ms) if endpoint.metrics else "N/A" }} ms</td>
                <td>{{ "%.2f"|format(endpoint.metrics.p95_response_time_ms) if endpoint.metrics else "N/A" }} ms</td>
                <td>{{ "%.2f"|format(endpoint.metrics.error_rate * 100) if endpoint.metrics else "N/A" }}%</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>"""
