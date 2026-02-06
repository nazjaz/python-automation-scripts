# Warranty Claims Processor

## Project Title and Description

The warranty claims processor automatically processes customer warranty claims by
validating coverage, tracking claim status, coordinating with service providers,
and generating comprehensive warranty analytics.

It is designed for warranty management teams, customer service operations, and
business analysts who need to efficiently process warranty claims, ensure proper
coverage validation, coordinate service delivery, and analyze claim patterns.

## Features

- **Coverage Validation**: Automatically validate warranty coverage including
  active status, expiration dates, and coverage type matching.
- **Claim Status Tracking**: Track claims through workflow stages (submitted,
  validated, approved, in_progress, completed, denied, cancelled).
- **Service Provider Coordination**: Automatically assign service providers based
  on capacity and availability.
- **Auto-Approval**: Automatically approve low-value claims below threshold.
- **Warranty Analytics**: Generate comprehensive analytics including:
  - Claims by status
  - Coverage validation results
  - Service provider performance metrics
  - Monthly claim trends
  - Approval rates and claim amounts
- **Markdown Reporting**: Generate detailed warranty analytics reports.

## Prerequisites

- **Python**: 3.10 or newer.
- **System dependencies**:
  - Ability to create virtual environments.
  - Access to warranty, claim, and service provider data files (CSV or JSON format).

No external services or APIs are required.

## Installation

1. **Clone or copy the project into your automation workspace.**

2. **Create and activate a virtual environment**:

   ```bash
   cd warranty_claims_processor
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

   - Ensure your warranty, claim, and service provider data files are available.
   - Update `config.yaml` to point to your data files.

## Configuration

Configuration is driven primarily by `config.yaml` plus optional environment variables.

- **Environment variables**:
  - `CONFIG_PATH`: Path to configuration file (default: `config.yaml`).

- **Config file (`config.yaml`)**:
  - `warranty_data`: Configuration for warranty data source:
    - `file_path`: Path to warranty data file.
    - `format`: File format (`csv` or `json`).
    - `warranty_id_column`: Column name for warranty ID.
    - `customer_id_column`: Column name for customer ID.
    - `product_id_column`: Column name for product ID.
    - `purchase_date_column`: Column name for purchase date.
    - `warranty_start_date_column`: Column name for warranty start date.
    - `warranty_duration_months_column`: Column name for warranty duration.
    - `coverage_type_column`: Column name for coverage type (optional).
  - `claim_data`: Configuration for claim data source:
    - `file_path`: Path to claim data file.
    - `format`: File format (`csv` or `json`).
    - `claim_id_column`: Column name for claim ID.
    - `warranty_id_column`: Column name for warranty ID.
    - `claim_date_column`: Column name for claim date.
    - `issue_description_column`: Column name for issue description.
    - `status_column`: Column name for claim status (optional).
    - `service_provider_column`: Column name for service provider (optional).
    - `claim_amount_column`: Column name for claim amount (optional).
  - `service_provider`: Service provider configuration:
    - `file_path`: Path to service provider file (optional).
    - `format`: File format (`csv` or `json`).
    - `provider_id_column`: Column name for provider ID.
    - `provider_name_column`: Column name for provider name.
    - `service_areas_column`: Column name for service areas (optional).
    - `capacity_column`: Column name for capacity (optional).
  - `validation`: Validation settings:
    - `require_active_warranty`: Require warranty to be active.
    - `validate_coverage_type`: Validate coverage type matches issue.
    - `auto_approve_threshold`: Auto-approve claims below this amount.
  - `analytics`: Analytics report settings:
    - `output_format`: Report format (`markdown` or `html`).
    - `output_path`: Path for analytics report.

### Example configuration

See the provided `config.yaml` in the project root for a complete example.

## Usage

After configuration, run the processor from the project root:

```bash
source .venv/bin/activate  # if not already active
python -m warranty_claims_processor.src.main
```

This will:

- Load warranty, claim, and service provider data.
- Validate warranty coverage for each claim.
- Update claim statuses based on validation results.
- Assign service providers to approved claims.
- Auto-approve low-value claims.
- Generate warranty analytics.
- Write a markdown report and JSON file with processed claims.

## Project Structure

```
warranty_claims_processor/
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

Tests cover core functionality including coverage validation, claim processing,
and analytics generation.

## Troubleshooting

### Common Issues

**Error: "Warranty data file not found"**
- Ensure the `warranty_data.file_path` in `config.yaml` points to a valid file.
- Check that relative paths are resolved from the project root.

**Error: "Missing required columns"**
- Verify your data files contain the required columns specified in `config.yaml`.
- Check column names match exactly (case-sensitive).

**Claims not being validated**
- Verify warranty data includes matching warranty IDs.
- Check that warranty dates are in correct format.
- Ensure `require_active_warranty` setting matches your requirements.

**Service providers not assigned**
- Verify service provider file exists and is properly formatted.
- Check provider capacity settings if using capacity limits.
- Ensure providers have available capacity.

**Coverage validation failing**
- Review warranty start dates and durations.
- Check that claim dates fall within warranty periods.
- Verify coverage type validation logic if enabled.

## Contributing

1. Follow PEP 8 style guidelines.
2. Add type hints to all functions.
3. Include docstrings for public functions.
4. Write tests for new functionality.
5. Update documentation as needed.

## License

This project is provided as-is for internal use.
