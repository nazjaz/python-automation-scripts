# Deployment Monitor

## Project Title and Description

The deployment monitor analyzes application deployment data to track deployment
frequency, monitor success rates, identify regression patterns, and generate
comprehensive release quality metrics.

It is designed for DevOps teams, release managers, and engineering leaders who need
data-driven insights into deployment health, quality trends, and early warning
signals for deployment regressions.

## Features

- **Deployment Frequency Tracking**: Calculate average deployments per day over
  configurable time windows.
- **Success Rate Monitoring**: Track deployment success rates and identify trends.
- **Regression Detection**: Automatically identify regression patterns by comparing
  recent performance to historical baselines.
- **Quality Metrics**: Calculate key DevOps metrics including:
  - Deployment frequency
  - Success rate
  - Change failure rate
  - Mean Time To Recovery (MTTR)
- **Environment Breakdown**: Analyze deployment patterns by environment.
- **Version Analysis**: Track success rates by version.
- **Markdown Reporting**: Generate comprehensive deployment metrics reports.

## Prerequisites

- **Python**: 3.10 or newer.
- **System dependencies**:
  - Ability to create virtual environments.
  - Access to deployment data files (CSV or JSON format).

No external services or APIs are required.

## Installation

1. **Clone or copy the project into your automation workspace.**

2. **Create and activate a virtual environment**:

   ```bash
   cd deployment_monitor
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

   - Ensure your deployment data CSV or JSON file is available.
   - Update `config.yaml` to point to your data file.

## Configuration

Configuration is driven primarily by `config.yaml` plus optional environment variables.

- **Environment variables**:
  - `CONFIG_PATH`: Path to configuration file (default: `config.yaml`).

- **Config file (`config.yaml`)**:
  - `deployment_data`: Configuration for deployment data source:
    - `file_path`: Path to deployment data file.
    - `format`: File format (`csv` or `json`).
    - `deployment_id_column`: Column name for deployment ID.
    - `timestamp_column`: Column name for deployment timestamp.
    - `status_column`: Column name for deployment status.
    - `environment_column`: Column name for environment (optional).
    - `version_column`: Column name for version (optional).
    - `duration_column`: Column name for deployment duration (optional).
    - `error_message_column`: Column name for error message (optional).
  - `regression`: Regression detection settings:
    - `lookback_window_days`: Days to look back for baseline comparison.
    - `comparison_window_days`: Days in recent window for comparison.
    - `success_rate_threshold`: Success rate drop threshold for regression.
    - `failure_rate_threshold`: Failure rate threshold for critical regression.
  - `metrics`: Quality metrics settings:
    - `mttr_window_days`: Days to calculate MTTR over.
    - `deployment_frequency_window_days`: Days to calculate deployment frequency over.
    - `change_failure_rate_window_days`: Days to calculate change failure rate over.
  - `report`: Report generation settings:
    - `output_format`: Report format (`markdown` or `html`).
    - `output_path`: Path for metrics report.

### Example configuration

See the provided `config.yaml` in the project root for a complete example.

## Usage

After configuration, run the monitor from the project root:

```bash
source .venv/bin/activate  # if not already active
python -m deployment_monitor.src.main
```

This will:

- Load deployment data from the configured file.
- Calculate deployment frequency and success rates.
- Identify regression patterns.
- Generate quality metrics (MTTR, change failure rate, etc.).
- Analyze deployments by environment and version.
- Write a markdown report with all metrics.

## Project Structure

```
deployment_monitor/
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

Tests cover core functionality including metrics calculation, regression detection,
and data loading.

## Troubleshooting

### Common Issues

**Error: "Deployment data file not found"**
- Ensure the `deployment_data.file_path` in `config.yaml` points to a valid file.
- Check that relative paths are resolved from the project root.

**Error: "Missing required columns"**
- Verify your deployment data file contains the required columns specified in `config.yaml`.
- Check column names match exactly (case-sensitive).

**No regression patterns detected**
- Review `success_rate_threshold` and `failure_rate_threshold` settings.
- Ensure sufficient historical data for baseline comparison.
- Check that `lookback_window_days` and `comparison_window_days` are appropriate.

**MTTR not calculated**
- MTTR requires at least 2 failed deployments with successful recoveries.
- Ensure `mttr_window_days` covers sufficient historical data.
- Verify deployment timestamps are accurate.

**Low deployment frequency**
- Check that `deployment_frequency_window_days` is appropriate for your deployment cadence.
- Verify deployment data includes recent deployments.

## Contributing

1. Follow PEP 8 style guidelines.
2. Add type hints to all functions.
3. Include docstrings for public functions.
4. Write tests for new functionality.
5. Update documentation as needed.

## License

This project is provided as-is for internal use.
