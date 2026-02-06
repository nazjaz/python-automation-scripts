# Event Registration System

Automated event registration system that processes event registrations, sends confirmation emails, generates attendee lists, creates name badges, and manages waitlists with capacity tracking.

## Project Description

This automation system streamlines event registration management by automating key tasks including registration processing, email confirmations, attendee list generation, badge creation, and waitlist management. The system provides capacity tracking to ensure events don't exceed limits and automatically manages waitlists when events are full.

### Target Audience

- Event organizers managing registrations
- Conference coordinators handling attendee management
- Marketing teams organizing events
- Administrative staff processing event registrations

## Features

- **Event Management**: Create and manage events with capacity limits and waitlist options
- **Registration Processing**: Automatically process registrations with capacity tracking
- **Confirmation Emails**: Send automated confirmation emails with HTML templates
- **Waitlist Management**: Automatically manage waitlists with position tracking and promotion
- **Attendee Lists**: Generate CSV and HTML attendee lists with optional waitlist inclusion
- **Name Badges**: Generate printable name badges in HTML format
- **Capacity Tracking**: Real-time capacity monitoring and automatic waitlist activation
- **Database Persistence**: Stores all event and registration data in SQLite database

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)
- SMTP server access (for email functionality)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd event-registration
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
DATABASE_URL=sqlite:///event_registration.db
APP_NAME=Event Registration System
LOG_LEVEL=INFO

SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
```

**Note**: For Gmail, you'll need to generate an App Password instead of your regular password. Enable 2-factor authentication and generate an app-specific password.

### Step 5: Configure Application Settings

Edit `config.yaml` to customize email templates, badge settings, and registration options:

```yaml
events:
  default_capacity: 100
  allow_waitlist: true
  auto_confirm: true

registration:
  confirmation_email:
    enabled: true
    subject: "Event Registration Confirmation - {{event_name}}"
    template: "templates/confirmation_email.html"
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///event_registration.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |
| `SMTP_USERNAME` | SMTP authentication username | Yes (for email) |
| `SMTP_PASSWORD` | SMTP authentication password | Yes (for email) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **events**: Default event settings including capacity and waitlist options
- **registration**: Registration processing settings and email templates
- **badges**: Badge generation settings and templates
- **waitlist**: Waitlist management settings
- **email**: SMTP server configuration
- **logging**: Log file location, rotation, and format settings

## Usage

### Create an Event

Create a new event:

```bash
python src/main.py --create-event --name "Tech Conference 2024" --event-date "2024-06-15 09:00" --location "Convention Center" --capacity 200
```

### Register an Attendee

Register an attendee for an event:

```bash
python src/main.py --register --event-id 1 --name "John Doe" --email "john@example.com" --company "Tech Corp" --ticket-type "VIP"
```

### Generate Attendee List

Generate attendee list in CSV format:

```bash
python src/main.py --generate-list --event-id 1 --format csv
```

Generate attendee list in HTML format with waitlist:

```bash
python src/main.py --generate-list --event-id 1 --format html --include-waitlist
```

### Generate Name Badges

Generate badges for all confirmed attendees:

```bash
python src/main.py --generate-badges --event-id 1
```

Generate badge for specific registration:

```bash
python src/main.py --generate-badges --event-id 1 --registration-id 5
```

### Command-Line Arguments

```
--create-event          Create a new event
--name NAME            Event name or registrant name
--event-date DATE      Event date and time (ISO format or YYYY-MM-DD HH:MM)
--location LOCATION    Event location
--description DESC     Event description
--capacity N           Event capacity (default: 100)
--allow-waitlist     Allow waitlist (default: True)

--register             Register an attendee
--event-id ID          Event ID (required for registration)
--email EMAIL          Registrant email address (required)
--company COMPANY      Company name
--phone PHONE          Phone number
--ticket-type TYPE     Ticket type
--dietary-restrictions RESTRICTIONS  Dietary restrictions
--special-requests REQUESTS          Special requests

--generate-list        Generate attendee list
--include-waitlist     Include waitlist in attendee list
--format FORMAT        Output format: csv or html (default: csv)

--generate-badges       Generate name badges
--registration-id ID   Specific registration ID for badge generation

--config PATH          Path to configuration file (default: config.yaml)
```

## Project Structure

```
event-registration/
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
│   ├── registration_processor.py # Registration processing
│   ├── email_service.py      # Email sending service
│   ├── badge_generator.py    # Badge generation
│   └── attendee_list_generator.py # Attendee list generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Email and badge templates
│   ├── confirmation_email.html
│   ├── waitlist_email.html
│   ├── badge_template.html
│   └── attendee_list.html
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point with CLI interface for all operations
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models for events and registrations
- **src/registration_processor.py**: Processes registrations with capacity tracking and waitlist management
- **src/email_service.py**: Sends confirmation and waitlist notification emails
- **src/badge_generator.py**: Generates printable name badges
- **src/attendee_list_generator.py**: Generates CSV and HTML attendee lists
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
- Registration processing and capacity tracking
- Waitlist management
- Email service functionality
- Badge generation
- Attendee list generation
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

### Email Sending Failures

**Problem**: Confirmation emails are not being sent.

**Solutions**:
- Verify SMTP credentials in `.env` file
- For Gmail, ensure you're using an App Password, not your regular password
- Check firewall settings for SMTP port access
- Verify SMTP server hostname and port are correct
- Review logs in `logs/event_registration.log` for detailed error messages

### Registration Not Processing

**Problem**: Registrations are not being processed or confirmed.

**Solutions**:
- Verify event exists and is active
- Check event capacity and current registration count
- Ensure `auto_confirm` is enabled in `config.yaml` if immediate confirmation is desired
- Review registration status in database
- Check logs for processing errors

### Waitlist Not Working

**Problem**: Waitlist is not being created when event is full.

**Solutions**:
- Verify `allow_waitlist` is enabled for the event
- Check that event capacity is correctly set
- Ensure registration count is being updated correctly
- Review waitlist configuration in `config.yaml`

### Badge Generation Failures

**Problem**: Badges are not being generated.

**Solutions**:
- Verify badge template exists in `templates/` directory
- Check that registration status is "confirmed"
- Ensure output directory is writable
- Review badge configuration in `config.yaml`
- Check logs for generation errors

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Event not found`: Verify event ID exists in database
- `Registration already exists`: Email address already registered for this event
- `Event is full and waitlist is not available`: Event at capacity and waitlist disabled
- `SMTP credentials not configured`: Set `SMTP_USERNAME` and `SMTP_PASSWORD` in `.env`

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

## Waitlist Management

The system automatically manages waitlists:

1. **Automatic Waitlist**: When event reaches capacity, new registrations are added to waitlist
2. **Position Tracking**: Waitlist positions are automatically assigned and updated
3. **Auto-Promotion**: When a confirmed registration is cancelled, the first waitlist registrant is automatically promoted
4. **Notifications**: Waitlist registrants receive email notifications with their position

## Capacity Tracking

The system tracks event capacity in real-time:

- **Current Registrations**: Automatically updated when registrations are confirmed or cancelled
- **Available Spots**: Calculated as capacity minus current registrations
- **Waitlist Activation**: Automatically activates when available spots reach zero
- **Automatic Promotion**: Promotes waitlist registrants when spots become available

## Email Templates

Email templates use Jinja2 templating and support:

- **Confirmation Email**: Sent to confirmed registrants with event details
- **Waitlist Email**: Sent to waitlisted registrants with position information
- **Customizable**: Templates can be customized in `templates/` directory
- **Variables**: Support for event name, date, location, registrant info, etc.

## Badge Generation

Badges are generated as HTML files suitable for printing:

- **Standard Size**: 3.375" x 2.125" (standard badge size)
- **Printable**: Optimized for printing with proper page size
- **Customizable**: Template can be customized in `templates/badge_template.html`
- **Information**: Includes name, company, ticket type, and event name

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
