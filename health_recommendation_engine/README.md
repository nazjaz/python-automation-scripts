# Health Recommendation Engine

## Project Title and Description

The health recommendation engine analyzes activity data, sleep patterns, and health
metrics to generate personalized health recommendations, manage goals, and track
progress over time.

It is designed for individuals, health coaches, and wellness programs that need
data-driven insights to improve health outcomes through personalized recommendations
and goal tracking.

## Features

- **Activity Analysis**: Analyze steps, calories, active minutes, and distance data.
- **Sleep Pattern Analysis**: Evaluate sleep duration, quality, and consistency.
- **Health Metrics Tracking**: Monitor weight, heart rate, and blood pressure trends.
- **Personalized Recommendations**: Generate actionable health recommendations based on
  individual data patterns.
- **Goal Setting**: Define and track health goals with progress monitoring.
- **Progress Tracking**: Automatically update goal progress based on current metrics.
- **Markdown Reporting**: Generate comprehensive health reports with insights.

## Prerequisites

- **Python**: 3.10 or newer.
- **System dependencies**:
  - Ability to create virtual environments.
  - Access to health data files (CSV or JSON format).

No external services or APIs are required.

## Installation

1. **Clone or copy the project into your automation workspace.**

2. **Create and activate a virtual environment**:

   ```bash
   cd health_recommendation_engine
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

   - Ensure your activity, sleep, and health metrics data files are available.
   - Optionally create a goals file if you want to track specific health goals.
   - Update `config.yaml` to point to your data files.

## Configuration

Configuration is driven primarily by `config.yaml` plus optional environment variables.

- **Environment variables**:
  - `CONFIG_PATH`: Path to configuration file (default: `config.yaml`).

- **Config file (`config.yaml`)**:
  - `activity_data`: Configuration for activity data source:
    - `file_path`: Path to activity data file.
    - `format`: File format (`csv` or `json`).
    - `date_column`: Column name for date.
    - `steps_column`: Column name for steps (optional).
    - `calories_column`: Column name for calories (optional).
    - `active_minutes_column`: Column name for active minutes (optional).
    - `distance_column`: Column name for distance (optional).
  - `sleep_data`: Configuration for sleep data source:
    - `file_path`: Path to sleep data file.
    - `format`: File format (`csv` or `json`).
    - `date_column`: Column name for date.
    - `sleep_hours_column`: Column name for sleep hours.
    - `sleep_quality_column`: Column name for sleep quality (optional).
    - `bedtime_column`: Column name for bedtime (optional).
    - `wake_time_column`: Column name for wake time (optional).
  - `health_metrics`: Configuration for health metrics data source:
    - `file_path`: Path to health metrics file.
    - `format`: File format (`csv` or `json`).
    - `date_column`: Column name for date.
    - `weight_column`: Column name for weight (optional).
    - `heart_rate_column`: Column name for heart rate (optional).
    - `blood_pressure_column`: Column name for blood pressure (optional).
  - `recommendation`: Recommendation settings:
    - `target_steps_per_day`: Target steps per day.
    - `target_sleep_hours`: Target sleep hours per night.
    - `min_sleep_hours`: Minimum recommended sleep hours.
    - `max_sleep_hours`: Maximum recommended sleep hours.
    - `target_active_minutes`: Target active minutes per day.
  - `goal`: Goal management settings:
    - `goals_file`: Path to goals file (optional).
    - `progress_file`: Path to progress tracking file.

### Example configuration

See the provided `config.yaml` in the project root for a complete example.

## Usage

After configuration, run the analysis from the project root:

```bash
source .venv/bin/activate  # if not already active
python -m health_recommendation_engine.src.main
```

This will:

- Load activity, sleep, and health metrics data.
- Analyze patterns and calculate summary statistics.
- Generate personalized recommendations.
- Update goal progress if goals are configured.
- Write a markdown report and JSON recommendations file.

## Project Structure

```
health_recommendation_engine/
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

Tests cover core functionality including data loading, analysis, and recommendation
generation.

## Troubleshooting

### Common Issues

**Error: "Activity data file not found"**
- Ensure the `activity_data.file_path` in `config.yaml` points to a valid file.
- Check that relative paths are resolved from the project root.

**Error: "Missing required columns"**
- Verify your data files contain the required columns specified in `config.yaml`.
- Check column names match exactly (case-sensitive).

**No recommendations generated**
- Ensure data files contain sufficient historical data.
- Check that values are within expected ranges.

**Goal progress not updating**
- Verify goals file format matches expected structure.
- Ensure goal categories match data categories (Activity, Sleep).

## Contributing

1. Follow PEP 8 style guidelines.
2. Add type hints to all functions.
3. Include docstrings for public functions.
4. Write tests for new functionality.
5. Update documentation as needed.

## License

This project is provided as-is for internal use.
