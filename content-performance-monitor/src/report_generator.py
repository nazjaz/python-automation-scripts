"""Report generator for content strategy recommendations."""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager
from src.strategy_recommender import StrategyRecommender
from src.top_content_identifier import TopContentIdentifier

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates content strategy reports in various formats."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        top_content_identifier: TopContentIdentifier,
        strategy_recommender: StrategyRecommender,
        config: Dict,
    ) -> None:
        """Initialize report generator.

        Args:
            db_manager: Database manager instance.
            top_content_identifier: Top content identifier instance.
            strategy_recommender: Strategy recommender instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.top_content_identifier = top_content_identifier
        self.strategy_recommender = strategy_recommender
        self.config = config
        self.reporting_config = config.get("reporting", {})
        self.output_dir = Path(self.reporting_config.get("output_directory", "reports"))

    def generate_html_report(
        self,
        platform: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate HTML content strategy report.

        Args:
            platform: Optional platform filter.
            output_path: Optional output file path.

        Returns:
            Path to generated HTML report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            platform_suffix = f"_{platform}" if platform else ""
            filename = f"content_strategy_report{platform_suffix}_{timestamp}.html"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        top_content = self.top_content_identifier.get_top_content(
            platform=platform, days=30
        )
        recommendations = self.strategy_recommender.generate_recommendations(
            platform=platform
        )
        trends = self.strategy_recommender.analyze_content_trends(
            platform=platform, days=7
        )

        template_path = Path(__file__).parent.parent / "templates" / "strategy_report.html"
        if not template_path.exists():
            html_content = self._get_default_html_template()
        else:
            with open(template_path, "r") as f:
                html_content = f.read()

        template = Template(html_content)

        platform_name = platform.title() if platform else "All Platforms"
        report_data = {
            "platform": platform_name,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "top_content": top_content[:10],
            "recommendations": recommendations,
            "trends": trends,
            "total_content_items": len(top_content),
        }

        rendered_html = template.render(**report_data)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        logger.info(
            f"Generated HTML report: {output_path}",
            extra={"output_path": str(output_path), "platform": platform},
        )

        return output_path

    def generate_csv_report(
        self,
        platform: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate CSV content performance report.

        Args:
            platform: Optional platform filter.
            output_path: Optional output file path.

        Returns:
            Path to generated CSV report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            platform_suffix = f"_{platform}" if platform else ""
            filename = f"content_performance{platform_suffix}_{timestamp}.csv"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        top_content = self.top_content_identifier.get_top_content(
            platform=platform, days=30
        )

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            if not top_content:
                writer = csv.writer(f)
                writer.writerow(["No content data available"])
            else:
                fieldnames = [
                    "content_id",
                    "platform",
                    "title",
                    "content_type",
                    "posted_at",
                    "overall_score",
                    "engagement_score",
                    "reach_score",
                    "views_score",
                ]

                metrics_fields = set()
                for item in top_content:
                    metrics = item.get("metrics", {})
                    metrics_fields.update(metrics.keys())

                fieldnames.extend(sorted(metrics_fields))

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for item in top_content:
                    row = {
                        "content_id": item.get("content_id", ""),
                        "platform": item.get("platform", ""),
                        "title": item.get("title", "") or "",
                        "content_type": item.get("content_type", "") or "",
                        "posted_at": item.get("posted_at", "") or "",
                        "overall_score": item.get("overall_score", 0.0),
                        "engagement_score": item.get("engagement_score", 0.0),
                        "reach_score": item.get("reach_score") or "",
                        "views_score": item.get("views_score", 0.0),
                    }

                    metrics = item.get("metrics", {})
                    for metric_name in sorted(metrics_fields):
                        row[metric_name] = metrics.get(metric_name, "")

                    writer.writerow(row)

        logger.info(
            f"Generated CSV report: {output_path}",
            extra={"output_path": str(output_path), "platform": platform},
        )

        return output_path

    def generate_reports(
        self, platform: Optional[str] = None
    ) -> Dict[str, Path]:
        """Generate all configured report types.

        Args:
            platform: Optional platform filter.

        Returns:
            Dictionary mapping report types to output paths.
        """
        reports = {}

        if self.reporting_config.get("generate_html", True):
            reports["html"] = self.generate_html_report(platform=platform)

        if self.reporting_config.get("generate_csv", True):
            reports["csv"] = self.generate_csv_report(platform=platform)

        return reports

    def _get_default_html_template(self) -> str:
        """Get default HTML template for reports.

        Returns:
            HTML template string.
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Content Strategy Report - {{ platform }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
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
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
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
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }
        .recommendation {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 4px;
        }
        .recommendation.high {
            border-left-color: #e74c3c;
        }
        .recommendation.medium {
            border-left-color: #f39c12;
        }
        .recommendation.low {
            border-left-color: #3498db;
        }
        .recommendation h3 {
            margin-top: 0;
            color: #333;
        }
        .content-item {
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 4px;
            border-left: 3px solid #667eea;
        }
        .content-item h3 {
            margin-top: 0;
            color: #667eea;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }
        .metric {
            background: white;
            padding: 10px;
            border-radius: 4px;
            text-align: center;
        }
        .metric-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 1.2em;
            font-weight: bold;
            color: #667eea;
        }
        .trends {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .trend-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
        }
        .trend-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }
        .trend-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }
        .footer {
            text-align: center;
            color: #666;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Content Strategy Report</h1>
        <p>{{ platform }} - Generated on {{ generated_at }}</p>
    </div>

    <div class="section">
        <h2>Summary</h2>
        <div class="trends">
            <div class="trend-item">
                <div class="trend-label">Total Content Items</div>
                <div class="trend-value">{{ total_content_items }}</div>
            </div>
            <div class="trend-item">
                <div class="trend-label">Average Engagement</div>
                <div class="trend-value">{{ "%.2f"|format(trends.avg_engagement * 100) }}%</div>
            </div>
            <div class="trend-item">
                <div class="trend-label">Top Content Type</div>
                <div class="trend-value">{{ trends.top_content_type or "N/A" }}</div>
            </div>
            <div class="trend-item">
                <div class="trend-label">Best Posting Day</div>
                <div class="trend-value">{{ trends.best_posting_day or "N/A" }}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Strategy Recommendations</h2>
        {% for rec in recommendations %}
        <div class="recommendation {{ rec.priority }}">
            <h3>{{ rec.title }}</h3>
            <p>{{ rec.description }}</p>
        </div>
        {% endfor %}
    </div>

    <div class="section">
        <h2>Top Performing Content</h2>
        {% for item in top_content %}
        <div class="content-item">
            <h3>{{ item.title or item.content_id }}</h3>
            <p><strong>Platform:</strong> {{ item.platform }} | <strong>Type:</strong> {{ item.content_type or "N/A" }} | <strong>Posted:</strong> {{ item.posted_at or "N/A" }}</p>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">Overall Score</div>
                    <div class="metric-value">{{ "%.2f"|format(item.overall_score * 100) }}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Engagement</div>
                    <div class="metric-value">{{ "%.2f"|format(item.engagement_score * 100) }}%</div>
                </div>
                {% if item.views_score %}
                <div class="metric">
                    <div class="metric-label">Views Score</div>
                    <div class="metric-value">{{ "%.2f"|format(item.views_score * 100) }}%</div>
                </div>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="footer">
        <p>Report generated by Content Performance Monitor</p>
    </div>
</body>
</html>"""
