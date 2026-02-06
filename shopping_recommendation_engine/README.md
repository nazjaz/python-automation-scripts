# Shopping Recommendation Engine

## Project Title and Description

The shopping recommendation engine automatically generates personalized shopping
recommendations by analyzing purchase history, browsing behavior, and seasonal
trends with inventory availability checking.

It is designed for e-commerce platforms, retail analytics teams, and marketing
professionals who need to provide personalized product recommendations to customers
based on their behavior patterns and current inventory availability.

## Features

- **Purchase History Analysis**: Analyze customer purchase patterns with recency
  and frequency weighting.
- **Browsing Behavior Analysis**: Track product views, cart additions, wishlist
  items, and view duration.
- **Seasonal Trend Detection**: Identify products with seasonal purchase patterns
  and boost recommendations accordingly.
- **Inventory Availability Checking**: Verify product availability before
  recommending.
- **Personalized Scoring**: Combine multiple signals with configurable weights.
- **Priority Classification**: Categorize recommendations by priority (high,
  medium, low).
- **Markdown Reporting**: Generate comprehensive recommendation reports.

## Prerequisites

- **Python**: 3.10 or newer.
- **System dependencies**:
  - Ability to create virtual environments.
  - Access to purchase history, browsing behavior, and inventory data files
    (CSV or JSON format).

No external services or APIs are required.

## Installation

1. **Clone or copy the project into your automation workspace.**

2. **Create and activate a virtual environment**:

   ```bash
   cd shopping_recommendation_engine
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

   - Ensure your purchase history, browsing behavior, and inventory data files
     are available.
   - Update `config.yaml` to point to your data files.

## Configuration

Configuration is driven primarily by `config.yaml` plus optional environment variables.

- **Environment variables**:
  - `CONFIG_PATH`: Path to configuration file (default: `config.yaml`).

- **Config file (`config.yaml`)**:
  - `purchase_history`: Configuration for purchase history data source.
  - `browsing_behavior`: Configuration for browsing behavior data source.
  - `inventory`: Configuration for inventory data source.
  - `seasonal`: Seasonal trends settings:
    - `enable_seasonal_boost`: Enable seasonal trend boosting.
    - `seasonal_categories`: Mapping of seasons to month numbers.
    - `seasonal_boost_multiplier`: Multiplier for seasonal products.
  - `recommendation`: Recommendation generation settings:
    - `max_recommendations`: Maximum number of recommendations.
    - `min_score_threshold`: Minimum recommendation score.
    - `purchase_history_weight`: Weight for purchase history.
    - `browsing_weight`: Weight for browsing behavior.
    - `seasonal_weight`: Weight for seasonal trends.
    - `require_in_stock`: Only recommend in-stock items.

### Example configuration

See the provided `config.yaml` in the project root for a complete example.

## Usage

After configuration, run the recommendation engine from the project root:

```bash
source .venv/bin/activate  # if not already active
python -m shopping_recommendation_engine.src.main CUSTOMER_ID
```

Replace `CUSTOMER_ID` with the actual customer identifier.

This will:

- Load purchase history, browsing behavior, and inventory data.
- Analyze customer purchase patterns and browsing behavior.
- Identify seasonal product trends.
- Check inventory availability.
- Generate personalized recommendations.
- Write a markdown report and JSON recommendations file.

## Project Structure

```
shopping_recommendation_engine/
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

Tests cover core functionality including purchase analysis, browsing analysis,
seasonal detection, and recommendation generation.

## Troubleshooting

### Common Issues

**Error: "Purchase history file not found"**
- Ensure the `purchase_history.file_path` in `config.yaml` points to a valid file.
- Check that relative paths are resolved from the project root.

**Error: "Missing required columns"**
- Verify your data files contain the required columns specified in `config.yaml`.
- Check column names match exactly (case-sensitive).

**No recommendations generated**
- Check that customer has purchase history or browsing behavior data.
- Verify `min_score_threshold` is not too high.
- Ensure inventory data is available if `require_in_stock` is enabled.

**Seasonal products not detected**
- Verify sufficient historical purchase data across seasons.
- Check `seasonal_categories` configuration matches your data.
- Ensure `enable_seasonal_boost` is set to true.

**Inventory checking not working**
- Verify inventory file contains product IDs matching recommendation candidates.
- Check that `in_stock_column` or quantity-based logic is configured correctly.

## Contributing

1. Follow PEP 8 style guidelines.
2. Add type hints to all functions.
3. Include docstrings for public functions.
4. Write tests for new functionality.
5. Update documentation as needed.

## License

This project is provided as-is for internal use.
