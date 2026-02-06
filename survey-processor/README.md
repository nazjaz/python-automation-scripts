# Survey Processor

Automated customer survey processing system that analyzes responses, identifies trends, calculates satisfaction scores, and generates executive summaries with insights.

## Project Description

This automation system provides comprehensive survey analysis and reporting for customer feedback. The system processes survey responses from CSV or JSON files, analyzes question responses, identifies trends, calculates satisfaction scores, and generates executive summaries with actionable insights and recommendations. This helps product teams, customer success teams, and business analysts quickly understand customer sentiment and identify areas for improvement.

### Target Audience

- Product managers analyzing customer feedback
- Customer success teams tracking satisfaction
- Business analysts generating survey insights
- Market researchers processing survey data
- Executive teams reviewing customer sentiment

## Features

- **Response Processing**: Imports survey responses from CSV and JSON files
- **Response Analysis**: Analyzes responses by question type (rating, multiple choice, text)
- **Trend Identification**: Automatically identifies trends in responses with confidence scores
- **Satisfaction Calculation**: Calculates satisfaction scores from rating questions with distribution analysis
- **Executive Summary Generation**: Generates comprehensive executive summaries with key insights and recommendations
- **Insight Generation**: Automatically generates insights from analysis results with priority classification
- **Comprehensive Reporting**: Creates HTML and CSV reports with visualizations and detailed metrics
- **Database Persistence**: Stores all survey data, responses, trends, insights, and summaries in SQLite database
- **Flexible Question Types**: Supports rating, multiple choice, and text questions
- **Multi-Survey Support**: Processes multiple surveys with individual analysis and summaries

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd survey-processor
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
DATABASE_URL=sqlite:///survey_processor.db
APP_NAME=Survey Processor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize analysis settings, trend identification, satisfaction calculation, and summary generation:

```yaml
trends:
  min_occurrences: 3
  confidence_threshold: 0.6

satisfaction:
  rating_questions_weight: 0.7
  satisfaction_thresholds:
    very_satisfied: 4.5
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///survey_processor.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **import**: Response import settings including file encoding
- **analysis**: Analysis configuration settings
- **trends**: Trend identification settings including minimum occurrences and confidence thresholds
- **satisfaction**: Satisfaction calculation settings including question weights and thresholds
- **summary**: Summary generation settings including template configuration
- **reporting**: Report generation settings including output formats and directory
- **logging**: Log file location, rotation, and format settings

## Usage

### Create Survey

Create a new survey:

```bash
python src/main.py --create-survey "Customer Satisfaction Survey" "Q4 2024 customer feedback"
```

### Import Responses

Import responses from CSV file:

```bash
python src/main.py --import 1 responses.csv --format csv
```

Import responses from JSON file:

```bash
python src/main.py --import 1 responses.json --format json
```

### Analyze Responses

Analyze survey responses:

```bash
python src/main.py --analyze 1
```

### Identify Trends

Identify trends in survey responses:

```bash
python src/main.py --identify-trends 1
```

### Calculate Satisfaction

Calculate satisfaction scores:

```bash
python src/main.py --calculate-satisfaction 1
```

### Generate Executive Summary

Generate executive summary with insights:

```bash
python src/main.py --generate-summary 1
```

### Generate Reports

Generate HTML and CSV reports:

```bash
python src/main.py --report --survey-id 1
```

### Complete Workflow

Run complete survey processing workflow:

```bash
# Create survey and add questions (manually or via API)
python src/main.py --create-survey "Customer Survey" "Customer feedback"

# Import responses
python src/main.py --import 1 responses.csv --format csv

# Process survey
python src/main.py --analyze 1 --identify-trends 1 --calculate-satisfaction 1 --generate-summary 1 --report
```

### Command-Line Arguments

```
--create-survey NAME DESCRIPTION    Create a new survey
--import SURVEY_ID FILE             Import responses from CSV or JSON file
--analyze SURVEY_ID                 Analyze survey responses
--identify-trends SURVEY_ID         Identify trends in responses
--calculate-satisfaction SURVEY_ID  Calculate satisfaction scores
--generate-summary SURVEY_ID        Generate executive summary
--report                            Generate analysis reports
--survey-id ID                      Filter by survey ID
--format FORMAT                     File format for import (csv or json, default: csv)
--survey-type TYPE                  Survey type
--config PATH                       Path to configuration file (default: config.yaml)
```

## Project Structure

```
survey-processor/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml               # Application configuration
├── .env.example              # Environment variable template
├── .gitignore               # Git ignore rules
├── src/                     # Source code
│   ├── __init__.py
│   ├── main.py              # Main entry point
│   ├── config.py             # Configuration management
│   ├── database.py           # Database models and operations
│   ├── response_processor.py # Response import and processing
│   ├── survey_analyzer.py    # Survey response analysis
│   ├── trend_identifier.py # Trend identification
│   ├── satisfaction_calculator.py # Satisfaction score calculation
│   ├── summary_generator.py # Executive summary generation
│   └── report_generator.py  # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── survey_report.html    # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point that orchestrates survey creation, response import, analysis, trend identification, satisfaction calculation, summary generation, and reporting
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models and database operations for surveys, questions, responses, answers, trends, insights, and summaries
- **src/response_processor.py**: Imports and processes responses from CSV and JSON files
- **src/survey_analyzer.py**: Analyzes survey responses by question type
- **src/trend_identifier.py**: Identifies trends in responses with confidence scoring
- **src/satisfaction_calculator.py**: Calculates satisfaction scores and distributions
- **src/summary_generator.py**: Generates executive summaries with insights and recommendations
- **src/report_generator.py**: Generates HTML and CSV reports with analysis results
- **tests/test_main.py**: Comprehensive unit tests with mocking

## Testing

### Run Tests

```bash
pytest tests/
```

### Run Tests with Coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

The test suite aims for minimum 80% code coverage and includes:

- Response import functionality (CSV and JSON)
- Survey analysis algorithms
- Trend identification logic
- Satisfaction score calculation
- Summary generation
- Report generation (HTML and CSV)
- Database operations and models
- Configuration loading and validation

## Troubleshooting

### Database Errors

**Problem**: Database connection or operation errors.

**Solutions**:
- Ensure SQLite is available (included with Python)
- Check file permissions for database file location
- Verify `DATABASE_URL` in `.env` is correctly formatted
- Delete existing database file to recreate schema if needed

### Configuration Errors

**Problem**: Configuration file not found or invalid.

**Solutions**:
- Ensure `config.yaml` exists in project root directory
- Validate YAML syntax using an online YAML validator
- Check that all required configuration sections are present
- Review error messages in logs for specific validation issues

### Import Errors

**Problem**: Response import fails or imports incorrect data.

**Solutions**:
- Verify CSV/JSON file format matches expected structure
- Check file encoding (should be UTF-8)
- Ensure file contains required columns/fields
- Review CSV headers match question IDs or use standard format
- Check that survey questions exist before importing responses
- Verify file path is correct and file is readable

### No Trends Identified

**Problem**: Trend identification returns no results.

**Solutions**:
- Verify minimum occurrences threshold in `config.yaml` (default: 3)
- Ensure sufficient responses have been imported
- Check that responses contain answer data
- Review trend identification settings
- Lower confidence threshold if needed

### Satisfaction Scores Not Calculated

**Problem**: Satisfaction scores are not being calculated.

**Solutions**:
- Verify survey contains rating-type questions
- Ensure responses have answers for rating questions
- Check that answer values are numeric for rating questions
- Review satisfaction calculation settings
- Verify responses are properly linked to questions

### Summary Generation Issues

**Problem**: Executive summary is not being generated or is incomplete.

**Solutions**:
- Ensure survey has been analyzed first (run `--analyze`)
- Verify trends have been identified (run `--identify-trends`)
- Check that satisfaction scores have been calculated (run `--calculate-satisfaction`)
- Ensure sufficient response data exists
- Review summary generation settings

### Report Generation Failures

**Problem**: Reports are not being generated or are incomplete.

**Solutions**:
- Ensure output directory exists and is writable
- Check that template file exists in `templates/` directory
- Verify sufficient survey data exists (responses, trends, insights)
- Review logs for specific error messages
- Ensure all required dependencies are installed

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Survey not found`: Verify survey ID is correct and survey exists
- `CSV file not found`: Verify the file path provided to `--import` is correct
- `No responses found`: Ensure responses have been imported before analysis
- `Template not found`: HTML template file missing, system will use default template

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make changes following PEP 8 and project standards
4. Write tests for new functionality
5. Ensure all tests pass: `pytest tests/`
6. Commit with conventional commit messages
7. Submit a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Use type hints for all function signatures
- Write comprehensive docstrings (Google style)
- Keep functions focused and under 50 lines
- Use meaningful variable and function names
- Include error handling and logging

### Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Write clear commit messages following conventional format
4. Provide description of changes and testing performed

## CSV Import Format

The system supports CSV files with the following format:

```csv
respondent_id,respondent_email,question_1,question_2,question_3
resp1,user1@example.com,4.5,Yes,Great service
resp2,user2@example.com,3.0,No,Needs improvement
```

Where `question_N` corresponds to question IDs in the survey.

## JSON Import Format

The system supports JSON files with the following format:

```json
{
  "responses": [
    {
      "respondent_id": "resp1",
      "respondent_email": "user1@example.com",
      "answers": {
        "question_1": 4.5,
        "question_2": "Yes",
        "question_3": "Great service"
      }
    }
  ]
}
```

## Question Types

The system supports various question types:

- **rating**: Numeric rating questions (typically 1-5 scale)
- **multiple_choice**: Multiple choice questions with predefined options
- **text**: Free-form text response questions

Question types determine how responses are analyzed and how satisfaction scores are calculated.

## Trend Types

The system identifies various trend types:

- **positive**: Trends indicating positive feedback
- **negative**: Trends indicating negative feedback
- **neutral**: Trends indicating neutral feedback
- **dominant**: Dominant choice patterns in multiple choice questions
- **distributed**: Distributed choice patterns

Trends are identified with confidence scores based on response frequency and patterns.

## Insight Types

The system generates various insight types:

- **positive**: Positive insights from high ratings or positive feedback
- **negative**: Negative insights from low ratings or negative feedback
- **neutral**: Neutral insights from moderate feedback

Insights are prioritized (low, medium, high) based on severity and impact.

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
