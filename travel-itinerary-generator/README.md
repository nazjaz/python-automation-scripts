# Travel Itinerary Generator

Automated travel itinerary generation system that integrates flight, hotel, and activity bookings, sends reminders, and provides real-time travel updates.

## Project Description

This automation system streamlines travel planning by automatically generating personalized itineraries from flight, hotel, and activity bookings. The system sends timely reminders, monitors for travel updates (gate changes, delays, etc.), and generates professional itinerary documents in multiple formats.

### Target Audience

- Travel agencies managing multiple client itineraries
- Corporate travel departments
- Personal travel planners
- Travel management platforms

## Features

- **Multi-Booking Integration**: Seamlessly integrates flight, hotel, and activity bookings
- **Automated Reminders**: Sends email reminders at configurable intervals before trips
- **Real-Time Updates**: Monitors and notifies about flight changes, gate updates, and delays
- **Document Generation**: Creates professional HTML and PDF itineraries
- **Database Storage**: Persistent storage of all bookings and itineraries
- **Email Notifications**: Automated email notifications for reminders and updates
- **Configurable**: Flexible configuration for different API providers and notification preferences

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SMTP server access (Gmail, Outlook, or custom SMTP server)
- API keys for flight, hotel, and activity booking services (optional for testing)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd travel-itinerary-generator
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
FLIGHT_API_KEY=your-flight-api-key
FLIGHT_API_SECRET=your-flight-api-secret
HOTEL_API_KEY=your-hotel-api-key
ACTIVITY_API_KEY=your-activity-api-key

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@example.com
```

**Note**: For Gmail, you'll need to generate an App Password instead of your regular password. Enable 2-factor authentication and generate an app-specific password.

### Step 5: Configure Application Settings

Edit `config.yaml` to customize API providers, reminder schedules, and output formats:

```yaml
itinerary:
  reminder_hours_before: [72, 24, 2]
  output_format: ["html", "pdf"]
  output_directory: "itineraries"

flights:
  api_provider: "amadeus"
  check_in_reminder_hours: 24
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FLIGHT_API_KEY` | Flight booking API key | Yes |
| `FLIGHT_API_SECRET` | Flight booking API secret | Yes |
| `HOTEL_API_KEY` | Hotel booking API key | Yes |
| `ACTIVITY_API_KEY` | Activity booking API key | Yes |
| `SMTP_HOST` | SMTP server hostname | Yes |
| `SMTP_PORT` | SMTP server port | Yes |
| `SMTP_USERNAME` | SMTP username | Yes |
| `SMTP_PASSWORD` | SMTP password | Yes |
| `SMTP_FROM_EMAIL` | Sender email address | Yes |
| `SMS_API_KEY` | SMS API key (optional) | No |
| `SMS_API_SECRET` | SMS API secret (optional) | No |
| `SMS_FROM_NUMBER` | SMS sender number (optional) | No |

### Configuration File (config.yaml)

The `config.yaml` file contains:

- **itinerary**: Itinerary generation settings, reminder schedules, output formats
- **flights**: Flight booking API configuration and reminder settings
- **hotels**: Hotel booking API configuration and reminder settings
- **activities**: Activity booking API configuration
- **notifications**: Email and SMS notification settings
- **database**: Database connection URL
- **logging**: Log file configuration

## Usage

### Create New Itinerary

```bash
python src/main.py --create \
  --name "John Doe" \
  --email "john@example.com" \
  --start-date "2024-06-01 10:00" \
  --end-date "2024-06-07 18:00" \
  --destination "Paris"
```

### Process Reminders

Send due reminders to travelers:

```bash
python src/main.py --reminders
```

### Check for Updates

Check for travel updates (gate changes, delays, etc.):

```bash
python src/main.py --updates
```

### Command-Line Arguments

```
--create              Create new itinerary
--name NAME          Traveler name (required for create)
--email EMAIL        Traveler email (required for create)
--phone PHONE        Traveler phone (optional)
--start-date DATE    Trip start date (YYYY-MM-DD HH:MM)
--end-date DATE      Trip end date (YYYY-MM-DD HH:MM)
--destination DEST   Trip destination (required for create)
--reminders          Process and send due reminders
--updates            Check for travel updates
--config PATH        Path to configuration file (optional)
```

## Project Structure

```
travel-itinerary-generator/
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
│   ├── flight_service.py    # Flight booking integration
│   ├── hotel_service.py     # Hotel booking integration
│   ├── activity_service.py  # Activity booking integration
│   ├── notification_service.py # Email and SMS notifications
│   ├── reminder_service.py  # Reminder scheduling and sending
│   ├── update_checker.py    # Real-time update checking
│   └── itinerary_generator.py # Itinerary document generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                 # Document templates
│   └── itinerary.html        # HTML itinerary template
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main orchestrator that coordinates itinerary creation and management
- **src/config.py**: Configuration loading with environment variable substitution
- **src/database.py**: SQLAlchemy models for storing itineraries and bookings
- **src/flight_service.py**: Flight search and booking integration
- **src/hotel_service.py**: Hotel search and booking integration
- **src/activity_service.py**: Activity search and booking integration
- **src/notification_service.py**: Email and SMS notification sending
- **src/reminder_service.py**: Reminder scheduling and processing
- **src/update_checker.py**: Real-time travel update monitoring
- **src/itinerary_generator.py**: HTML and PDF itinerary generation

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

- Flight, hotel, and activity service functionality
- Notification service with email sending
- Reminder scheduling and processing
- Itinerary generation
- Database operations

## Troubleshooting

### Email Sending Failures

**Problem**: Reminders or notifications are not being sent.

**Solutions**:
- Verify SMTP credentials in `.env` file
- For Gmail, ensure you're using an App Password, not your regular password
- Check firewall settings for SMTP port access
- Verify SMTP server hostname and port are correct
- Review logs in `logs/itinerary.log` for detailed error messages

### API Integration Issues

**Problem**: Flight, hotel, or activity searches return no results.

**Solutions**:
- Verify API keys are correct in `.env` file
- Check API provider documentation for required parameters
- Review API rate limits and quotas
- Test API connectivity using API provider's test tools
- Check logs for API error messages

### Database Errors

**Problem**: Database connection or operation errors.

**Solutions**:
- Ensure SQLite is available (included with Python)
- Check file permissions for database file location
- Verify `DATABASE_URL` in `config.yaml` is correctly formatted
- Delete existing database file to recreate schema if needed

### Itinerary Generation Issues

**Problem**: Itineraries are not being generated or are incomplete.

**Solutions**:
- Verify output directory exists and is writable
- Check disk space availability
- Ensure required dependencies are installed (reportlab for PDF)
- Review template file paths in configuration
- Check logs for template rendering errors

### Reminder Not Sending

**Problem**: Reminders are scheduled but not being sent.

**Solutions**:
- Run `--reminders` command to process due reminders
- Verify reminder times are in the future when scheduling
- Check email configuration is correct
- Review logs for reminder processing errors
- Ensure system time is synchronized

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Itinerary not found`: Verify itinerary ID exists in database
- `Failed to send email`: Check SMTP configuration and credentials
- `API error`: Verify API keys and check API provider status

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
