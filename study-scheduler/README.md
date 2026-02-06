# Study Scheduler

Automated study schedule generator that creates personalized study schedules based on exam dates, course load, and learning preferences, with progress tracking and adjustment recommendations.

## Project Description

This automation system helps students and learners create optimized study schedules by analyzing exam dates, course requirements, and individual learning preferences. It tracks study progress, identifies areas needing attention, and provides intelligent recommendations for schedule adjustments and learning method improvements.

### Target Audience

- Students managing multiple courses and exams
- Learners preparing for standardized tests
- Professionals studying for certifications
- Anyone needing structured study planning

## Features

- **Personalized Schedule Generation**: Creates study schedules based on exam dates, course load, and learning preferences
- **Exam Date Integration**: Automatically prioritizes study sessions based on upcoming exam dates
- **Learning Preferences**: Supports different study styles (visual, auditory, kinesthetic, reading/writing)
- **Progress Tracking**: Tracks daily and weekly study progress with completion rates
- **Adjustment Recommendations**: Provides intelligent recommendations for schedule and learning method improvements
- **Course Management**: Manages multiple courses with different difficulty levels and priorities
- **Time Optimization**: Optimizes study time allocation across courses based on exam proximity and priority
- **Progress Reports**: Generates HTML and CSV reports of study schedules and progress

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd study-scheduler
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
DATABASE_URL=sqlite:///study_scheduler.db
APP_NAME=Study Scheduler
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize scheduling preferences, study styles, and tracking options:

```yaml
scheduling:
  default_study_hours_per_day: 4
  study_session_duration_minutes: 90
  preferred_study_times:
    - "09:00"
    - "14:00"
    - "19:00"

learning_preferences:
  study_styles:
    - "visual"
    - "auditory"
    - "kinesthetic"
    - "reading_writing"
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///study_scheduler.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **scheduling**: Default study hours, session duration, preferred times, break frequency
- **learning_preferences**: Study styles, review frequency, active recall, spaced repetition
- **progress_tracking**: Completion thresholds, adjustment thresholds, tracking intervals
- **recommendations**: Recommendation generation settings and intervals
- **courses**: Default difficulty and priority levels
- **logging**: Log file location, rotation, and format settings

## Usage

### Add a Course

Add a course to the system:

```bash
python src/main.py --add-course --name "Introduction to Computer Science" --code "CS101" --difficulty "medium" --priority "high" --total-hours 40
```

### Add an Exam

Add an exam for a course:

```bash
python src/main.py --add-exam --course-id 1 --name "Midterm Exam" --exam-date "2024-06-15" --prep-hours 20
```

### Set Learning Preferences

Set your learning preferences:

```bash
python src/main.py --set-preferences --study-style "reading_writing" --daily-hours 4 --preferred-times "09:00,14:00,19:00" --break-frequency 90 --review-frequency 7
```

### Generate Study Schedule

Generate a personalized study schedule:

```bash
python src/main.py --generate-schedule --start-date "2024-05-01" --end-date "2024-06-15"
```

### Track Progress

Record progress for a study session:

```bash
python src/main.py --track-progress --session-id 1 --hours-studied 1.5 --completion-percentage 1.0 --topics-mastered 3
```

### Get Recommendations

Get adjustment recommendations:

```bash
python src/main.py --get-recommendations --recommendation-days 7
```

### Generate Report

Generate study schedule report:

```bash
python src/main.py --generate-report --start-date "2024-05-01" --end-date "2024-06-15" --format html
```

### Command-Line Arguments

```
--add-course              Add a course
--name NAME               Course name or exam name
--code CODE               Course code
--difficulty LEVEL        Course difficulty (easy, medium, hard)
--priority LEVEL          Course priority (low, medium, high, critical)
--total-hours HOURS       Total hours required for course

--add-exam                Add an exam
--course-id ID            Course ID (required)
--exam-date DATE          Exam date (YYYY-MM-DD, required)
--exam-type TYPE          Exam type
--weight PERCENTAGE        Exam weight percentage
--prep-hours HOURS         Preparation hours required

--set-preferences         Set learning preferences
--study-style STYLE       Study style (visual, auditory, kinesthetic, reading_writing)
--daily-hours HOURS       Daily study hours
--preferred-times TIMES    Preferred study times (comma-separated)
--break-frequency MIN      Break frequency in minutes
--review-frequency DAYS    Review frequency in days

--generate-schedule        Generate study schedule
--start-date DATE          Start date (YYYY-MM-DD)
--end-date DATE            End date (YYYY-MM-DD)

--track-progress           Record study session progress
--session-id ID            Study session ID (required)
--hours-studied HOURS      Hours studied (required)
--completion-percentage P  Completion percentage (0.0 to 1.0)
--topics-mastered COUNT     Number of topics mastered
--topics-reviewed COUNT     Number of topics reviewed

--get-recommendations      Get adjustment recommendations
--recommendation-days DAYS Days to analyze (default: 7)

--generate-report          Generate study schedule report
--format FORMAT            Report format (html or csv, default: html)

--config PATH              Path to configuration file (default: config.yaml)
```

## Project Structure

```
study-scheduler/
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
│   ├── schedule_generator.py # Schedule generation
│   ├── progress_tracker.py   # Progress tracking
│   ├── recommendation_engine.py # Recommendation generation
│   └── report_generator.py   # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── study_schedule.html    # HTML schedule template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point with CLI interface for all operations
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models for courses, exams, study sessions, and progress
- **src/schedule_generator.py**: Generates personalized study schedules based on preferences
- **src/progress_tracker.py**: Tracks study progress and completion rates
- **src/recommendation_engine.py**: Generates recommendations for schedule and method adjustments
- **src/report_generator.py**: Generates HTML and CSV study schedule reports
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
- Schedule generation algorithms
- Progress tracking and calculation
- Recommendation generation
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

### Schedule Not Generated

**Problem**: No study schedule is generated.

**Solutions**:
- Ensure courses and exams have been added to the system
- Verify exam dates are in the future
- Check that learning preferences are set
- Review date range parameters (start-date and end-date)
- Ensure courses have total_hours_required set

### Progress Not Tracking

**Problem**: Progress is not being recorded or updated.

**Solutions**:
- Verify study session ID exists in database
- Check that hours_studied is provided
- Ensure session completion_status is being updated
- Review progress tracking configuration
- Check logs for recording errors

### Recommendations Not Generated

**Problem**: No recommendations are being generated.

**Solutions**:
- Verify recommendation generation is enabled in `config.yaml`
- Ensure sufficient study sessions exist for analysis
- Check that progress has been tracked
- Review recommendation thresholds
- Check logs for generation errors

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Course not found`: Verify course ID exists in database
- `Exam date must be in the future`: Check exam date is after today
- `Invalid date format`: Use YYYY-MM-DD format for dates
- `Session not found`: Verify study session ID exists

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

## Schedule Generation Algorithm

The schedule generator uses a priority-based algorithm:

1. **Exam Proximity**: Sessions are prioritized based on days until exam
2. **Course Priority**: Higher priority courses get more study time
3. **Difficulty Weighting**: Harder courses receive additional time allocation
4. **Completion Status**: Courses with lower completion rates get priority
5. **Time Preferences**: Sessions are scheduled at preferred study times
6. **Daily Limits**: Respects maximum daily study hours

## Learning Preferences

The system supports various learning preferences:

- **Study Styles**: Visual, Auditory, Kinesthetic, Reading/Writing
- **Preferred Times**: Customizable study time slots
- **Daily Hours**: Configurable daily study hour limits
- **Break Frequency**: Automatic break scheduling
- **Review Frequency**: Spaced repetition intervals
- **Active Recall**: Enable/disable active recall techniques
- **Spaced Repetition**: Enable/disable spaced repetition

## Progress Tracking

The system tracks:

- **Session Completion**: Whether scheduled sessions were completed
- **Hours Studied**: Actual hours spent studying
- **Topics Mastered**: Number of topics fully understood
- **Topics Reviewed**: Number of topics reviewed
- **Completion Rates**: Daily, weekly, and course-level completion rates
- **Effectiveness Ratings**: Optional session effectiveness ratings

## Recommendations

The recommendation engine provides:

- **Schedule Adjustments**: Suggestions for improving completion rates
- **Exam Preparation**: Warnings for upcoming exams needing more preparation
- **Load Balance**: Suggestions for balancing study time across courses
- **Learning Methods**: Recommendations for improving study effectiveness
- **Time Management**: Tips for better time allocation

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
