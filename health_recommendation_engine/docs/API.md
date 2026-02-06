# Health Recommendation Engine API Documentation

## Overview

This document describes the public API for the health recommendation engine system.

## Configuration Models

### ActivityDataConfig

Configuration for activity data source.

**Fields:**
- `file_path` (str): Path to activity data file
- `format` (str): File format (`csv` or `json`)
- `date_column` (str): Column name for date
- `steps_column` (Optional[str]): Column name for steps
- `calories_column` (Optional[str]): Column name for calories burned
- `active_minutes_column` (Optional[str]): Column name for active minutes
- `distance_column` (Optional[str]): Column name for distance

### SleepDataConfig

Configuration for sleep data source.

**Fields:**
- `file_path` (str): Path to sleep data file
- `format` (str): File format (`csv` or `json`)
- `date_column` (str): Column name for date
- `sleep_hours_column` (str): Column name for sleep hours
- `sleep_quality_column` (Optional[str]): Column name for sleep quality score
- `bedtime_column` (Optional[str]): Column name for bedtime
- `wake_time_column` (Optional[str]): Column name for wake time

### HealthMetricsConfig

Configuration for health metrics data source.

**Fields:**
- `file_path` (str): Path to health metrics file
- `format` (str): File format (`csv` or `json`)
- `date_column` (str): Column name for date
- `weight_column` (Optional[str]): Column name for weight
- `heart_rate_column` (Optional[str]): Column name for resting heart rate
- `blood_pressure_column` (Optional[str]): Column name for blood pressure

### RecommendationConfig

Configuration for recommendation generation.

**Fields:**
- `target_steps_per_day` (int): Target steps per day
- `target_sleep_hours` (float): Target sleep hours per night
- `min_sleep_hours` (float): Minimum recommended sleep hours
- `max_sleep_hours` (float): Maximum recommended sleep hours
- `target_active_minutes` (int): Target active minutes per day

## Data Models

### ActivityMetrics

Activity metrics for analysis.

**Fields:**
- `date` (datetime): Date of the activity record
- `steps` (Optional[int]): Number of steps
- `calories` (Optional[float]): Calories burned
- `active_minutes` (Optional[int]): Active minutes
- `distance` (Optional[float]): Distance traveled

### SleepMetrics

Sleep metrics for analysis.

**Fields:**
- `date` (datetime): Date of the sleep record
- `sleep_hours` (float): Hours of sleep
- `sleep_quality` (Optional[float]): Sleep quality score
- `bedtime` (Optional[datetime]): Bedtime
- `wake_time` (Optional[datetime]): Wake time

### HealthMetrics

Health metrics for analysis.

**Fields:**
- `date` (datetime): Date of the health record
- `weight` (Optional[float]): Weight measurement
- `heart_rate` (Optional[int]): Resting heart rate
- `blood_pressure` (Optional[str]): Blood pressure reading

### HealthRecommendation

Personalized health recommendation.

**Fields:**
- `category` (str): Recommendation category (e.g., "Activity", "Sleep")
- `title` (str): Recommendation title
- `description` (str): Detailed description
- `priority` (RecommendationPriority): Priority level
- `rationale` (str): Explanation for the recommendation
- `action_items` (List[str]): List of actionable steps
- `target_value` (Optional[float]): Target metric value
- `current_value` (Optional[float]): Current metric value

### HealthGoal

Health goal definition.

**Fields:**
- `goal_id` (str): Unique goal identifier
- `category` (str): Goal category
- `title` (str): Goal title
- `target_value` (float): Target value
- `unit` (str): Unit of measurement
- `start_date` (datetime): Goal start date
- `target_date` (datetime): Goal target date
- `status` (GoalStatus): Current goal status
- `current_value` (Optional[float]): Current progress value
- `progress_percentage` (float): Progress percentage (0-100)

### HealthAnalysis

Complete health analysis results.

**Fields:**
- `activity_summary` (Dict[str, float]): Activity summary statistics
- `sleep_summary` (Dict[str, float]): Sleep summary statistics
- `health_metrics_summary` (Dict[str, float]): Health metrics summary
- `recommendations` (List[HealthRecommendation]): Generated recommendations
- `goals` (List[HealthGoal]): Health goals
- `progress_updates` (List[Dict[str, any]]): Progress update records
- `generated_at` (datetime): Analysis generation timestamp

## Functions

### load_config(config_path: Path) -> Config

Load and validate configuration from YAML file.

**Parameters:**
- `config_path` (Path): Path to configuration YAML file

**Returns:**
- `Config`: Validated configuration object

**Raises:**
- `FileNotFoundError`: If config file does not exist
- `ValueError`: If configuration is invalid

### load_activity_data(config: ActivityDataConfig, project_root: Path) -> List[ActivityMetrics]

Load activity data from file.

**Parameters:**
- `config` (ActivityDataConfig): Activity data configuration
- `project_root` (Path): Project root directory

**Returns:**
- `List[ActivityMetrics]`: List of activity metrics

**Raises:**
- `FileNotFoundError`: If data file does not exist
- `ValueError`: If data format is invalid

### load_sleep_data(config: SleepDataConfig, project_root: Path) -> List[SleepMetrics]

Load sleep data from file.

**Parameters:**
- `config` (SleepDataConfig): Sleep data configuration
- `project_root` (Path): Project root directory

**Returns:**
- `List[SleepMetrics]`: List of sleep metrics

**Raises:**
- `FileNotFoundError`: If data file does not exist
- `ValueError`: If data format is invalid

### analyze_activity(activities: List[ActivityMetrics], config: RecommendationConfig) -> Dict[str, float]

Analyze activity data and calculate summary statistics.

**Parameters:**
- `activities` (List[ActivityMetrics]): List of activity metrics
- `config` (RecommendationConfig): Recommendation configuration

**Returns:**
- `Dict[str, float]`: Dictionary of summary statistics

### analyze_sleep(sleep_records: List[SleepMetrics], config: RecommendationConfig) -> Dict[str, float]

Analyze sleep data and calculate summary statistics.

**Parameters:**
- `sleep_records` (List[SleepMetrics]): List of sleep metrics
- `config` (RecommendationConfig): Recommendation configuration

**Returns:**
- `Dict[str, float]`: Dictionary of summary statistics

### generate_recommendations(activity_summary: Dict[str, float], sleep_summary: Dict[str, float], health_summary: Dict[str, float], config: RecommendationConfig) -> List[HealthRecommendation]

Generate personalized health recommendations.

**Parameters:**
- `activity_summary` (Dict[str, float]): Activity summary statistics
- `sleep_summary` (Dict[str, float]): Sleep summary statistics
- `health_summary` (Dict[str, float]): Health metrics summary
- `config` (RecommendationConfig): Recommendation configuration

**Returns:**
- `List[HealthRecommendation]`: List of health recommendations

### process_health_analysis(config_path: Path) -> HealthAnalysis

Process health data and generate recommendations.

**Parameters:**
- `config_path` (Path): Path to configuration file

**Returns:**
- `HealthAnalysis`: Complete health analysis

**Raises:**
- `FileNotFoundError`: If config or data files are missing
- `ValueError`: If configuration is invalid

## Example Usage

```python
from pathlib import Path
from health_recommendation_engine.src.main import process_health_analysis

config_path = Path("config.yaml")
analysis = process_health_analysis(config_path)

print(f"Generated {len(analysis.recommendations)} recommendations")
for rec in analysis.recommendations:
    print(f"- {rec.title} ({rec.priority.value}): {rec.description}")

print(f"\nTracking {len(analysis.goals)} goals")
for goal in analysis.goals:
    print(f"- {goal.title}: {goal.progress_percentage:.1f}% complete")
```
