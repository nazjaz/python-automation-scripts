"""Shopping Recommendation Engine.

Automatically generates personalized shopping recommendations by analyzing
purchase history, browsing behavior, and seasonal trends with inventory
availability checking.
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


class RecommendationPriority(str, Enum):
    """Priority level for recommendations."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PurchaseHistoryConfig(BaseModel):
    """Configuration for purchase history data source."""

    file_path: str = Field(..., description="Path to purchase history file")
    format: str = Field(default="csv", description="File format: csv or json")
    customer_id_column: str = Field(
        default="customer_id", description="Column name for customer ID"
    )
    product_id_column: str = Field(
        default="product_id", description="Column name for product ID"
    )
    purchase_date_column: str = Field(
        default="purchase_date", description="Column name for purchase date"
    )
    quantity_column: Optional[str] = Field(
        default=None, description="Column name for quantity"
    )
    category_column: Optional[str] = Field(
        default=None, description="Column name for product category"
    )
    price_column: Optional[str] = Field(
        default=None, description="Column name for price"
    )


class BrowsingBehaviorConfig(BaseModel):
    """Configuration for browsing behavior data source."""

    file_path: str = Field(..., description="Path to browsing behavior file")
    format: str = Field(default="csv", description="File format: csv or json")
    customer_id_column: str = Field(
        default="customer_id", description="Column name for customer ID"
    )
    product_id_column: str = Field(
        default="product_id", description="Column name for product ID"
    )
    timestamp_column: str = Field(
        default="timestamp", description="Column name for timestamp"
    )
    action_type_column: Optional[str] = Field(
        default=None, description="Column name for action type"
    )
    view_duration_column: Optional[str] = Field(
        default=None, description="Column name for view duration"
    )


class InventoryConfig(BaseModel):
    """Configuration for inventory data source."""

    file_path: str = Field(..., description="Path to inventory file")
    format: str = Field(default="csv", description="File format: csv or json")
    product_id_column: str = Field(
        default="product_id", description="Column name for product ID"
    )
    quantity_column: str = Field(
        default="quantity", description="Column name for available quantity"
    )
    in_stock_column: Optional[str] = Field(
        default=None, description="Column name for in-stock status"
    )


class SeasonalTrendsConfig(BaseModel):
    """Configuration for seasonal trends."""

    enable_seasonal_boost: bool = Field(
        default=True, description="Enable seasonal trend boosting"
    )
    seasonal_categories: Dict[str, List[int]] = Field(
        default_factory=lambda: {
            "winter": [12, 1, 2],
            "spring": [3, 4, 5],
            "summer": [6, 7, 8],
            "fall": [9, 10, 11],
        },
        description="Mapping of seasons to month numbers",
    )
    seasonal_boost_multiplier: float = Field(
        default=1.5, description="Multiplier for seasonal products"
    )


class RecommendationConfig(BaseModel):
    """Configuration for recommendation generation."""

    max_recommendations: int = Field(
        default=20, description="Maximum number of recommendations"
    )
    min_score_threshold: float = Field(
        default=0.3, description="Minimum recommendation score"
    )
    purchase_history_weight: float = Field(
        default=0.4, description="Weight for purchase history"
    )
    browsing_weight: float = Field(
        default=0.3, description="Weight for browsing behavior"
    )
    seasonal_weight: float = Field(
        default=0.3, description="Weight for seasonal trends"
    )
    require_in_stock: bool = Field(
        default=True, description="Only recommend in-stock items"
    )


class Config(BaseModel):
    """Main configuration model."""

    purchase_history: PurchaseHistoryConfig = Field(
        ..., description="Purchase history data source configuration"
    )
    browsing_behavior: BrowsingBehaviorConfig = Field(
        ..., description="Browsing behavior data source configuration"
    )
    inventory: InventoryConfig = Field(
        ..., description="Inventory data source configuration"
    )
    seasonal: SeasonalTrendsConfig = Field(
        default_factory=SeasonalTrendsConfig,
        description="Seasonal trends settings",
    )
    recommendation: RecommendationConfig = Field(
        default_factory=RecommendationConfig,
        description="Recommendation generation settings",
    )
    output_file: str = Field(
        default="logs/recommendations.json",
        description="Path to save recommendations",
    )
    report_file: str = Field(
        default="logs/recommendation_report.md",
        description="Path for recommendation report",
    )


class AppSettings(BaseSettings):
    """Application settings from environment variables."""

    config_path: str = "config.yaml"


@dataclass
class PurchaseRecord:
    """Represents a purchase record."""

    customer_id: str
    product_id: str
    purchase_date: datetime
    quantity: int = 1
    category: Optional[str] = None
    price: Optional[float] = None


@dataclass
class BrowsingRecord:
    """Represents a browsing behavior record."""

    customer_id: str
    product_id: str
    timestamp: datetime
    action_type: Optional[str] = None
    view_duration: Optional[float] = None


@dataclass
class InventoryItem:
    """Represents an inventory item."""

    product_id: str
    quantity: int
    in_stock: bool = True


@dataclass
class Recommendation:
    """Personalized shopping recommendation."""

    product_id: str
    customer_id: str
    score: float
    priority: RecommendationPriority
    reasons: List[str]
    category: Optional[str] = None
    in_stock: bool = True
    available_quantity: int = 0


@dataclass
class RecommendationAnalysis:
    """Complete recommendation analysis results."""

    customer_id: str
    recommendations: List[Recommendation]
    purchase_history_summary: Dict[str, int]
    browsing_summary: Dict[str, int]
    seasonal_products: List[str]
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


def load_purchase_history(
    config: PurchaseHistoryConfig, project_root: Path
) -> List[PurchaseRecord]:
    """Load purchase history data from file.

    Args:
        config: Purchase history configuration
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
        raise FileNotFoundError(f"Purchase history file not found: {data_path}")

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
            config.product_id_column,
            config.purchase_date_column,
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
                product_id=str(row[config.product_id_column]),
                purchase_date=row[config.purchase_date_column],
            )

            if config.quantity_column and config.quantity_column in df.columns:
                if pd.notna(row[config.quantity_column]):
                    purchase.quantity = int(row[config.quantity_column])

            if config.category_column and config.category_column in df.columns:
                if pd.notna(row[config.category_column]):
                    purchase.category = str(row[config.category_column])

            if config.price_column and config.price_column in df.columns:
                if pd.notna(row[config.price_column]):
                    purchase.price = float(row[config.price_column])

            purchases.append(purchase)

        logger.info(f"Loaded {len(purchases)} purchase records")
        return purchases

    except pd.errors.EmptyDataError:
        logger.warning(f"Purchase history file is empty: {data_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to load purchase history: {e}")
        raise


def load_browsing_behavior(
    config: BrowsingBehaviorConfig, project_root: Path
) -> List[BrowsingRecord]:
    """Load browsing behavior data from file.

    Args:
        config: Browsing behavior configuration
        project_root: Project root directory

    Returns:
        List of BrowsingRecord objects

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        raise FileNotFoundError(f"Browsing behavior file not found: {data_path}")

    browsing_records = []

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        required_columns = [
            config.customer_id_column,
            config.product_id_column,
            config.timestamp_column,
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df[config.timestamp_column] = pd.to_datetime(df[config.timestamp_column])

        for _, row in df.iterrows():
            browsing = BrowsingRecord(
                customer_id=str(row[config.customer_id_column]),
                product_id=str(row[config.product_id_column]),
                timestamp=row[config.timestamp_column],
            )

            if (
                config.action_type_column
                and config.action_type_column in df.columns
            ):
                if pd.notna(row[config.action_type_column]):
                    browsing.action_type = str(row[config.action_type_column])

            if (
                config.view_duration_column
                and config.view_duration_column in df.columns
            ):
                if pd.notna(row[config.view_duration_column]):
                    browsing.view_duration = float(
                        row[config.view_duration_column]
                    )

            browsing_records.append(browsing)

        logger.info(f"Loaded {len(browsing_records)} browsing records")
        return browsing_records

    except pd.errors.EmptyDataError:
        logger.warning(f"Browsing behavior file is empty: {data_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to load browsing behavior: {e}")
        raise


def load_inventory(
    config: InventoryConfig, project_root: Path
) -> Dict[str, InventoryItem]:
    """Load inventory data from file.

    Args:
        config: Inventory configuration
        project_root: Project root directory

    Returns:
        Dictionary mapping product_id to InventoryItem

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        raise FileNotFoundError(f"Inventory file not found: {data_path}")

    inventory = {}

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        required_columns = [
            config.product_id_column,
            config.quantity_column,
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        for _, row in df.iterrows():
            product_id = str(row[config.product_id_column])
            quantity = int(row[config.quantity_column])

            in_stock = True
            if config.in_stock_column and config.in_stock_column in df.columns:
                if pd.notna(row[config.in_stock_column]):
                    in_stock = bool(row[config.in_stock_column])
                else:
                    in_stock = quantity > 0
            else:
                in_stock = quantity > 0

            inventory[product_id] = InventoryItem(
                product_id=product_id, quantity=quantity, in_stock=in_stock
            )

        logger.info(f"Loaded inventory for {len(inventory)} products")
        return inventory

    except pd.errors.EmptyDataError:
        logger.warning(f"Inventory file is empty: {data_path}")
        return {}
    except Exception as e:
        logger.error(f"Failed to load inventory: {e}")
        raise


def analyze_purchase_history(
    purchases: List[PurchaseRecord], customer_id: str
) -> Dict[str, float]:
    """Analyze purchase history for a customer.

    Args:
        purchases: List of purchase records
        customer_id: Customer identifier

    Returns:
        Dictionary mapping product_id to purchase score
    """
    customer_purchases = [
        p for p in purchases if p.customer_id == customer_id
    ]

    product_scores: Dict[str, float] = defaultdict(float)
    recent_cutoff = datetime.now() - timedelta(days=90)

    for purchase in customer_purchases:
        recency_factor = 1.0
        if purchase.purchase_date >= recent_cutoff:
            days_ago = (datetime.now() - purchase.purchase_date).days
            recency_factor = 1.0 + (1.0 - days_ago / 90.0)

        quantity_factor = purchase.quantity
        product_scores[purchase.product_id] += (
            recency_factor * quantity_factor
        )

    return dict(product_scores)


def analyze_browsing_behavior(
    browsing_records: List[BrowsingRecord], customer_id: str
) -> Dict[str, float]:
    """Analyze browsing behavior for a customer.

    Args:
        browsing_records: List of browsing records
        customer_id: Customer identifier

    Returns:
        Dictionary mapping product_id to browsing score
    """
    customer_browsing = [
        b for b in browsing_records if b.customer_id == customer_id
    ]

    product_scores: Dict[str, float] = defaultdict(float)
    recent_cutoff = datetime.now() - timedelta(days=30)

    for browsing in customer_browsing:
        if browsing.timestamp < recent_cutoff:
            continue

        recency_factor = 1.0
        days_ago = (datetime.now() - browsing.timestamp).days
        recency_factor = 1.0 + (1.0 - days_ago / 30.0)

        duration_factor = 1.0
        if browsing.view_duration:
            duration_factor = min(2.0, browsing.view_duration / 60.0)

        action_factor = 1.0
        if browsing.action_type:
            action_multipliers = {
                "view": 1.0,
                "add_to_cart": 2.0,
                "wishlist": 1.5,
                "compare": 1.2,
            }
            action_factor = action_multipliers.get(
                browsing.action_type.lower(), 1.0
            )

        product_scores[browsing.product_id] += (
            recency_factor * duration_factor * action_factor
        )

    return dict(product_scores)


def identify_seasonal_products(
    purchases: List[PurchaseRecord],
    seasonal_config: SeasonalTrendsConfig,
) -> Set[str]:
    """Identify products with seasonal trends.

    Args:
        purchases: List of purchase records
        seasonal_config: Seasonal trends configuration

    Returns:
        Set of product IDs with seasonal patterns
    """
    if not seasonal_config.enable_seasonal_boost:
        return set()

    current_month = datetime.now().month
    current_season = None

    for season, months in seasonal_config.seasonal_categories.items():
        if current_month in months:
            current_season = season
            break

    if not current_season:
        return set()

    seasonal_products = set()
    monthly_counts: Dict[int, Dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )

    for purchase in purchases:
        month = purchase.purchase_date.month
        monthly_counts[month][purchase.product_id] += purchase.quantity

    season_months = seasonal_config.seasonal_categories.get(current_season, [])
    other_months = [
        m
        for m in range(1, 13)
        if m not in season_months
    ]

    for product_id in set(p.product_id for p in purchases):
        season_total = sum(
            monthly_counts[m].get(product_id, 0) for m in season_months
        )
        other_total = sum(
            monthly_counts[m].get(product_id, 0) for m in other_months
        )

        if season_total > 0 and other_total > 0:
            ratio = season_total / (other_total + 1)
            if ratio >= 1.5:
                seasonal_products.add(product_id)

    return seasonal_products


def generate_recommendations(
    customer_id: str,
    purchase_scores: Dict[str, float],
    browsing_scores: Dict[str, float],
    seasonal_products: Set[str],
    inventory: Dict[str, InventoryItem],
    purchases: List[PurchaseRecord],
    config: RecommendationConfig,
    seasonal_config: SeasonalTrendsConfig,
) -> List[Recommendation]:
    """Generate personalized recommendations for a customer.

    Args:
        customer_id: Customer identifier
        purchase_scores: Purchase history scores
        browsing_scores: Browsing behavior scores
        seasonal_products: Set of seasonal product IDs
        inventory: Dictionary of inventory items
        purchases: List of purchase records
        config: Recommendation configuration
        seasonal_config: Seasonal trends configuration

    Returns:
        List of recommendations sorted by score
    """
    all_products = set(purchase_scores.keys()) | set(browsing_scores.keys())
    purchased_products = set(purchase_scores.keys())

    recommendations = []

    for product_id in all_products:
        if product_id in purchased_products:
            continue

        if product_id not in inventory:
            if config.require_in_stock:
                continue
        else:
            item = inventory[product_id]
            if config.require_in_stock and not item.in_stock:
                continue

        purchase_score = purchase_scores.get(product_id, 0.0)
        browsing_score = browsing_scores.get(product_id, 0.0)

        seasonal_score = 0.0
        if product_id in seasonal_products:
            seasonal_score = seasonal_config.seasonal_boost_multiplier

        total_score = (
            purchase_score * config.purchase_history_weight
            + browsing_score * config.browsing_weight
            + seasonal_score * config.seasonal_weight
        )

        if total_score < config.min_score_threshold:
            continue

        reasons = []
        if purchase_score > 0:
            reasons.append("Based on your purchase history")
        if browsing_score > 0:
            reasons.append("Based on your browsing behavior")
        if product_id in seasonal_products:
            reasons.append("Seasonal trend")

        priority = RecommendationPriority.MEDIUM
        if total_score > 0.7:
            priority = RecommendationPriority.HIGH
        elif total_score < 0.5:
            priority = RecommendationPriority.LOW

        category = None
        for purchase in purchases:
            if purchase.product_id == product_id:
                category = purchase.category
                break

        in_stock = True
        available_quantity = 0
        if product_id in inventory:
            item = inventory[product_id]
            in_stock = item.in_stock
            available_quantity = item.quantity

        recommendations.append(
            Recommendation(
                product_id=product_id,
                customer_id=customer_id,
                score=total_score,
                priority=priority,
                reasons=reasons,
                category=category,
                in_stock=in_stock,
                available_quantity=available_quantity,
            )
        )

    recommendations.sort(key=lambda x: x.score, reverse=True)
    return recommendations[: config.max_recommendations]


def write_markdown_report(
    analysis: RecommendationAnalysis, output_path: Path
) -> None:
    """Write recommendation report to markdown file.

    Args:
        analysis: Recommendation analysis results
        output_path: Path to write the report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Personalized Shopping Recommendations\n\n")
        f.write(
            f"**Generated:** {analysis.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )
        f.write(f"**Customer ID:** {analysis.customer_id}\n\n")

        f.write("## Recommendations\n\n")
        if analysis.recommendations:
            f.write(
                "| Product ID | Score | Priority | In Stock | "
                "Available | Reasons |\n"
            )
            f.write(
                "|------------|-------|----------|----------|"
                "-----------|----------|\n"
            )
            for rec in analysis.recommendations:
                reasons_str = "; ".join(rec.reasons)
                f.write(
                    f"| {rec.product_id} | {rec.score:.2f} | "
                    f"{rec.priority.value} | {rec.in_stock} | "
                    f"{rec.available_quantity} | {reasons_str} |\n"
                )
        else:
            f.write("No recommendations available.\n")
        f.write("\n")

        f.write("## Purchase History Summary\n\n")
        if analysis.purchase_history_summary:
            f.write("| Product ID | Purchase Count |\n")
            f.write("|------------|----------------|\n")
            for product_id, count in sorted(
                analysis.purchase_history_summary.items(),
                key=lambda x: -x[1],
            )[:10]:
                f.write(f"| {product_id} | {count} |\n")
        f.write("\n")

        f.write("## Browsing Summary\n\n")
        if analysis.browsing_summary:
            f.write("| Product ID | View Count |\n")
            f.write("|------------|------------|\n")
            for product_id, count in sorted(
                analysis.browsing_summary.items(),
                key=lambda x: -x[1],
            )[:10]:
                f.write(f"| {product_id} | {count} |\n")

    logger.info(f"Report written to {output_path}")


def process_recommendations(config_path: Path, customer_id: str) -> RecommendationAnalysis:
    """Process data and generate recommendations for a customer.

    Args:
        config_path: Path to configuration file
        customer_id: Customer identifier

    Returns:
        Complete recommendation analysis

    Raises:
        FileNotFoundError: If config or data files are missing
        ValueError: If configuration is invalid
    """
    config = load_config(config_path)
    project_root = config_path.parent

    purchases = load_purchase_history(config.purchase_history, project_root)
    browsing_records = load_browsing_behavior(
        config.browsing_behavior, project_root
    )
    inventory = load_inventory(config.inventory, project_root)

    purchase_scores = analyze_purchase_history(purchases, customer_id)
    browsing_scores = analyze_browsing_behavior(browsing_records, customer_id)
    seasonal_products = identify_seasonal_products(
        purchases, config.seasonal
    )

    recommendations = generate_recommendations(
        customer_id,
        purchase_scores,
        browsing_scores,
        seasonal_products,
        inventory,
        purchases,
        config.recommendation,
        config.seasonal,
    )

    purchase_summary = {
        p.product_id: sum(
            1
            for pur in purchases
            if pur.customer_id == customer_id and pur.product_id == p.product_id
        )
        for p in purchases
        if p.customer_id == customer_id
    }

    browsing_summary = {
        b.product_id: sum(
            1
            for br in browsing_records
            if br.customer_id == customer_id and br.product_id == b.product_id
        )
        for b in browsing_records
        if b.customer_id == customer_id
    }

    analysis = RecommendationAnalysis(
        customer_id=customer_id,
        recommendations=recommendations,
        purchase_history_summary=purchase_summary,
        browsing_summary=browsing_summary,
        seasonal_products=list(seasonal_products),
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
        "customer_id": customer_id,
        "generated_at": analysis.generated_at.isoformat(),
        "recommendations": [
            {
                "product_id": rec.product_id,
                "score": rec.score,
                "priority": rec.priority.value,
                "reasons": rec.reasons,
                "category": rec.category,
                "in_stock": rec.in_stock,
                "available_quantity": rec.available_quantity,
            }
            for rec in recommendations
        ],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Recommendations saved to {output_path}")

    return analysis


def main() -> None:
    """Main entry point for the shopping recommendation engine."""
    import sys

    settings = AppSettings()
    config_path = Path(settings.config_path)

    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent
        config_path = project_root / config_path

    if len(sys.argv) < 2:
        logger.error("Customer ID required as command line argument")
        sys.exit(1)

    customer_id = sys.argv[1]

    try:
        logger.info(f"Starting recommendation generation for customer: {customer_id}")
        analysis = process_recommendations(config_path, customer_id)
        logger.info(
            f"Processing complete. Generated {len(analysis.recommendations)} "
            f"recommendations for customer {customer_id}."
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
