# Testimonial Processor

## Project Title and Description

The testimonial processor automatically processes customer testimonials by extracting
quotes, categorizing by product or service, and generating marketing materials with
permission tracking.

It is designed for marketing teams, content creators, and product managers who need
to efficiently process customer feedback, extract usable quotes, and generate
marketing-ready materials while maintaining proper permission tracking.

## Features

- **Quote Extraction**: Automatically extract meaningful quotes from testimonial text.
- **Categorization**: Categorize testimonials by product or service using keyword
  matching.
- **Marketing Material Generation**: Generate markdown and HTML marketing materials.
- **Permission Tracking**: Track permission status for each testimonial to ensure
  compliance.
- **Multiple Output Formats**: Support for markdown and HTML output formats.
- **Configurable Extraction**: Customizable quote length limits and extraction rules.
- **Rating Integration**: Include customer ratings in marketing materials when
  available.

## Prerequisites

- **Python**: 3.10 or newer.
- **System dependencies**:
  - Ability to create virtual environments.
  - Access to testimonial data files (CSV or JSON format).

No external services or APIs are required.

## Installation

1. **Clone or copy the project into your automation workspace.**

2. **Create and activate a virtual environment**:

   ```bash
   cd testimonial_processor
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

   - Ensure your testimonial data CSV or JSON file is available.
   - Update `config.yaml` to point to your data file.
   - Configure product and service keywords for categorization.

## Configuration

Configuration is driven primarily by `config.yaml` plus optional environment variables.

- **Environment variables**:
  - `CONFIG_PATH`: Path to configuration file (default: `config.yaml`).

- **Config file (`config.yaml`)**:
  - `testimonial_data`: Configuration for testimonial data source:
    - `file_path`: Path to testimonial data file.
    - `format`: File format (`csv` or `json`).
    - `testimonial_id_column`: Column name for testimonial ID.
    - `customer_name_column`: Column name for customer name.
    - `testimonial_text_column`: Column name for testimonial text.
    - `product_column`: Column name for product name (optional).
    - `category_column`: Column name for category (optional).
    - `rating_column`: Column name for rating (optional).
    - `date_column`: Column name for date (optional).
  - `quote_extraction`: Quote extraction settings:
    - `min_quote_length`: Minimum quote length in characters.
    - `max_quote_length`: Maximum quote length in characters.
    - `extract_full_sentences`: Extract complete sentences only.
    - `quote_indicators`: List of indicators that suggest quoted content.
  - `categorization`: Categorization settings:
    - `product_keywords`: Mapping of product names to keyword lists.
    - `service_keywords`: Mapping of service names to keyword lists.
    - `auto_categorize`: Automatically categorize based on keywords.
  - `marketing`: Marketing material generation settings:
    - `output_formats`: List of output formats (`markdown`, `html`).
    - `include_customer_name`: Include customer name in materials.
    - `include_rating`: Include rating if available.
    - `include_date`: Include testimonial date.
    - `template_path`: Path to custom template file (optional).
  - `permission`: Permission tracking settings:
    - `permission_file`: Path to permission tracking file.
    - `default_permission_status`: Default permission status.
    - `require_permission_for_use`: Require granted permission for marketing use.

### Example configuration

See the provided `config.yaml` in the project root for a complete example.

## Usage

After configuration, run the processor from the project root:

```bash
source .venv/bin/activate  # if not already active
python -m testimonial_processor.src.main
```

This will:

- Load testimonial data from the configured file.
- Extract quotes from each testimonial.
- Categorize testimonials by product or service.
- Track permission statuses.
- Generate marketing materials in configured formats.
- Save materials to the output directory.

## Project Structure

```
testimonial_processor/
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

Tests cover core functionality including quote extraction, categorization, and
marketing material generation.

## Troubleshooting

### Common Issues

**Error: "Testimonial data file not found"**
- Ensure the `testimonial_data.file_path` in `config.yaml` points to a valid file.
- Check that relative paths are resolved from the project root.

**Error: "Missing required columns"**
- Verify your testimonial data file contains the required columns specified in `config.yaml`.
- Check column names match exactly (case-sensitive).

**No quotes extracted**
- Review `min_quote_length` and `max_quote_length` settings.
- Check that testimonial text contains sufficient content.
- Verify `quote_indicators` match patterns in your testimonials.

**Testimonials not categorized**
- Ensure product or service keywords are configured in `config.yaml`.
- Check that `auto_categorize` is enabled.
- Verify keywords match content in testimonial text (case-insensitive).

**Permission tracking not working**
- Check that `permission_file` path is writable.
- Verify permission status values match enum values (granted, pending, denied, etc.).

## Contributing

1. Follow PEP 8 style guidelines.
2. Add type hints to all functions.
3. Include docstrings for public functions.
4. Write tests for new functionality.
5. Update documentation as needed.

## License

This project is provided as-is for internal use.
