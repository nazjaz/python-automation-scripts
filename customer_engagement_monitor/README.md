# Customer Engagement Monitor

## Project Title and Description

The customer engagement monitor analyzes customer engagement across all touchpoints,
calculates lifetime value (LTV), identifies high-value customer segments, and
generates personalized engagement strategy recommendations.

It is designed for marketing teams, customer success managers, and business analysts
who need data-driven insights into customer engagement patterns, value segmentation,
and actionable strategies for improving customer relationships.

## Features

- **Multi-Touchpoint Monitoring**: Track engagement across email, web, mobile,
  social, support, purchase, and review touchpoints.
- **Lifetime Value Calculation**: Calculate customer LTV using revenue, frequency,
  and discount rate.
- **Customer Segmentation**: Automatically segment customers into tiers:
  - Champion: High LTV and high engagement
  - Loyal: High LTV or high engagement
  - Potential: Medium value with growth opportunity
  - At Risk: Low recent engagement
  - Lost: No engagement for extended period
- **Engagement Scoring**: Calculate normalized engagement scores based on
  touchpoint types and frequencies.
- **Strategy Recommendations**: Generate personalized engagement strategies for
  each segment.
- **Markdown Reporting**: Generate comprehensive engagement analysis reports.

## Prerequisites

- **Python**: 3.10 or newer.
- **System dependencies**:
  - Ability to create virtual environments.
  - Access to engagement and purchase data files (CSV or JSON format).

No external services or APIs are required.

## Installation

1. **Clone or copy the project into your automation workspace.**

2. **Create and activate a virtual environment**:

   ```bash
   cd customer_engagement_monitor
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

   - Ensure your engagement and purchase data CSV or JSON files are available.
   - Update `config.yaml` to point to your data files.

## Configuration

Configuration is driven primarily by `config.yaml` plus optional environment variables.

- **Environment variables**:
  - `CONFIG_PATH`: Path to configuration file (default: `config.yaml`).

- **Config file (`config.yaml`)**:
  - `engagement_data`: Configuration for engagement data source:
    - `file_path`: Path to engagement data file.
    - `format`: File format (`csv` or `json`).
    - `customer_id_column`: Column name for customer ID.
    - `touchpoint_column`: Column name for touchpoint type.
    - `timestamp_column`: Column name for timestamp.
    - `engagement_score_column`: Column name for engagement score (optional).
  - `purchase_data`: Configuration for purchase data source:
    - `file_path`: Path to purchase data file.
    - `format`: File format (`csv` or `json`).
    - `customer_id_column`: Column name for customer ID.
    - `purchase_date_column`: Column name for purchase date.
    - `amount_column`: Column name for purchase amount.
  - `ltv`: LTV calculation settings:
    - `discount_rate`: Discount rate for LTV calculation.
    - `average_customer_lifespan_years`: Average customer lifespan.
    - `lookback_months`: Months to look back for revenue calculation.
  - `segmentation`: Segmentation settings:
    - `ltv_threshold_high`: High LTV threshold.
    - `ltv_threshold_medium`: Medium LTV threshold.
    - `engagement_threshold_high`: High engagement threshold.
    - `engagement_threshold_low`: Low engagement threshold.
    - `recency_threshold_days`: Days for recency threshold.
  - `strategy`: Strategy generation settings:
    - `max_recommendations_per_segment`: Maximum recommendations per segment.

### Example configuration

See the provided `config.yaml` in the project root for a complete example.

## Usage

After configuration, run the monitor from the project root:

```bash
source .venv/bin/activate  # if not already active
python -m customer_engagement_monitor.src.main
```

This will:

- Load engagement and purchase data from configured files.
- Calculate lifetime value for each customer.
- Calculate engagement scores across touchpoints.
- Segment customers into tiers.
- Generate engagement strategies for each segment.
- Write a markdown report and JSON analysis file.

## Project Structure

```
customer_engagement_monitor/
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

Tests cover core functionality including LTV calculation, engagement scoring,
segmentation, and strategy generation.

## Troubleshooting

### Common Issues

**Error: "Engagement data file not found"**
- Ensure the `engagement_data.file_path` in `config.yaml` points to a valid file.
- Check that relative paths are resolved from the project root.

**Error: "Missing required columns"**
- Verify your data files contain the required columns specified in `config.yaml`.
- Check column names match exactly (case-sensitive).

**LTV calculations seem incorrect**
- Review `lookback_months` setting - may need adjustment for your data.
- Check that purchase amounts are in consistent currency units.
- Verify `average_customer_lifespan_years` matches your business model.

**All customers in same segment**
- Adjust segmentation thresholds in `config.yaml`.
- Review LTV and engagement score distributions.
- Check that data spans sufficient time period.

**No engagement strategies generated**
- Verify segment analysis completed successfully.
- Check that customers were assigned to segments.
- Review strategy generation logic.

## Contributing

1. Follow PEP 8 style guidelines.
2. Add type hints to all functions.
3. Include docstrings for public functions.
4. Write tests for new functionality.
5. Update documentation as needed.

## License

This project is provided as-is for internal use.
