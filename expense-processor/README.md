# Expense Processor

Automated expense report processing system that extracts receipts, validates expenses against policies, calculates reimbursements, and routes reports for approvals.

## Project Description

This automation system streamlines expense report processing by automating key tasks including receipt extraction using OCR, expense validation against company policies, reimbursement calculation, and automatic routing for approvals based on amount thresholds and organizational hierarchy.

### Target Audience

- Finance teams processing expense reports
- HR departments managing employee expenses
- Accounting teams calculating reimbursements
- Managers approving expense reports

## Features

- **Receipt Extraction**: Automatically extracts data from receipt images and PDFs using OCR
- **Expense Validation**: Validates expenses against configurable company policies
- **Reimbursement Calculation**: Calculates reimbursable amounts based on validation results
- **Approval Routing**: Automatically routes reports for approval based on amount and hierarchy
- **Policy Management**: Configurable expense policies with category-specific rules
- **Multi-Format Reports**: Generates HTML and CSV expense reports
- **Database Persistence**: Stores all expense data, receipts, and approvals in SQLite database

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)
- Tesseract OCR (for receipt extraction)
  - macOS: `brew install tesseract`
  - Linux: `sudo apt-get install tesseract-ocr`
  - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd expense-processor
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
DATABASE_URL=sqlite:///expense_processor.db
APP_NAME=Expense Processor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize expense policies, validation rules, and approval routing:

```yaml
expense_policies:
  max_daily_meal: 75.00
  require_receipt_threshold: 25.00
  allowed_categories:
    - "meals"
    - "lodging"
    - "transportation"

approval:
  routing_enabled: true
  auto_approve_under: 25.00
  approval_levels:
    - level: 1
      max_amount: 100.00
      approver_role: "manager"
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///expense_processor.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **expense_policies**: Maximum amounts, receipt requirements, allowed categories
- **receipt_extraction**: OCR settings, supported formats, extraction options
- **validation**: Validation rules, duplicate checking, strict mode
- **reimbursement**: Calculation method, tax rates, rounding
- **approval**: Routing settings, approval levels, auto-approve thresholds
- **reporting**: Output formats, directory, inclusion options
- **logging**: Log file location, rotation, and format settings

## Usage

### Add an Employee

Add an employee to the system:

```bash
python src/main.py --add-employee --employee-id "EMP001" --name "John Doe" --email "john@example.com" --department "Engineering" --role "employee"
```

### Create Expense Report

Create a new expense report:

```bash
python src/main.py --create-report --employee-id "EMP001" --report-date "2024-06-15" --description "Business trip expenses"
```

### Add Expense

Add an expense to a report:

```bash
python src/main.py --add-expense --report-id 1 --expense-date "2024-06-15" --category "meals" --amount 45.50 --merchant "Restaurant ABC"
```

### Extract Receipt

Extract data from a receipt file:

```bash
python src/main.py --extract-receipt --report-id 1 --receipt-file "receipts/receipt.jpg"
```

### Process Report

Process expense report (validate, calculate, route):

```bash
python src/main.py --process-report --report-id 1
```

### Generate Report

Generate expense report:

```bash
python src/main.py --generate-report --report-id 1 --format html
```

### Complete Workflow

Run complete expense processing workflow:

```bash
# Create report and add expenses
python src/main.py --create-report --employee-id "EMP001" --report-date "2024-06-15"
python src/main.py --add-expense --report-id 1 --expense-date "2024-06-15" --category "meals" --amount 45.50
python src/main.py --extract-receipt --report-id 1 --receipt-file "receipt.jpg"

# Process and generate report
python src/main.py --process-report --report-id 1
python src/main.py --generate-report --report-id 1
```

### Command-Line Arguments

```
--add-employee          Add an employee
--employee-id ID        Employee ID (required)
--name NAME             Employee name (required)
--email EMAIL           Employee email (required)
--department DEPT       Department
--manager-id ID         Manager employee ID
--role ROLE             Role (employee, manager, director, vp)

--create-report         Create expense report
--employee-id ID        Employee ID (required)
--report-date DATE      Report date YYYY-MM-DD (required)
--description DESC      Report description

--add-expense           Add expense to report
--report-id ID          Report ID (required)
--expense-date DATE     Expense date YYYY-MM-DD (required)
--category CAT          Category (required)
--amount AMOUNT         Amount (required)
--merchant MERCHANT     Merchant name
--description DESC      Expense description

--extract-receipt       Extract receipt data
--report-id ID          Report ID (required)
--receipt-file PATH     Path to receipt file (required)

--process-report        Process expense report
--report-id ID          Report ID (required)

--generate-report       Generate expense report
--report-id ID          Report ID (required)
--format FORMAT         Format (html or csv, default: html)

--config PATH           Path to configuration file (default: config.yaml)
```

## Project Structure

```
expense-processor/
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
│   ├── receipt_extractor.py  # Receipt extraction using OCR
│   ├── expense_validator.py  # Expense validation
│   ├── reimbursement_calculator.py # Reimbursement calculation
│   ├── approval_router.py    # Approval routing
│   └── report_generator.py   # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── expense_report.html   # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point with CLI interface for all operations
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models for employees, reports, expenses, receipts, policies, approvals
- **src/receipt_extractor.py**: Extracts data from receipt images/PDFs using OCR
- **src/expense_validator.py**: Validates expenses against policies
- **src/reimbursement_calculator.py**: Calculates reimbursable amounts
- **src/approval_router.py**: Routes reports for approval based on hierarchy
- **src/report_generator.py**: Generates HTML and CSV expense reports
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

- Database operations and models
- Receipt extraction functionality
- Expense validation algorithms
- Reimbursement calculations
- Approval routing logic
- Report generation
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

### OCR/Receipt Extraction Failures

**Problem**: Receipt extraction fails or returns no data.

**Solutions**:
- Verify Tesseract OCR is installed and in PATH
- Check receipt file format is supported (PDF, JPG, PNG)
- Ensure receipt image quality is sufficient for OCR
- Review OCR confidence threshold in `config.yaml`
- Check logs for specific OCR errors

### Validation Failures

**Problem**: Expenses are not validating correctly.

**Solutions**:
- Verify expense policies are configured in `config.yaml`
- Check that expense categories match allowed categories
- Ensure receipt requirements are met for threshold amounts
- Review validation notes in database
- Check logs for validation errors

### Approval Routing Issues

**Problem**: Reports are not being routed for approval.

**Solutions**:
- Verify approval routing is enabled in `config.yaml`
- Check that employee manager relationships are set up
- Ensure approvers with correct roles exist
- Review approval level thresholds
- Check logs for routing errors

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Employee not found`: Verify employee ID exists in database
- `Tesseract not found`: Install Tesseract OCR and ensure it's in PATH
- `Invalid date format`: Use YYYY-MM-DD format for dates
- `Receipt file not found`: Verify receipt file path is correct

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

## Receipt Extraction

The system extracts the following data from receipts:

- **Merchant Name**: Extracted from receipt header
- **Date**: Parsed from date patterns in receipt
- **Amount**: Extracted from total/amount fields
- **Category**: Inferred from merchant name and keywords
- **Confidence Score**: OCR extraction confidence (0.0 to 1.0)

Supported formats:
- PDF files
- JPEG/JPG images
- PNG images

## Expense Validation

Expenses are validated against:

- **Category Limits**: Maximum amounts per category
- **Daily Limits**: Maximum daily amounts per category
- **Receipt Requirements**: Receipt required for amounts over threshold
- **Allowed Categories**: Only expenses in allowed categories
- **Duplicate Detection**: Checks for duplicate expenses

## Approval Routing

Reports are routed for approval based on:

- **Amount Thresholds**: Different approval levels for different amounts
- **Organizational Hierarchy**: Routes to employee's manager
- **Role-Based**: Routes to approvers with specific roles
- **Auto-Approval**: Automatically approves reports under threshold

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
