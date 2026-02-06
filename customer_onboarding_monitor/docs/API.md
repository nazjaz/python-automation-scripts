# Customer Onboarding Monitoring API

## Module `src.main`

### `analyze_onboarding(config_path: Path) -> AnalysisResult`

Run the full onboarding analysis pipeline:

- Load configuration from the provided `config_path`.
- Read onboarding events from the configured CSV.
- Compute stage metrics and time-to-value.
- Generate optimization recommendations.
- Persist a markdown summary to `config.output_path`.

Returns an `AnalysisResult` containing computed metrics and recommendations.

### `compute_stage_metrics(df: pd.DataFrame, config: Config) -> List[StageMetrics]`

Compute per stage metrics using the raw events data frame and configuration.
Metrics include:

- Number of customers entering the stage.
- Completion rate for the stage.
- Median time to move from the previous stage to the current stage.

### `compute_time_to_value(df: pd.DataFrame, config: Config) -> Optional[float]`

Compute the average time-to-value in hours using:

- First event for each customer.
- First occurrence of the configured `time_to_value_event`.

Returns `None` if there is insufficient data.

### `generate_recommendations(stage_metrics: List[StageMetrics], config: Config, average_ttv_hours: Optional[float]) -> List[str]`

Generate ordered human readable recommendations based on:

- Underperforming completion rates relative to targets.
- Stages with median completion time above target.
- Overall time-to-value performance.

### Data Models

- `Config`: Application configuration parsed from YAML.
- `StageConfig`: Definition of a single onboarding stage and performance
  targets.
- `StageMetrics`: Computed metrics per stage.
- `AnalysisResult`: Aggregated result including all metrics and
  recommendations.
