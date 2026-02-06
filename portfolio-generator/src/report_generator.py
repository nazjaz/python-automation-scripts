"""Generates portfolio reports."""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from src.database import DatabaseManager

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates portfolio reports in various formats."""

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
        portfolio_id: int,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate HTML portfolio report.

        Args:
            portfolio_id: Portfolio ID.
            output_path: Optional output file path.

        Returns:
            Path to generated HTML report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"portfolio_report_{portfolio_id}_{timestamp}.html"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        from src.database import Portfolio, Holding, Investor, RebalancingRecommendation

        portfolio = (
            self.db_manager.get_session()
            .query(Portfolio)
            .filter(Portfolio.id == portfolio_id)
            .first()
        )

        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")

        investor = (
            self.db_manager.get_session()
            .query(Investor)
            .filter(Investor.id == portfolio.investor_id)
            .first()
        )

        holdings = portfolio.holdings
        total_value = sum(h.market_value or 0.0 for h in holdings)

        for holding in holdings:
            if total_value > 0:
                holding.current_allocation = (holding.market_value or 0.0) / total_value
            else:
                holding.current_allocation = 0.0

        recommendations = self.db_manager.get_unimplemented_recommendations(portfolio_id=portfolio_id)

        report_data = {
            "portfolio_id": portfolio.id,
            "portfolio_name": portfolio.name,
            "investor_name": investor.name if investor else "Unknown",
            "investor_email": investor.email if investor else "",
            "risk_tolerance": portfolio.risk_tolerance,
            "total_value": total_value,
            "currency": portfolio.currency,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "holdings": [
                {
                    "symbol": h.asset_symbol,
                    "name": h.asset_name,
                    "asset_class": h.asset_class,
                    "quantity": h.quantity,
                    "current_price": h.current_price,
                    "market_value": h.market_value or 0.0,
                    "target_allocation": h.target_allocation,
                    "current_allocation": h.current_allocation if hasattr(h, 'current_allocation') else 0.0,
                }
                for h in holdings
            ],
            "rebalancing_recommendations": [
                {
                    "asset_symbol": r.asset_symbol,
                    "action_type": r.action_type,
                    "recommended_action": r.recommended_action,
                    "current_allocation": r.current_allocation,
                    "target_allocation": r.target_allocation,
                    "amount_change": r.amount_change,
                    "priority": r.priority,
                }
                for r in recommendations
            ],
        }

        template_path = Path(__file__).parent.parent / "templates" / "portfolio_report.html"
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
            extra={"output_path": str(output_path), "portfolio_id": portfolio_id},
        )

        return output_path

    def generate_csv_report(
        self,
        portfolio_id: int,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate CSV portfolio report.

        Args:
            portfolio_id: Portfolio ID.
            output_path: Optional output file path.

        Returns:
            Path to generated CSV report.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"portfolio_report_{portfolio_id}_{timestamp}.csv"
            output_path = self.output_dir / filename

        self.output_dir.mkdir(parents=True, exist_ok=True)

        from src.database import Portfolio, Holding

        portfolio = (
            self.db_manager.get_session()
            .query(Portfolio)
            .filter(Portfolio.id == portfolio_id)
            .first()
        )

        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")

        holdings = portfolio.holdings
        total_value = sum(h.market_value or 0.0 for h in holdings)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "asset_symbol",
                "asset_name",
                "asset_class",
                "quantity",
                "current_price",
                "market_value",
                "target_allocation",
                "current_allocation",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            writer.writerow(
                {
                    "asset_symbol": "PORTFOLIO",
                    "asset_name": "Total Portfolio Value",
                    "asset_class": "SUMMARY",
                    "quantity": "",
                    "current_price": "",
                    "market_value": total_value,
                    "target_allocation": "",
                    "current_allocation": "",
                }
            )

            for holding in holdings:
                current_allocation = (holding.market_value or 0.0) / total_value if total_value > 0 else 0.0
                writer.writerow(
                    {
                        "asset_symbol": holding.asset_symbol,
                        "asset_name": holding.asset_name,
                        "asset_class": holding.asset_class,
                        "quantity": holding.quantity,
                        "current_price": holding.current_price or "",
                        "market_value": holding.market_value or 0.0,
                        "target_allocation": f"{holding.target_allocation:.4f}",
                        "current_allocation": f"{current_allocation:.4f}",
                    }
                )

        logger.info(
            f"Generated CSV report: {output_path}",
            extra={"output_path": str(output_path), "portfolio_id": portfolio_id},
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
    <title>Portfolio Report</title>
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
        <h1>Portfolio Report</h1>
        <p>Investor: {{ investor_name }}</p>
        <p>Portfolio: {{ portfolio_name }}</p>
    </div>

    <h2>Holdings</h2>
    <table>
        <thead>
            <tr>
                <th>Asset</th>
                <th>Class</th>
                <th>Market Value</th>
                <th>Target Allocation</th>
                <th>Current Allocation</th>
            </tr>
        </thead>
        <tbody>
            {% for holding in holdings %}
            <tr>
                <td>{{ holding.symbol }}</td>
                <td>{{ holding.asset_class }}</td>
                <td>${{ "%.2f"|format(holding.market_value) }}</td>
                <td>{{ "%.1f"|format(holding.target_allocation * 100) }}%</td>
                <td>{{ "%.1f"|format(holding.current_allocation * 100) }}%</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>"""
