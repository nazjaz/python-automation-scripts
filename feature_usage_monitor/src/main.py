"""Feature Usage Monitor.

Monitors application feature usage, identifies unused features, tracks
adoption rates, and generates product usage insights for product teams.
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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


class UsageDataConfig(BaseModel):
    """Configuration for usage data source."""

    file_path: str = Field(..., description="Path to usage data file")
    format: str = Field(default="csv", description="File format: csv or json")
    user_id_column: str = Field(
        default="user_id", description="Column name for user ID"
    )
    feature_name_column: str = Field(
        default="feature_name", description="Column name for feature name"
    )
    timestamp_column: str = Field(
        default="timestamp", description="Column name for event timestamp"
    )
    event_type_column: Optional[str] = Field(
        default=None, description="Column name for event type"
    )
    session_id_column: Optional[str] = Field(
        default=None, description="Column name for session ID"
    )


class FeatureConfig(BaseModel):
    """Configuration for feature definitions."""

    features_file: Optional[str] = Field(
        default=None, description="Path to file listing all features"
    )
    min_usage_threshold: int = Field(
        default=10, description="Minimum usage count to consider feature active"
    )
    adoption_threshold_days: int = Field(
        default=7, description="Days to consider for adoption rate calculation"
    )
    unused_threshold_percentage: float = Field(
        default=0.01, description="Percentage threshold for unused feature detection"
    )


class AnalysisConfig(BaseModel):
    """Configuration for analysis parameters."""

    lookback_days: int = Field(
        default=30, description="Days of historical data to analyze"
    )
    analysis_window_days: int = Field(
        default=7, description="Time window for trend analysis"
    )
    min_users_for_feature: int = Field(
        default=5, description="Minimum unique users for feature analysis"
    )


class ReportConfig(BaseModel):
    """Configuration for report generation."""

    output_format: str = Field(
        default="markdown", description="Report format: markdown or html"
    )
    output_path: str = Field(
        default="logs/feature_usage_report.md",
        description="Path for output report",
    )
    include_top_features: int = Field(
        default=20, description="Number of top features to highlight"
    )


class Config(BaseModel):
    """Main configuration model."""

    usage_data: UsageDataConfig = Field(
        ..., description="Usage data source configuration"
    )
    features: FeatureConfig = Field(
        default_factory=FeatureConfig,
        description="Feature definition settings",
    )
    analysis: AnalysisConfig = Field(
        default_factory=AnalysisConfig,
        description="Analysis parameters",
    )
    report: ReportConfig = Field(
        default_factory=ReportConfig, description="Report generation settings"
    )


class AppSettings(BaseSettings):
    """Application settings from environment variables."""

    config_path: str = "config.yaml"


@dataclass
class FeatureUsage:
    """Usage statistics for a feature."""

    feature_name: str
    total_usage_count: int
    unique_users: int
    adoption_rate: float
    avg_usage_per_user: float
    last_used: Optional[datetime] = None
    usage_trend: str = "stable"


@dataclass
class UnusedFeature:
    """Information about an unused feature."""

    feature_name: str
    total_usage_count: int
    unique_users: int
    last_used: Optional[datetime] = None
    days_since_last_use: Optional[int] = None


@dataclass
class AdoptionMetrics:
    """Adoption metrics for a feature."""

    feature_name: str
    total_users: int
    adopted_users: int
    adoption_percentage: float
    adoption_velocity: float
    days_to_adoption: Optional[float] = None


@dataclass
class UsageInsights:
    """Complete usage insights analysis."""

    total_features: int
    active_features: int
    unused_features: int
    feature_usage_stats: List[FeatureUsage]
    unused_features_list: List[UnusedFeature]
    adoption_metrics: List[AdoptionMetrics]
    top_features: List[str]
    insights: List[str]
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


def load_usage_data(
    config: UsageDataConfig, project_root: Path
) -> pd.DataFrame:
    """Load usage data from CSV or JSON file.

    Args:
        config: Usage data configuration
        project_root: Project root directory

    Returns:
        DataFrame with usage data

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        raise FileNotFoundError(f"Usage data file not found: {data_path}")

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        required_columns = [
            config.user_id_column,
            config.feature_name_column,
            config.timestamp_column,
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df[config.timestamp_column] = pd.to_datetime(
            df[config.timestamp_column]
        )

        logger.info(f"Loaded {len(df)} usage events from {data_path}")
        return df

    except pd.errors.EmptyDataError:
        logger.warning(f"Data file is empty: {data_path}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Failed to load usage data: {e}")
        raise


def load_feature_list(features_file: Optional[Path]) -> Set[str]:
    """Load list of all features from file.

    Args:
        features_file: Path to features file (optional)

    Returns:
        Set of feature names
    """
    if not features_file or not features_file.exists():
        return set()

    try:
        if features_file.suffix.lower() == ".csv":
            df = pd.read_csv(features_file)
            if "feature_name" in df.columns:
                return set(df["feature_name"].astype(str))
            return set()
        elif features_file.suffix.lower() == ".json":
            with open(features_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return set(str(item) for item in data)
            elif isinstance(data, dict) and "features" in data:
                return set(str(f) for f in data["features"])
        elif features_file.suffix.lower() == ".txt":
            with open(features_file, "r", encoding="utf-8") as f:
                return set(line.strip() for line in f if line.strip())
    except Exception as e:
        logger.warning(f"Failed to load feature list: {e}")

    return set()


def analyze_feature_usage(
    df: pd.DataFrame,
    config: UsageDataConfig,
    analysis_config: AnalysisConfig,
) -> Dict[str, FeatureUsage]:
    """Analyze usage statistics for each feature.

    Args:
        df: DataFrame with usage data
        config: Usage data configuration
        analysis_config: Analysis configuration

    Returns:
        Dictionary mapping feature name to FeatureUsage
    """
    if df.empty:
        return {}

    cutoff_date = datetime.now() - timedelta(days=analysis_config.lookback_days)
    df_filtered = df[df[config.timestamp_column] >= cutoff_date].copy()

    feature_stats: Dict[str, Dict] = defaultdict(
        lambda: {
            "usage_count": 0,
            "users": set(),
            "timestamps": [],
        }
    )

    for _, row in df_filtered.iterrows():
        feature_name = str(row[config.feature_name_column])
        user_id = str(row[config.user_id_column])
        timestamp = row[config.timestamp_column]

        feature_stats[feature_name]["usage_count"] += 1
        feature_stats[feature_name]["users"].add(user_id)
        feature_stats[feature_name]["timestamps"].append(timestamp)

    trend_window = datetime.now() - timedelta(
        days=analysis_config.analysis_window_days
    )

    feature_usage = {}

    for feature_name, stats in feature_stats.items():
        total_usage = stats["usage_count"]
        unique_users = len(stats["users"])
        avg_usage_per_user = (
            total_usage / unique_users if unique_users > 0 else 0.0
        )

        recent_usage = sum(
            1 for ts in stats["timestamps"] if ts >= trend_window
        )
        older_usage = total_usage - recent_usage

        if older_usage > 0:
            trend_ratio = recent_usage / older_usage
            if trend_ratio > 1.2:
                trend = "increasing"
            elif trend_ratio < 0.8:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "new" if recent_usage > 0 else "stable"

        last_used = max(stats["timestamps"]) if stats["timestamps"] else None

        feature_usage[feature_name] = FeatureUsage(
            feature_name=feature_name,
            total_usage_count=total_usage,
            unique_users=unique_users,
            adoption_rate=0.0,
            avg_usage_per_user=avg_usage_per_user,
            last_used=last_used,
            usage_trend=trend,
        )

    logger.info(f"Analyzed usage for {len(feature_usage)} features")
    return feature_usage


def calculate_adoption_rates(
    df: pd.DataFrame,
    config: UsageDataConfig,
    feature_config: FeatureConfig,
    analysis_config: AnalysisConfig,
) -> Dict[str, AdoptionMetrics]:
    """Calculate adoption rates for features.

    Args:
        df: DataFrame with usage data
        config: Usage data configuration
        feature_config: Feature configuration
        analysis_config: Analysis configuration

    Returns:
        Dictionary mapping feature name to AdoptionMetrics
    """
    if df.empty:
        return {}

    cutoff_date = datetime.now() - timedelta(days=analysis_config.lookback_days)
    df_filtered = df[df[config.timestamp_column] >= cutoff_date].copy()

    total_users = df_filtered[config.user_id_column].nunique()

    feature_adoption: Dict[str, Dict] = defaultdict(
        lambda: {
            "users": set(),
            "first_use": {},
        }
    )

    for _, row in df_filtered.iterrows():
        feature_name = str(row[config.feature_name_column])
        user_id = str(row[config.user_id_column])
        timestamp = row[config.timestamp_column]

        feature_adoption[feature_name]["users"].add(user_id)

        if (
            user_id not in feature_adoption[feature_name]["first_use"]
            or timestamp < feature_adoption[feature_name]["first_use"][user_id]
        ):
            feature_adoption[feature_name]["first_use"][user_id] = timestamp

    adoption_metrics = {}

    for feature_name, stats in feature_adoption.items():
        adopted_users = len(stats["users"])
        adoption_percentage = (
            (adopted_users / total_users) * 100 if total_users > 0 else 0.0
        )

        days_to_adoption = None
        if stats["first_use"]:
            first_uses = list(stats["first_use"].values())
            avg_first_use = sum(
                (datetime.now() - ts).days for ts in first_uses
            ) / len(first_uses)
            days_to_adoption = avg_first_use

        adoption_velocity = (
            adopted_users / analysis_config.lookback_days
            if analysis_config.lookback_days > 0
            else 0.0
        )

        adoption_metrics[feature_name] = AdoptionMetrics(
            feature_name=feature_name,
            total_users=total_users,
            adopted_users=adopted_users,
            adoption_percentage=adoption_percentage,
            adoption_velocity=adoption_velocity,
            days_to_adoption=days_to_adoption,
        )

    logger.info(f"Calculated adoption rates for {len(adoption_metrics)} features")
    return adoption_metrics


def identify_unused_features(
    feature_usage: Dict[str, FeatureUsage],
    all_features: Set[str],
    feature_config: FeatureConfig,
    total_users: int,
) -> List[UnusedFeature]:
    """Identify unused or rarely used features.

    Args:
        feature_usage: Dictionary of feature usage statistics
        all_features: Set of all known features
        feature_config: Feature configuration
        total_users: Total number of users

    Returns:
        List of unused features
    """
    unused_features = []

    used_features = set(feature_usage.keys())
    missing_features = all_features - used_features

    for feature_name in missing_features:
        unused_features.append(
            UnusedFeature(
                feature_name=feature_name,
                total_usage_count=0,
                unique_users=0,
                last_used=None,
                days_since_last_use=None,
            )
        )

    threshold_users = max(
        1, int(total_users * feature_config.unused_threshold_percentage)
    )

    for feature_name, usage in feature_usage.items():
        if (
            usage.unique_users < threshold_users
            or usage.total_usage_count < feature_config.min_usage_threshold
        ):
            days_since_last_use = None
            if usage.last_used:
                days_since_last_use = (datetime.now() - usage.last_used).days

            unused_features.append(
                UnusedFeature(
                    feature_name=feature_name,
                    total_usage_count=usage.total_usage_count,
                    unique_users=usage.unique_users,
                    last_used=usage.last_used,
                    days_since_last_use=days_since_last_use,
                )
            )

    unused_features.sort(
        key=lambda x: (
            x.total_usage_count,
            x.unique_users if x.unique_users else 0,
        )
    )

    logger.info(f"Identified {len(unused_features)} unused or rarely used features")
    return unused_features


def generate_insights(
    feature_usage: Dict[str, FeatureUsage],
    unused_features: List[UnusedFeature],
    adoption_metrics: Dict[str, AdoptionMetrics],
) -> List[str]:
    """Generate actionable insights from usage data.

    Args:
        feature_usage: Dictionary of feature usage statistics
        unused_features: List of unused features
        adoption_metrics: Dictionary of adoption metrics

    Returns:
        List of insight strings
    """
    insights = []

    if unused_features:
        insights.append(
            f"{len(unused_features)} features are unused or rarely used. "
            "Consider deprecation or improved onboarding."
        )

    top_features = sorted(
        feature_usage.values(),
        key=lambda x: x.total_usage_count,
        reverse=True,
    )[:5]

    if top_features:
        top_names = ", ".join(f.feature_name for f in top_features)
        insights.append(
            f"Top performing features: {top_names}. "
            "Consider promoting similar functionality."
        )

    increasing_trend = [
        f.feature_name
        for f in feature_usage.values()
        if f.usage_trend == "increasing"
    ]
    if increasing_trend:
        insights.append(
            f"{len(increasing_trend)} features show increasing usage trends. "
            "Monitor for scaling needs."
        )

    decreasing_trend = [
        f.feature_name
        for f in feature_usage.values()
        if f.usage_trend == "decreasing"
    ]
    if decreasing_trend:
        insights.append(
            f"{len(decreasing_trend)} features show decreasing usage. "
            "Investigate user feedback and consider improvements."
        )

    high_adoption = [
        m.feature_name
        for m in adoption_metrics.values()
        if m.adoption_percentage > 50.0
    ]
    if high_adoption:
        insights.append(
            f"{len(high_adoption)} features have adoption rates above 50%. "
            "These are successful features to learn from."
        )

    low_adoption = [
        m.feature_name
        for m in adoption_metrics.values()
        if m.adoption_percentage < 5.0 and m.adopted_users > 0
    ]
    if low_adoption:
        insights.append(
            f"{len(low_adoption)} features have low adoption rates (<5%). "
            "Consider improved discoverability or user education."
        )

    return insights


def write_markdown_report(insights: UsageInsights, output_path: Path) -> None:
    """Write usage insights report to markdown file.

    Args:
        insights: Usage insights data
        output_path: Path to write the report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Feature Usage Insights Report\n\n")
        f.write(
            f"**Generated:** {insights.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        f.write("## Executive Summary\n\n")
        f.write(f"- **Total Features:** {insights.total_features}\n")
        f.write(f"- **Active Features:** {insights.active_features}\n")
        f.write(f"- **Unused Features:** {insights.unused_features}\n")
        f.write("\n")

        f.write("## Key Insights\n\n")
        for insight in insights.insights:
            f.write(f"- {insight}\n")
        f.write("\n")

        f.write("## Top Features by Usage\n\n")
        if insights.top_features:
            f.write("| Rank | Feature Name |\n")
            f.write("|------|--------------|\n")
            for i, feature_name in enumerate(insights.top_features[:20], 1):
                f.write(f"| {i} | {feature_name} |\n")
            f.write("\n")

        f.write("## Feature Usage Statistics\n\n")
        if insights.feature_usage_stats:
            f.write(
                "| Feature | Total Usage | Unique Users | Avg per User | "
                "Trend |\n"
            )
            f.write(
                "|--------|-------------|--------------|--------------|"
                "-------|\n"
            )
            for usage in sorted(
                insights.feature_usage_stats,
                key=lambda x: x.total_usage_count,
                reverse=True,
            )[:20]:
                f.write(
                    f"| {usage.feature_name} | {usage.total_usage_count} | "
                    f"{usage.unique_users} | {usage.avg_usage_per_user:.2f} | "
                    f"{usage.usage_trend} |\n"
                )
            f.write("\n")

        f.write("## Unused or Rarely Used Features\n\n")
        if insights.unused_features_list:
            f.write(
                "| Feature | Usage Count | Unique Users | Days Since Last Use |\n"
            )
            f.write(
                "|---------|-------------|--------------|---------------------|\n"
            )
            for unused in insights.unused_features_list[:20]:
                days_str = (
                    str(unused.days_since_last_use)
                    if unused.days_since_last_use is not None
                    else "N/A"
                )
                f.write(
                    f"| {unused.feature_name} | {unused.total_usage_count} | "
                    f"{unused.unique_users} | {days_str} |\n"
                )
            f.write("\n")

        f.write("## Adoption Metrics\n\n")
        if insights.adoption_metrics:
            f.write(
                "| Feature | Adopted Users | Adoption % | "
                "Adoption Velocity |\n"
            )
            f.write(
                "|---------|----------------|------------|"
                "-------------------|\n"
            )
            for metric in sorted(
                insights.adoption_metrics,
                key=lambda x: x.adoption_percentage,
                reverse=True,
            )[:20]:
                f.write(
                    f"| {metric.feature_name} | {metric.adopted_users} | "
                    f"{metric.adoption_percentage:.1f}% | "
                    f"{metric.adoption_velocity:.2f} users/day |\n"
                )

    logger.info(f"Report written to {output_path}")


def process_feature_usage(config_path: Path) -> UsageInsights:
    """Process feature usage data and generate insights.

    Args:
        config_path: Path to configuration file

    Returns:
        Complete usage insights

    Raises:
        FileNotFoundError: If config or data files are missing
        ValueError: If configuration is invalid
    """
    config = load_config(config_path)
    project_root = config_path.parent

    df = load_usage_data(config.usage_data, project_root)

    if df.empty:
        logger.warning("No usage data available for analysis")
        return UsageInsights(
            total_features=0,
            active_features=0,
            unused_features=0,
            feature_usage_stats=[],
            unused_features_list=[],
            adoption_metrics=[],
            top_features=[],
            insights=[],
            generated_at=datetime.now(),
        )

    all_features = set()
    if config.features.features_file:
        features_file = Path(config.features.features_file)
        if not features_file.is_absolute():
            features_file = project_root / features_file
        all_features = load_feature_list(features_file)

    if not all_features:
        all_features = set(df[config.usage_data.feature_name_column].unique())

    feature_usage = analyze_feature_usage(
        df, config.usage_data, config.analysis
    )

    total_users = df[config.usage_data.user_id_column].nunique()

    unused_features = identify_unused_features(
        feature_usage, all_features, config.features, total_users
    )

    adoption_metrics_dict = calculate_adoption_rates(
        df, config.usage_data, config.features, config.analysis
    )

    top_features = [
        f.feature_name
        for f in sorted(
            feature_usage.values(),
            key=lambda x: x.total_usage_count,
            reverse=True,
        )[: config.report.include_top_features]
    ]

    insights_list = generate_insights(
        feature_usage, unused_features, adoption_metrics_dict
    )

    usage_insights = UsageInsights(
        total_features=len(all_features),
        active_features=len(feature_usage),
        unused_features=len(unused_features),
        feature_usage_stats=list(feature_usage.values()),
        unused_features_list=unused_features,
        adoption_metrics=list(adoption_metrics_dict.values()),
        top_features=top_features,
        insights=insights_list,
        generated_at=datetime.now(),
    )

    report_path = Path(config.report.output_path)
    if not report_path.is_absolute():
        report_path = project_root / report_path

    write_markdown_report(usage_insights, report_path)

    return usage_insights


def main() -> None:
    """Main entry point for the feature usage monitor."""
    settings = AppSettings()
    config_path = Path(settings.config_path)

    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent
        config_path = project_root / config_path

    try:
        logger.info("Starting feature usage monitoring")
        insights = process_feature_usage(config_path)
        logger.info(
            f"Analysis complete. Analyzed {insights.total_features} features, "
            f"identified {insights.unused_features} unused features, "
            f"and generated {len(insights.insights)} insights."
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
