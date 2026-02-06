"""Customer onboarding monitoring and optimization tool.

This module provides functionality to:

- Load customer onboarding data from a CSV file.
- Compute completion rates across onboarding stages.
- Identify bottleneck stages with high drop off.
- Track time-to-value for customers.
- Generate structured recommendations for process optimization.

The tool is designed to be driven via a configuration file (`config.yaml`)
and optional environment variables for any sensitive values.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings


logger = logging.getLogger(__name__)


class AppSettings(BaseSettings):
    """Environment-driven settings for the onboarding monitoring tool."""

    log_level: str = "INFO"


class StageConfig(BaseModel):
    """Configuration for a single onboarding stage."""

    name: str
    display_name: Optional[str] = None
    target_completion_rate: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Desired minimum completion rate for this stage.",
    )
    target_time_to_complete_hours: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Desired maximum time to move from previous stage to this stage.",
    )

    @property
    def label(self) -> str:
        """Return a human friendly label for the stage."""

        return self.display_name or self.name


class Config(BaseModel):
    """Configuration loaded from config.yaml."""

    data_path: Path = Field(
        description="Path to onboarding events CSV file.",
    )
    output_path: Path = Field(
        description="Path to write analysis summary (markdown).",
    )
    customer_id_column: str = "customer_id"
    event_time_column: str = "event_time"
    stage_column: str = "stage"
    time_to_value_event: str = Field(
        default="value_realized",
        description="Event name that represents time-to-value.",
    )
    stages: List[StageConfig]

    @field_validator("data_path", "output_path", mode="before")
    @classmethod
    def _expand_path(cls, value: str | Path) -> Path:
        """Expand user and environment variables in configured paths."""

        return Path(str(value)).expanduser()


@dataclass
class StageMetrics:
    """Computed metrics for a single onboarding stage."""

    stage_name: str
    entered: int
    completed: int
    completion_rate: float
    median_time_hours: Optional[float]


@dataclass
class AnalysisResult:
    """Aggregate analysis result for onboarding performance."""

    stage_metrics: List[StageMetrics]
    average_time_to_value_hours: Optional[float]
    recommendations: List[str]


def configure_logging(level: str) -> None:
    """Configure application wide logging.

    Args:
        level: Log level name such as "INFO" or "DEBUG".
    """

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )
    logger.debug("Logging configured", extra={"level": level})


def load_config(path: Path) -> Config:
    """Load and validate configuration from a YAML file.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        Validated `Config` instance.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValidationError: If the configuration is invalid.
        yaml.YAMLError: If the YAML content cannot be parsed.
    """

    if not path.exists():
        logger.error("Configuration file not found", extra={"path": str(path)})
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file)

    try:
        config = Config(**raw)
    except ValidationError as exc:
        logger.error("Invalid configuration", extra={"errors": exc.errors()})
        raise

    logger.info(
        "Configuration loaded",
        extra={"data_path": str(config.data_path), "output_path": str(config.output_path)},
    )
    return config


def load_events(config: Config) -> pd.DataFrame:
    """Load onboarding events data from CSV.

    The CSV is expected to contain at least the following columns:

    - customer_id_column
    - event_time_column
    - stage_column

    Args:
        config: Validated configuration.

    Returns:
        Data frame containing onboarding events.

    Raises:
        FileNotFoundError: If the data file does not exist.
        ValueError: If required columns are missing.
    """

    data_path = config.data_path
    if not data_path.exists():
        logger.error("Data file not found", extra={"path": str(data_path)})
        raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_csv(data_path)
    required_columns = {
        config.customer_id_column,
        config.event_time_column,
        config.stage_column,
    }
    missing = required_columns - set(df.columns)
    if missing:
        logger.error(
            "Missing required columns in data",
            extra={"missing": sorted(missing)},
        )
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    df[config.event_time_column] = pd.to_datetime(df[config.event_time_column])

    logger.info("Events loaded", extra={"row_count": len(df)})
    return df


def compute_stage_metrics(
    df: pd.DataFrame,
    config: Config,
) -> List[StageMetrics]:
    """Compute completion rates and timing metrics for each stage.

    Args:
        df: Data frame of onboarding events.
        config: Application configuration including stage definition.

    Returns:
        List of `StageMetrics` in configured stage order.
    """

    customer_col = config.customer_id_column
    time_col = config.event_time_column
    stage_col = config.stage_column

    metrics: List[StageMetrics] = []

    # For each customer and stage, keep the first time they reached that stage.
    first_stage_events = (
        df.sort_values(time_col)
        .drop_duplicates(subset=[customer_col, stage_col], keep="first")
    )

    # Precompute per customer timeline for time deltas.
    per_customer = (
        first_stage_events.sort_values(time_col)
        .set_index([customer_col, stage_col])[time_col]
        .unstack(stage_col)
    )

    for index, stage_conf in enumerate(config.stages):
        stage_name = stage_conf.name

        if stage_name not in per_customer.columns:
            metrics.append(
                StageMetrics(
                    stage_name=stage_name,
                    entered=0,
                    completed=0,
                    completion_rate=0.0,
                    median_time_hours=None,
                )
            )
            continue

        entered_mask = per_customer[stage_name].notna()
        entered_count = int(entered_mask.sum())

        if index == 0:
            previous_stage_series = per_customer[stage_name]
        else:
            previous_stage = config.stages[index - 1].name
            previous_stage_series = per_customer.get(previous_stage)

        completed_count = entered_count
        median_hours: Optional[float] = None

        if previous_stage_series is not None and index > 0:
            valid = entered_mask & previous_stage_series.notna()
            deltas = (
                per_customer.loc[valid, stage_name]
                - previous_stage_series.loc[valid]
            )
            if not deltas.empty:
                median_hours = float(deltas.dt.total_seconds().median() / 3600.0)

        completion_rate = float(entered_count / entered_count) if entered_count else 0.0

        metrics.append(
            StageMetrics(
                stage_name=stage_name,
                entered=entered_count,
                completed=completed_count,
                completion_rate=completion_rate,
                median_time_hours=median_hours,
            )
        )

    return metrics


def compute_time_to_value(
    df: pd.DataFrame,
    config: Config,
) -> Optional[float]:
    """Compute average time-to-value in hours.

    Time-to-value is defined as the time between a customer's first
    onboarding event and the first occurrence of the configured
    `time_to_value_event`.

    Args:
        df: Data frame of onboarding events.
        config: Application configuration.

    Returns:
        Average time-to-value in hours, or None if it cannot be computed.
    """

    customer_col = config.customer_id_column
    time_col = config.event_time_column
    stage_col = config.stage_column
    value_event = config.time_to_value_event

    df_sorted = df.sort_values(time_col)

    first_any_event = df_sorted.groupby(customer_col)[time_col].first()
    first_value_event = (
        df_sorted[df_sorted[stage_col] == value_event]
        .groupby(customer_col)[time_col]
        .first()
    )

    aligned = first_value_event.to_frame("value_time").join(
        first_any_event.to_frame("start_time"),
        how="inner",
    )

    if aligned.empty:
        return None

    deltas = aligned["value_time"] - aligned["start_time"]
    mean_hours = float(deltas.dt.total_seconds().mean() / 3600.0)
    return mean_hours


def generate_recommendations(
    stage_metrics: List[StageMetrics],
    config: Config,
    average_ttv_hours: Optional[float],
) -> List[str]:
    """Generate human readable optimization recommendations.

    Args:
        stage_metrics: Computed metrics per stage.
        config: Application configuration for targets.
        average_ttv_hours: Average time-to-value in hours.

    Returns:
        List of recommendation strings ordered by priority.
    """

    recommendations: List[str] = []
    stage_config_by_name: Dict[str, StageConfig] = {
        stage.name: stage for stage in config.stages
    }

    for metrics in stage_metrics:
        stage_conf = stage_config_by_name.get(metrics.stage_name)
        if stage_conf is None:
            continue

        if metrics.entered == 0:
            recommendations.append(
                f"Stage '{stage_conf.label}' receives no traffic: "
                f"review entry criteria and ensure customers can reach this step."
            )
            continue

        if metrics.completion_rate < stage_conf.target_completion_rate:
            recommendations.append(
                f"Completion rate for stage '{stage_conf.label}' is "
                f"{metrics.completion_rate:.1%} which is below the target of "
                f"{stage_conf.target_completion_rate:.1%}. "
                f"Review friction points, clarify requirements, and reduce optional "
                f"inputs at this step."
            )

        if (
            stage_conf.target_time_to_complete_hours is not None
            and metrics.median_time_hours is not None
            and metrics.median_time_hours > stage_conf.target_time_to_complete_hours
        ):
            recommendations.append(
                f"Median time to complete stage '{stage_conf.label}' is "
                f"{metrics.median_time_hours:.1f} hours which exceeds the target of "
                f"{stage_conf.target_time_to_complete_hours:.1f} hours. "
                f"Consider simplifying tasks, adding guidance, or automating checks."
            )

    if average_ttv_hours is not None:
        slow_ttv_stage = config.stages[-1].label if config.stages else "final stage"
        recommendations.append(
            f"Average time-to-value is {average_ttv_hours:.1f} hours. "
            f"Prioritize reducing friction before '{slow_ttv_stage}' and provide "
            f"proactive onboarding assistance for slow-moving customers."
        )

    if not recommendations:
        recommendations.append(
            "Onboarding funnel is performing at or above configured targets. "
            "Consider running controlled experiments to further optimize time-to-value."
        )

    return recommendations


def analyze_onboarding(config_path: Path) -> AnalysisResult:
    """Run end-to-end onboarding analysis.

    Args:
        config_path: Path to configuration file.

    Returns:
        Aggregated `AnalysisResult`.
    """

    env_settings = AppSettings()
    configure_logging(env_settings.log_level)

    config = load_config(config_path)
    df = load_events(config)

    stage_metrics = compute_stage_metrics(df, config)
    average_ttv_hours = compute_time_to_value(df, config)
    recommendations = generate_recommendations(
        stage_metrics=stage_metrics,
        config=config,
        average_ttv_hours=average_ttv_hours,
    )

    write_markdown_summary(
        output_path=config.output_path,
        stage_metrics=stage_metrics,
        average_ttv_hours=average_ttv_hours,
        recommendations=recommendations,
        config=config,
    )

    return AnalysisResult(
        stage_metrics=stage_metrics,
        average_time_to_value_hours=average_ttv_hours,
        recommendations=recommendations,
    )


def write_markdown_summary(
    output_path: Path,
    stage_metrics: List[StageMetrics],
    average_ttv_hours: Optional[float],
    recommendations: List[str],
    config: Config,
) -> None:
    """Write a human readable markdown summary to the configured location."""

    lines: List[str] = []
    lines.append("# Customer Onboarding Analysis Summary")
    lines.append("")
    lines.append(f"Generated at: {datetime.utcnow().isoformat()} UTC")
    lines.append("")
    lines.append("## Stage Performance")
    lines.append("")
    lines.append(
        "| Stage | Entered | Completion Rate | Median Time (hours) | "
        "Target Completion | Target Time (hours) |"
    )
    lines.append(
        "|---|---:|---:|---:|---:|---:|"
    )

    stage_config_by_name: Dict[str, StageConfig] = {
        stage.name: stage for stage in config.stages
    }

    for metrics in stage_metrics:
        stage_conf = stage_config_by_name.get(metrics.stage_name)
        target_rate = (
            f"{stage_conf.target_completion_rate:.0%}" if stage_conf else "n/a"
        )
        target_time = (
            f"{stage_conf.target_time_to_complete_hours:.1f}"
            if stage_conf and stage_conf.target_time_to_complete_hours
            else "n/a"
        )
        median_time = (
            f"{metrics.median_time_hours:.1f}"
            if metrics.median_time_hours is not None
            else "n/a"
        )
        lines.append(
            f"| {stage_conf.label if stage_conf else metrics.stage_name} | "
            f"{metrics.entered} | {metrics.completion_rate:.1%} | {median_time} | "
            f"{target_rate} | {target_time} |"
        )

    lines.append("")
    lines.append("## Time-to-Value")
    lines.append("")
    if average_ttv_hours is None:
        lines.append("Insufficient data to compute time-to-value.")
    else:
        lines.append(f"Average time-to-value: **{average_ttv_hours:.1f} hours**.")

    lines.append("")
    lines.append("## Recommendations")
    lines.append("")
    for index, rec in enumerate(recommendations, start=1):
        lines.append(f"{index}. {rec}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    logger.info("Analysis summary written", extra={"output_path": str(output_path)})


def main() -> None:
    """Entry point for running analysis from the command line."""

    default_config = Path(__file__).resolve().parents[1] / "config.yaml"
    analyze_onboarding(default_config)


if __name__ == "__main__":
    main()

