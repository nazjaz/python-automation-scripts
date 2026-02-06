# Learning Recommender

Automated personalized learning recommendation system that analyzes user behavior, course completion rates, and learning objectives with adaptive difficulty to generate personalized learning recommendations.

## Project Description

This automation system provides comprehensive personalized learning recommendations for educational platforms. The system analyzes user behavior patterns, tracks course completion rates, monitors learning objectives, adapts difficulty levels based on performance, and generates personalized course recommendations. This helps learners discover relevant content, educators understand learning patterns, and platform administrators optimize course offerings.

### Target Audience

- Educational platform administrators managing course catalogs
- Learning management system (LMS) operators
- E-learning content creators optimizing course recommendations
- Educational data analysts studying learning patterns
- Individual learners seeking personalized learning paths

## Features

- **User Behavior Analysis**: Analyzes user behavior patterns including viewing, clicking, and searching behaviors with learning style identification
- **Completion Rate Analysis**: Tracks and analyzes course completion rates with trend identification
- **Adaptive Difficulty**: Automatically adapts difficulty levels based on user performance and skill assessment
- **Learning Objective Tracking**: Tracks user learning objectives and progress toward goals
- **Personalized Recommendations**: Generates personalized course recommendations based on behavior, objectives, and difficulty adaptation
- **Learning Style Detection**: Identifies user learning styles (exploratory, interactive, visual, structured, balanced)
- **Category Preferences**: Analyzes user preferences for different course categories
- **Comprehensive Reporting**: Generates HTML and CSV reports with learning profiles, recommendations, and progress
- **Database Persistence**: Stores all user data, courses, enrollments, progress, behaviors, objectives, and recommendations in SQLite database
- **Flexible Configuration**: Customizable analysis settings, difficulty thresholds, and recommendation parameters
- **Multi-User Support**: Supports multiple users with individual learning profiles and recommendations

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd learning-recommender
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
DATABASE_URL=sqlite:///learning_recommender.db
APP_NAME=Learning Recommender
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize behavior analysis, difficulty adaptation, and recommendation settings:

```yaml
difficulty_adaptation:
  score_thresholds:
    beginner: 0.7
    intermediate: 0.75
    advanced: 0.8

recommendations:
  min_confidence: 0.5
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///learning_recommender.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **behavior_analysis**: User behavior analysis configuration
- **completion_analysis**: Course completion rate analysis settings
- **difficulty_adaptation**: Adaptive difficulty settings including score thresholds
- **objective_tracking**: Learning objective tracking configuration
- **recommendations**: Recommendation generation settings including minimum confidence
- **reporting**: Report generation settings including output formats and directory
- **logging**: Log file location, rotation, and format settings

## Usage

### Analyze User Behavior

Analyze user behavior patterns:

```bash
python src/main.py --analyze-behavior user1
```

### Analyze Completion Rates

Analyze course completion rates:

```bash
python src/main.py --analyze-completion course1 --days 30
```

### Adapt Difficulty

Adapt difficulty level for user and course:

```bash
python src/main.py --adapt-difficulty user1 course1
```

### Track Learning Objectives

Track user learning objectives:

```bash
python src/main.py --track-objectives user1
```

### Generate Recommendations

Generate personalized learning recommendations:

```bash
python src/main.py --generate-recommendations user1 --limit 10
```

### Generate Reports

Generate HTML and CSV reports:

```bash
python src/main.py --report --user-id user1
```

### Complete Workflow

Run complete learning recommendation workflow:

```bash
# Analyze user behavior
python src/main.py --analyze-behavior user1

# Track objectives
python src/main.py --track-objectives user1

# Generate personalized recommendations
python src/main.py --generate-recommendations user1 --limit 10

# Generate reports
python src/main.py --report --user-id user1
```

### Command-Line Arguments

```
--analyze-behavior USER_ID        Analyze user behavior
--analyze-completion COURSE_ID    Analyze course completion rates
--adapt-difficulty USER_ID COURSE_ID  Adapt difficulty level
--track-objectives USER_ID        Track learning objectives
--generate-recommendations USER_ID Generate personalized recommendations
--report                          Generate analysis reports
--user-id USER_ID                 Filter by user ID
--limit LIMIT                     Maximum number of recommendations (default: 10)
--days DAYS                       Number of days to analyze
--config PATH                     Path to configuration file (default: config.yaml)
```

## Project Structure

```
learning-recommender/
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
│   ├── behavior_analyzer.py  # User behavior analysis
│   ├── completion_analyzer.py # Completion rate analysis
│   ├── difficulty_adapter.py # Adaptive difficulty
│   ├── objective_tracker.py  # Learning objective tracking
│   ├── recommendation_generator.py # Recommendation generation
│   └── report_generator.py  # Report generation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── learning_report.html  # HTML report template
├── docs/                     # Documentation
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point that orchestrates behavior analysis, completion analysis, difficulty adaptation, objective tracking, recommendation generation, and reporting
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models and database operations for users, courses, enrollments, progress, behaviors, objectives, recommendations, and completion rates
- **src/behavior_analyzer.py**: Analyzes user behavior patterns and identifies learning styles
- **src/completion_analyzer.py**: Analyzes course completion rates and trends
- **src/difficulty_adapter.py**: Adapts difficulty levels based on user performance
- **src/objective_tracker.py**: Tracks learning objectives and progress
- **src/recommendation_generator.py**: Generates personalized learning recommendations
- **src/report_generator.py**: Generates HTML and CSV reports with learning data
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

- User behavior analysis functionality
- Completion rate analysis algorithms
- Difficulty adaptation logic
- Objective tracking
- Recommendation generation
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

### No Behavior Data

**Problem**: Behavior analysis returns no results.

**Solutions**:
- Verify user behaviors have been recorded
- Check that user ID is correct
- Ensure behavior data exists in database
- Review behavior analysis settings

### No Recommendations Generated

**Problem**: Recommendation generation returns no results.

**Solutions**:
- Verify user has sufficient behavior data
- Check that courses exist in database
- Ensure minimum confidence threshold is appropriate
- Review recommendation generation settings
- Lower minimum confidence threshold if needed

### Difficulty Adaptation Issues

**Problem**: Difficulty adaptation not working correctly.

**Solutions**:
- Verify user has enrollment and progress data
- Check that course difficulty levels are set
- Ensure score thresholds are appropriate
- Review difficulty adaptation settings
- Verify user performance scores are being calculated

### Objective Tracking Problems

**Problem**: Objective tracking not showing progress.

**Solutions**:
- Verify learning objectives are defined
- Check that user has enrollments in relevant courses
- Ensure course categories match objective target skills
- Review objective tracking settings

### Report Generation Failures

**Problem**: Reports are not being generated or are incomplete.

**Solutions**:
- Ensure output directory exists and is writable
- Check that template file exists in `templates/` directory
- Verify sufficient user data exists
- Review logs for specific error messages
- Ensure all required dependencies are installed

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `User not found`: Verify user ID is correct and user exists
- `Course not found`: Verify course ID is correct and course exists
- `No recommendations generated`: Check that user has sufficient data and courses exist
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

## Learning Styles

The system identifies various learning styles:

- **exploratory**: Users who frequently search and explore content
- **interactive**: Users who engage with interactive elements
- **visual**: Users who primarily view content
- **structured**: Users with high completion rates
- **balanced**: Users with mixed learning patterns

Learning styles are determined based on behavior ratios and completion rates.

## Difficulty Levels

The system supports three difficulty levels:

- **beginner**: Entry-level courses for new learners
- **intermediate**: Courses for learners with some experience
- **advanced**: Advanced courses for experienced learners

Difficulty adaptation is based on user performance scores and completion rates.

## Recommendation Types

The system generates various recommendation types:

- **general**: General recommendations based on behavior
- **difficulty_match**: Recommendations matching user's skill level
- **objective_aligned**: Recommendations aligned with learning objectives
- **objective_based**: Recommendations specifically for objectives

Recommendations are prioritized (low, medium, high) and include confidence scores.

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
