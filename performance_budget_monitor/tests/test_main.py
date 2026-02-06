"""Tests for performance budget monitoring."""

from datetime import datetime, timedelta

import pytest

from performance_budget_monitor.src.main import (
    BudgetConfig,
    BudgetStatus,
    CostConfig,
    OptimizationConfig,
    OptimizationPriority,
    PerformanceRecord,
    ResourceType,
    check_budget_status,
    identify_optimization_opportunities,
)


def test_check_budget_status_within_budget():
    """Test budget status check for resources within budget."""
    records = [
        PerformanceRecord(
            timestamp=datetime.now(),
            resource_type=ResourceType.CPU,
            resource_name="server_001",
            consumption=50.0,
        ),
        PerformanceRecord(
            timestamp=datetime.now(),
            resource_type=ResourceType.CPU,
            resource_name="server_001",
            consumption=60.0,
        ),
    ]

    budget_config = BudgetConfig(
        budgets={"cpu": {"server_001": 80.0}},
        warning_threshold=0.8,
        critical_threshold=0.95,
    )

    alerts = check_budget_status(records, budget_config)

    assert len(alerts) == 0


def test_check_budget_status_approaching_limit():
    """Test budget status check for resources approaching limit."""
    records = [
        PerformanceRecord(
            timestamp=datetime.now(),
            resource_type=ResourceType.CPU,
            resource_name="server_001",
            consumption=70.0,
        ),
    ]

    budget_config = BudgetConfig(
        budgets={"cpu": {"server_001": 80.0}},
        warning_threshold=0.8,
        critical_threshold=0.95,
    )

    alerts = check_budget_status(records, budget_config)

    assert len(alerts) > 0
    assert alerts[0].status == BudgetStatus.APPROACHING_LIMIT
    assert alerts[0].utilization_percentage >= 80.0


def test_check_budget_status_exceeded():
    """Test budget status check for exceeded budgets."""
    records = [
        PerformanceRecord(
            timestamp=datetime.now(),
            resource_type=ResourceType.MEMORY,
            resource_name="server_001",
            consumption=70.0,
        ),
    ]

    budget_config = BudgetConfig(
        budgets={"memory": {"server_001": 64.0}},
        warning_threshold=0.8,
        critical_threshold=0.95,
    )

    alerts = check_budget_status(records, budget_config)

    assert len(alerts) > 0
    assert alerts[0].status == BudgetStatus.EXCEEDED


def test_check_budget_status_critical():
    """Test budget status check for critical thresholds."""
    records = [
        PerformanceRecord(
            timestamp=datetime.now(),
            resource_type=ResourceType.CPU,
            resource_name="server_001",
            consumption=78.0,
        ),
    ]

    budget_config = BudgetConfig(
        budgets={"cpu": {"server_001": 80.0}},
        warning_threshold=0.8,
        critical_threshold=0.95,
    )

    alerts = check_budget_status(records, budget_config)

    assert len(alerts) > 0
    assert alerts[0].status == BudgetStatus.CRITICAL


def test_identify_optimization_opportunities():
    """Test optimization opportunity identification."""
    now = datetime.now()
    baseline_date = now - timedelta(days=60)
    recent_date = now - timedelta(days=5)

    records = []
    for i in range(15):
        records.append(
            PerformanceRecord(
                timestamp=baseline_date + timedelta(days=i),
                resource_type=ResourceType.CPU,
                resource_name="server_001",
                consumption=50.0,
            )
        )

    for i in range(15):
        records.append(
            PerformanceRecord(
                timestamp=recent_date + timedelta(days=i),
                resource_type=ResourceType.CPU,
                resource_name="server_001",
                consumption=75.0,
            )
        )

    optimization_config = OptimizationConfig(
        consumption_increase_threshold=0.2,
        min_data_points=10,
        lookback_days=30,
    )

    cost_config = CostConfig()

    opportunities = identify_optimization_opportunities(
        records, optimization_config, cost_config
    )

    assert len(opportunities) > 0
    assert opportunities[0].increase_percentage > 0
    assert opportunities[0].resource_name == "server_001"


def test_identify_optimization_opportunities_priority():
    """Test optimization opportunity priority assignment."""
    now = datetime.now()
    baseline_date = now - timedelta(days=60)
    recent_date = now - timedelta(days=5)

    records = []
    for i in range(15):
        records.append(
            PerformanceRecord(
                timestamp=baseline_date + timedelta(days=i),
                resource_type=ResourceType.MEMORY,
                resource_name="server_002",
                consumption=30.0,
            )
        )

    for i in range(15):
        records.append(
            PerformanceRecord(
                timestamp=recent_date + timedelta(days=i),
                resource_type=ResourceType.MEMORY,
                resource_name="server_002",
                consumption=60.0,
            )
        )

    optimization_config = OptimizationConfig(
        consumption_increase_threshold=0.2,
        min_data_points=10,
        lookback_days=30,
    )

    cost_config = CostConfig()

    opportunities = identify_optimization_opportunities(
        records, optimization_config, cost_config
    )

    assert len(opportunities) > 0
    high_priority = [
        opp for opp in opportunities if opp.priority == OptimizationPriority.HIGH
    ]
    assert len(high_priority) > 0


def test_identify_optimization_opportunities_insufficient_data():
    """Test optimization detection with insufficient data."""
    records = [
        PerformanceRecord(
            timestamp=datetime.now(),
            resource_type=ResourceType.CPU,
            resource_name="server_001",
            consumption=50.0,
        )
    ] * 5

    optimization_config = OptimizationConfig(
        consumption_increase_threshold=0.2,
        min_data_points=10,
        lookback_days=30,
    )

    cost_config = CostConfig()

    opportunities = identify_optimization_opportunities(
        records, optimization_config, cost_config
    )

    assert len(opportunities) == 0


def test_budget_status_calculation():
    """Test budget utilization percentage calculation."""
    records = [
        PerformanceRecord(
            timestamp=datetime.now(),
            resource_type=ResourceType.STORAGE,
            resource_name="database_001",
            consumption=800.0,
        ),
    ]

    budget_config = BudgetConfig(
        budgets={"storage": {"database_001": 1000.0}},
        warning_threshold=0.8,
        critical_threshold=0.95,
    )

    alerts = check_budget_status(records, budget_config)

    assert len(alerts) > 0
    assert alerts[0].utilization_percentage == pytest.approx(80.0, abs=0.1)
