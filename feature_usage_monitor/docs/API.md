# Feature Usage Monitor API Documentation

## Overview

This document describes the public API for the feature usage monitoring system.

## Configuration Models

### UsageDataConfig

Configuration for usage data source.

**Fields:**
- `file_path` (str): Path to usage data file
- `format` (str): File format (`csv` or `json`)
- `user_id_column` (str): Column name for user identifiers
- `feature_name_column` (str): Column name for feature names
- `timestamp_column` (str): Column name for event timestamps
- `event_type_column` (Optional[str]): Column name for event types
- `session_id_column` (Optional[str]): Column name for session identifiers

### FeatureConfig

Configuration for feature definitions.

**Fields:**
- `features_file` (Optional[str]): Path to file listing all features
- `min_usage_threshold` (int): Minimum usage count to consider feature active
- `adoption_threshold_days` (int): Days to consider for adoption calculation
- `unused_threshold_percentage` (float): Percentage threshold for unused detection

### AnalysisConfig

Configuration for analysis parameters.

**Fields:**
- `lookback_days` (int): Days of historical data to analyze
- `analysis_window_days` (int): Time window for trend analysis
- `min_users_for_feature` (int): Minimum unique users for feature analysis

## Data Models

### FeatureUsage

Usage statistics for a feature.

**Fields:**
- `feature_name` (str): Name of the feature
- `total_usage_count` (int): Total number of usage events
- `unique_users` (int): Number of unique users who used the feature
- `adoption_rate` (float): Adoption rate percentage
- `avg_usage_per_user` (float): Average usage count per user
- `last_used` (Optional[datetime]): Last usage timestamp
- `usage_trend` (str): Usage trend (`increasing`, `decreasing`, `stable`, `new`)

### UnusedFeature

Information about an unused feature.

**Fields:**
- `feature_name` (str): Name of the feature
- `total_usage_count` (int): Total usage count
- `unique_users` (int): Number of unique users
- `last_used` (Optional[datetime]): Last usage timestamp
- `days_since_last_use` (Optional[int]): Days since last use

### AdoptionMetrics

Adoption metrics for a feature.

**Fields:**
- `feature_name` (str): Name of the feature
- `total_users` (int): Total number of users in dataset
- `adopted_users` (int): Number of users who adopted the feature
- `adoption_percentage` (float): Adoption percentage
- `adoption_velocity` (float): Adoption velocity (users per day)
- `days_to_adoption` (Optional[float]): Average days to adoption

### UsageInsights

Complete usage insights analysis.

**Fields:**
- `total_features` (int): Total number of features
- `active_features` (int): Number of active features
- `unused_features` (int): Number of unused features
- `feature_usage_stats` (List[FeatureUsage]): Usage statistics for all features
- `unused_features_list` (List[UnusedFeature]): List of unused features
- `adoption_metrics` (List[AdoptionMetrics]): Adoption metrics for all features
- `top_features` (List[str]): Top features by usage
- `insights` (List[str]): Generated insights
- `generated_at` (datetime): Generation timestamp

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

### load_usage_data(config: UsageDataConfig, project_root: Path) -> pd.DataFrame

Load usage data from CSV or JSON file.

**Parameters:**
- `config` (UsageDataConfig): Usage data configuration
- `project_root` (Path): Project root directory

**Returns:**
- `pd.DataFrame`: DataFrame with usage data

**Raises:**
- `FileNotFoundError`: If data file does not exist
- `ValueError`: If data format is invalid

### analyze_feature_usage(df: pd.DataFrame, config: UsageDataConfig, analysis_config: AnalysisConfig) -> Dict[str, FeatureUsage]

Analyze usage statistics for each feature.

**Parameters:**
- `df` (pd.DataFrame): DataFrame with usage data
- `config` (UsageDataConfig): Usage data configuration
- `analysis_config` (AnalysisConfig): Analysis configuration

**Returns:**
- `Dict[str, FeatureUsage]`: Dictionary mapping feature name to FeatureUsage

### calculate_adoption_rates(df: pd.DataFrame, config: UsageDataConfig, feature_config: FeatureConfig, analysis_config: AnalysisConfig) -> Dict[str, AdoptionMetrics]

Calculate adoption rates for features.

**Parameters:**
- `df` (pd.DataFrame): DataFrame with usage data
- `config` (UsageDataConfig): Usage data configuration
- `feature_config` (FeatureConfig): Feature configuration
- `analysis_config` (AnalysisConfig): Analysis configuration

**Returns:**
- `Dict[str, AdoptionMetrics]`: Dictionary mapping feature name to AdoptionMetrics

### identify_unused_features(feature_usage: Dict[str, FeatureUsage], all_features: Set[str], feature_config: FeatureConfig, total_users: int) -> List[UnusedFeature]

Identify unused or rarely used features.

**Parameters:**
- `feature_usage` (Dict[str, FeatureUsage]): Dictionary of feature usage statistics
- `all_features` (Set[str]): Set of all known features
- `feature_config` (FeatureConfig): Feature configuration
- `total_users` (int): Total number of users

**Returns:**
- `List[UnusedFeature]`: List of unused features

### process_feature_usage(config_path: Path) -> UsageInsights

Process feature usage data and generate insights.

**Parameters:**
- `config_path` (Path): Path to configuration file

**Returns:**
- `UsageInsights`: Complete usage insights

**Raises:**
- `FileNotFoundError`: If config or data files are missing
- `ValueError`: If configuration is invalid

## Example Usage

```python
from pathlib import Path
from feature_usage_monitor.src.main import process_feature_usage

config_path = Path("config.yaml")
insights = process_feature_usage(config_path)

print(f"Total features: {insights.total_features}")
print(f"Active features: {insights.active_features}")
print(f"Unused features: {insights.unused_features}")

for insight in insights.insights:
    print(f"- {insight}")
```
