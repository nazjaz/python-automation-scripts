"""Performance Budget Monitor.

Monitors application performance budgets, tracks resource consumption,
identifies optimization opportunities, and generates cost-performance
trade-off analyses.
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


class ResourceType(str, Enum):
    """Resource type enumeration."""

    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    API_CALLS = "api_calls"


class BudgetStatus(str, Enum):
    """Budget status enumeration."""

    WITHIN_BUDGET = "within_budget"
    APPROACHING_LIMIT = "approaching_limit"
    EXCEEDED = "exceeded"
    CRITICAL = "critical"


class OptimizationPriority(str, Enum):
    """Optimization priority levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PerformanceDataConfig(BaseModel):
    """Configuration for performance data source."""

    file_path: str = Field(..., description="Path to performance data file")
    format: str = Field(default="csv", description="File format: csv or json")
    timestamp_column: str = Field(
        default="timestamp", description="Column name for timestamp"
    )
    resource_type_column: str = Field(
        default="resource_type", description="Column name for resource type"
    )
    resource_name_column: str = Field(
        default="resource_name", description="Column name for resource name"
    )
    consumption_column: str = Field(
        default="consumption", description="Column name for consumption value"
    )
    unit_column: Optional[str] = Field(
        default=None, description="Column name for unit"
    )
    cost_column: Optional[str] = Field(
        default=None, description="Column name for cost"
    )


class BudgetConfig(BaseModel):
    """Configuration for performance budgets."""

    budgets: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Budget definitions by resource type and name",
    )
    warning_threshold: float = Field(
        default=0.8, description="Warning threshold as percentage of budget"
    )
    critical_threshold: float = Field(
        default=0.95, description="Critical threshold as percentage of budget"
    )


class CostConfig(BaseModel):
    """Configuration for cost calculations."""

    cost_per_unit: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Cost per unit by resource type and unit",
    )
    optimization_cost_threshold: float = Field(
        default=100.0, description="Minimum cost savings for optimization"
    )


class OptimizationConfig(BaseModel):
    """Configuration for optimization detection."""

    consumption_increase_threshold: float = Field(
        default=0.2, description="Percentage increase to flag as optimization opportunity"
    )
    min_data_points: int = Field(
        default=10, description="Minimum data points for trend analysis"
    )
    lookback_days: int = Field(
        default=30, description="Days to look back for trend analysis"
    )


class AnalysisConfig(BaseModel):
    """Configuration for cost-performance analysis."""

    output_format: str = Field(
        default="markdown", description="Report format: markdown or html"
    )
    output_path: str = Field(
        default="logs/performance_analysis.md",
        description="Path for analysis report",
    )


class Config(BaseModel):
    """Main configuration model."""

    performance_data: PerformanceDataConfig = Field(
        ..., description="Performance data source configuration"
    )
    budget: BudgetConfig = Field(
        default_factory=BudgetConfig, description="Budget configuration"
    )
    cost: CostConfig = Field(
        default_factory=CostConfig, description="Cost configuration"
    )
    optimization: OptimizationConfig = Field(
        default_factory=OptimizationConfig,
        description="Optimization detection settings",
    )
    analysis: AnalysisConfig = Field(
        default_factory=AnalysisConfig,
        description="Analysis generation settings",
    )
    alerts_output_file: str = Field(
        default="logs/budget_alerts.json",
        description="Path to save budget alerts",
    )


class AppSettings(BaseSettings):
    """Application settings from environment variables."""

    config_path: str = "config.yaml"


@dataclass
class PerformanceRecord:
    """Represents a performance measurement record."""

    timestamp: datetime
    resource_type: ResourceType
    resource_name: str
    consumption: float
    unit: Optional[str] = None
    cost: Optional[float] = None


@dataclass
class BudgetAlert:
    """Budget alert for a resource."""

    resource_type: ResourceType
    resource_name: str
    current_consumption: float
    budget_limit: float
    utilization_percentage: float
    status: BudgetStatus
    timestamp: datetime


@dataclass
class OptimizationOpportunity:
    """Identified optimization opportunity."""

    resource_type: ResourceType
    resource_name: str
    current_consumption: float
    baseline_consumption: float
    increase_percentage: float
    potential_savings: Optional[float] = None
    priority: OptimizationPriority = OptimizationPriority.MEDIUM
    recommendation: str = ""


@dataclass
class CostPerformanceTradeoff:
    """Cost-performance trade-off analysis."""

    resource_name: str
    resource_type: ResourceType
    current_cost: float
    current_performance: float
    optimization_cost: float
    optimized_performance: float
    cost_savings: float
    performance_impact: float
    roi: float
    recommendation: str


@dataclass
class PerformanceAnalysis:
    """Complete performance analysis results."""

    budget_alerts: List[BudgetAlert]
    optimization_opportunities: List[OptimizationOpportunity]
    cost_performance_tradeoffs: List[CostPerformanceTradeoff]
    resource_summary: Dict[str, Dict[str, float]]
    total_cost: float
    potential_savings: float
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


def load_performance_data(
    config: PerformanceDataConfig, project_root: Path
) -> List[PerformanceRecord]:
    """Load performance data from file.

    Args:
        config: Performance data configuration
        project_root: Project root directory

    Returns:
        List of PerformanceRecord objects

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        raise FileNotFoundError(f"Performance data file not found: {data_path}")

    records = []

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        required_columns = [
            config.timestamp_column,
            config.resource_type_column,
            config.resource_name_column,
            config.consumption_column,
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df[config.timestamp_column] = pd.to_datetime(df[config.timestamp_column])

        for _, row in df.iterrows():
            resource_type_str = str(row[config.resource_type_column]).lower()
            try:
                resource_type = ResourceType(resource_type_str)
            except ValueError:
                logger.warning(f"Unknown resource type: {resource_type_str}")
                continue

            record = PerformanceRecord(
                timestamp=row[config.timestamp_column],
                resource_type=resource_type,
                resource_name=str(row[config.resource_name_column]),
                consumption=float(row[config.consumption_column]),
            )

            if config.unit_column and config.unit_column in df.columns:
                if pd.notna(row[config.unit_column]):
                    record.unit = str(row[config.unit_column])

            if config.cost_column and config.cost_column in df.columns:
                if pd.notna(row[config.cost_column]):
                    record.cost = float(row[config.cost_column])

            records.append(record)

        logger.info(f"Loaded {len(records)} performance records")
        return records

    except pd.errors.EmptyDataError:
        logger.warning(f"Performance data file is empty: {data_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to load performance data: {e}")
        raise


def calculate_resource_costs(
    records: List[PerformanceRecord], cost_config: CostConfig
) -> List[PerformanceRecord]:
    """Calculate costs for performance records.

    Args:
        records: List of performance records
        cost_config: Cost configuration

    Returns:
        List of records with calculated costs
    """
    for record in records:
        if record.cost is None and record.unit:
            resource_costs = cost_config.cost_per_unit.get(
                record.resource_type.value, {}
            )
            unit_cost = resource_costs.get(record.unit, 0.0)
            if unit_cost > 0:
                record.cost = record.consumption * unit_cost

    return records


def check_budget_status(
    records: List[PerformanceRecord],
    budget_config: BudgetConfig,
) -> List[BudgetAlert]:
    """Check budget status for all resources.

    Args:
        records: List of performance records
        budget_config: Budget configuration

    Returns:
        List of budget alerts
    """
    alerts = []
    now = datetime.now()

    resource_consumption: Dict[Tuple[str, str], List[float]] = defaultdict(list)

    for record in records:
        key = (record.resource_type.value, record.resource_name)
        resource_consumption[key].append(record.consumption)

    for (resource_type_str, resource_name), consumptions in resource_consumption.items():
        resource_type = ResourceType(resource_type_str)
        budget_key = f"{resource_type.value}.{resource_name}"

        budget_limit = None
        if resource_type.value in budget_config.budgets:
            budget_limit = budget_config.budgets[resource_type.value].get(
                resource_name
            )

        if budget_limit is None:
            continue

        current_consumption = sum(consumptions) / len(consumptions)
        utilization = current_consumption / budget_limit

        if utilization >= budget_config.critical_threshold:
            status = BudgetStatus.CRITICAL
        elif utilization >= budget_config.warning_threshold:
            status = BudgetStatus.APPROACHING_LIMIT
        elif utilization >= 1.0:
            status = BudgetStatus.EXCEEDED
        else:
            status = BudgetStatus.WITHIN_BUDGET

        if status != BudgetStatus.WITHIN_BUDGET:
            alerts.append(
                BudgetAlert(
                    resource_type=resource_type,
                    resource_name=resource_name,
                    current_consumption=current_consumption,
                    budget_limit=budget_limit,
                    utilization_percentage=utilization * 100,
                    status=status,
                    timestamp=now,
                )
            )

    logger.info(f"Generated {len(alerts)} budget alerts")
    return alerts


def identify_optimization_opportunities(
    records: List[PerformanceRecord],
    optimization_config: OptimizationConfig,
    cost_config: CostConfig,
) -> List[OptimizationOpportunity]:
    """Identify optimization opportunities.

    Args:
        records: List of performance records
        optimization_config: Optimization configuration
        cost_config: Cost configuration

    Returns:
        List of optimization opportunities
    """
    opportunities = []
    cutoff_date = datetime.now() - timedelta(
        days=optimization_config.lookback_days
    )

    recent_records = [r for r in records if r.timestamp >= cutoff_date]
    older_records = [r for r in records if r.timestamp < cutoff_date]

    resource_groups: Dict[Tuple[str, str], List[PerformanceRecord]] = (
        defaultdict(list)
    )

    for record in recent_records:
        key = (record.resource_type.value, record.resource_name)
        resource_groups[key].append(record)

    baseline_groups: Dict[Tuple[str, str], List[PerformanceRecord]] = (
        defaultdict(list)
    )

    for record in older_records:
        key = (record.resource_type.value, record.resource_name)
        baseline_groups[key].append(record)

    for (resource_type_str, resource_name), recent_group in resource_groups.items():
        if len(recent_group) < optimization_config.min_data_points:
            continue

        baseline_group = baseline_groups.get(
            (resource_type_str, resource_name), []
        )

        if len(baseline_group) < optimization_config.min_data_points:
            continue

        recent_avg = sum(r.consumption for r in recent_group) / len(recent_group)
        baseline_avg = sum(r.consumption for r in baseline_group) / len(
            baseline_group
        )

        if baseline_avg == 0:
            continue

        increase_percentage = (recent_avg - baseline_avg) / baseline_avg

        if increase_percentage >= optimization_config.consumption_increase_threshold:
            resource_type = ResourceType(resource_type_str)

            potential_savings = None
            if recent_group[0].cost is not None and baseline_group[0].cost is not None:
                recent_cost = sum(r.cost or 0 for r in recent_group) / len(
                    recent_group
                )
                baseline_cost = sum(r.cost or 0 for r in baseline_group) / len(
                    baseline_group
                )
                potential_savings = recent_cost - baseline_cost

            priority = OptimizationPriority.HIGH
            if increase_percentage < 0.5:
                priority = OptimizationPriority.MEDIUM
            elif increase_percentage < 0.3:
                priority = OptimizationPriority.LOW

            recommendation = (
                f"Resource consumption increased by {increase_percentage:.1%}. "
                f"Consider optimization to reduce {resource_type.value} usage."
            )

            opportunities.append(
                OptimizationOpportunity(
                    resource_type=resource_type,
                    resource_name=resource_name,
                    current_consumption=recent_avg,
                    baseline_consumption=baseline_avg,
                    increase_percentage=increase_percentage * 100,
                    potential_savings=potential_savings,
                    priority=priority,
                    recommendation=recommendation,
                )
            )

    logger.info(f"Identified {len(opportunities)} optimization opportunities")
    return opportunities


def analyze_cost_performance_tradeoffs(
    records: List[PerformanceRecord],
    opportunities: List[OptimizationOpportunity],
    cost_config: CostConfig,
) -> List[CostPerformanceTradeoff]:
    """Analyze cost-performance trade-offs.

    Args:
        records: List of performance records
        opportunities: List of optimization opportunities
        cost_config: Cost configuration

    Returns:
        List of cost-performance trade-off analyses
    """
    tradeoffs = []

    for opp in opportunities:
        resource_records = [
            r
            for r in records
            if r.resource_type == opp.resource_type
            and r.resource_name == opp.resource_name
        ]

        if not resource_records:
            continue

        current_cost = (
            sum(r.cost or 0 for r in resource_records) / len(resource_records)
        )
        current_performance = opp.current_consumption

        optimization_cost = 0.0
        if opp.potential_savings:
            optimization_cost = abs(opp.potential_savings) * 0.1

        optimized_performance = opp.baseline_consumption
        cost_savings = opp.potential_savings or 0.0

        performance_impact = (
            (current_performance - optimized_performance) / current_performance
            if current_performance > 0
            else 0.0
        )

        roi = (
            (cost_savings - optimization_cost) / optimization_cost
            if optimization_cost > 0
            else 0.0
        )

        if cost_savings >= cost_config.optimization_cost_threshold:
            recommendation = (
                f"Optimization recommended. Estimated savings: "
                f"${cost_savings:.2f} with ROI of {roi:.1%}"
            )
        else:
            recommendation = (
                f"Optimization may not be cost-effective. "
                f"Estimated savings below threshold."
            )

        tradeoffs.append(
            CostPerformanceTradeoff(
                resource_name=opp.resource_name,
                resource_type=opp.resource_type,
                current_cost=current_cost,
                current_performance=current_performance,
                optimization_cost=optimization_cost,
                optimized_performance=optimized_performance,
                cost_savings=cost_savings,
                performance_impact=performance_impact,
                roi=roi,
                recommendation=recommendation,
            )
        )

    logger.info(f"Generated {len(tradeoffs)} cost-performance trade-off analyses")
    return tradeoffs


def write_markdown_report(
    analysis: PerformanceAnalysis, output_path: Path
) -> None:
    """Write performance analysis report to markdown file.

    Args:
        analysis: Performance analysis results
        output_path: Path to write the report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Performance Budget Analysis Report\n\n")
        f.write(
            f"**Generated:** {analysis.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        f.write("## Summary\n\n")
        f.write(f"- **Total Cost:** ${analysis.total_cost:,.2f}\n")
        f.write(
            f"- **Potential Savings:** ${analysis.potential_savings:,.2f}\n"
        )
        f.write(f"- **Budget Alerts:** {len(analysis.budget_alerts)}\n")
        f.write(
            f"- **Optimization Opportunities:** {len(analysis.optimization_opportunities)}\n"
        )
        f.write("\n")

        f.write("## Budget Alerts\n\n")
        if analysis.budget_alerts:
            f.write(
                "| Resource | Type | Consumption | Budget | Utilization | Status |\n"
            )
            f.write(
                "|----------|------|-------------|--------|-------------|--------|\n"
            )
            for alert in analysis.budget_alerts:
                f.write(
                    f"| {alert.resource_name} | {alert.resource_type.value} | "
                    f"{alert.current_consumption:.2f} | {alert.budget_limit:.2f} | "
                    f"{alert.utilization_percentage:.1f}% | "
                    f"{alert.status.value.replace('_', ' ').title()} |\n"
                )
        else:
            f.write("No budget alerts.\n")
        f.write("\n")

        f.write("## Optimization Opportunities\n\n")
        if analysis.optimization_opportunities:
            f.write(
                "| Resource | Type | Increase % | Potential Savings | Priority |\n"
            )
            f.write(
                "|----------|------|------------|-------------------|----------|\n"
            )
            for opp in sorted(
                analysis.optimization_opportunities,
                key=lambda x: x.increase_percentage,
                reverse=True,
            ):
                savings_str = (
                    f"${opp.potential_savings:,.2f}"
                    if opp.potential_savings
                    else "N/A"
                )
                f.write(
                    f"| {opp.resource_name} | {opp.resource_type.value} | "
                    f"{opp.increase_percentage:.1f}% | {savings_str} | "
                    f"{opp.priority.value} |\n"
                )
        else:
            f.write("No optimization opportunities identified.\n")
        f.write("\n")

        f.write("## Cost-Performance Trade-off Analysis\n\n")
        if analysis.cost_performance_tradeoffs:
            f.write(
                "| Resource | Current Cost | Savings | ROI | Performance Impact |\n"
            )
            f.write(
                "|----------|--------------|---------|-----|-------------------|\n"
            )
            for tradeoff in sorted(
                analysis.cost_performance_tradeoffs,
                key=lambda x: x.roi,
                reverse=True,
            ):
                f.write(
                    f"| {tradeoff.resource_name} | ${tradeoff.current_cost:,.2f} | "
                    f"${tradeoff.cost_savings:,.2f} | {tradeoff.roi:.1%} | "
                    f"{tradeoff.performance_impact:.1%} |\n"
                )
        else:
            f.write("No trade-off analyses available.\n")

    logger.info(f"Report written to {output_path}")


def process_performance_analysis(config_path: Path) -> PerformanceAnalysis:
    """Process performance data and generate analysis.

    Args:
        config_path: Path to configuration file

    Returns:
        Complete performance analysis

    Raises:
        FileNotFoundError: If config or data files are missing
        ValueError: If configuration is invalid
    """
    config = load_config(config_path)
    project_root = config_path.parent

    records = load_performance_data(config.performance_data, project_root)

    if not records:
        logger.warning("No performance data available for analysis")
        return PerformanceAnalysis(
            budget_alerts=[],
            optimization_opportunities=[],
            cost_performance_tradeoffs=[],
            resource_summary={},
            total_cost=0.0,
            potential_savings=0.0,
            generated_at=datetime.now(),
        )

    records = calculate_resource_costs(records, config.cost)

    budget_alerts = check_budget_status(records, config.budget)
    optimization_opportunities = identify_optimization_opportunities(
        records, config.optimization, config.cost
    )
    cost_performance_tradeoffs = analyze_cost_performance_tradeoffs(
        records, optimization_opportunities, config.cost
    )

    total_cost = sum(r.cost or 0 for r in records)
    potential_savings = sum(
        opp.potential_savings or 0 for opp in optimization_opportunities
    )

    resource_summary = defaultdict(lambda: defaultdict(float))
    for record in records:
        resource_summary[record.resource_type.value][record.resource_name] += (
            record.consumption
        )

    analysis = PerformanceAnalysis(
        budget_alerts=budget_alerts,
        optimization_opportunities=optimization_opportunities,
        cost_performance_tradeoffs=cost_performance_tradeoffs,
        resource_summary={k: dict(v) for k, v in resource_summary.items()},
        total_cost=total_cost,
        potential_savings=potential_savings,
        generated_at=datetime.now(),
    )

    report_path = Path(config.analysis.output_path)
    if not report_path.is_absolute():
        report_path = project_root / report_path

    write_markdown_report(analysis, report_path)

    alerts_output = Path(config.alerts_output_file)
    if not alerts_output.is_absolute():
        alerts_output = project_root / alerts_output

    alerts_output.parent.mkdir(parents=True, exist_ok=True)
    alerts_data = [
        {
            "resource_type": alert.resource_type.value,
            "resource_name": alert.resource_name,
            "current_consumption": alert.current_consumption,
            "budget_limit": alert.budget_limit,
            "utilization_percentage": alert.utilization_percentage,
            "status": alert.status.value,
            "timestamp": alert.timestamp.isoformat(),
        }
        for alert in budget_alerts
    ]

    with open(alerts_output, "w", encoding="utf-8") as f:
        json.dump(alerts_data, f, indent=2)

    logger.info(f"Budget alerts saved to {alerts_output}")

    return analysis


def main() -> None:
    """Main entry point for the performance budget monitor."""
    settings = AppSettings()
    config_path = Path(settings.config_path)

    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent
        config_path = project_root / config_path

    try:
        logger.info("Starting performance budget analysis")
        analysis = process_performance_analysis(config_path)
        logger.info(
            f"Analysis complete. Generated {len(analysis.budget_alerts)} alerts, "
            f"identified {len(analysis.optimization_opportunities)} optimization "
            f"opportunities, and potential savings of ${analysis.potential_savings:,.2f}."
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
