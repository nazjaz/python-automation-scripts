"""Health Recommendation Engine.

Automatically generates personalized health recommendations by analyzing
activity data, sleep patterns, and health metrics, with goal setting and
progress tracking.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

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


class GoalStatus(str, Enum):
    """Status of a health goal."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    AT_RISK = "at_risk"


class ActivityDataConfig(BaseModel):
    """Configuration for activity data source."""

    file_path: str = Field(..., description="Path to activity data file")
    format: str = Field(default="csv", description="File format: csv or json")
    date_column: str = Field(
        default="date", description="Column name for date"
    )
    steps_column: Optional[str] = Field(
        default=None, description="Column name for steps"
    )
    calories_column: Optional[str] = Field(
        default=None, description="Column name for calories burned"
    )
    active_minutes_column: Optional[str] = Field(
        default=None, description="Column name for active minutes"
    )
    distance_column: Optional[str] = Field(
        default=None, description="Column name for distance"
    )


class SleepDataConfig(BaseModel):
    """Configuration for sleep data source."""

    file_path: str = Field(..., description="Path to sleep data file")
    format: str = Field(default="csv", description="File format: csv or json")
    date_column: str = Field(
        default="date", description="Column name for date"
    )
    sleep_hours_column: str = Field(
        default="sleep_hours", description="Column name for sleep hours"
    )
    sleep_quality_column: Optional[str] = Field(
        default=None, description="Column name for sleep quality score"
    )
    bedtime_column: Optional[str] = Field(
        default=None, description="Column name for bedtime"
    )
    wake_time_column: Optional[str] = Field(
        default=None, description="Column name for wake time"
    )


class HealthMetricsConfig(BaseModel):
    """Configuration for health metrics data source."""

    file_path: str = Field(..., description="Path to health metrics file")
    format: str = Field(default="csv", description="File format: csv or json")
    date_column: str = Field(
        default="date", description="Column name for date"
    )
    weight_column: Optional[str] = Field(
        default=None, description="Column name for weight"
    )
    heart_rate_column: Optional[str] = Field(
        default=None, description="Column name for resting heart rate"
    )
    blood_pressure_column: Optional[str] = Field(
        default=None, description="Column name for blood pressure"
    )


class RecommendationConfig(BaseModel):
    """Configuration for recommendation generation."""

    target_steps_per_day: int = Field(
        default=10000, description="Target steps per day"
    )
    target_sleep_hours: float = Field(
        default=7.5, description="Target sleep hours per night"
    )
    min_sleep_hours: float = Field(
        default=7.0, description="Minimum recommended sleep hours"
    )
    max_sleep_hours: float = Field(
        default=9.0, description="Maximum recommended sleep hours"
    )
    target_active_minutes: int = Field(
        default=30, description="Target active minutes per day"
    )


class GoalConfig(BaseModel):
    """Configuration for goal management."""

    goals_file: Optional[str] = Field(
        default=None, description="Path to goals file"
    )
    progress_file: str = Field(
        default="logs/goals_progress.json",
        description="Path to progress tracking file",
    )


class Config(BaseModel):
    """Main configuration model."""

    activity_data: ActivityDataConfig = Field(
        ..., description="Activity data source configuration"
    )
    sleep_data: SleepDataConfig = Field(
        ..., description="Sleep data source configuration"
    )
    health_metrics: HealthMetricsConfig = Field(
        ..., description="Health metrics data source configuration"
    )
    recommendation: RecommendationConfig = Field(
        default_factory=RecommendationConfig,
        description="Recommendation settings",
    )
    goal: GoalConfig = Field(
        default_factory=GoalConfig, description="Goal management settings"
    )
    output_file: str = Field(
        default="logs/health_recommendations.json",
        description="Path to save recommendations",
    )
    report_file: str = Field(
        default="logs/health_report.md",
        description="Path for health report",
    )


class AppSettings(BaseSettings):
    """Application settings from environment variables."""

    config_path: str = "config.yaml"


@dataclass
class ActivityMetrics:
    """Activity metrics for analysis."""

    date: datetime
    steps: Optional[int] = None
    calories: Optional[float] = None
    active_minutes: Optional[int] = None
    distance: Optional[float] = None


@dataclass
class SleepMetrics:
    """Sleep metrics for analysis."""

    date: datetime
    sleep_hours: float
    sleep_quality: Optional[float] = None
    bedtime: Optional[datetime] = None
    wake_time: Optional[datetime] = None


@dataclass
class HealthMetrics:
    """Health metrics for analysis."""

    date: datetime
    weight: Optional[float] = None
    heart_rate: Optional[int] = None
    blood_pressure: Optional[str] = None


@dataclass
class HealthRecommendation:
    """Personalized health recommendation."""

    category: str
    title: str
    description: str
    priority: RecommendationPriority
    rationale: str
    action_items: List[str]
    target_value: Optional[float] = None
    current_value: Optional[float] = None


@dataclass
class HealthGoal:
    """Health goal definition."""

    goal_id: str
    category: str
    title: str
    target_value: float
    unit: str
    start_date: datetime
    target_date: datetime
    status: GoalStatus = GoalStatus.NOT_STARTED
    current_value: Optional[float] = None
    progress_percentage: float = 0.0


@dataclass
class HealthAnalysis:
    """Complete health analysis results."""

    activity_summary: Dict[str, float]
    sleep_summary: Dict[str, float]
    health_metrics_summary: Dict[str, float]
    recommendations: List[HealthRecommendation]
    goals: List[HealthGoal]
    progress_updates: List[Dict[str, any]]
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


def load_activity_data(
    config: ActivityDataConfig, project_root: Path
) -> List[ActivityMetrics]:
    """Load activity data from file.

    Args:
        config: Activity data configuration
        project_root: Project root directory

    Returns:
        List of ActivityMetrics objects

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        raise FileNotFoundError(f"Activity data file not found: {data_path}")

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        if config.date_column not in df.columns:
            raise ValueError(f"Date column '{config.date_column}' not found")

        df[config.date_column] = pd.to_datetime(df[config.date_column])

        activities = []
        for _, row in df.iterrows():
            activity = ActivityMetrics(date=row[config.date_column])

            if config.steps_column and config.steps_column in df.columns:
                activity.steps = (
                    int(row[config.steps_column])
                    if pd.notna(row[config.steps_column])
                    else None
                )

            if config.calories_column and config.calories_column in df.columns:
                activity.calories = (
                    float(row[config.calories_column])
                    if pd.notna(row[config.calories_column])
                    else None
                )

            if (
                config.active_minutes_column
                and config.active_minutes_column in df.columns
            ):
                activity.active_minutes = (
                    int(row[config.active_minutes_column])
                    if pd.notna(row[config.active_minutes_column])
                    else None
                )

            if config.distance_column and config.distance_column in df.columns:
                activity.distance = (
                    float(row[config.distance_column])
                    if pd.notna(row[config.distance_column])
                    else None
                )

            activities.append(activity)

        logger.info(f"Loaded {len(activities)} activity records")
        return activities

    except pd.errors.EmptyDataError:
        logger.warning(f"Activity data file is empty: {data_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to load activity data: {e}")
        raise


def load_sleep_data(
    config: SleepDataConfig, project_root: Path
) -> List[SleepMetrics]:
    """Load sleep data from file.

    Args:
        config: Sleep data configuration
        project_root: Project root directory

    Returns:
        List of SleepMetrics objects

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        raise FileNotFoundError(f"Sleep data file not found: {data_path}")

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        if config.date_column not in df.columns:
            raise ValueError(f"Date column '{config.date_column}' not found")
        if config.sleep_hours_column not in df.columns:
            raise ValueError(
                f"Sleep hours column '{config.sleep_hours_column}' not found"
            )

        df[config.date_column] = pd.to_datetime(df[config.date_column])

        sleep_records = []
        for _, row in df.iterrows():
            sleep_hours = float(row[config.sleep_hours_column])

            sleep_metric = SleepMetrics(
                date=row[config.date_column], sleep_hours=sleep_hours
            )

            if (
                config.sleep_quality_column
                and config.sleep_quality_column in df.columns
            ):
                sleep_metric.sleep_quality = (
                    float(row[config.sleep_quality_column])
                    if pd.notna(row[config.sleep_quality_column])
                    else None
                )

            if config.bedtime_column and config.bedtime_column in df.columns:
                if pd.notna(row[config.bedtime_column]):
                    sleep_metric.bedtime = pd.to_datetime(
                        row[config.bedtime_column]
                    )

            if config.wake_time_column and config.wake_time_column in df.columns:
                if pd.notna(row[config.wake_time_column]):
                    sleep_metric.wake_time = pd.to_datetime(
                        row[config.wake_time_column]
                    )

            sleep_records.append(sleep_metric)

        logger.info(f"Loaded {len(sleep_records)} sleep records")
        return sleep_records

    except pd.errors.EmptyDataError:
        logger.warning(f"Sleep data file is empty: {data_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to load sleep data: {e}")
        raise


def load_health_metrics(
    config: HealthMetricsConfig, project_root: Path
) -> List[HealthMetrics]:
    """Load health metrics data from file.

    Args:
        config: Health metrics configuration
        project_root: Project root directory

    Returns:
        List of HealthMetrics objects

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        raise FileNotFoundError(f"Health metrics file not found: {data_path}")

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        if config.date_column not in df.columns:
            raise ValueError(f"Date column '{config.date_column}' not found")

        df[config.date_column] = pd.to_datetime(df[config.date_column])

        metrics = []
        for _, row in df.iterrows():
            health_metric = HealthMetrics(date=row[config.date_column])

            if config.weight_column and config.weight_column in df.columns:
                health_metric.weight = (
                    float(row[config.weight_column])
                    if pd.notna(row[config.weight_column])
                    else None
                )

            if config.heart_rate_column and config.heart_rate_column in df.columns:
                health_metric.heart_rate = (
                    int(row[config.heart_rate_column])
                    if pd.notna(row[config.heart_rate_column])
                    else None
                )

            if (
                config.blood_pressure_column
                and config.blood_pressure_column in df.columns
            ):
                health_metric.blood_pressure = (
                    str(row[config.blood_pressure_column])
                    if pd.notna(row[config.blood_pressure_column])
                    else None
                )

            metrics.append(health_metric)

        logger.info(f"Loaded {len(metrics)} health metric records")
        return metrics

    except pd.errors.EmptyDataError:
        logger.warning(f"Health metrics file is empty: {data_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to load health metrics: {e}")
        raise


def analyze_activity(
    activities: List[ActivityMetrics], config: RecommendationConfig
) -> Dict[str, float]:
    """Analyze activity data and calculate summary statistics.

    Args:
        activities: List of activity metrics
        config: Recommendation configuration

    Returns:
        Dictionary of summary statistics
    """
    if not activities:
        return {}

    summary = {}
    steps_list = [a.steps for a in activities if a.steps is not None]
    calories_list = [a.calories for a in activities if a.calories is not None]
    active_minutes_list = [
        a.active_minutes for a in activities if a.active_minutes is not None
    ]

    if steps_list:
        summary["avg_steps_per_day"] = sum(steps_list) / len(steps_list)
        summary["total_steps"] = sum(steps_list)
        summary["days_with_data"] = len(steps_list)
        summary["steps_target_met_days"] = sum(
            1 for s in steps_list if s >= config.target_steps_per_day
        )
    else:
        summary["avg_steps_per_day"] = 0.0

    if calories_list:
        summary["avg_calories_per_day"] = sum(calories_list) / len(calories_list)
        summary["total_calories"] = sum(calories_list)

    if active_minutes_list:
        summary["avg_active_minutes"] = sum(active_minutes_list) / len(
            active_minutes_list
        )
        summary["active_minutes_target_met_days"] = sum(
            1 for m in active_minutes_list if m >= config.target_active_minutes
        )

    return summary


def analyze_sleep(
    sleep_records: List[SleepMetrics], config: RecommendationConfig
) -> Dict[str, float]:
    """Analyze sleep data and calculate summary statistics.

    Args:
        sleep_records: List of sleep metrics
        config: Recommendation configuration

    Returns:
        Dictionary of summary statistics
    """
    if not sleep_records:
        return {}

    summary = {}
    sleep_hours_list = [s.sleep_hours for s in sleep_records]
    quality_list = [
        s.sleep_quality for s in sleep_records if s.sleep_quality is not None
    ]

    summary["avg_sleep_hours"] = sum(sleep_hours_list) / len(sleep_hours_list)
    summary["min_sleep_hours"] = min(sleep_hours_list)
    summary["max_sleep_hours"] = max(sleep_hours_list)
    summary["days_with_data"] = len(sleep_records)

    summary["sleep_target_met_days"] = sum(
        1
        for s in sleep_hours_list
        if config.min_sleep_hours <= s <= config.max_sleep_hours
    )

    if quality_list:
        summary["avg_sleep_quality"] = sum(quality_list) / len(quality_list)

    return summary


def generate_recommendations(
    activity_summary: Dict[str, float],
    sleep_summary: Dict[str, float],
    health_summary: Dict[str, float],
    config: RecommendationConfig,
) -> List[HealthRecommendation]:
    """Generate personalized health recommendations.

    Args:
        activity_summary: Activity summary statistics
        sleep_summary: Sleep summary statistics
        health_summary: Health metrics summary
        config: Recommendation configuration

    Returns:
        List of health recommendations
    """
    recommendations = []

    if activity_summary:
        avg_steps = activity_summary.get("avg_steps_per_day", 0)
        if avg_steps < config.target_steps_per_day * 0.8:
            deficit = config.target_steps_per_day - avg_steps
            recommendations.append(
                HealthRecommendation(
                    category="Activity",
                    title="Increase Daily Steps",
                    description=f"Your average daily steps ({avg_steps:.0f}) is below the target ({config.target_steps_per_day}).",
                    priority=RecommendationPriority.HIGH,
                    rationale=f"You are averaging {deficit:.0f} fewer steps per day than recommended.",
                    action_items=[
                        "Take a 10-minute walk after each meal",
                        "Use stairs instead of elevators",
                        "Park farther from destinations",
                        "Set hourly movement reminders",
                    ],
                    target_value=float(config.target_steps_per_day),
                    current_value=avg_steps,
                )
            )

        avg_active_minutes = activity_summary.get("avg_active_minutes", 0)
        if avg_active_minutes < config.target_active_minutes:
            recommendations.append(
                HealthRecommendation(
                    category="Activity",
                    title="Increase Active Minutes",
                    description=f"Your average active minutes ({avg_active_minutes:.0f}) is below the target ({config.target_active_minutes}).",
                    priority=RecommendationPriority.MEDIUM,
                    rationale="Regular physical activity improves cardiovascular health and overall fitness.",
                    action_items=[
                        "Schedule 30 minutes of exercise daily",
                        "Try brisk walking, cycling, or swimming",
                        "Break activity into 10-minute sessions",
                        "Track progress with a fitness app",
                    ],
                    target_value=float(config.target_active_minutes),
                    current_value=avg_active_minutes,
                )
            )

    if sleep_summary:
        avg_sleep = sleep_summary.get("avg_sleep_hours", 0)
        if avg_sleep < config.min_sleep_hours:
            recommendations.append(
                HealthRecommendation(
                    category="Sleep",
                    title="Improve Sleep Duration",
                    description=f"Your average sleep ({avg_sleep:.1f} hours) is below the recommended minimum ({config.min_sleep_hours} hours).",
                    priority=RecommendationPriority.HIGH,
                    rationale="Insufficient sleep can impact cognitive function, mood, and physical health.",
                    action_items=[
                        "Establish a consistent bedtime routine",
                        "Avoid screens 1 hour before bed",
                        "Create a dark, quiet sleep environment",
                        "Limit caffeine intake after 2 PM",
                    ],
                    target_value=config.target_sleep_hours,
                    current_value=avg_sleep,
                )
            )
        elif avg_sleep > config.max_sleep_hours:
            recommendations.append(
                HealthRecommendation(
                    category="Sleep",
                    title="Optimize Sleep Duration",
                    description=f"Your average sleep ({avg_sleep:.1f} hours) exceeds the recommended maximum ({config.max_sleep_hours} hours).",
                    priority=RecommendationPriority.LOW,
                    rationale="Excessive sleep may indicate underlying health issues or poor sleep quality.",
                    action_items=[
                        "Evaluate sleep quality, not just duration",
                        "Consider consulting a healthcare provider",
                        "Maintain consistent wake times",
                    ],
                    target_value=config.target_sleep_hours,
                    current_value=avg_sleep,
                )
            )

        sleep_quality = sleep_summary.get("avg_sleep_quality", None)
        if sleep_quality is not None and sleep_quality < 7.0:
            recommendations.append(
                HealthRecommendation(
                    category="Sleep",
                    title="Improve Sleep Quality",
                    description=f"Your average sleep quality score ({sleep_quality:.1f}/10) indicates room for improvement.",
                    priority=RecommendationPriority.MEDIUM,
                    rationale="Sleep quality is as important as sleep duration for overall health.",
                    action_items=[
                        "Maintain a regular sleep schedule",
                        "Keep bedroom temperature cool",
                        "Use relaxation techniques before bed",
                        "Avoid large meals before bedtime",
                    ],
                    current_value=sleep_quality,
                )
            )

    return recommendations


def load_goals(goals_file: Optional[Path]) -> List[HealthGoal]:
    """Load health goals from file.

    Args:
        goals_file: Path to goals file (optional)

    Returns:
        List of HealthGoal objects
    """
    if not goals_file or not goals_file.exists():
        return []

    try:
        with open(goals_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        goals = []
        if isinstance(data, list):
            for item in data:
                goal = HealthGoal(
                    goal_id=str(item.get("goal_id", "")),
                    category=str(item.get("category", "")),
                    title=str(item.get("title", "")),
                    target_value=float(item.get("target_value", 0)),
                    unit=str(item.get("unit", "")),
                    start_date=datetime.fromisoformat(item["start_date"]),
                    target_date=datetime.fromisoformat(item["target_date"]),
                    status=GoalStatus(item.get("status", "not_started")),
                    current_value=(
                        float(item["current_value"])
                        if item.get("current_value") is not None
                        else None
                    ),
                    progress_percentage=float(
                        item.get("progress_percentage", 0.0)
                    ),
                )
                goals.append(goal)

        logger.info(f"Loaded {len(goals)} health goals")
        return goals

    except Exception as e:
        logger.warning(f"Failed to load goals: {e}")
        return []


def update_goal_progress(
    goals: List[HealthGoal],
    activity_summary: Dict[str, float],
    sleep_summary: Dict[str, float],
) -> List[Dict[str, any]]:
    """Update progress for health goals.

    Args:
        goals: List of health goals
        activity_summary: Activity summary statistics
        sleep_summary: Sleep summary statistics

    Returns:
        List of progress update dictionaries
    """
    updates = []

    for goal in goals:
        current_value = goal.current_value
        progress = goal.progress_percentage

        if goal.category == "Activity" and activity_summary:
            if "steps" in goal.title.lower():
                current_value = activity_summary.get("avg_steps_per_day", 0)
            elif "active" in goal.title.lower():
                current_value = activity_summary.get("avg_active_minutes", 0)

        elif goal.category == "Sleep" and sleep_summary:
            if "sleep" in goal.title.lower():
                current_value = sleep_summary.get("avg_sleep_hours", 0)

        if current_value is not None and goal.target_value > 0:
            progress = min(100.0, (current_value / goal.target_value) * 100)

            if progress >= 100.0:
                status = GoalStatus.COMPLETED
            elif progress > 0:
                days_remaining = (goal.target_date - datetime.now()).days
                if days_remaining < 7 and progress < 50.0:
                    status = GoalStatus.AT_RISK
                else:
                    status = GoalStatus.IN_PROGRESS
            else:
                status = GoalStatus.NOT_STARTED
        else:
            status = goal.status

        goal.current_value = current_value
        goal.progress_percentage = progress
        goal.status = status

        updates.append(
            {
                "goal_id": goal.goal_id,
                "current_value": current_value,
                "progress_percentage": progress,
                "status": status.value,
                "updated_at": datetime.now().isoformat(),
            }
        )

    return updates


def write_markdown_report(analysis: HealthAnalysis, output_path: Path) -> None:
    """Write health analysis report to markdown file.

    Args:
        analysis: Health analysis results
        output_path: Path to write the report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Health Analysis Report\n\n")
        f.write(
            f"**Generated:** {analysis.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        f.write("## Activity Summary\n\n")
        if analysis.activity_summary:
            for key, value in analysis.activity_summary.items():
                if isinstance(value, float):
                    f.write(f"- **{key.replace('_', ' ').title()}:** {value:.2f}\n")
                else:
                    f.write(f"- **{key.replace('_', ' ').title()}:** {value}\n")
        else:
            f.write("No activity data available.\n")
        f.write("\n")

        f.write("## Sleep Summary\n\n")
        if analysis.sleep_summary:
            for key, value in analysis.sleep_summary.items():
                if isinstance(value, float):
                    f.write(f"- **{key.replace('_', ' ').title()}:** {value:.2f}\n")
                else:
                    f.write(f"- **{key.replace('_', ' ').title()}:** {value}\n")
        else:
            f.write("No sleep data available.\n")
        f.write("\n")

        f.write("## Health Recommendations\n\n")
        if analysis.recommendations:
            for i, rec in enumerate(analysis.recommendations, 1):
                f.write(f"### {i}. {rec.title} ({rec.priority.value.upper()})\n\n")
                f.write(f"**Category:** {rec.category}\n\n")
                f.write(f"{rec.description}\n\n")
                f.write(f"**Rationale:** {rec.rationale}\n\n")
                if rec.current_value is not None and rec.target_value is not None:
                    f.write(
                        f"**Current:** {rec.current_value:.2f} | "
                        f"**Target:** {rec.target_value:.2f}\n\n"
                    )
                f.write("**Action Items:**\n")
                for action in rec.action_items:
                    f.write(f"- {action}\n")
                f.write("\n")
        else:
            f.write("No recommendations at this time.\n")
        f.write("\n")

        f.write("## Goals Progress\n\n")
        if analysis.goals:
            f.write(
                "| Goal | Category | Progress | Status | Target Date |\n"
            )
            f.write("|------|----------|----------|--------|-------------|\n")
            for goal in analysis.goals:
                f.write(
                    f"| {goal.title} | {goal.category} | "
                    f"{goal.progress_percentage:.1f}% | {goal.status.value} | "
                    f"{goal.target_date.strftime('%Y-%m-%d')} |\n"
                )
        else:
            f.write("No active goals.\n")

    logger.info(f"Report written to {output_path}")


def process_health_analysis(config_path: Path) -> HealthAnalysis:
    """Process health data and generate recommendations.

    Args:
        config_path: Path to configuration file

    Returns:
        Complete health analysis

    Raises:
        FileNotFoundError: If config or data files are missing
        ValueError: If configuration is invalid
    """
    config = load_config(config_path)
    project_root = config_path.parent

    activities = load_activity_data(config.activity_data, project_root)
    sleep_records = load_sleep_data(config.sleep_data, project_root)
    health_metrics = load_health_metrics(config.health_metrics, project_root)

    activity_summary = analyze_activity(activities, config.recommendation)
    sleep_summary = analyze_sleep(sleep_records, config.recommendation)
    health_summary = {}

    if health_metrics:
        weight_list = [m.weight for m in health_metrics if m.weight is not None]
        if weight_list:
            health_summary["avg_weight"] = sum(weight_list) / len(weight_list)

    recommendations = generate_recommendations(
        activity_summary, sleep_summary, health_summary, config.recommendation
    )

    goals_file = None
    if config.goal.goals_file:
        goals_file = Path(config.goal.goals_file)
        if not goals_file.is_absolute():
            goals_file = project_root / goals_file

    goals = load_goals(goals_file)
    progress_updates = update_goal_progress(goals, activity_summary, sleep_summary)

    if progress_updates:
        progress_path = Path(config.goal.progress_file)
        if not progress_path.is_absolute():
            progress_path = project_root / progress_path
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(progress_updates, f, indent=2)

    analysis = HealthAnalysis(
        activity_summary=activity_summary,
        sleep_summary=sleep_summary,
        health_metrics_summary=health_summary,
        recommendations=recommendations,
        goals=goals,
        progress_updates=progress_updates,
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
        "recommendations": [
            {
                "category": rec.category,
                "title": rec.title,
                "description": rec.description,
                "priority": rec.priority.value,
                "rationale": rec.rationale,
                "action_items": rec.action_items,
                "target_value": rec.target_value,
                "current_value": rec.current_value,
            }
            for rec in recommendations
        ],
        "goals": [
            {
                "goal_id": goal.goal_id,
                "category": goal.category,
                "title": goal.title,
                "target_value": goal.target_value,
                "current_value": goal.current_value,
                "progress_percentage": goal.progress_percentage,
                "status": goal.status.value,
            }
            for goal in goals
        ],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Recommendations saved to {output_path}")

    return analysis


def main() -> None:
    """Main entry point for the health recommendation engine."""
    settings = AppSettings()
    config_path = Path(settings.config_path)

    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent
        config_path = project_root / config_path

    try:
        logger.info("Starting health recommendation analysis")
        analysis = process_health_analysis(config_path)
        logger.info(
            f"Analysis complete. Generated {len(analysis.recommendations)} "
            f"recommendations and tracked {len(analysis.goals)} goals."
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
