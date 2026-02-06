"""Deployment Monitor.

Monitors application deployment frequency, tracks deployment success rates,
identifies regression patterns, and generates release quality metrics.
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DeploymentStatus(str, Enum):
    """Deployment status enumeration."""

    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    PARTIAL = "partial"


class RegressionSeverity(str, Enum):
    """Regression severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DeploymentDataConfig(BaseModel):
    """Configuration for deployment data source."""

    file_path: str = Field(..., description="Path to deployment data file")
    format: str = Field(default="csv", description="File format: csv or json")
    deployment_id_column: str = Field(
        default="deployment_id", description="Column name for deployment ID"
    )
    timestamp_column: str = Field(
        default="timestamp", description="Column name for deployment timestamp"
    )
    status_column: str = Field(
        default="status", description="Column name for deployment status"
    )
    environment_column: Optional[str] = Field(
        default=None, description="Column name for environment"
    )
    version_column: Optional[str] = Field(
        default=None, description="Column name for version"
    )
    duration_column: Optional[str] = Field(
        default=None, description="Column name for deployment duration"
    )
    error_message_column: Optional[str] = Field(
        default=None, description="Column name for error message"
    )


class RegressionConfig(BaseModel):
    """Configuration for regression detection."""

    lookback_window_days: int = Field(
        default=30, description="Days to look back for baseline comparison"
    )
    comparison_window_days: int = Field(
        default=7, description="Days in recent window for comparison"
    )
    success_rate_threshold: float = Field(
        default=0.05, description="Success rate drop threshold for regression"
    )
    failure_rate_threshold: float = Field(
        default=0.20, description="Failure rate threshold for critical regression"
    )


class MetricsConfig(BaseModel):
    """Configuration for quality metrics."""

    mttr_window_days: int = Field(
        default=30, description="Days to calculate MTTR over"
    )
    deployment_frequency_window_days: int = Field(
        default=7, description="Days to calculate deployment frequency over"
    )
    change_failure_rate_window_days: int = Field(
        default=30, description="Days to calculate change failure rate over"
    )


class ReportConfig(BaseModel):
    """Configuration for report generation."""

    output_format: str = Field(
        default="markdown", description="Report format: markdown or html"
    )
    output_path: str = Field(
        default="logs/deployment_metrics.md",
        description="Path for metrics report",
    )


class Config(BaseModel):
    """Main configuration model."""

    deployment_data: DeploymentDataConfig = Field(
        ..., description="Deployment data source configuration"
    )
    regression: RegressionConfig = Field(
        default_factory=RegressionConfig,
        description="Regression detection settings",
    )
    metrics: MetricsConfig = Field(
        default_factory=MetricsConfig,
        description="Quality metrics settings",
    )
    report: ReportConfig = Field(
        default_factory=ReportConfig, description="Report generation settings"
    )


class AppSettings(BaseSettings):
    """Application settings from environment variables."""

    config_path: str = "config.yaml"


@dataclass
class DeploymentRecord:
    """Represents a deployment record."""

    deployment_id: str
    timestamp: datetime
    status: DeploymentStatus
    environment: Optional[str] = None
    version: Optional[str] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class RegressionPattern:
    """Identified regression pattern."""

    pattern_type: str
    severity: RegressionSeverity
    description: str
    baseline_metric: float
    current_metric: float
    change_percentage: float
    affected_deployments: List[str] = field(default_factory=list)


@dataclass
class QualityMetrics:
    """Release quality metrics."""

    deployment_frequency: float
    success_rate: float
    failure_rate: float
    change_failure_rate: float
    mean_time_to_recovery: Optional[float] = None
    deployment_count: int = 0
    successful_deployments: int = 0
    failed_deployments: int = 0
    rolled_back_deployments: int = 0


@dataclass
class DeploymentAnalysis:
    """Complete deployment analysis results."""

    quality_metrics: QualityMetrics
    regression_patterns: List[RegressionPattern]
    daily_deployment_counts: Dict[str, int]
    environment_breakdown: Dict[str, Dict[str, int]]
    version_success_rates: Dict[str, float]
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


def load_deployment_data(
    config: DeploymentDataConfig, project_root: Path
) -> List[DeploymentRecord]:
    """Load deployment data from CSV or JSON file.

    Args:
        config: Deployment data configuration
        project_root: Project root directory

    Returns:
        List of DeploymentRecord objects

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        raise FileNotFoundError(f"Deployment data file not found: {data_path}")

    deployments = []

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        required_columns = [
            config.deployment_id_column,
            config.timestamp_column,
            config.status_column,
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df[config.timestamp_column] = pd.to_datetime(df[config.timestamp_column])

        for _, row in df.iterrows():
            status_str = str(row[config.status_column]).lower()
            try:
                status = DeploymentStatus(status_str)
            except ValueError:
                logger.warning(f"Unknown deployment status: {status_str}")
                continue

            deployment = DeploymentRecord(
                deployment_id=str(row[config.deployment_id_column]),
                timestamp=row[config.timestamp_column],
                status=status,
            )

            if config.environment_column and config.environment_column in df.columns:
                if pd.notna(row[config.environment_column]):
                    deployment.environment = str(row[config.environment_column])

            if config.version_column and config.version_column in df.columns:
                if pd.notna(row[config.version_column]):
                    deployment.version = str(row[config.version_column])

            if config.duration_column and config.duration_column in df.columns:
                if pd.notna(row[config.duration_column]):
                    deployment.duration_seconds = float(
                        row[config.duration_column]
                    )

            if (
                config.error_message_column
                and config.error_message_column in df.columns
            ):
                if pd.notna(row[config.error_message_column]):
                    deployment.error_message = str(row[config.error_message_column])

            deployments.append(deployment)

        logger.info(f"Loaded {len(deployments)} deployment records")
        return deployments

    except pd.errors.EmptyDataError:
        logger.warning(f"Deployment data file is empty: {data_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to load deployment data: {e}")
        raise


def calculate_deployment_frequency(
    deployments: List[DeploymentRecord], window_days: int
) -> float:
    """Calculate average deployments per day.

    Args:
        deployments: List of deployment records
        window_days: Time window in days

    Returns:
        Average deployments per day
    """
    if not deployments:
        return 0.0

    cutoff_date = datetime.now() - timedelta(days=window_days)
    recent_deployments = [
        d for d in deployments if d.timestamp >= cutoff_date
    ]

    if not recent_deployments:
        return 0.0

    days_covered = min(
        window_days,
        (datetime.now() - min(d.timestamp for d in recent_deployments)).days + 1,
    )

    return len(recent_deployments) / days_covered if days_covered > 0 else 0.0


def calculate_success_rate(deployments: List[DeploymentRecord]) -> Tuple[float, int, int]:
    """Calculate deployment success rate.

    Args:
        deployments: List of deployment records

    Returns:
        Tuple of (success_rate, successful_count, total_count)
    """
    if not deployments:
        return 0.0, 0, 0

    successful = sum(
        1
        for d in deployments
        if d.status == DeploymentStatus.SUCCESS
    )
    total = len(deployments)

    success_rate = successful / total if total > 0 else 0.0
    return success_rate, successful, total


def calculate_mttr(
    deployments: List[DeploymentRecord], window_days: int
) -> Optional[float]:
    """Calculate Mean Time To Recovery (MTTR) in hours.

    Args:
        deployments: List of deployment records
        window_days: Time window in days

    Returns:
        MTTR in hours, or None if insufficient data
    """
    cutoff_date = datetime.now() - timedelta(days=window_days)
    recent_deployments = [
        d for d in deployments if d.timestamp >= cutoff_date
    ]

    failed_deployments = [
        d
        for d in recent_deployments
        if d.status in [DeploymentStatus.FAILED, DeploymentStatus.ROLLED_BACK]
    ]

    if len(failed_deployments) < 2:
        return None

    recovery_times = []
    sorted_deployments = sorted(recent_deployments, key=lambda x: x.timestamp)

    for i in range(len(sorted_deployments) - 1):
        current = sorted_deployments[i]
        next_deployment = sorted_deployments[i + 1]

        if current.status in [
            DeploymentStatus.FAILED,
            DeploymentStatus.ROLLED_BACK,
        ]:
            if next_deployment.status == DeploymentStatus.SUCCESS:
                recovery_time = (
                    next_deployment.timestamp - current.timestamp
                ).total_seconds() / 3600
                recovery_times.append(recovery_time)

    if not recovery_times:
        return None

    return sum(recovery_times) / len(recovery_times)


def calculate_change_failure_rate(
    deployments: List[DeploymentRecord], window_days: int
) -> float:
    """Calculate change failure rate.

    Args:
        deployments: List of deployment records
        window_days: Time window in days

    Returns:
        Change failure rate (0.0 to 1.0)
    """
    cutoff_date = datetime.now() - timedelta(days=window_days)
    recent_deployments = [
        d for d in deployments if d.timestamp >= cutoff_date
    ]

    if not recent_deployments:
        return 0.0

    failed = sum(
        1
        for d in recent_deployments
        if d.status in [DeploymentStatus.FAILED, DeploymentStatus.ROLLED_BACK]
    )

    return failed / len(recent_deployments)


def identify_regression_patterns(
    deployments: List[DeploymentRecord], config: RegressionConfig
) -> List[RegressionPattern]:
    """Identify regression patterns in deployments.

    Args:
        deployments: List of deployment records
        config: Regression detection configuration

    Returns:
        List of identified regression patterns
    """
    patterns = []
    now = datetime.now()

    baseline_start = now - timedelta(
        days=config.lookback_window_days + config.comparison_window_days
    )
    baseline_end = now - timedelta(days=config.comparison_window_days)
    comparison_start = baseline_end

    baseline_deployments = [
        d
        for d in deployments
        if baseline_start <= d.timestamp < baseline_end
    ]
    comparison_deployments = [
        d for d in deployments if d.timestamp >= comparison_start
    ]

    if not baseline_deployments or not comparison_deployments:
        return patterns

    baseline_success_rate, _, _ = calculate_success_rate(baseline_deployments)
    comparison_success_rate, _, _ = calculate_success_rate(comparison_deployments)

    success_rate_drop = baseline_success_rate - comparison_success_rate

    if success_rate_drop >= config.success_rate_threshold:
        severity = (
            RegressionSeverity.CRITICAL
            if comparison_success_rate <= (1.0 - config.failure_rate_threshold)
            else RegressionSeverity.HIGH
        )

        patterns.append(
            RegressionPattern(
                pattern_type="success_rate_decline",
                severity=severity,
                description=(
                    f"Success rate dropped from {baseline_success_rate:.1%} "
                    f"to {comparison_success_rate:.1%}"
                ),
                baseline_metric=baseline_success_rate,
                current_metric=comparison_success_rate,
                change_percentage=success_rate_drop * 100,
                affected_deployments=[
                    d.deployment_id for d in comparison_deployments
                ],
            )
        )

    baseline_frequency = calculate_deployment_frequency(
        baseline_deployments, config.lookback_window_days
    )
    comparison_frequency = calculate_deployment_frequency(
        comparison_deployments, config.comparison_window_days
    )

    if baseline_frequency > 0:
        frequency_change = (
            (comparison_frequency - baseline_frequency) / baseline_frequency
        ) * 100

        if frequency_change < -20:
            patterns.append(
                RegressionPattern(
                    pattern_type="deployment_frequency_decline",
                    severity=RegressionSeverity.MEDIUM,
                    description=(
                        f"Deployment frequency decreased by {abs(frequency_change):.1f}%"
                    ),
                    baseline_metric=baseline_frequency,
                    current_metric=comparison_frequency,
                    change_percentage=frequency_change,
                    affected_deployments=[
                        d.deployment_id for d in comparison_deployments
                    ],
                )
            )

    return patterns


def calculate_quality_metrics(
    deployments: List[DeploymentRecord], config: MetricsConfig
) -> QualityMetrics:
    """Calculate release quality metrics.

    Args:
        deployments: List of deployment records
        config: Metrics configuration

    Returns:
        QualityMetrics object
    """
    deployment_frequency = calculate_deployment_frequency(
        deployments, config.deployment_frequency_window_days
    )

    success_rate, successful, total = calculate_success_rate(deployments)
    failure_rate = 1.0 - success_rate

    change_failure_rate = calculate_change_failure_rate(
        deployments, config.change_failure_rate_window_days
    )

    mttr = calculate_mttr(deployments, config.mttr_window_days)

    failed_count = sum(
        1
        for d in deployments
        if d.status == DeploymentStatus.FAILED
    )
    rolled_back_count = sum(
        1
        for d in deployments
        if d.status == DeploymentStatus.ROLLED_BACK
    )

    return QualityMetrics(
        deployment_frequency=deployment_frequency,
        success_rate=success_rate,
        failure_rate=failure_rate,
        change_failure_rate=change_failure_rate,
        mean_time_to_recovery=mttr,
        deployment_count=total,
        successful_deployments=successful,
        failed_deployments=failed_count,
        rolled_back_deployments=rolled_back_count,
    )


def generate_daily_counts(
    deployments: List[DeploymentRecord],
) -> Dict[str, int]:
    """Generate daily deployment counts.

    Args:
        deployments: List of deployment records

    Returns:
        Dictionary mapping date strings to deployment counts
    """
    daily_counts = defaultdict(int)
    for deployment in deployments:
        date_key = deployment.timestamp.strftime("%Y-%m-%d")
        daily_counts[date_key] += 1
    return dict(daily_counts)


def generate_environment_breakdown(
    deployments: List[DeploymentRecord],
) -> Dict[str, Dict[str, int]]:
    """Generate breakdown by environment.

    Args:
        deployments: List of deployment records

    Returns:
        Dictionary mapping environment to status counts
    """
    breakdown = defaultdict(lambda: defaultdict(int))
    for deployment in deployments:
        env = deployment.environment or "unknown"
        breakdown[env][deployment.status.value] += 1
    return {env: dict(counts) for env, counts in breakdown.items()}


def generate_version_success_rates(
    deployments: List[DeploymentRecord],
) -> Dict[str, float]:
    """Generate success rates by version.

    Args:
        deployments: List of deployment records

    Returns:
        Dictionary mapping version to success rate
    """
    version_deployments: Dict[str, List[DeploymentRecord]] = defaultdict(list)
    for deployment in deployments:
        if deployment.version:
            version_deployments[deployment.version].append(deployment)

    success_rates = {}
    for version, version_deploys in version_deployments.items():
        success_rate, _, _ = calculate_success_rate(version_deploys)
        success_rates[version] = success_rate

    return success_rates


def write_markdown_report(
    analysis: DeploymentAnalysis, output_path: Path
) -> None:
    """Write deployment metrics report to markdown file.

    Args:
        analysis: Deployment analysis results
        output_path: Path to write the report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Deployment Quality Metrics Report\n\n")
        f.write(
            f"**Generated:** {analysis.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        f.write("## Quality Metrics\n\n")
        metrics = analysis.quality_metrics
        f.write(f"- **Deployment Frequency:** {metrics.deployment_frequency:.2f} deployments/day\n")
        f.write(f"- **Success Rate:** {metrics.success_rate:.1%}\n")
        f.write(f"- **Failure Rate:** {metrics.failure_rate:.1%}\n")
        f.write(f"- **Change Failure Rate:** {metrics.change_failure_rate:.1%}\n")
        if metrics.mean_time_to_recovery:
            f.write(f"- **Mean Time To Recovery (MTTR):** {metrics.mean_time_to_recovery:.2f} hours\n")
        f.write(f"- **Total Deployments:** {metrics.deployment_count}\n")
        f.write(f"- **Successful:** {metrics.successful_deployments}\n")
        f.write(f"- **Failed:** {metrics.failed_deployments}\n")
        f.write(f"- **Rolled Back:** {metrics.rolled_back_deployments}\n")
        f.write("\n")

        f.write("## Regression Patterns\n\n")
        if analysis.regression_patterns:
            f.write(
                "| Pattern Type | Severity | Description | Change % |\n"
            )
            f.write("|--------------|----------|-------------|----------|\n")
            for pattern in analysis.regression_patterns:
                f.write(
                    f"| {pattern.pattern_type.replace('_', ' ').title()} | "
                    f"{pattern.severity.value.upper()} | {pattern.description} | "
                    f"{pattern.change_percentage:.1f}% |\n"
                )
        else:
            f.write("No regression patterns detected.\n")
        f.write("\n")

        f.write("## Environment Breakdown\n\n")
        if analysis.environment_breakdown:
            f.write("| Environment | Success | Failed | Rolled Back |\n")
            f.write("|-------------|---------|--------|-------------|\n")
            for env, counts in sorted(analysis.environment_breakdown.items()):
                f.write(
                    f"| {env} | {counts.get('success', 0)} | "
                    f"{counts.get('failed', 0)} | "
                    f"{counts.get('rolled_back', 0)} |\n"
                )
        f.write("\n")

        f.write("## Version Success Rates\n\n")
        if analysis.version_success_rates:
            f.write("| Version | Success Rate |\n")
            f.write("|---------|--------------|\n")
            for version, rate in sorted(
                analysis.version_success_rates.items(),
                key=lambda x: -x[1],
            )[:20]:
                f.write(f"| {version} | {rate:.1%} |\n")

    logger.info(f"Report written to {output_path}")


def process_deployments(config_path: Path) -> DeploymentAnalysis:
    """Process deployment data and generate analysis.

    Args:
        config_path: Path to configuration file

    Returns:
        Complete deployment analysis

    Raises:
        FileNotFoundError: If config or data files are missing
        ValueError: If configuration is invalid
    """
    config = load_config(config_path)
    project_root = config_path.parent

    deployments = load_deployment_data(config.deployment_data, project_root)

    if not deployments:
        logger.warning("No deployment data available for analysis")
        return DeploymentAnalysis(
            quality_metrics=QualityMetrics(
                deployment_frequency=0.0,
                success_rate=0.0,
                failure_rate=0.0,
                change_failure_rate=0.0,
            ),
            regression_patterns=[],
            daily_deployment_counts={},
            environment_breakdown={},
            version_success_rates={},
            generated_at=datetime.now(),
        )

    quality_metrics = calculate_quality_metrics(deployments, config.metrics)
    regression_patterns = identify_regression_patterns(
        deployments, config.regression
    )
    daily_counts = generate_daily_counts(deployments)
    environment_breakdown = generate_environment_breakdown(deployments)
    version_success_rates = generate_version_success_rates(deployments)

    analysis = DeploymentAnalysis(
        quality_metrics=quality_metrics,
        regression_patterns=regression_patterns,
        daily_deployment_counts=daily_counts,
        environment_breakdown=environment_breakdown,
        version_success_rates=version_success_rates,
        generated_at=datetime.now(),
    )

    report_path = Path(config.report.output_path)
    if not report_path.is_absolute():
        report_path = project_root / report_path

    write_markdown_report(analysis, report_path)

    return analysis


def main() -> None:
    """Main entry point for the deployment monitor."""
    settings = AppSettings()
    config_path = Path(settings.config_path)

    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent
        config_path = project_root / config_path

    try:
        logger.info("Starting deployment monitoring analysis")
        analysis = process_deployments(config_path)
        logger.info(
            f"Analysis complete. Processed {analysis.quality_metrics.deployment_count} "
            f"deployments, identified {len(analysis.regression_patterns)} regression patterns."
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
