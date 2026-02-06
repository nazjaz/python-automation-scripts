# Feature Usage Monitor

## Project Title and Description

The feature usage monitor analyzes application feature usage data to track adoption
rates, identify unused features, monitor usage trends, and generate actionable
insights for product teams.

It is designed for product managers, data analysts, and engineering teams who need
data-driven insights into how features are being used across their application.

## Features

- **Usage tracking**: Monitor total usage counts and unique user engagement per feature.
- **Adoption rate calculation**: Measure feature adoption percentages and velocity.
- **Unused feature detection**: Identify features with minimal or no usage.
- **Trend analysis**: Detect increasing, decreasing, or stable usage patterns.
- **Insights generation**: Automatically generate actionable recommendations.
- **Markdown reporting**: Generate comprehensive usage reports for stakeholders.

## Prerequisites

- **Python**: 3.10 or newer.
- **System dependencies**:
  - Ability to create virtual environments.
  - Access to feature usage data file (CSV or JSON).

No external services or APIs are required.

## Installation

1. **Clone or copy the project into your automation workspace.**

2. **Create and activate a virtual environment**:

   ```bash
   cd feature_usage_monitor
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

   - Ensure your feature usage data CSV or JSON file is available.
   - Optionally create a features list file if you want to track all features.
   - Update `config.yaml` to point to your data files.

## Configuration

Configuration is driven primarily by `config.yaml` plus optional environment variables.

- **Environment variables**:
  - `CONFIG_PATH`: Path to configuration file (default: `config.yaml`).

- **Config file (`config.yaml`)**:
  - `usage_data`: Configuration for usage data source:
    - `file_path`: Path to usage data file.
    - `format`: File format (`csv` or `json`).
    - `user_id_column`: Column name for user identifiers.
    - `feature_name_column`: Column name for feature names.
    - `timestamp_column`: Column name for event timestamps.
    - `event_type_column`: Optional column for event types.
    - `session_id_column`: Optional column for session identifiers.
  - `features`: Feature definition settings:
    - `features_file`: Optional path to file listing all features.
    - `min_usage_threshold`: Minimum usage count to consider feature active.
    - `adoption_threshold_days`: Days to consider for adoption calculation.
    - `unused_threshold_percentage`: Percentage threshold for unused detection.
  - `analysis`: Analysis parameters:
    - `lookback_days`: Days of historical data to analyze.
    - `analysis_window_days`: Time window for trend analysis.
    - `min_users_for_feature`: Minimum unique users for feature analysis.
  - `report`: Report generation settings:
    - `output_format`: Report format (`markdown` or `html`).
    - `output_path`: Path for output report.
    - `include_top_features`: Number of top features to highlight.

### Example configuration

See the provided `config.yaml` in the project root for a complete example.

## Usage

After configuration, run the analysis from the project root:

```bash
source .venv/bin/activate  # if not already active
python -m feature_usage_monitor.src.main
```

This will:

- Load feature usage data from the configured file.
- Analyze usage statistics for each feature.
- Calculate adoption rates and metrics.
- Identify unused or rarely used features.
- Generate actionable insights.
- Write a markdown report to the configured output path.

## Project Structure

```
feature_usage_monitor/
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

Tests cover core functionality including usage analysis, adoption rate calculation,
and unused feature detection.

## Troubleshooting

### Common Issues

**Error: "Usage data file not found"**
- Ensure the `usage_data.file_path` in `config.yaml` points to a valid file.
- Check that relative paths are resolved from the project root.

**Error: "Missing required columns"**
- Verify your data file contains the required columns specified in `config.yaml`.
- Check column names match exactly (case-sensitive).

**No features detected**
- Ensure `feature_name_column` values are populated in your data.
- Check that timestamps are in a parseable format.

**Low adoption rates**
- Review `adoption_threshold_days` setting.
- Verify user_id values are consistent across records.

## Contributing

1. Follow PEP 8 style guidelines.
2. Add type hints to all functions.
3. Include docstrings for public functions.
4. Write tests for new functionality.
5. Update documentation as needed.

## License

This project is provided as-is for internal use.
