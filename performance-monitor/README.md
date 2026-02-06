# Performance Monitor

Automated employee performance monitoring system that monitors performance metrics, tracks goal completion, generates performance reviews, and identifies training needs with development plans.

## Project Description

This automation system provides comprehensive employee performance management capabilities. It continuously monitors employee performance metrics across multiple dimensions, tracks goal completion and identifies overdue goals, automatically generates performance reviews with detailed analysis, and identifies training needs to create personalized development plans for employee growth.

### Target Audience

- HR departments managing employee performance
- People managers tracking team performance
- Performance management teams conducting reviews
- Learning and development teams identifying training needs

## Features

- **Performance Monitoring**: Tracks multiple performance metrics (productivity, quality, attendance, collaboration, innovation)
- **Goal Tracking**: Monitors goal completion, identifies overdue goals, calculates completion rates
- **Performance Reviews**: Automatically generates comprehensive performance reviews with ratings and recommendations
- **Training Needs Identification**: Identifies training needs based on performance gaps and goal requirements
- **Development Plans**: Creates personalized development plans with objectives, milestones, and resources
- **Multi-Metric Analysis**: Calculates overall performance scores from multiple metrics
- **Rating Categories**: Classifies performance as excellent, good, satisfactory, needs improvement, or poor
- **HTML Reports**: Generates formatted HTML performance review documents

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd performance-monitor
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
DATABASE_URL=sqlite:///performance_monitor.db
APP_NAME=Performance Monitor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize performance thresholds, goal settings, and review options:

```yaml
performance:
  performance_thresholds:
    excellent: 0.90
    good: 0.75
    satisfactory: 0.60

goals:
  overdue_threshold_days: 7
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///performance_monitor.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **performance**: Metrics to track, evaluation periods, performance thresholds
- **goals**: Goal types, statuses, auto-check intervals, overdue thresholds
- **reviews**: Review types, generation settings, template configuration
- **training**: Skill categories, training types, priority levels, identification criteria
- **development_plans**: Plan duration, milestone settings, review frequency
- **reporting**: Output formats, directory, inclusion options
- **logging**: Log file location, rotation, and format settings

## Usage

### Add Employee

Add an employee to the system:

```bash
python src/main.py --add-employee --employee-id "EMP001" --name "John Doe" --email "john@example.com" --department "Engineering" --position "Software Engineer"
```

### Add Performance Metric

Add a performance metric:

```bash
python src/main.py --add-metric --employee-id "EMP001" --metric-type "productivity" --value 85.0 --target-value 80.0
```

### Track Goals

Track goal completion:

```bash
python src/main.py --track-goals --employee-id "EMP001"
```

### Monitor Performance

Monitor employee performance:

```bash
python src/main.py --monitor-performance --employee-id "EMP001"
```

### Generate Performance Review

Generate a performance review:

```bash
python src/main.py --generate-review --employee-id "EMP001" --review-type "quarterly" --output "reviews/review_EMP001.html"
```

### Identify Training Needs

Identify training needs:

```bash
python src/main.py --identify-training --employee-id "EMP001"
```

### Create Development Plan

Create a development plan:

```bash
python src/main.py --create-plan --employee-id "EMP001" --plan-title "Professional Development Plan 2024"
```

### Complete Workflow

Run complete performance management workflow:

```bash
# Add employee
python src/main.py --add-employee --employee-id "EMP001" --name "John Doe" --email "john@example.com"

# Add metrics
python src/main.py --add-metric --employee-id "EMP001" --metric-type "productivity" --value 85.0 --target-value 80.0
python src/main.py --add-metric --employee-id "EMP001" --metric-type "quality" --value 90.0 --target-value 85.0

# Monitor performance
python src/main.py --monitor-performance --employee-id "EMP001"

# Track goals
python src/main.py --track-goals --employee-id "EMP001"

# Generate review
python src/main.py --generate-review --employee-id "EMP001" --review-type "quarterly"

# Identify training needs
python src/main.py --identify-training --employee-id "EMP001"

# Create development plan
python src/main.py --create-plan --employee-id "EMP001"
```

### Command-Line Arguments

```
--add-employee              Add an employee
--employee-id ID            Employee ID (required)
--name NAME                 Employee name (required)
--email EMAIL               Employee email (required)
--department DEPT           Department
--position POS              Position

--add-metric                Add performance metric
--employee-id ID            Employee ID (required)
--metric-type TYPE          Metric type (required)
--value VALUE               Metric value (required)
--metric-date DATE          Metric date (YYYY-MM-DD)
--target-value VALUE        Target value

--track-goals               Track goal completion
--employee-id ID            Optional employee ID filter

--monitor-performance       Monitor employee performance
--employee-id ID           Employee ID (required)

--generate-review           Generate performance review
--employee-id ID            Employee ID (required)
--review-type TYPE          Review type: quarterly, annual, mid_year, probationary (required)
--output PATH               Output file path

--identify-training         Identify training needs
--employee-id ID            Employee ID (required)

--create-plan               Create development plan
--employee-id ID            Employee ID (required)
--plan-title TITLE          Development plan title

--config PATH               Path to configuration file (default: config.yaml)
```

## Project Structure

```
performance-monitor/
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
│   ├── performance_monitor.py # Performance monitoring
│   ├── goal_tracker.py       # Goal tracking
│   ├── review_generator.py   # Performance review generation
│   └── training_analyzer.py  # Training needs and development plans
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Report templates
│   └── performance_review.html # HTML review template
├── docs/                     # Documentation
├── reports/                  # Generated reports
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point with CLI interface for all operations
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models for employees, metrics, goals, reviews, training needs, development plans
- **src/performance_monitor.py**: Monitors and calculates performance scores from metrics
- **src/goal_tracker.py**: Tracks goal completion and identifies overdue goals
- **src/review_generator.py**: Generates comprehensive performance reviews
- **src/training_analyzer.py**: Identifies training needs and creates development plans
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
- Performance monitoring and score calculation
- Goal tracking and completion analysis
- Review generation logic
- Training needs identification
- Development plan creation
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

### Employee Not Found Errors

**Problem**: Employee ID not found in database.

**Solutions**:
- Verify employee exists using `--add-employee` first
- Check employee ID spelling and format
- Ensure employee is active (not deactivated)
- Review logs for specific error messages

### Performance Score Calculation Issues

**Problem**: Performance scores showing unexpected values.

**Solutions**:
- Verify metrics have been added for the employee
- Check metric values and target values are correct
- Ensure evaluation period includes metric dates
- Review performance thresholds in configuration
- Check logs for calculation details

### Goal Tracking Issues

**Problem**: Goals not being tracked or updated correctly.

**Solutions**:
- Verify goals have been created for the employee
- Check goal dates (start_date, due_date) are correct
- Ensure goal status values are valid
- Review overdue threshold settings
- Check logs for tracking errors

### Review Generation Failures

**Problem**: Performance reviews not being generated.

**Solutions**:
- Verify employee has sufficient metrics for review
- Check review period dates are valid
- Ensure template file exists or default template is used
- Verify output directory permissions
- Review logs for generation errors

### Training Needs Not Identified

**Problem**: No training needs being identified.

**Solutions**:
- Verify employee has performance metrics recorded
- Check performance scores are below thresholds
- Ensure goal completion data exists
- Review training identification criteria in configuration
- Check logs for identification process

### Common Error Messages

- `Configuration file not found`: Ensure `config.yaml` exists in project root
- `Failed to load settings`: Check that all required environment variables are set in `.env`
- `Employee not found`: Verify employee ID exists in database
- `Goal not found`: Verify goal ID exists in database
- `Insufficient data for review`: Ensure employee has metrics and goals recorded
- `No training needs identified`: Check that performance gaps exist

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

## Performance Metrics

The system tracks the following performance metrics:

- **Productivity**: Measures output and efficiency
- **Quality**: Measures work quality and accuracy
- **Attendance**: Tracks attendance and punctuality
- **Collaboration**: Measures teamwork and collaboration
- **Innovation**: Tracks innovative contributions

## Performance Ratings

Performance is rated based on overall score:

- **Excellent**: Score >= 0.90
- **Good**: Score >= 0.75
- **Satisfactory**: Score >= 0.60
- **Needs Improvement**: Score >= 0.40
- **Poor**: Score < 0.40

## Goal Types

Supported goal types:

- **Quantitative**: Goals with measurable numeric targets
- **Qualitative**: Goals with descriptive outcomes
- **Development**: Personal and professional development goals
- **Project**: Project-specific goals

## Goal Statuses

Goal status values:

- **not_started**: Goal not yet started
- **in_progress**: Goal in progress
- **completed**: Goal completed
- **cancelled**: Goal cancelled
- **overdue**: Goal past due date

## Review Types

Supported review types:

- **quarterly**: Quarterly performance review (90 days)
- **annual**: Annual performance review (365 days)
- **mid_year**: Mid-year review (180 days)
- **probationary**: Probationary period review

## Training Needs Identification

Training needs are identified based on:

- **Performance Gaps**: Low performance in specific metrics
- **Goal Requirements**: Skills needed to achieve goals
- **Career Aspirations**: Skills for career advancement
- **Skill Assessments**: Identified skill deficiencies

## Development Plans

Development plans include:

- **Objectives**: Clear learning objectives
- **Milestones**: Key progress milestones
- **Timeline**: Start and end dates
- **Resources**: Recommended training resources
- **Review Schedule**: Regular review intervals

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
