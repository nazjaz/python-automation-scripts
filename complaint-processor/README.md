# Complaint Processor

Automated customer complaint processing system that categorizes issues, routes to appropriate departments, tracks resolution, and generates customer satisfaction follow-ups.

## Project Description

This automation system provides comprehensive complaint processing for customer service operations. The system automatically categorizes complaints by issue type, routes them to appropriate departments based on rules and keywords, tracks resolution progress, and generates customer satisfaction follow-ups. This helps customer service teams, support managers, and quality assurance teams efficiently handle complaints and improve customer satisfaction.

### Target Audience

- Customer service teams processing complaints
- Support managers monitoring resolution rates
- Quality assurance teams tracking complaint categories
- Operations managers optimizing complaint handling
- Customer success teams managing customer relationships

## Features

- **Issue Categorization**: Automatically categorizes complaints by issue type (product quality, billing, shipping, customer service, technical, account) with confidence scoring
- **Department Routing**: Routes complaints to appropriate departments based on category, keywords, and priority with configurable routing rules
- **Resolution Tracking**: Tracks complaint resolution progress with status updates, resolution time tracking, and overdue complaint identification
- **Customer Satisfaction Follow-ups**: Generates personalized follow-up messages for resolved complaints with satisfaction survey capabilities
- **Complaint Processing**: Complete complaint processing workflow from receipt to resolution
- **Performance Metrics**: Tracks key performance indicators including resolution rates, average resolution time, and category distribution
- **Comprehensive Reporting**: Generates HTML and CSV reports with complaint metrics, open complaints, and resolution statistics
- **Database Persistence**: Stores all customers, complaints, departments, routing rules, resolutions, updates, and follow-ups in SQLite database
- **Flexible Configuration**: Customizable categorization keywords, routing rules, follow-up templates, and processing settings
- **Multi-Department Support**: Supports multiple departments with individual routing rules and workload tracking

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd complaint-processor
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
DATABASE_URL=sqlite:///complaint_processor.db
APP_NAME=Complaint Processor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize categorization keywords, routing rules, and follow-up templates:

```yaml
categorization:
  category_keywords:
    billing:
      - "charge"
      - "billing"
      - "invoice"

routing:
  default_department: "Customer Service"
  category_mapping:
    billing: "Billing"
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///complaint_processor.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **categorization**: Issue categorization settings including category keywords and subcategory keywords
- **routing**: Department routing settings including default department and category mapping
- **processing**: Complaint processing configuration
- **resolution_tracking**: Resolution tracking settings
- **followups**: Follow-up generation settings including templates and delay hours
- **reporting**: Report generation settings including output formats and directory
- **logging**: Log file location, rotation, and format settings

## Usage

### Process Complaint

Process a new complaint:

```bash
python src/main.py --process "COMP001" "CUST001" "I was charged incorrectly on my invoice" "John Doe" --email "john@example.com"
```

### Resolve Complaint

Resolve a complaint:

```bash
python src/main.py --resolve "COMP001" "Refunded the incorrect charge" "refund" "Agent1"
```

### Track Resolution

Track complaint resolution:

```bash
python src/main.py --track "COMP001"
```

### Generate Follow-up

Generate customer satisfaction follow-up:

```bash
python src/main.py --generate-followup "COMP001"
```

### Generate Reports

Generate HTML and CSV reports:

```bash
python src/main.py --report --complaint-id "COMP001"
```

### Complete Workflow

Run complete complaint processing workflow:

```bash
# Process complaint
python src/main.py --process "COMP001" "CUST001" "Billing issue" "John Doe"

# Resolve complaint
python src/main.py --resolve "COMP001" "Issue resolved" "refund" "Agent1"

# Generate follow-up
python src/main.py --generate-followup "COMP001"

# Generate reports
python src/main.py --report
```

### Command-Line Arguments

```
--process COMPLAINT_ID CUSTOMER_ID TEXT NAME    Process a new complaint
--resolve COMPLAINT_ID TEXT TYPE BY          Resolve a complaint
--track COMPLAINT_ID                         Track complaint resolution
--generate-followup COMPLAINT_ID             Generate follow-up for complaint
--report                                     Generate analysis reports
--complaint-id ID                            Filter by complaint ID
--email EMAIL                                Customer email
--config PATH                                Path to configuration file (default: config.yaml)
```

## Project Structure

```
complaint-processor/
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
│   ├── complaint_processor.py # Complaint processing
│   ├── issue_categorizer.py  # Issue categorization
│   ├── department_router.py  # Department routing
│   ├── resolution_tracker.py # Resolution tracking
│   ├── followup_generator.py # Follow-up generation
│   └── report_generator.py  # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── complaint_report.html # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point that orchestrates complaint processing, categorization, routing, resolution tracking, follow-up generation, and reporting
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models and database operations for customers, complaints, departments, routing rules, resolutions, updates, follow-ups, and metrics
- **src/complaint_processor.py**: Processes complaints through complete workflow
- **src/issue_categorizer.py**: Categorizes complaints by issue type with keyword matching
- **src/department_router.py**: Routes complaints to appropriate departments based on rules
- **src/resolution_tracker.py**: Tracks complaint resolution with time tracking
- **src/followup_generator.py**: Generates customer satisfaction follow-ups
- **src/report_generator.py**: Generates HTML and CSV reports with complaint data
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

- Complaint processing functionality
- Issue categorization algorithms
- Department routing logic
- Resolution tracking
- Follow-up generation
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

### Complaint Not Categorized

**Problem**: Complaint categorization returns incorrect or no category.

**Solutions**:
- Verify categorization keywords are configured in `config.yaml`
- Check that complaint text contains recognizable keywords
- Review category keyword lists for completeness
- Lower confidence threshold if needed
- Add custom keywords for specific categories

### Complaint Not Routed

**Problem**: Complaint is not routed to appropriate department.

**Solutions**:
- Verify departments exist in database
- Check routing rules are configured correctly
- Ensure category mapping is set up in `config.yaml`
- Review default department setting
- Verify routing rule keywords match complaint text

### Resolution Not Tracked

**Problem**: Resolution tracking not working correctly.

**Solutions**:
- Verify complaint exists and is in correct status
- Check that resolution was added properly
- Ensure complaint status is updated to "resolved"
- Review resolution tracking settings
- Check that resolution time is calculated correctly

### Follow-up Not Generated

**Problem**: Follow-up is not being generated for resolved complaints.

**Solutions**:
- Verify complaint is in "resolved" status
- Check that resolution exists for complaint
- Ensure follow-up templates are configured
- Review follow-up delay settings
- Check that customer information is available

### Report Generation Failures

**Problem**: Reports are not being generated or are incomplete.

**Solutions**:
- Ensure output directory exists and is writable
- Check that template file exists in `templates/` directory
- Verify sufficient complaint data exists
- Review logs for specific error messages
- Ensure all required dependencies are installed

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Complaint not found`: Verify complaint ID is correct and complaint exists
- `Customer not found`: Customer will be created automatically if not found
- `Department not found`: Ensure departments are created before routing complaints
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

## Complaint Categories

The system supports various complaint categories:

- **product_quality**: Product defects, quality issues
- **billing**: Billing errors, payment issues, refunds
- **shipping**: Delivery problems, shipping delays
- **customer_service**: Service quality, support issues
- **technical**: Technical errors, system issues
- **account**: Account access, login problems

Categories are determined by keyword matching in complaint text.

## Complaint Statuses

The system tracks various complaint statuses:

- **new**: Complaint just received
- **assigned**: Complaint assigned to department
- **in_progress**: Complaint being worked on
- **resolved**: Complaint has been resolved
- **closed**: Complaint is closed

Status updates are tracked through complaint updates.

## Priority Levels

Complaints can have different priority levels:

- **low**: Low priority complaints
- **medium**: Normal priority (default)
- **high**: High priority complaints
- **urgent**: Urgent priority complaints

Priority affects routing and resolution time expectations.

## Resolution Types

The system supports various resolution types:

- **refund**: Monetary refund provided
- **replacement**: Product/service replacement
- **apology**: Apology and explanation
- **fix**: Technical fix applied
- **escalation**: Escalated to higher level
- **other**: Other resolution types

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
