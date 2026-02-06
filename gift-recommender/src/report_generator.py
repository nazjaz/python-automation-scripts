"""Report generator for gift recommendations."""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager, GiftItem, Recipient
from src.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates gift recommendation reports in various formats."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        recommendation_engine: RecommendationEngine,
        output_dir: str = "reports",
    ) -> None:
        """Initialize report generator.

        Args:
            db_manager: Database manager instance.
            recommendation_engine: Recommendation engine instance.
            output_dir: Output directory for reports.
        """
        self.db_manager = db_manager
        self.recommendation_engine = recommendation_engine
        self.output_dir = Path(output_dir)

    def generate_html_report(
        self,
        recipient_id: int,
        recommendations: List[Dict],
        occasion: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate HTML gift recommendation report.

        Args:
            recipient_id: Recipient ID.
            recommendations: List of recommendation dictionaries.
            occasion: Optional occasion type.
            output_path: Optional output file path.

        Returns:
            Path to generated HTML report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gift_recommendations_{recipient_id}_{timestamp}.html"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        recipient = self.db_manager.get_recipient(recipient_id)

        template_path = (
            Path(__file__).parent.parent / "templates" / "gift_recommendations.html"
        )
        if not template_path.exists():
            html_content = self._get_default_html_template()
        else:
            with open(template_path, "r") as f:
                html_content = f.read()

        template = Template(html_content)

        report_data = {
            "recipient_name": recipient.name if recipient else "Recipient",
            "recipient_email": recipient.email if recipient else "",
            "occasion": occasion or "General",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "recommendations": [
                {
                    "name": rec["item"].name,
                    "category": rec["item"].category,
                    "price": rec["item"].price,
                    "description": rec["item"].description or "",
                    "brand": rec["item"].brand or "",
                    "score": rec["score"],
                    "price_category": rec["price_category"],
                    "reasoning": rec["reasoning"],
                }
                for rec in recommendations
            ],
            "total_recommendations": len(recommendations),
        }

        rendered_html = template.render(**report_data)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        logger.info(
            f"Generated HTML report: {output_path}",
            extra={"output_path": str(output_path), "recipient_id": recipient_id},
        )

        return output_path

    def generate_csv_report(
        self,
        recipient_id: int,
        recommendations: List[Dict],
        occasion: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate CSV gift recommendation report.

        Args:
            recipient_id: Recipient ID.
            recommendations: List of recommendation dictionaries.
            occasion: Optional occasion type.
            output_path: Optional output file path.

        Returns:
            Path to generated CSV report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gift_recommendations_{recipient_id}_{timestamp}.csv"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "name",
                "category",
                "price",
                "brand",
                "description",
                "score",
                "price_category",
                "reasoning",
                "occasion",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for rec in recommendations:
                item = rec["item"]
                writer.writerow(
                    {
                        "name": item.name,
                        "category": item.category,
                        "price": item.price,
                        "brand": item.brand or "",
                        "description": item.description or "",
                        "score": rec["score"],
                        "price_category": rec["price_category"],
                        "reasoning": rec["reasoning"],
                        "occasion": occasion or "",
                    }
                )

        logger.info(
            f"Generated CSV report: {output_path}",
            extra={"output_path": str(output_path), "recipient_id": recipient_id},
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gift Recommendations for {{ recipient_name }}</title>
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
        .recommendation {
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        .recommendation h3 {
            margin-top: 0;
            color: #667eea;
        }
        .recommendation-meta {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        .meta-item {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
        }
        .meta-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }
        .meta-value {
            font-size: 1.1em;
            font-weight: bold;
            color: #333;
        }
        .price {
            color: #667eea;
            font-size: 1.3em;
        }
        .score {
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            display: inline-block;
            font-weight: bold;
        }
        .reasoning {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin-top: 15px;
            font-style: italic;
            color: #555;
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
        <h1>Gift Recommendations</h1>
        <p>For {{ recipient_name }} - {{ occasion }} - Generated on {{ generated_at }}</p>
    </div>

    <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        <h2>Summary</h2>
        <p><strong>Total Recommendations:</strong> {{ total_recommendations }}</p>
        <p><strong>Occasion:</strong> {{ occasion }}</p>
    </div>

    {% for rec in recommendations %}
    <div class="recommendation">
        <h3>{{ rec.name }}</h3>
        {% if rec.brand %}
        <p><strong>Brand:</strong> {{ rec.brand }}</p>
        {% endif %}
        {% if rec.description %}
        <p>{{ rec.description }}</p>
        {% endif %}
        <div class="recommendation-meta">
            <div class="meta-item">
                <div class="meta-label">Category</div>
                <div class="meta-value">{{ rec.category }}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Price</div>
                <div class="meta-value price">${{ "%.2f"|format(rec.price) }}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Price Range</div>
                <div class="meta-value">{{ rec.price_category }}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Match Score</div>
                <div class="meta-value">
                    <span class="score">{{ "%.1f"|format(rec.score * 100) }}%</span>
                </div>
            </div>
        </div>
        <div class="reasoning">
            <strong>Why this gift:</strong> {{ rec.reasoning }}
        </div>
    </div>
    {% endfor %}

    <div class="footer">
        <p>Report generated by Gift Recommender</p>
    </div>
</body>
</html>"""
