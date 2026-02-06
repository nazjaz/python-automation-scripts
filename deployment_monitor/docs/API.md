# Deployment Monitor API Documentation

## Overview

This document describes the public API for the deployment monitoring system.

## Configuration Models

### DeploymentDataConfig

Configuration for deployment data source.

**Fields:**
- `file_path` (str): Path to deployment data file
- `format` (str): File format (`csv` or `json`)
- `deployment_id_column` (str): Column name for deployment ID
- `timestamp_column` (str): Column name for deployment timestamp
- `status_column` (str): Column name for deployment status
- `environment_column` (Optional[str]): Column name for environment
- `version_column` (Optional[str]): Column name for version
- `duration_column` (Optional[str]): Column name for deployment duration
- `error_message_column` (Optional[str]): Column name for error message

### RegressionConfig

Configuration for regression detection.

**Fields:**
- `lookback_window_days` (int): Days to look back for baseline comparison
- `comparison_window_days` (int): Days in recent window for comparison
- `success_rate_threshold` (float): Success rate drop threshold for regression
- `failure_rate_threshold` (float): Failure rate threshold for critical regression

### MetricsConfig

Configuration for quality metrics.

**Fields:**
- `mttr_window_days` (int): Days to calculate MTTR over
- `deployment_frequency_window_days` (int): Days to calculate deployment frequency over
- `change_failure_rate_window_days` (int): Days to calculate change failure rate over

## Data Models

### DeploymentRecord

Represents a deployment record.

**Fields:**
- `deployment_id` (str): Unique deployment identifier
- `timestamp` (datetime): Deployment timestamp
- `status` (DeploymentStatus): Deployment status
- `environment` (Optional[str]): Environment name
- `version` (Optional[str]): Version identifier
- `duration_seconds` (Optional[float]): Deployment duration in seconds
- `error_message` (Optional[str]): Error message if failed

### RegressionPattern

Identified regression pattern.

**Fields:**
- `pattern_type` (str): Type of regression pattern
- `severity` (RegressionSeverity): Severity level
- `description` (str): Human-readable description
- `baseline_metric` (float): Baseline metric value
- `current_metric` (float): Current metric value
- `change_percentage` (float): Percentage change
- `affected_deployments` (List[str]): List of affected deployment IDs

### QualityMetrics

Release quality metrics.

**Fields:**
- `deployment_frequency` (float): Average deployments per day
- `success_rate` (float): Success rate (0.0 to 1.0)
- `failure_rate` (float): Failure rate (0.0 to 1.0)
- `change_failure_rate` (float): Change failure rate (0.0 to 1.0)
- `mean_time_to_recovery` (Optional[float]): MTTR in hours
- `deployment_count` (int): Total deployment count
- `successful_deployments` (int): Number of successful deployments
- `failed_deployments` (int): Number of failed deployments
- `rolled_back_deployments` (int): Number of rolled back deployments

### DeploymentAnalysis

Complete deployment analysis results.

**Fields:**
- `quality_metrics` (QualityMetrics): Quality metrics
- `regression_patterns` (List[RegressionPattern]): Identified regression patterns
- `daily_deployment_counts` (Dict[str, int]): Daily deployment counts
- `environment_breakdown` (Dict[str, Dict[str, int]]): Breakdown by environment
- `version_success_rates` (Dict[str, float]): Success rates by version
- `generated_at` (datetime): Analysis generation timestamp

## Enumerations

### DeploymentStatus

Deployment status enumeration.

**Values:**
- `SUCCESS`: Deployment succeeded
- `FAILED`: Deployment failed
- `ROLLED_BACK`: Deployment rolled back
- `PARTIAL`: Partial deployment

### RegressionSeverity

Regression severity levels.

**Values:**
- `CRITICAL`: Critical regression
- `HIGH`: High severity regression
- `MEDIUM`: Medium severity regression
- `LOW`: Low severity regression

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

### load_deployment_data(config: DeploymentDataConfig, project_root: Path) -> List[DeploymentRecord]

Load deployment data from CSV or JSON file.

**Parameters:**
- `config` (DeploymentDataConfig): Deployment data configuration
- `project_root` (Path): Project root directory

**Returns:**
- `List[DeploymentRecord]`: List of deployment records

**Raises:**
- `FileNotFoundError`: If data file does not exist
- `ValueError`: If data format is invalid

### calculate_deployment_frequency(deployments: List[DeploymentRecord], window_days: int) -> float

Calculate average deployments per day.

**Parameters:**
- `deployments` (List[DeploymentRecord]): List of deployment records
- `window_days` (int): Time window in days

**Returns:**
- `float`: Average deployments per day

### calculate_success_rate(deployments: List[DeploymentRecord]) -> Tuple[float, int, int]

Calculate deployment success rate.

**Parameters:**
- `deployments` (List[DeploymentRecord]): List of deployment records

**Returns:**
- `Tuple[float, int, int]`: (success_rate, successful_count, total_count)

### calculate_mttr(deployments: List[DeploymentRecord], window_days: int) -> Optional[float]

Calculate Mean Time To Recovery (MTTR) in hours.

**Parameters:**
- `deployments` (List[DeploymentRecord]): List of deployment records
- `window_days` (int): Time window in days

**Returns:**
- `Optional[float]`: MTTR in hours, or None if insufficient data

### identify_regression_patterns(deployments: List[DeploymentRecord], config: RegressionConfig) -> List[RegressionPattern]

Identify regression patterns in deployments.

**Parameters:**
- `deployments` (List[DeploymentRecord]): List of deployment records
- `config` (RegressionConfig): Regression detection configuration

**Returns:**
- `List[RegressionPattern]`: List of identified regression patterns

### calculate_quality_metrics(deployments: List[DeploymentRecord], config: MetricsConfig) -> QualityMetrics

Calculate release quality metrics.

**Parameters:**
- `deployments` (List[DeploymentRecord]): List of deployment records
- `config` (MetricsConfig): Metrics configuration

**Returns:**
- `QualityMetrics`: Quality metrics object

### process_deployments(config_path: Path) -> DeploymentAnalysis

Process deployment data and generate analysis.

**Parameters:**
- `config_path` (Path): Path to configuration file

**Returns:**
- `DeploymentAnalysis`: Complete deployment analysis

**Raises:**
- `FileNotFoundError`: If config or data files are missing
- `ValueError`: If configuration is invalid

## Example Usage

```python
from pathlib import Path
from deployment_monitor.src.main import process_deployments

config_path = Path("config.yaml")
analysis = process_deployments(config_path)

print(f"Deployment Frequency: {analysis.quality_metrics.deployment_frequency:.2f}/day")
print(f"Success Rate: {analysis.quality_metrics.success_rate:.1%}")
print(f"MTTR: {analysis.quality_metrics.mean_time_to_recovery:.2f} hours")
print(f"Regression Patterns: {len(analysis.regression_patterns)}")

for pattern in analysis.regression_patterns:
    print(f"- {pattern.description} ({pattern.severity.value})")
```
