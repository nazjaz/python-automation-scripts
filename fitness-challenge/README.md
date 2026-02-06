# Fitness Challenge

Automated fitness challenge system that generates personalized fitness challenges, sets goals, tracks progress, creates leaderboards, and sends motivational messages to participants.

## Project Description

This automation system provides a comprehensive fitness challenge platform for managing participants, generating personalized challenges and goals, tracking progress, maintaining leaderboards, and engaging participants with motivational messages. The system helps fitness coaches, gyms, and wellness programs automate challenge management and participant engagement.

### Target Audience

- Fitness coaches managing client challenges
- Gym managers running fitness competitions
- Wellness program coordinators
- Corporate wellness administrators
- Personal trainers tracking client progress

## Features

- **Personalized Challenge Generation**: Automatically generates fitness challenges tailored to participant fitness levels
- **Goal Setting**: Sets personalized fitness goals based on participant profiles and fitness levels
- **Progress Tracking**: Tracks progress entries for challenges and goals with detailed statistics
- **Leaderboard Generation**: Creates and maintains leaderboards for challenges with automatic ranking
- **Motivational Messages**: Sends personalized motivational, achievement, and reminder messages to participants
- **Comprehensive Reporting**: Generates HTML and CSV reports with participant statistics and leaderboards
- **Database Persistence**: Stores all participant data, challenges, goals, progress, and messages in SQLite database
- **Flexible Configuration**: Customizable challenge templates, goal templates, and message templates
- **Multi-Participant Support**: Manages multiple participants with individual progress tracking

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd fitness-challenge
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
DATABASE_URL=sqlite:///fitness_challenge.db
APP_NAME=Fitness Challenge
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize challenge templates, goal templates, message templates, and other settings:

```yaml
challenges:
  challenge_templates:
    steps:
      name: "Daily Steps Challenge"
      base_value: 10000
      duration_days: 7

goals:
  fitness_levels:
    beginner:
      default_goals:
        - type: "steps"
          target_value: 5000
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///fitness_challenge.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **challenges**: Challenge generation settings including templates, default duration, and base values
- **goals**: Goal setting configuration including templates, fitness level profiles, and default goals
- **progress**: Progress tracking settings
- **leaderboard**: Leaderboard generation settings including update frequency and ranking method
- **messages**: Message sending configuration including templates and delivery options
- **reporting**: Report generation settings including output formats and directory
- **logging**: Log file location, rotation, and format settings

## Usage

### Add Participant

Add a new participant to the system:

```bash
python src/main.py --add-participant "John Doe" "john@example.com" --fitness-level beginner --phone "+1234567890"
```

### Generate Challenges

Generate personalized challenges for a participant:

```bash
python src/main.py --generate-challenges 1 --challenge-count 3
```

### Set Goals

Set personalized goals for a participant:

```bash
python src/main.py --set-goals 1
```

### Record Progress

Record progress entry for a participant:

```bash
python src/main.py --record-progress 1 5000 steps --challenge-id 1
```

### Update Leaderboard

Update leaderboard for a challenge or globally:

```bash
python src/main.py --update-leaderboard --challenge-id 1
```

### Send Messages

Send motivational messages to participants:

```bash
python src/main.py --send-messages --participant-id 1 --message-type motivational
```

Send messages to all participants:

```bash
python src/main.py --send-messages --message-type reminder
```

### Generate Reports

Generate HTML and CSV reports:

```bash
python src/main.py --report --participant-id 1
```

### Complete Workflow

Run a complete workflow for a new participant:

```bash
# Add participant
python src/main.py --add-participant "Jane Doe" "jane@example.com" --fitness-level intermediate

# Generate challenges and set goals
python src/main.py --generate-challenges 1 --set-goals 1

# Record some progress
python src/main.py --record-progress 1 10000 steps

# Update leaderboard and send message
python src/main.py --update-leaderboard --send-messages --participant-id 1

# Generate report
python src/main.py --report --participant-id 1
```

### Command-Line Arguments

```
--add-participant NAME EMAIL    Add a new participant
--generate-challenges ID        Generate personalized challenges for participant
--set-goals ID                  Set personalized goals for participant
--record-progress ID VALUE UNIT Record progress entry
--update-leaderboard            Update leaderboard
--send-messages                 Send motivational messages
--report                        Generate analysis reports
--participant-id ID              Filter by participant ID
--challenge-id ID                Filter by challenge ID
--message-type TYPE             Message type (default: motivational)
--challenge-count COUNT         Number of challenges to generate (default: 3)
--phone PHONE                   Participant phone number
--fitness-level LEVEL           Fitness level (beginner, intermediate, advanced)
--config PATH                   Path to configuration file (default: config.yaml)
```

## Project Structure

```
fitness-challenge/
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
│   ├── challenge_generator.py # Challenge generation
│   ├── goal_setter.py         # Goal setting
│   ├── progress_tracker.py    # Progress tracking
│   ├── leaderboard_generator.py # Leaderboard generation
│   ├── message_sender.py       # Message sending
│   └── report_generator.py   # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── fitness_report.html   # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point that orchestrates participant management, challenge generation, goal setting, progress tracking, leaderboard updates, message sending, and reporting
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models and database operations for participants, challenges, goals, progress entries, leaderboards, and messages
- **src/challenge_generator.py**: Generates personalized fitness challenges based on participant profiles
- **src/goal_setter.py**: Sets and manages personalized fitness goals
- **src/progress_tracker.py**: Tracks progress entries and calculates statistics
- **src/leaderboard_generator.py**: Generates and maintains leaderboards for challenges
- **src/message_sender.py**: Sends motivational, achievement, and reminder messages to participants
- **src/report_generator.py**: Generates HTML and CSV reports with participant statistics and leaderboards
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

- Challenge generation functionality
- Goal setting logic
- Progress tracking algorithms
- Leaderboard generation
- Message sending
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

### Challenge Generation Issues

**Problem**: Challenges not being generated or seem incorrect.

**Solutions**:
- Verify participant exists and has fitness level set
- Check challenge templates in `config.yaml`
- Ensure participant ID is valid
- Review challenge generation settings

### Progress Tracking Issues

**Problem**: Progress not being recorded or calculated incorrectly.

**Solutions**:
- Verify participant ID, challenge ID, and goal ID are valid
- Check that value and unit match expected format
- Ensure progress entries are linked to correct challenge or goal
- Review progress tracking logic in logs

### Leaderboard Not Updating

**Problem**: Leaderboard shows incorrect rankings or doesn't update.

**Solutions**:
- Run `--update-leaderboard` command after recording progress
- Verify progress entries exist for participants
- Check leaderboard calculation logic
- Ensure challenge ID is correct if filtering by challenge

### Messages Not Sending

**Problem**: Messages are not being sent to participants.

**Solutions**:
- Check email/SMS settings in `config.yaml` (currently disabled by default)
- Verify participant has email or phone number set
- Review message templates configuration
- Check logs for message sending errors
- Note: Email and SMS functionality requires additional setup (not included by default)

### Report Generation Failures

**Problem**: Reports are not being generated or are incomplete.

**Solutions**:
- Ensure output directory exists and is writable
- Check that template file exists in `templates/` directory
- Verify sufficient data exists (participants, challenges, goals)
- Review logs for specific error messages
- Ensure all required dependencies are installed

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Participant not found`: Verify participant ID is correct and participant exists
- `Challenge not found`: Verify challenge ID is correct and challenge exists
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

## Challenge Types

The system supports various challenge types:

- **steps**: Daily steps challenges
- **distance**: Distance-based challenges (walking, running, cycling)
- **calories**: Calorie burn challenges
- **workouts**: Workout completion challenges

Challenge types can be customized in `config.yaml` by adding new templates with base values, units, and duration settings.

## Goal Types

The system supports various goal types:

- **weight_loss**: Weight loss goals
- **muscle_gain**: Muscle gain goals
- **steps**: Daily steps goals
- **distance**: Distance goals
- **calories**: Calorie goals

Goal types can be customized in `config.yaml` by adding new templates and fitness level profiles.

## Fitness Levels

The system supports three fitness levels with different default goals:

- **beginner**: Lower targets suitable for beginners
- **intermediate**: Moderate targets for intermediate participants
- **advanced**: Higher targets for advanced participants

Fitness level profiles can be customized in `config.yaml` to adjust default goals and challenge targets.

## Message Types

The system supports various message types:

- **motivational**: Encouraging messages to keep participants motivated
- **achievement**: Messages celebrating achievements and milestones
- **reminder**: Reminders to log progress or complete activities

Message templates can be customized in `config.yaml` with placeholders for participant name, progress, and achievements.

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
