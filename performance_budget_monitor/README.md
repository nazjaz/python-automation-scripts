# Performance Budget Monitor

## Project Title and Description

The performance budget monitor tracks application performance budgets, monitors
resource consumption, identifies optimization opportunities, and generates
cost-performance trade-off analyses.

It is designed for DevOps teams, infrastructure managers, and cost optimization
specialists who need to monitor resource usage against budgets, identify
performance degradation, and make data-driven decisions about cost and performance
trade-offs.

## Features

- **Performance Budget Monitoring**: Track resource consumption against defined
  budgets with configurable warning and critical thresholds.
- **Resource Consumption Tracking**: Monitor CPU, memory, storage, network,
  database, and API call consumption.
- **Budget Alerts**: Generate alerts when resources approach or exceed budget
  limits.
- **Optimization Opportunity Detection**: Identify resources with increasing
  consumption trends that may benefit from optimization.
- **Cost-Performance Trade-off Analysis**: Calculate ROI and performance impact
  for optimization opportunities.
- **Cost Calculation**: Automatically calculate costs based on consumption and
  unit costs.
- **Trend Analysis**: Compare recent consumption to historical baselines.
- **Markdown Reporting**: Generate comprehensive performance analysis reports.

## Prerequisites

- **Python**: 3.10 or newer.
- **System dependencies**:
  - Ability to create virtual environments.
  - Access to performance data files (CSV or JSON format).

No external services or APIs are required.

## Installation

1. **Clone or copy the project into your automation workspace.**

2. **Create and activate a virtual environment**:

   ```bash
   cd performance_budget_monitor
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:

   - Copy `.env.example` to `.env`.
   - Adjust values to match your environment.

5. **Prepare data files**:

   - Ensure your performance data CSV or JSON file is available.
   - Update `config.yaml` to define performance budgets and cost per unit.
   - Configure resource types and names in budget settings.

## Configuration

Configuration is driven primarily by `config.yaml` plus optional environment variables.

- **Environment variables**:
  - `CONFIG_PATH`: Path to configuration file (default: `config.yaml`).

- **Config file (`config.yaml`)**:
  - `performance_data`: Configuration for performance data source:
    - `file_path`: Path to performance data file.
    - `format`: File format (`csv` or `json`).
    - `timestamp_column`: Column name for timestamp.
    - `resource_type_column`: Column name for resource type.
    - `resource_name_column`: Column name for resource name.
    - `consumption_column`: Column name for consumption value.
    - `unit_column`: Column name for unit (optional).
    - `cost_column`: Column name for cost (optional).
  - `budget`: Budget configuration:
    - `budgets`: Dictionary of budget limits by resource type and name.
    - `warning_threshold`: Warning threshold as percentage of budget.
    - `critical_threshold`: Critical threshold as percentage of budget.
  - `cost`: Cost calculation settings:
    - `cost_per_unit`: Dictionary of cost per unit by resource type and unit.
    - `optimization_cost_threshold`: Minimum cost savings for optimization.
  - `optimization`: Optimization detection settings:
    - `consumption_increase_threshold`: Percentage increase to flag as opportunity.
    - `min_data_points`: Minimum data points for trend analysis.
    - `lookback_days`: Days to look back for trend analysis.
  - `analysis`: Analysis report settings:
    - `output_format`: Report format (`markdown` or `html`).
    - `output_path`: Path for analysis report.

### Example configuration

See the provided `config.yaml` in the project root for a complete example.

## Usage

After configuration, run the monitor from the project root:

```bash
source .venv/bin/activate  # if not already active
python -m performance_budget_monitor.src.main
```

This will:

- Load performance data from the configured file.
- Calculate resource costs if not provided.
- Check budget status and generate alerts.
- Identify optimization opportunities.
- Generate cost-performance trade-off analyses.
- Write a markdown report and JSON alerts file.

## Project Structure

```
performance_budget_monitor/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Environment variable template
├── .gitignore               # Git ignore rules
├── src/
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation
└── logs/
    └── .gitkeep            # Placeholder for logs directory
```

## Testing

Run tests using pytest:

```bash
pytest tests/
```

Tests cover core functionality including budget checking, optimization detection,
and cost calculation.

## Troubleshooting

### Common Issues

**Error: "Performance data file not found"**
- Ensure the `performance_data.file_path` in `config.yaml` points to a valid file.
- Check that relative paths are resolved from the project root.

**Error: "Missing required columns"**
- Verify your performance data file contains the required columns specified in `config.yaml`.
- Check column names match exactly (case-sensitive).

**No budget alerts generated**
- Verify budgets are configured in `config.yaml` for your resources.
- Check that resource types and names match between data and budget configuration.
- Ensure consumption values are within expected ranges.

**No optimization opportunities identified**
- Review `consumption_increase_threshold` setting.
- Ensure sufficient historical data (check `lookback_days` and `min_data_points`).
- Verify data spans sufficient time period for trend analysis.

**Cost calculations incorrect**
- Verify `cost_per_unit` configuration matches your resource types and units.
- Check that unit values in data match unit keys in cost configuration.
- Ensure cost values are in consistent currency units.

## Contributing

1. Follow PEP 8 style guidelines.
2. Add type hints to all functions.
3. Include docstrings for public functions.
4. Write tests for new functionality.
5. Update documentation as needed.

## License

This project is provided as-is for internal use.
