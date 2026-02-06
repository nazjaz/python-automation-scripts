# Performance Budget Monitor API Documentation

## Overview

This document describes the public API for the performance budget monitoring system.

## Configuration Models

### PerformanceDataConfig

Configuration for performance data source.

**Fields:**
- `file_path` (str): Path to performance data file
- `format` (str): File format (`csv` or `json`)
- `timestamp_column` (str): Column name for timestamp
- `resource_type_column` (str): Column name for resource type
- `resource_name_column` (str): Column name for resource name
- `consumption_column` (str): Column name for consumption value
- `unit_column` (Optional[str]): Column name for unit
- `cost_column` (Optional[str]): Column name for cost

### BudgetConfig

Configuration for performance budgets.

**Fields:**
- `budgets` (Dict[str, Dict[str, float]]): Budget definitions by resource type and name
- `warning_threshold` (float): Warning threshold as percentage of budget
- `critical_threshold` (float): Critical threshold as percentage of budget

### CostConfig

Configuration for cost calculations.

**Fields:**
- `cost_per_unit` (Dict[str, Dict[str, float]]): Cost per unit by resource type and unit
- `optimization_cost_threshold` (float): Minimum cost savings for optimization

### OptimizationConfig

Configuration for optimization detection.

**Fields:**
- `consumption_increase_threshold` (float): Percentage increase to flag as opportunity
- `min_data_points` (int): Minimum data points for trend analysis
- `lookback_days` (int): Days to look back for trend analysis

## Data Models

### PerformanceRecord

Represents a performance measurement record.

**Fields:**
- `timestamp` (datetime): Measurement timestamp
- `resource_type` (ResourceType): Type of resource
- `resource_name` (str): Name of the resource
- `consumption` (float): Consumption value
- `unit` (Optional[str]): Unit of measurement
- `cost` (Optional[float]): Cost for this consumption

### BudgetAlert

Budget alert for a resource.

**Fields:**
- `resource_type` (ResourceType): Type of resource
- `resource_name` (str): Name of the resource
- `current_consumption` (float): Current consumption value
- `budget_limit` (float): Budget limit
- `utilization_percentage` (float): Utilization as percentage
- `status` (BudgetStatus): Alert status
- `timestamp` (datetime): Alert timestamp

### OptimizationOpportunity

Identified optimization opportunity.

**Fields:**
- `resource_type` (ResourceType): Type of resource
- `resource_name` (str): Name of the resource
- `current_consumption` (float): Current average consumption
- `baseline_consumption` (float): Baseline average consumption
- `increase_percentage` (float): Percentage increase
- `potential_savings` (Optional[float]): Potential cost savings
- `priority` (OptimizationPriority): Priority level
- `recommendation` (str): Optimization recommendation

### CostPerformanceTradeoff

Cost-performance trade-off analysis.

**Fields:**
- `resource_name` (str): Resource name
- `resource_type` (ResourceType): Resource type
- `current_cost` (float): Current cost
- `current_performance` (float): Current performance metric
- `optimization_cost` (float): Cost to implement optimization
- `optimized_performance` (float): Performance after optimization
- `cost_savings` (float): Estimated cost savings
- `performance_impact` (float): Performance impact percentage
- `roi` (float): Return on investment
- `recommendation` (str): Recommendation text

### PerformanceAnalysis

Complete performance analysis results.

**Fields:**
- `budget_alerts` (List[BudgetAlert]): List of budget alerts
- `optimization_opportunities` (List[OptimizationOpportunity]): List of optimization opportunities
- `cost_performance_tradeoffs` (List[CostPerformanceTradeoff]): List of trade-off analyses
- `resource_summary` (Dict[str, Dict[str, float]]): Resource consumption summary
- `total_cost` (float): Total cost
- `potential_savings` (float): Total potential savings
- `generated_at` (datetime): Analysis generation timestamp

## Enumerations

### ResourceType

Resource type enumeration.

**Values:**
- `CPU`: CPU usage
- `MEMORY`: Memory usage
- `STORAGE`: Storage usage
- `NETWORK`: Network bandwidth
- `DATABASE`: Database resources
- `API_CALLS`: API call volume

### BudgetStatus

Budget status enumeration.

**Values:**
- `WITHIN_BUDGET`: Within budget limits
- `APPROACHING_LIMIT`: Approaching warning threshold
- `EXCEEDED`: Exceeded budget limit
- `CRITICAL`: At or above critical threshold

### OptimizationPriority

Optimization priority levels.

**Values:**
- `HIGH`: High priority optimization
- `MEDIUM`: Medium priority optimization
- `LOW`: Low priority optimization

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

### load_performance_data(config: PerformanceDataConfig, project_root: Path) -> List[PerformanceRecord]

Load performance data from file.

**Parameters:**
- `config` (PerformanceDataConfig): Performance data configuration
- `project_root` (Path): Project root directory

**Returns:**
- `List[PerformanceRecord]`: List of performance records

**Raises:**
- `FileNotFoundError`: If data file does not exist
- `ValueError`: If data format is invalid

### check_budget_status(records: List[PerformanceRecord], budget_config: BudgetConfig) -> List[BudgetAlert]

Check budget status for all resources.

**Parameters:**
- `records` (List[PerformanceRecord]): List of performance records
- `budget_config` (BudgetConfig): Budget configuration

**Returns:**
- `List[BudgetAlert]`: List of budget alerts

### identify_optimization_opportunities(records: List[PerformanceRecord], optimization_config: OptimizationConfig, cost_config: CostConfig) -> List[OptimizationOpportunity]

Identify optimization opportunities.

**Parameters:**
- `records` (List[PerformanceRecord]): List of performance records
- `optimization_config` (OptimizationConfig): Optimization configuration
- `cost_config` (CostConfig): Cost configuration

**Returns:**
- `List[OptimizationOpportunity]`: List of optimization opportunities

### analyze_cost_performance_tradeoffs(records: List[PerformanceRecord], opportunities: List[OptimizationOpportunity], cost_config: CostConfig) -> List[CostPerformanceTradeoff]

Analyze cost-performance trade-offs.

**Parameters:**
- `records` (List[PerformanceRecord]): List of performance records
- `opportunities` (List[OptimizationOpportunity]): List of optimization opportunities
- `cost_config` (CostConfig): Cost configuration

**Returns:**
- `List[CostPerformanceTradeoff]`: List of trade-off analyses

### process_performance_analysis(config_path: Path) -> PerformanceAnalysis

Process performance data and generate analysis.

**Parameters:**
- `config_path` (Path): Path to configuration file

**Returns:**
- `PerformanceAnalysis`: Complete performance analysis

**Raises:**
- `FileNotFoundError`: If config or data files are missing
- `ValueError`: If configuration is invalid

## Example Usage

```python
from pathlib import Path
from performance_budget_monitor.src.main import process_performance_analysis

config_path = Path("config.yaml")
analysis = process_performance_analysis(config_path)

print(f"Total Cost: ${analysis.total_cost:,.2f}")
print(f"Potential Savings: ${analysis.potential_savings:,.2f}")
print(f"Budget Alerts: {len(analysis.budget_alerts)}")
print(f"Optimization Opportunities: {len(analysis.optimization_opportunities)}")

for alert in analysis.budget_alerts:
    print(f"Alert: {alert.resource_name} - {alert.status.value}")

for tradeoff in analysis.cost_performance_tradeoffs:
    print(f"Trade-off: {tradeoff.resource_name} - ROI: {tradeoff.roi:.1%}")
```
