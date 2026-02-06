"""Customer Engagement Monitor.

Monitors customer engagement across all touchpoints, calculates lifetime value,
identifies high-value segments, and generates engagement strategy recommendations.
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

import pandas as pd
import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TouchpointType(str, Enum):
    """Customer touchpoint types."""

    EMAIL = "email"
    WEB = "web"
    MOBILE = "mobile"
    SOCIAL = "social"
    SUPPORT = "support"
    PURCHASE = "purchase"
    REVIEW = "review"


class SegmentTier(str, Enum):
    """Customer segment tier levels."""

    CHAMPION = "champion"
    LOYAL = "loyal"
    POTENTIAL = "potential"
    AT_RISK = "at_risk"
    LOST = "lost"


class EngagementDataConfig(BaseModel):
    """Configuration for engagement data source."""

    file_path: str = Field(..., description="Path to engagement data file")
    format: str = Field(default="csv", description="File format: csv or json")
    customer_id_column: str = Field(
        default="customer_id", description="Column name for customer ID"
    )
    touchpoint_column: str = Field(
        default="touchpoint", description="Column name for touchpoint type"
    )
    timestamp_column: str = Field(
        default="timestamp", description="Column name for timestamp"
    )
    engagement_score_column: Optional[str] = Field(
        default=None, description="Column name for engagement score"
    )


class PurchaseDataConfig(BaseModel):
    """Configuration for purchase data source."""

    file_path: str = Field(..., description="Path to purchase data file")
    format: str = Field(default="csv", description="File format: csv or json")
    customer_id_column: str = Field(
        default="customer_id", description="Column name for customer ID"
    )
    purchase_date_column: str = Field(
        default="purchase_date", description="Column name for purchase date"
    )
    amount_column: str = Field(
        default="amount", description="Column name for purchase amount"
    )


class LTVConfig(BaseModel):
    """Configuration for LTV calculation."""

    discount_rate: float = Field(
        default=0.1, description="Discount rate for LTV calculation"
    )
    average_customer_lifespan_years: float = Field(
        default=3.0, description="Average customer lifespan in years"
    )
    lookback_months: int = Field(
        default=12, description="Months to look back for revenue calculation"
    )


class SegmentationConfig(BaseModel):
    """Configuration for customer segmentation."""

    ltv_threshold_high: float = Field(
        default=1000.0, description="High LTV threshold"
    )
    ltv_threshold_medium: float = Field(
        default=500.0, description="Medium LTV threshold"
    )
    engagement_threshold_high: float = Field(
        default=0.7, description="High engagement threshold"
    )
    engagement_threshold_low: float = Field(
        default=0.3, description="Low engagement threshold"
    )
    recency_threshold_days: int = Field(
        default=90, description="Days for recency threshold"
    )


class StrategyConfig(BaseModel):
    """Configuration for strategy generation."""

    max_recommendations_per_segment: int = Field(
        default=5, description="Maximum recommendations per segment"
    )


class Config(BaseModel):
    """Main configuration model."""

    engagement_data: EngagementDataConfig = Field(
        ..., description="Engagement data source configuration"
    )
    purchase_data: PurchaseDataConfig = Field(
        ..., description="Purchase data source configuration"
    )
    ltv: LTVConfig = Field(
        default_factory=LTVConfig, description="LTV calculation settings"
    )
    segmentation: SegmentationConfig = Field(
        default_factory=SegmentationConfig,
        description="Segmentation settings",
    )
    strategy: StrategyConfig = Field(
        default_factory=StrategyConfig,
        description="Strategy generation settings",
    )
    output_file: str = Field(
        default="logs/engagement_analysis.json",
        description="Path to save analysis results",
    )
    report_file: str = Field(
        default="logs/engagement_report.md",
        description="Path for engagement report",
    )


class AppSettings(BaseSettings):
    """Application settings from environment variables."""

    config_path: str = "config.yaml"


@dataclass
class EngagementRecord:
    """Represents an engagement record."""

    customer_id: str
    touchpoint: TouchpointType
    timestamp: datetime
    engagement_score: Optional[float] = None


@dataclass
class PurchaseRecord:
    """Represents a purchase record."""

    customer_id: str
    purchase_date: datetime
    amount: float


@dataclass
class CustomerMetrics:
    """Customer engagement and value metrics."""

    customer_id: str
    lifetime_value: float
    total_revenue: float
    purchase_count: int
    engagement_score: float
    touchpoint_count: Dict[TouchpointType, int]
    last_engagement_date: Optional[datetime] = None
    days_since_last_engagement: Optional[int] = None
    segment: SegmentTier = SegmentTier.POTENTIAL


@dataclass
class SegmentAnalysis:
    """Analysis for a customer segment."""

    segment: SegmentTier
    customer_count: int
    avg_ltv: float
    avg_engagement_score: float
    total_revenue: float
    recommendations: List[str]


@dataclass
class EngagementAnalysis:
    """Complete engagement analysis results."""

    total_customers: int
    customer_metrics: List[CustomerMetrics]
    segment_analyses: List[SegmentAnalysis]
    overall_metrics: Dict[str, float]
    generated_at: datetime


def load_config(config_path: Path) -> Config:
    """Load and validate configuration from YAML file.

    Args:
        config_path: Path to configuration YAML file

    Returns:
        Validated configuration object

    Raises:
        FileNotFoundError: If config file does not exist
        ValueError: If configuration is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        config = Config(**config_data)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in configuration file: {e}")
        raise ValueError(f"Invalid YAML configuration: {e}") from e
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


def load_engagement_data(
    config: EngagementDataConfig, project_root: Path
) -> List[EngagementRecord]:
    """Load engagement data from file.

    Args:
        config: Engagement data configuration
        project_root: Project root directory

    Returns:
        List of EngagementRecord objects

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        raise FileNotFoundError(f"Engagement data file not found: {data_path}")

    engagements = []

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        required_columns = [
            config.customer_id_column,
            config.touchpoint_column,
            config.timestamp_column,
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df[config.timestamp_column] = pd.to_datetime(df[config.timestamp_column])

        for _, row in df.iterrows():
            touchpoint_str = str(row[config.touchpoint_column]).lower()
            try:
                touchpoint = TouchpointType(touchpoint_str)
            except ValueError:
                logger.warning(f"Unknown touchpoint type: {touchpoint_str}")
                continue

            engagement = EngagementRecord(
                customer_id=str(row[config.customer_id_column]),
                touchpoint=touchpoint,
                timestamp=row[config.timestamp_column],
            )

            if (
                config.engagement_score_column
                and config.engagement_score_column in df.columns
            ):
                if pd.notna(row[config.engagement_score_column]):
                    engagement.engagement_score = float(
                        row[config.engagement_score_column]
                    )

            engagements.append(engagement)

        logger.info(f"Loaded {len(engagements)} engagement records")
        return engagements

    except pd.errors.EmptyDataError:
        logger.warning(f"Engagement data file is empty: {data_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to load engagement data: {e}")
        raise


def load_purchase_data(
    config: PurchaseDataConfig, project_root: Path
) -> List[PurchaseRecord]:
    """Load purchase data from file.

    Args:
        config: Purchase data configuration
        project_root: Project root directory

    Returns:
        List of PurchaseRecord objects

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        raise FileNotFoundError(f"Purchase data file not found: {data_path}")

    purchases = []

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        required_columns = [
            config.customer_id_column,
            config.purchase_date_column,
            config.amount_column,
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df[config.purchase_date_column] = pd.to_datetime(
            df[config.purchase_date_column]
        )

        for _, row in df.iterrows():
            purchase = PurchaseRecord(
                customer_id=str(row[config.customer_id_column]),
                purchase_date=row[config.purchase_date_column],
                amount=float(row[config.amount_column]),
            )
            purchases.append(purchase)

        logger.info(f"Loaded {len(purchases)} purchase records")
        return purchases

    except pd.errors.EmptyDataError:
        logger.warning(f"Purchase data file is empty: {data_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to load purchase data: {e}")
        raise


def calculate_ltv(
    purchases: List[PurchaseRecord],
    customer_id: str,
    config: LTVConfig,
) -> Tuple[float, float, int]:
    """Calculate customer lifetime value.

    Args:
        purchases: List of purchase records
        config: LTV configuration

    Returns:
        Tuple of (LTV, total_revenue, purchase_count)
    """
    customer_purchases = [
        p for p in purchases if p.customer_id == customer_id
    ]

    if not customer_purchases:
        return 0.0, 0.0, 0

    cutoff_date = datetime.now() - timedelta(
        days=config.lookback_months * 30
    )
    recent_purchases = [
        p for p in customer_purchases if p.purchase_date >= cutoff_date
    ]

    total_revenue = sum(p.amount for p in recent_purchases)
    purchase_count = len(recent_purchases)

    if purchase_count == 0:
        return 0.0, 0.0, 0

    avg_order_value = total_revenue / purchase_count
    purchase_frequency = purchase_count / config.lookback_months
    customer_value = avg_order_value * purchase_frequency

    lifespan_months = config.average_customer_lifespan_years * 12
    ltv = customer_value * lifespan_months

    discount_factor = 1.0 / (
        (1.0 + config.discount_rate) ** config.average_customer_lifespan_years
    )
    ltv_discounted = ltv * discount_factor

    return ltv_discounted, total_revenue, purchase_count


def calculate_engagement_score(
    engagements: List[EngagementRecord], customer_id: str
) -> Tuple[float, Dict[TouchpointType, int], Optional[datetime]]:
    """Calculate customer engagement score.

    Args:
        engagements: List of engagement records
        customer_id: Customer identifier

    Returns:
        Tuple of (engagement_score, touchpoint_counts, last_engagement_date)
    """
    customer_engagements = [
        e for e in engagements if e.customer_id == customer_id
    ]

    if not customer_engagements:
        return 0.0, {}, None

    touchpoint_counts: Dict[TouchpointType, int] = defaultdict(int)
    total_score = 0.0
    score_count = 0
    last_engagement = None

    touchpoint_weights = {
        TouchpointType.PURCHASE: 5.0,
        TouchpointType.REVIEW: 4.0,
        TouchpointType.SUPPORT: 3.0,
        TouchpointType.WEB: 2.0,
        TouchpointType.MOBILE: 2.0,
        TouchpointType.EMAIL: 1.5,
        TouchpointType.SOCIAL: 1.0,
    }

    for engagement in customer_engagements:
        touchpoint_counts[engagement.touchpoint] += 1

        if engagement.engagement_score is not None:
            total_score += engagement.engagement_score
            score_count += 1
        else:
            weight = touchpoint_weights.get(engagement.touchpoint, 1.0)
            total_score += weight
            score_count += 1

        if last_engagement is None or engagement.timestamp > last_engagement:
            last_engagement = engagement.timestamp

    engagement_score = total_score / score_count if score_count > 0 else 0.0
    max_possible_score = sum(touchpoint_weights.values()) / len(touchpoint_weights)
    normalized_score = min(1.0, engagement_score / max_possible_score)

    return normalized_score, dict(touchpoint_counts), last_engagement


def assign_segment(
    metrics: CustomerMetrics, config: SegmentationConfig
) -> SegmentTier:
    """Assign customer to segment based on metrics.

    Args:
        metrics: Customer metrics
        config: Segmentation configuration

    Returns:
        Assigned segment tier
    """
    if metrics.lifetime_value >= config.ltv_threshold_high:
        if metrics.engagement_score >= config.engagement_threshold_high:
            return SegmentTier.CHAMPION
        else:
            return SegmentTier.LOYAL
    elif metrics.lifetime_value >= config.ltv_threshold_medium:
        if metrics.engagement_score >= config.engagement_threshold_high:
            return SegmentTier.LOYAL
        else:
            return SegmentTier.POTENTIAL
    else:
        if metrics.days_since_last_engagement:
            if metrics.days_since_last_engagement > config.recency_threshold_days:
                return SegmentTier.LOST
            else:
                return SegmentTier.AT_RISK
        else:
            return SegmentTier.POTENTIAL


def generate_segment_strategies(
    segment: SegmentTier, analysis: SegmentAnalysis
) -> List[str]:
    """Generate engagement strategies for a segment.

    Args:
        segment: Segment tier
        analysis: Segment analysis

    Returns:
        List of strategy recommendations
    """
    strategies = []

    if segment == SegmentTier.CHAMPION:
        strategies.append(
            "Implement VIP program with exclusive benefits and early access"
        )
        strategies.append("Request testimonials and referrals")
        strategies.append("Offer premium support and dedicated account management")
        strategies.append("Create exclusive content and experiences")
        strategies.append("Engage in co-creation and feedback programs")

    elif segment == SegmentTier.LOYAL:
        strategies.append("Increase cross-sell and up-sell opportunities")
        strategies.append("Implement loyalty rewards program")
        strategies.append("Provide personalized recommendations")
        strategies.append("Engage through multiple touchpoints regularly")
        strategies.append("Offer special promotions and early access")

    elif segment == SegmentTier.POTENTIAL:
        strategies.append("Increase engagement frequency across touchpoints")
        strategies.append("Provide educational content and onboarding")
        strategies.append("Offer incentives for first purchase or upgrade")
        strategies.append("Implement retargeting campaigns")
        strategies.append("Create personalized messaging based on behavior")

    elif segment == SegmentTier.AT_RISK:
        strategies.append("Send win-back campaigns with special offers")
        strategies.append("Conduct satisfaction surveys to identify issues")
        strategies.append("Provide personalized re-engagement content")
        strategies.append("Offer discounts or incentives to return")
        strategies.append("Reach out through preferred communication channel")

    elif segment == SegmentTier.LOST:
        strategies.append("Implement win-back campaigns with compelling offers")
        strategies.append("Analyze churn reasons and address root causes")
        strategies.append("Re-engage through multiple channels")
        strategies.append("Offer significant incentives for return")
        strategies.append("Survey to understand why they left")

    return strategies[:5]


def process_engagement_analysis(config_path: Path) -> EngagementAnalysis:
    """Process engagement data and generate analysis.

    Args:
        config_path: Path to configuration file

    Returns:
        Complete engagement analysis

    Raises:
        FileNotFoundError: If config or data files are missing
        ValueError: If configuration is invalid
    """
    config = load_config(config_path)
    project_root = config_path.parent

    engagements = load_engagement_data(config.engagement_data, project_root)
    purchases = load_purchase_data(config.purchase_data, project_root)

    if not engagements and not purchases:
        logger.warning("No engagement or purchase data available")
        return EngagementAnalysis(
            total_customers=0,
            customer_metrics=[],
            segment_analyses=[],
            overall_metrics={},
            generated_at=datetime.now(),
        )

    all_customer_ids = set()
    if engagements:
        all_customer_ids.update(e.customer_id for e in engagements)
    if purchases:
        all_customer_ids.update(p.customer_id for p in purchases)

    customer_metrics_list = []

    for customer_id in all_customer_ids:
        ltv, total_revenue, purchase_count = calculate_ltv(
            purchases, customer_id, config.ltv
        )

        engagement_score, touchpoint_counts, last_engagement = (
            calculate_engagement_score(engagements, customer_id)
        )

        days_since_last_engagement = None
        if last_engagement:
            days_since_last_engagement = (
                datetime.now() - last_engagement
            ).days

        metrics = CustomerMetrics(
            customer_id=customer_id,
            lifetime_value=ltv,
            total_revenue=total_revenue,
            purchase_count=purchase_count,
            engagement_score=engagement_score,
            touchpoint_count=touchpoint_counts,
            last_engagement_date=last_engagement,
            days_since_last_engagement=days_since_last_engagement,
        )

        metrics.segment = assign_segment(metrics, config.segmentation)
        customer_metrics_list.append(metrics)

    segment_analyses = []
    for segment in SegmentTier:
        segment_customers = [
            m for m in customer_metrics_list if m.segment == segment
        ]

        if not segment_customers:
            continue

        avg_ltv = (
            sum(m.lifetime_value for m in segment_customers)
            / len(segment_customers)
        )
        avg_engagement = (
            sum(m.engagement_score for m in segment_customers)
            / len(segment_customers)
        )
        total_revenue = sum(m.total_revenue for m in segment_customers)

        segment_analysis = SegmentAnalysis(
            segment=segment,
            customer_count=len(segment_customers),
            avg_ltv=avg_ltv,
            avg_engagement_score=avg_engagement,
            total_revenue=total_revenue,
            recommendations=[],
        )

        segment_analysis.recommendations = generate_segment_strategies(
            segment, segment_analysis
        )

        segment_analyses.append(segment_analysis)

    overall_metrics = {
        "total_customers": len(customer_metrics_list),
        "avg_ltv": (
            sum(m.lifetime_value for m in customer_metrics_list)
            / len(customer_metrics_list)
            if customer_metrics_list
            else 0.0
        ),
        "avg_engagement_score": (
            sum(m.engagement_score for m in customer_metrics_list)
            / len(customer_metrics_list)
            if customer_metrics_list
            else 0.0
        ),
        "total_revenue": sum(m.total_revenue for m in customer_metrics_list),
    }

    analysis = EngagementAnalysis(
        total_customers=len(customer_metrics_list),
        customer_metrics=customer_metrics_list,
        segment_analyses=segment_analyses,
        overall_metrics=overall_metrics,
        generated_at=datetime.now(),
    )

    report_path = Path(config.report_file)
    if not report_path.is_absolute():
        report_path = project_root / report_path

    write_markdown_report(analysis, report_path)

    output_path = Path(config.output_file)
    if not output_path.is_absolute():
        output_path = project_root / output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_data = {
        "generated_at": analysis.generated_at.isoformat(),
        "overall_metrics": analysis.overall_metrics,
        "segments": [
            {
                "segment": sa.segment.value,
                "customer_count": sa.customer_count,
                "avg_ltv": sa.avg_ltv,
                "avg_engagement_score": sa.avg_engagement_score,
                "total_revenue": sa.total_revenue,
                "recommendations": sa.recommendations,
            }
            for sa in segment_analyses
        ],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Analysis saved to {output_path}")

    return analysis


def write_markdown_report(
    analysis: EngagementAnalysis, output_path: Path
) -> None:
    """Write engagement analysis report to markdown file.

    Args:
        analysis: Engagement analysis results
        output_path: Path to write the report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Customer Engagement Analysis Report\n\n")
        f.write(
            f"**Generated:** {analysis.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        f.write("## Overall Metrics\n\n")
        f.write(f"- **Total Customers:** {analysis.overall_metrics['total_customers']}\n")
        f.write(
            f"- **Average LTV:** ${analysis.overall_metrics['avg_ltv']:,.2f}\n"
        )
        f.write(
            f"- **Average Engagement Score:** "
            f"{analysis.overall_metrics['avg_engagement_score']:.2f}\n"
        )
        f.write(
            f"- **Total Revenue:** ${analysis.overall_metrics['total_revenue']:,.2f}\n"
        )
        f.write("\n")

        f.write("## Segment Analysis\n\n")
        for segment_analysis in analysis.segment_analyses:
            f.write(f"### {segment_analysis.segment.value.replace('_', ' ').title()}\n\n")
            f.write(f"- **Customer Count:** {segment_analysis.customer_count}\n")
            f.write(f"- **Average LTV:** ${segment_analysis.avg_ltv:,.2f}\n")
            f.write(
                f"- **Average Engagement Score:** "
                f"{segment_analysis.avg_engagement_score:.2f}\n"
            )
            f.write(
                f"- **Total Revenue:** ${segment_analysis.total_revenue:,.2f}\n"
            )
            f.write("\n")
            f.write("**Engagement Strategies:**\n\n")
            for i, rec in enumerate(segment_analysis.recommendations, 1):
                f.write(f"{i}. {rec}\n")
            f.write("\n")

        f.write("## High-Value Customers\n\n")
        high_value = sorted(
            analysis.customer_metrics,
            key=lambda x: x.lifetime_value,
            reverse=True,
        )[:20]

        f.write("| Customer ID | LTV | Engagement Score | Segment |\n")
        f.write("|-------------|-----|------------------|----------|\n")
        for metrics in high_value:
            f.write(
                f"| {metrics.customer_id} | ${metrics.lifetime_value:,.2f} | "
                f"{metrics.engagement_score:.2f} | {metrics.segment.value} |\n"
            )

    logger.info(f"Report written to {output_path}")


def main() -> None:
    """Main entry point for the customer engagement monitor."""
    settings = AppSettings()
    config_path = Path(settings.config_path)

    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent
        config_path = project_root / config_path

    try:
        logger.info("Starting customer engagement analysis")
        analysis = process_engagement_analysis(config_path)
        logger.info(
            f"Analysis complete. Analyzed {analysis.total_customers} customers "
            f"across {len(analysis.segment_analyses)} segments."
        )
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
