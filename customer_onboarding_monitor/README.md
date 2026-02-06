# Customer Onboarding Monitoring Tool

## Project Title and Description

The customer onboarding monitoring tool analyzes onboarding funnel data from a
CSV file to quantify completion rates, identify bottlenecks, track
time-to-value, and generate concrete optimization recommendations.

It is intended for product, growth, and operations teams that want a repeatable,
data driven view of how customers progress through onboarding.

## Features

- **Funnel analysis**: Calculate how many customers reach each onboarding stage.
- **Completion rates**: Measure completion rate per stage against configured targets.
- **Bottleneck detection**: Highlight stages with low completion or long dwell time.
- **Time-to-value tracking**: Compute average time between first onboarding touch
  and a configurable value-realization event.
- **Markdown reporting**: Generate a human readable summary report with metrics
  and recommendations.
- **Config driven**: All behavior controlled through `config.yaml` and
  environment variables.

## Prerequisites

- **Python**: 3.10 or newer.
- **System dependencies**:
  - Ability to create virtual environments.
  - Access to the onboarding CSV data file.

No external services or APIs are required.

## Installation

1. **Clone or copy the project into your automation workspace.**

2. **Create and activate a virtual environment**:

   ```bash
   cd customer_onboarding_monitor
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:

   - Copy `.env.example` to `.env`.
   - Adjust values to match your environment.

5. **Prepare data file**:

   - Ensure your onboarding events CSV is available.
   - Update `config.yaml:data_path` to point to the file.

## Configuration

Configuration is driven primarily by `config.yaml` plus optional environment
variables.

- **Environment variables**:
  - `LOG_LEVEL`: Application log level (for example, `INFO`, `DEBUG`).

- **Config file (`config.yaml`)**:
  - `data_path`: Path to onboarding events CSV (relative paths are resolved
    from the project root).
  - `output_path`: Path to the generated markdown report.
  - `customer_id_column`: Column containing unique customer identifiers.
  - `event_time_column`: Column containing event timestamps.
  - `stage_column`: Column representing onboarding stage or event type.
  - `time_to_value_event`: Event name indicating value realization.
  - `stages`: Ordered list of stage definitions:
    - `name`: Internal stage identifier (must match values in `stage_column`).
    - `display_name`: Human readable label.
    - `target_completion_rate`: Desired minimum completion rate (0.0 to 1.0).
    - `target_time_to_complete_hours`: Desired maximum time from previous
      stage to this stage.

### Example configuration

See the provided `config.yaml` in the project root for a complete example.

## Usage

After configuration, run the analysis from the project root:

```bash
source .venv/bin/activate  # if not already active
python -m customer_onboarding_monitor.src.main
```

This will:

- Load onboarding events from the configured CSV.
- Compute stage level metrics and time-to-value.
- Write a markdown report to the configured `output_path`.

You can also import the analysis functions in other Python code:

```python
from pathlib import Path
from customer_onboarding_monitor.src.main import analyze_onboarding

result = analyze_onboarding(Path("config.yaml"))
print(result.recommendations)
```

## Project Structure

High level layout:

- `README.md`: Project documentation.
- `requirements.txt`: Pinned Python dependencies.
- `config.yaml`: Application configuration.
- `.gitignore`: Standard Python ignore rules and logs.
- `src/main.py`: Core analytics and CLI entry point.
- `tests/test_main.py`: Unit tests for analytics functions.
- `docs/API.md`: API level documentation.
- `logs/`: Directory for generated log files and reports.

## Testing

Run tests from the project root with the virtual environment active:

```bash
pytest
```

Tests focus on:

- Stage metric calculation.
- Time-to-value computation.
- Recommendation generation.

## Troubleshooting

- **File not found errors**:
  - Verify `data_path` and `output_path` in `config.yaml`.
  - Confirm paths are relative to the project root or use absolute paths.

- **Missing columns**:
  - Ensure the CSV contains `customer_id_column`, `event_time_column`, and
    `stage_column` as configured.

- **Unexpected metrics**:
  - Confirm stages in `config.yaml` match values present in the CSV.
  - Check timestamp formatting and time zones in the input data.

## Contributing

- Follow PEP 8 and project standards described in `instruction.md`.
- Use type hints and docstrings for all public functions and classes.
- Write or update tests for any changes to analytics logic.
- Use conventional commit messages (for example,
  `feat(onboarding-monitor): add advanced bottleneck report`).

## License

Specify the license applicable to this project here.
