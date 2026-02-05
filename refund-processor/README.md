# Refund Processor

Automated customer refund processing system that validates requests, checks policies, calculates refund amounts, and updates payment systems with confirmation emails.

## Project Description

This automation system streamlines the refund process by automatically validating refund requests against business rules, checking refund policies, calculating refund amounts with fees, processing refunds through payment systems, and sending confirmation emails to customers.

### Target Audience

- E-commerce platforms processing customer refunds
- Payment processing teams managing refund workflows
- Customer service departments handling refund requests
- Finance teams tracking refund transactions

## Features

- **Request Validation**: Validates refund requests for required fields, order existence, and customer matching
- **Policy Checking**: Enforces refund policies including time limits, amount limits, and reason validation
- **Refund Calculation**: Calculates refund amounts with configurable restocking fees
- **Payment Integration**: Processes refunds through Stripe and PayPal payment systems
- **Automatic Approval**: Auto-approves refunds below threshold amounts
- **Email Notifications**: Sends confirmation emails with refund details
- **Database Tracking**: Maintains complete audit trail of all refund requests and transactions

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Payment provider API access (Stripe, PayPal, etc.)
- SMTP server access (Gmail, Outlook, or custom SMTP server)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd refund-processor
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
STRIPE_API_KEY=your-stripe-api-key
STRIPE_SECRET_KEY=your-stripe-secret-key

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@example.com
```

**Note**: For Gmail, you'll need to generate an App Password instead of your regular password. Enable 2-factor authentication and generate an app-specific password.

### Step 5: Configure Application Settings

Edit `config.yaml` to customize refund policies, validation rules, and email templates:

```yaml
refund_policies:
  max_refund_days: 90
  auto_approve_threshold: 50.00
  require_approval_above: 500.00
  restocking_fee_percentage: 0.10
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `STRIPE_API_KEY` | Stripe API key | Yes |
| `STRIPE_SECRET_KEY` | Stripe secret key | Yes |
| `PAYPAL_CLIENT_ID` | PayPal client ID (if using PayPal) | No |
| `PAYPAL_SECRET` | PayPal secret (if using PayPal) | No |
| `SMTP_HOST` | SMTP server hostname | Yes |
| `SMTP_PORT` | SMTP server port | Yes |
| `SMTP_USERNAME` | SMTP username | Yes |
| `SMTP_PASSWORD` | SMTP password | Yes |
| `SMTP_FROM_EMAIL` | Sender email address | Yes |

### Configuration File (config.yaml)

The `config.yaml` file contains:

- **refund_policies**: Refund policy rules including time limits, amount thresholds, and fees
- **payment_systems**: Payment provider configuration (Stripe, PayPal)
- **validation**: Validation rules for refund requests
- **email**: Email template and notification settings
- **database**: Database connection URL
- **logging**: Log file configuration

## Usage

### Process a Refund

```bash
python src/main.py \
  --order-id "ORD-12345" \
  --email "customer@example.com" \
  --amount 100.00 \
  --reason "defective_product" \
  --description "Product arrived damaged"
```

### Command-Line Arguments

```
--order-id ORDER_ID    Order identifier (required)
--email EMAIL          Customer email address (required)
--amount AMOUNT        Refund amount (required)
--reason REASON        Refund reason (required)
--description DESC     Additional description (optional)
--config PATH          Path to configuration file (optional)
```

### Refund Reasons

Valid refund reasons (configurable in config.yaml):
- `defective_product`
- `not_as_described`
- `wrong_item`
- `damaged_during_shipping`
- `customer_request`
- `duplicate_charge`
- `cancellation`

## Project Structure

```
refund-processor/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml               # Application configuration
├── .env.example              # Environment variable template
├── .gitignore               # Git ignore rules
├── src/                     # Source code
│   ├── __init__.py
│   ├── main.py              # Main entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database models and operations
│   ├── refund_validator.py  # Request validation
│   ├── policy_checker.py    # Policy enforcement
│   ├── refund_calculator.py # Refund amount calculation
│   ├── payment_integrator.py # Payment system integration
│   └── email_service.py     # Email notifications
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                 # Email templates
│   └── refund_confirmation.html # Refund confirmation template
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main orchestrator that coordinates the refund processing workflow
- **src/config.py**: Configuration loading with environment variable substitution
- **src/database.py**: SQLAlchemy models for orders, refund requests, and refunds
- **src/refund_validator.py**: Validates refund requests against business rules
- **src/policy_checker.py**: Checks refund requests against policy rules
- **src/refund_calculator.py**: Calculates refund amounts with fees
- **src/payment_integrator.py**: Integrates with payment providers (Stripe, PayPal)
- **src/email_service.py**: Sends refund confirmation emails

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

- Refund request validation
- Policy checking logic
- Refund amount calculation
- Payment integration
- Email service functionality

## Troubleshooting

### Validation Errors

**Problem**: Refund requests are being rejected during validation.

**Solutions**:
- Verify order ID exists in database
- Check customer email matches order customer
- Ensure all required fields are provided
- Review validation configuration in `config.yaml`
- Check logs for specific validation error messages

### Policy Violations

**Problem**: Refund requests fail policy checks.

**Solutions**:
- Verify order is within refund time window (max_refund_days)
- Check requested amount is within min/max limits
- Ensure refund reason is in allowed reasons list
- Review policy configuration in `config.yaml`
- Check if partial refunds are allowed for the request

### Payment Processing Failures

**Problem**: Refunds fail to process through payment system.

**Solutions**:
- Verify payment provider API credentials in `.env`
- Check payment transaction ID is valid
- Ensure sufficient funds or credit available
- Review payment provider API status
- Check logs for specific payment error messages
- Verify network connectivity to payment provider

### Email Sending Failures

**Problem**: Confirmation emails are not being sent.

**Solutions**:
- Verify SMTP credentials in `.env` file
- For Gmail, ensure you're using an App Password
- Check firewall settings for SMTP port access
- Verify SMTP server hostname and port are correct
- Review email template path in configuration
- Check logs for email sending error messages

### Database Errors

**Problem**: Database connection or operation errors.

**Solutions**:
- Ensure SQLite is available (included with Python)
- Check file permissions for database file location
- Verify `DATABASE_URL` in `config.yaml` is correctly formatted
- Delete existing database file to recreate schema if needed

### Common Error Messages

- `Order not found`: Verify order ID exists in database
- `Customer email does not match order customer`: Check customer email matches order
- `Refund request exceeds maximum refund period`: Order is too old for refund
- `Requested amount exceeds order total`: Refund amount cannot exceed original order amount
- `Refund requires manual approval`: Refund amount exceeds auto-approval threshold
- `Payment processing failed`: Check payment provider API credentials and transaction ID

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
