"""Support Capacity Planner.

Monitors customer support ticket volumes, predicts peak times, optimizes
staffing schedules, and generates capacity planning reports for management.
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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


class TicketDataConfig(BaseModel):
    """Configuration for ticket data source."""

    file_path: str = Field(..., description="Path to ticket data file")
    format: str = Field(default="csv", description="File format: csv or json")
    ticket_id_column: str = Field(
        default="ticket_id", description="Column name for ticket ID"
    )
    created_time_column: str = Field(
        default="created_at", description="Column name for creation timestamp"
    )
    resolved_time_column: Optional[str] = Field(
        default=None, description="Column name for resolution timestamp"
    )
    priority_column: Optional[str] = Field(
        default=None, description="Column name for ticket priority"
    )
    category_column: Optional[str] = Field(
        default=None, description="Column name for ticket category"
    )


class PredictionConfig(BaseModel):
    """Configuration for peak time prediction."""

    lookback_days: int = Field(
        default=30, description="Days of historical data to analyze"
    )
    prediction_horizon_days: int = Field(
        default=7, description="Days ahead to predict"
    )
    peak_threshold_multiplier: float = Field(
        default=1.5, description="Multiplier above average for peak detection"
    )
    time_window_hours: int = Field(
        default=1, description="Time window size in hours for analysis"
    )


class StaffingConfig(BaseModel):
    """Configuration for staffing optimization."""

    avg_tickets_per_agent_per_hour: float = Field(
        default=5.0, description="Average tickets an agent can handle per hour"
    )
    min_agents_per_shift: int = Field(
        default=2, description="Minimum agents required per shift"
    )
    max_agents_per_shift: int = Field(
        default=20, description="Maximum agents available per shift"
    )
    shift_duration_hours: int = Field(
        default=8, description="Standard shift duration in hours"
    )
    cost_per_agent_per_hour: float = Field(
        default=25.0, description="Cost per agent per hour"
    )
    target_service_level: float = Field(
        default=0.80, description="Target service level (tickets handled)"
    )


class ReportConfig(BaseModel):
    """Configuration for report generation."""

    output_format: str = Field(
        default="markdown", description="Report format: markdown or html"
    )
    include_charts: bool = Field(
        default=True, description="Include visualizations in report"
    )
    output_path: str = Field(
        default="logs/capacity_planning_report.md",
        description="Path for output report",
    )


class Config(BaseModel):
    """Main configuration model."""

    ticket_data: TicketDataConfig = Field(
        ..., description="Ticket data source configuration"
    )
    prediction: PredictionConfig = Field(
        default_factory=PredictionConfig,
        description="Peak time prediction settings",
    )
    staffing: StaffingConfig = Field(
        default_factory=StaffingConfig,
        description="Staffing optimization settings",
    )
    report: ReportConfig = Field(
        default_factory=ReportConfig, description="Report generation settings"
    )


class AppSettings(BaseSettings):
    """Application settings from environment variables."""

    config_path: str = "config.yaml"


@dataclass
class TimeSlotMetrics:
    """Metrics for a specific time slot."""

    hour: int
    day_of_week: int
    ticket_count: int
    avg_resolution_time_minutes: Optional[float] = None
    peak_indicator: bool = False


@dataclass
class PeakTimePrediction:
    """Prediction for peak ticket volume times."""

    datetime: datetime
    predicted_volume: int
    confidence: float
    recommended_agents: int


@dataclass
class StaffingSchedule:
    """Optimized staffing schedule for a time period."""

    start_time: datetime
    end_time: datetime
    recommended_agents: int
    predicted_ticket_volume: int
    cost_per_shift: float
    service_level: float


@dataclass
class CapacityAnalysis:
    """Complete capacity planning analysis."""

    historical_metrics: List[TimeSlotMetrics]
    peak_predictions: List[PeakTimePrediction]
    staffing_schedule: List[StaffingSchedule]
    summary_stats: Dict[str, float]
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


def load_ticket_data(config: TicketDataConfig, project_root: Path) -> pd.DataFrame:
    """Load ticket data from CSV or JSON file.

    Args:
        config: Ticket data configuration
        project_root: Project root directory

    Returns:
        DataFrame with ticket data

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        raise FileNotFoundError(f"Ticket data file not found: {data_path}")

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        required_columns = [
            config.ticket_id_column,
            config.created_time_column,
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df[config.created_time_column] = pd.to_datetime(
            df[config.created_time_column]
        )

        if config.resolved_time_column and config.resolved_time_column in df.columns:
            df[config.resolved_time_column] = pd.to_datetime(
                df[config.resolved_time_column], errors="coerce"
            )

        logger.info(f"Loaded {len(df)} tickets from {data_path}")
        return df

    except pd.errors.EmptyDataError:
        logger.warning(f"Data file is empty: {data_path}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Failed to load ticket data: {e}")
        raise


def analyze_historical_metrics(
    df: pd.DataFrame, config: TicketDataConfig, prediction_config: PredictionConfig
) -> List[TimeSlotMetrics]:
    """Analyze historical ticket volume metrics by time slot.

    Args:
        df: DataFrame with ticket data
        config: Ticket data configuration
        prediction_config: Prediction configuration

    Returns:
        List of time slot metrics
    """
    if df.empty:
        return []

    cutoff_date = datetime.now() - timedelta(days=prediction_config.lookback_days)
    df_filtered = df[df[config.created_time_column] >= cutoff_date].copy()

    df_filtered["hour"] = df_filtered[config.created_time_column].dt.hour
    df_filtered["day_of_week"] = df_filtered[config.created_time_column].dt.dayofweek

    metrics_by_slot: Dict[Tuple[int, int], List[int]] = defaultdict(list)

    for _, row in df_filtered.iterrows():
        slot_key = (row["hour"], row["day_of_week"])
        metrics_by_slot[slot_key].append(1)

        if (
            config.resolved_time_column
            and config.resolved_time_column in df_filtered.columns
            and pd.notna(row[config.resolved_time_column])
        ):
            resolution_time = (
                row[config.resolved_time_column] - row[config.created_time_column]
            )
            resolution_minutes = resolution_time.total_seconds() / 60
            if resolution_minutes > 0:
                metrics_by_slot[slot_key].append(resolution_minutes)

    time_slot_metrics = []
    all_counts = [len(counts) for counts in metrics_by_slot.values()]
    avg_count = sum(all_counts) / len(all_counts) if all_counts else 0
    peak_threshold = avg_count * prediction_config.peak_threshold_multiplier

    for (hour, day_of_week), values in metrics_by_slot.items():
        ticket_count = len([v for v in values if isinstance(v, int)])
        resolution_times = [v for v in values if isinstance(v, (int, float)) and v > 0]
        avg_resolution = (
            sum(resolution_times) / len(resolution_times)
            if resolution_times
            else None
        )

        is_peak = ticket_count >= peak_threshold

        time_slot_metrics.append(
            TimeSlotMetrics(
                hour=hour,
                day_of_week=day_of_week,
                ticket_count=ticket_count,
                avg_resolution_time_minutes=avg_resolution,
                peak_indicator=is_peak,
            )
        )

    logger.info(f"Analyzed {len(time_slot_metrics)} time slots")
    return time_slot_metrics


def predict_peak_times(
    historical_metrics: List[TimeSlotMetrics],
    config: PredictionConfig,
    staffing_config: StaffingConfig,
) -> List[PeakTimePrediction]:
    """Predict peak ticket volume times.

    Args:
        historical_metrics: Historical time slot metrics
        config: Prediction configuration
        staffing_config: Staffing configuration

    Returns:
        List of peak time predictions
    """
    if not historical_metrics:
        return []

    metrics_by_slot: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    for metric in historical_metrics:
        slot_key = (metric.hour, metric.day_of_week)
        metrics_by_slot[slot_key].append(metric.ticket_count)

    slot_averages = {
        slot: sum(counts) / len(counts)
        for slot, counts in metrics_by_slot.items()
    }

    overall_avg = (
        sum(slot_averages.values()) / len(slot_averages)
        if slot_averages
        else 0
    )

    predictions = []
    start_date = datetime.now().replace(minute=0, second=0, microsecond=0)

    for day_offset in range(config.prediction_horizon_days):
        current_date = start_date + timedelta(days=day_offset)
        day_of_week = current_date.weekday()

        for hour in range(24):
            slot_key = (hour, day_of_week)
            predicted_volume = int(
                slot_averages.get(slot_key, overall_avg)
            )

            if predicted_volume > overall_avg * config.peak_threshold_multiplier:
                confidence = min(
                    1.0,
                    len(metrics_by_slot.get(slot_key, [])) / 10.0,
                )

                recommended_agents = max(
                    staffing_config.min_agents_per_shift,
                    min(
                        staffing_config.max_agents_per_shift,
                        int(
                            predicted_volume
                            / staffing_config.avg_tickets_per_agent_per_hour
                        )
                        + 1,
                    ),
                )

                prediction_time = current_date.replace(hour=hour)
                predictions.append(
                    PeakTimePrediction(
                        datetime=prediction_time,
                        predicted_volume=predicted_volume,
                        confidence=confidence,
                        recommended_agents=recommended_agents,
                    )
                )

    predictions.sort(key=lambda x: x.predicted_volume, reverse=True)
    logger.info(f"Generated {len(predictions)} peak time predictions")
    return predictions


def optimize_staffing_schedule(
    predictions: List[PeakTimePrediction],
    config: StaffingConfig,
) -> List[StaffingSchedule]:
    """Optimize staffing schedule based on predictions.

    Args:
        predictions: List of peak time predictions
        config: Staffing configuration

    Returns:
        List of optimized staffing schedules
    """
    if not predictions:
        return []

    schedules = []
    shift_start = None
    current_agents = 0
    current_volume = 0
    prediction_count = 0

    for prediction in sorted(predictions, key=lambda x: x.datetime):
        if shift_start is None:
            shift_start = prediction.datetime

        current_agents = max(current_agents, prediction.recommended_agents)
        current_volume += prediction.predicted_volume
        prediction_count += 1

        hours_elapsed = (
            prediction.datetime - shift_start
        ).total_seconds() / 3600

        if hours_elapsed >= config.shift_duration_hours or prediction_count >= 8:
            shift_end = shift_start + timedelta(
                hours=config.shift_duration_hours
            )

            avg_volume_per_hour = current_volume / max(1, prediction_count)
            service_level = min(
                1.0,
                (current_agents * config.avg_tickets_per_agent_per_hour)
                / max(1, avg_volume_per_hour),
            )

            cost_per_shift = (
                current_agents * config.shift_duration_hours * config.cost_per_agent_per_hour
            )

            schedules.append(
                StaffingSchedule(
                    start_time=shift_start,
                    end_time=shift_end,
                    recommended_agents=current_agents,
                    predicted_ticket_volume=int(current_volume),
                    cost_per_shift=cost_per_shift,
                    service_level=service_level,
                )
            )

            shift_start = None
            current_agents = 0
            current_volume = 0
            prediction_count = 0

    if shift_start is not None:
        shift_end = shift_start + timedelta(hours=config.shift_duration_hours)
        avg_volume_per_hour = current_volume / max(1, prediction_count)
        service_level = min(
            1.0,
            (current_agents * config.avg_tickets_per_agent_per_hour)
            / max(1, avg_volume_per_hour),
        )
        cost_per_shift = (
            current_agents * config.shift_duration_hours * config.cost_per_agent_per_hour
        )

        schedules.append(
            StaffingSchedule(
                start_time=shift_start,
                end_time=shift_end,
                recommended_agents=current_agents,
                predicted_ticket_volume=int(current_volume),
                cost_per_shift=cost_per_shift,
                service_level=service_level,
            )
        )

    logger.info(f"Generated {len(schedules)} optimized staffing schedules")
    return schedules


def calculate_summary_stats(
    historical_metrics: List[TimeSlotMetrics],
    predictions: List[PeakTimePrediction],
    schedules: List[StaffingSchedule],
) -> Dict[str, float]:
    """Calculate summary statistics for the analysis.

    Args:
        historical_metrics: Historical time slot metrics
        predictions: Peak time predictions
        schedules: Staffing schedules

    Returns:
        Dictionary of summary statistics
    """
    stats = {}

    if historical_metrics:
        total_tickets = sum(m.ticket_count for m in historical_metrics)
        avg_tickets_per_slot = total_tickets / len(historical_metrics)
        peak_slots = sum(1 for m in historical_metrics if m.peak_indicator)

        stats["total_historical_tickets"] = float(total_tickets)
        stats["avg_tickets_per_slot"] = avg_tickets_per_slot
        stats["peak_slots_count"] = float(peak_slots)
        stats["peak_slots_percentage"] = (peak_slots / len(historical_metrics)) * 100

    if predictions:
        avg_predicted_volume = (
            sum(p.predicted_volume for p in predictions) / len(predictions)
        )
        max_predicted_volume = max(p.predicted_volume for p in predictions)
        avg_confidence = sum(p.confidence for p in predictions) / len(predictions)

        stats["avg_predicted_volume"] = avg_predicted_volume
        stats["max_predicted_volume"] = float(max_predicted_volume)
        stats["avg_prediction_confidence"] = avg_confidence

    if schedules:
        total_cost = sum(s.cost_per_shift for s in schedules)
        avg_agents = sum(s.recommended_agents for s in schedules) / len(schedules)
        avg_service_level = (
            sum(s.service_level for s in schedules) / len(schedules)
        )

        stats["total_staffing_cost"] = total_cost
        stats["avg_agents_per_shift"] = avg_agents
        stats["avg_service_level"] = avg_service_level

    return stats


def generate_markdown_report(
    analysis: CapacityAnalysis, output_path: Path
) -> None:
    """Generate markdown capacity planning report.

    Args:
        analysis: Complete capacity analysis
        output_path: Path to write the report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Support Capacity Planning Report\n\n")
        f.write(
            f"**Generated:** {analysis.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        f.write("## Executive Summary\n\n")
        f.write(
            "This report analyzes historical support ticket volumes, "
            "predicts peak times, and provides optimized staffing "
            "recommendations.\n\n"
        )

        if analysis.summary_stats:
            f.write("### Key Metrics\n\n")
            for key, value in sorted(analysis.summary_stats.items()):
                if isinstance(value, float):
                    if "percentage" in key.lower() or "level" in key.lower():
                        f.write(f"- **{key.replace('_', ' ').title()}:** {value:.1f}%\n")
                    elif "cost" in key.lower():
                        f.write(f"- **{key.replace('_', ' ').title()}:** ${value:,.2f}\n")
                    else:
                        f.write(f"- **{key.replace('_', ' ').title()}:** {value:.2f}\n")
                else:
                    f.write(f"- **{key.replace('_', ' ').title()}:** {value}\n")
            f.write("\n")

        f.write("## Historical Analysis\n\n")
        f.write(f"Analyzed {len(analysis.historical_metrics)} time slots.\n\n")

        if analysis.historical_metrics:
            peak_slots = [m for m in analysis.historical_metrics if m.peak_indicator]
            if peak_slots:
                f.write("### Peak Time Slots\n\n")
                f.write("| Hour | Day of Week | Ticket Count |\n")
                f.write("|------|-------------|--------------|\n")
                for slot in sorted(peak_slots, key=lambda x: -x.ticket_count)[:10]:
                    day_names = [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday",
                    ]
                    f.write(
                        f"| {slot.hour:02d}:00 | {day_names[slot.day_of_week]} | "
                        f"{slot.ticket_count} |\n"
                    )
                f.write("\n")

        f.write("## Peak Time Predictions\n\n")
        f.write(
            f"Generated {len(analysis.peak_predictions)} predictions for "
            f"upcoming peak times.\n\n"
        )

        if analysis.peak_predictions:
            f.write("### Top Predicted Peak Times\n\n")
            f.write(
                "| Date/Time | Predicted Volume | Recommended Agents | "
                "Confidence |\n"
            )
            f.write("|-----------|-------------------|---------------------|------------|\n")
            for pred in analysis.peak_predictions[:20]:
                f.write(
                    f"| {pred.datetime.strftime('%Y-%m-%d %H:%M')} | "
                    f"{pred.predicted_volume} | {pred.recommended_agents} | "
                    f"{pred.confidence:.2f} |\n"
                )
            f.write("\n")

        f.write("## Optimized Staffing Schedule\n\n")
        f.write(
            f"Generated {len(analysis.staffing_schedule)} optimized staffing "
            "schedules.\n\n"
        )

        if analysis.staffing_schedule:
            f.write(
                "| Start Time | End Time | Agents | Predicted Volume | "
                "Cost/Shift | Service Level |\n"
            )
            f.write(
                "|------------|----------|--------|------------------|"
                "------------|--------------|\n"
            )
            for schedule in analysis.staffing_schedule:
                f.write(
                    f"| {schedule.start_time.strftime('%Y-%m-%d %H:%M')} | "
                    f"{schedule.end_time.strftime('%Y-%m-%d %H:%M')} | "
                    f"{schedule.recommended_agents} | "
                    f"{schedule.predicted_ticket_volume} | "
                    f"${schedule.cost_per_shift:.2f} | "
                    f"{schedule.service_level:.1%} |\n"
                )
            f.write("\n")

        f.write("## Recommendations\n\n")
        f.write("1. **Staffing Allocation:** Focus agent allocation on predicted peak times.\n")
        f.write("2. **Cost Optimization:** Balance service levels with staffing costs.\n")
        f.write("3. **Monitoring:** Continuously monitor actual vs predicted volumes.\n")
        f.write("4. **Adjustment:** Update predictions based on recent trends.\n")

    logger.info(f"Report written to {output_path}")


def process_capacity_planning(config_path: Path) -> CapacityAnalysis:
    """Process capacity planning analysis.

    Args:
        config_path: Path to configuration file

    Returns:
        Complete capacity analysis

    Raises:
        FileNotFoundError: If config or data files are missing
        ValueError: If configuration is invalid
    """
    config = load_config(config_path)
    project_root = config_path.parent

    df = load_ticket_data(config.ticket_data, project_root)

    if df.empty:
        logger.warning("No ticket data available for analysis")
        return CapacityAnalysis(
            historical_metrics=[],
            peak_predictions=[],
            staffing_schedule=[],
            summary_stats={},
            generated_at=datetime.now(),
        )

    historical_metrics = analyze_historical_metrics(
        df, config.ticket_data, config.prediction
    )

    peak_predictions = predict_peak_times(
        historical_metrics, config.prediction, config.staffing
    )

    staffing_schedule = optimize_staffing_schedule(
        peak_predictions, config.staffing
    )

    summary_stats = calculate_summary_stats(
        historical_metrics, peak_predictions, staffing_schedule
    )

    analysis = CapacityAnalysis(
        historical_metrics=historical_metrics,
        peak_predictions=peak_predictions,
        staffing_schedule=staffing_schedule,
        summary_stats=summary_stats,
        generated_at=datetime.now(),
    )

    report_path = Path(config.report.output_path)
    if not report_path.is_absolute():
        report_path = project_root / report_path

    generate_markdown_report(analysis, report_path)

    return analysis


def main() -> None:
    """Main entry point for the support capacity planner."""
    settings = AppSettings()
    config_path = Path(settings.config_path)

    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent
        config_path = project_root / config_path

    try:
        logger.info("Starting support capacity planning analysis")
        analysis = process_capacity_planning(config_path)
        logger.info(
            f"Analysis complete. Generated {len(analysis.peak_predictions)} "
            f"predictions and {len(analysis.staffing_schedule)} staffing schedules."
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
