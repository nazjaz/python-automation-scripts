# Customer Onboarding Automation

Automated customer onboarding system that sends welcome emails, sets up accounts, assigns resources, and tracks onboarding progress with comprehensive completion metrics.

## Project Description

This automation system streamlines the customer onboarding process by automating key tasks including welcome email delivery, account configuration, resource assignment, and progress tracking. The system provides detailed metrics and completion tracking to ensure a smooth onboarding experience for new customers.

### Target Audience

- Operations teams managing customer onboarding workflows
- Customer success teams tracking onboarding progress
- Development teams integrating onboarding automation into existing systems

## Features

- **Automated Welcome Emails**: Sends personalized welcome emails with HTML templates and retry logic
- **Account Setup**: Automatically generates and configures customer accounts with unique identifiers
- **Resource Assignment**: Assigns default resources (documentation, support access) to new customers
- **Progress Tracking**: Tracks completion of each onboarding step with detailed metrics
- **Completion Metrics**: Provides comprehensive metrics including completion percentages and step-by-step progress
- **Database Persistence**: Stores all onboarding data in SQLite database for historical tracking
- **Error Handling**: Robust error handling with logging and retry mechanisms
- **API Integration**: Optional integration with external APIs for resource assignment

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SMTP server access (Gmail, Outlook, or custom SMTP server)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd customer-onboarding
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
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@example.com
SMTP_FROM_NAME=Customer Onboarding

DATABASE_URL=sqlite:///onboarding.db
APP_NAME=Customer Onboarding System
LOG_LEVEL=INFO

RESOURCE_API_URL=https://api.example.com/resources
RESOURCE_API_KEY=your-api-key-here
```

**Note**: For Gmail, you'll need to generate an App Password instead of your regular password. Enable 2-factor authentication and generate an app-specific password.

### Step 5: Configure Application Settings

Edit `config.yaml` to customize onboarding steps, email templates, and resource assignments:

```yaml
email:
  welcome_template: "templates/welcome_email.html"
  subject: "Welcome to {{company_name}}"
  retry_attempts: 3
  retry_delay_seconds: 5

onboarding:
  steps:
    - name: "welcome_email"
      required: true
      order: 1
    - name: "account_setup"
      required: true
      order: 2
    - name: "resource_assignment"
      required: true
      order: 3
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SMTP_HOST` | SMTP server hostname | Yes |
| `SMTP_PORT` | SMTP server port (587 for TLS) | Yes |
| `SMTP_USERNAME` | SMTP authentication username | Yes |
| `SMTP_PASSWORD` | SMTP authentication password | Yes |
| `SMTP_FROM_EMAIL` | Sender email address | Yes |
| `SMTP_FROM_NAME` | Sender display name | Yes |
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///onboarding.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |
| `RESOURCE_API_URL` | External API URL for resource assignment | No |
| `RESOURCE_API_KEY` | API key for external resource API | No |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **email**: Email service configuration including templates and retry settings
- **onboarding**: Onboarding step definitions and completion thresholds
- **resources**: Default resource assignments and API configuration
- **logging**: Log file location, rotation, and format settings

## Usage

### Basic Usage

Process onboarding for a single customer:

```bash
python src/main.py --email customer@example.com --name "John Doe" --company "Acme Corp"
```

### View Metrics

Display aggregated onboarding metrics for all customers:

```bash
python src/main.py --metrics
```

### Custom Configuration File

Use a custom configuration file:

```bash
python src/main.py --email customer@example.com --name "John Doe" --config /path/to/config.yaml
```

### Command-Line Arguments

```
--email EMAIL        Customer email address (required)
--name NAME          Customer full name (required)
--company COMPANY    Company name (optional)
--config PATH        Path to configuration file (optional)
--metrics            Display completion metrics for all customers
```

## Project Structure

```
customer-onboarding/
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
│   ├── email_service.py      # Email sending service
│   ├── account_manager.py    # Account setup and management
│   ├── resource_manager.py   # Resource assignment
│   └── onboarding_tracker.py # Progress tracking and metrics
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Email templates
│   └── welcome_email.html    # Welcome email template
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point that orchestrates the onboarding workflow
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models and database operations
- **src/email_service.py**: SMTP email sending with retry logic and template support
- **src/account_manager.py**: Account ID generation and account management
- **src/resource_manager.py**: Resource assignment with optional API integration
- **src/onboarding_tracker.py**: Progress tracking and completion metrics calculation
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

- Email service functionality and error handling
- Account setup and management
- Resource assignment (database and API)
- Onboarding step tracking and completion
- Configuration loading and validation

## Troubleshooting

### Email Sending Failures

**Problem**: Emails are not being sent.

**Solutions**:
- Verify SMTP credentials in `.env` file
- For Gmail, ensure you're using an App Password, not your regular password
- Check firewall settings for SMTP port access
- Verify SMTP server hostname and port are correct
- Review logs in `logs/onboarding.log` for detailed error messages

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

### Resource Assignment Failures

**Problem**: Resources not being assigned via API.

**Solutions**:
- Verify `RESOURCE_API_URL` and `RESOURCE_API_KEY` are set if using external API
- Check API endpoint accessibility and authentication
- Review API timeout settings in `config.yaml`
- System will fall back to database-only assignment if API fails

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Customer with email already exists`: Customer record already exists in database
- `Template not found`: Email template file missing, system will use default template

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

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
