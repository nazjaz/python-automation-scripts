# Research Data Processor

Automated research data processing system that cleans datasets, performs statistical analysis, generates visualizations, and creates publication-ready figures.

## Project Description

This automation system provides comprehensive research data processing capabilities. It automatically cleans datasets by handling missing values, removing outliers, and normalizing data. It performs statistical analysis including descriptive statistics, correlation analysis, and hypothesis testing. The system generates various types of visualizations and creates publication-ready figures with proper formatting, fonts, and styling suitable for academic and scientific publications.

### Target Audience

- Researchers processing experimental data
- Data scientists analyzing research datasets
- Academic researchers preparing publication figures
- Scientists conducting statistical analysis

## Features

- **Data Cleaning**: Handles missing values, removes outliers, eliminates duplicates
- **Statistical Analysis**: Descriptive statistics, correlation analysis, hypothesis testing (t-test, ANOVA, chi-square, etc.)
- **Visualization Generation**: Scatter plots, line plots, bar charts, histograms, boxplots, heatmaps, correlation matrices
- **Publication-Ready Figures**: Creates figures with proper formatting, fonts, and styling for publications
- **Multiple File Formats**: Supports CSV, Excel, JSON input and PNG, PDF, SVG output
- **Configurable Processing**: Customizable cleaning strategies, analysis options, and visualization styles
- **Database Tracking**: Tracks datasets, analyses, and generated figures
- **Multiple Figure Sizes**: Single column, double column, and full page figure presets

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included with Python)

## Installation

### Step 1: Clone or Navigate to Project

```bash
cd research-data-processor
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
DATABASE_URL=sqlite:///research_data_processor.db
APP_NAME=Research Data Processor
LOG_LEVEL=INFO
```

### Step 5: Configure Application Settings

Edit `config.yaml` to customize cleaning strategies, analysis options, and visualization settings:

```yaml
data_cleaning:
  missing_value_strategies:
    - "drop"
    - "mean"
    - "median"

statistical_analysis:
  significance_level: 0.05
  confidence_interval: 0.95

publication:
  dpi: 300
  figure_size:
    single_column: [3.5, 2.5]
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (default: sqlite:///research_data_processor.db) |
| `APP_NAME` | Application name | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |

### Configuration File (config.yaml)

The `config.yaml` file contains application-specific settings:

- **data_cleaning**: Missing value strategies, outlier detection, normalization, encoding
- **statistical_analysis**: Analysis types, significance levels, confidence intervals, test options
- **visualization**: Default style, figure formats, DPI, figure sizes, color palettes
- **publication**: Figure style, formats, DPI, size presets, font settings, axis settings
- **output**: Output directories, subdirectory creation, timestamp files
- **logging**: Log file location, rotation, and format settings

## Usage

### Clean Dataset

Clean a research dataset:

```bash
python src/main.py --clean --input data.csv --output data_cleaned.csv --missing-strategy mean
```

### Perform Statistical Analysis

Analyze dataset statistically:

```bash
python src/main.py --analyze --input data.csv
```

### Generate Visualization

Generate a visualization:

```bash
python src/main.py --visualize --input data.csv --figure-type scatter --x "x_column" --y "y_column" --output scatter_plot.png
```

### Create Publication-Ready Figure

Create a publication-ready figure:

```bash
python src/main.py --publication --input data.csv --figure-type scatter --x "x_column" --y "y_column" --size single_column --output figure_scatter.png
```

### Complete Workflow

Run complete data processing workflow:

```bash
# Clean dataset
python src/main.py --clean --input raw_data.csv --output cleaned_data.csv

# Analyze data
python src/main.py --analyze --input cleaned_data.csv

# Generate visualization
python src/main.py --visualize --input cleaned_data.csv --figure-type correlation --output correlation_matrix.png

# Create publication figure
python src/main.py --publication --input cleaned_data.csv --figure-type scatter --x "x" --y "y" --size single_column --output pub_figure.png
```

### Command-Line Arguments

```
--clean                    Clean dataset
--input PATH               Input file path (required)
--output PATH              Output file path
--missing-strategy STRATEGY Missing value strategy: drop, mean, median, mode, forward_fill, backward_fill

--analyze                  Perform statistical analysis
--input PATH               Input file path (required)

--visualize                Generate visualization
--input PATH               Input file path (required)
--figure-type TYPE         Figure type: scatter, line, bar, histogram, boxplot, correlation, heatmap (required)
--x COLUMN                 X-axis column name
--y COLUMN                 Y-axis column name
--output PATH              Output file path

--publication              Create publication-ready figure
--input PATH               Input file path (required)
--figure-type TYPE         Figure type (required)
--x COLUMN                 X-axis column name
--y COLUMN                 Y-axis column name
--size SIZE                Figure size: single_column, double_column, full_page (default: single_column)
--output PATH              Output file path

--config PATH              Path to configuration file (default: config.yaml)
```

## Project Structure

```
research-data-processor/
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
│   ├── data_cleaner.py       # Data cleaning functionality
│   ├── statistical_analyzer.py # Statistical analysis
│   ├── visualization_generator.py # Visualization generation
│   └── figure_creator.py     # Publication-ready figure creation
├── tests/                    # Unit tests
│   ├── __init__.py
│   └── test_main.py          # Test suite
├── templates/                # Templates
├── docs/                     # Documentation
├── output/                   # Output files
├── figures/                  # Generated figures
└── logs/                     # Log files
    └── .gitkeep
```

### File Descriptions

- **src/main.py**: Main entry point with CLI interface for all operations
- **src/config.py**: Configuration loading and validation using Pydantic
- **src/database.py**: SQLAlchemy models for datasets, analyses, and figures
- **src/data_cleaner.py**: Cleans datasets (missing values, outliers, duplicates)
- **src/statistical_analyzer.py**: Performs statistical analysis (descriptive, correlation, hypothesis testing)
- **src/visualization_generator.py**: Generates various types of visualizations
- **src/figure_creator.py**: Creates publication-ready figures with proper formatting
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
- Data cleaning functionality
- Statistical analysis algorithms
- Visualization generation
- Publication figure creation
- Configuration loading and validation

## Troubleshooting

### File Format Errors

**Problem**: Unsupported file format error.

**Solutions**:
- Ensure file format is supported (CSV, Excel, JSON)
- Check file extension matches actual format
- Verify file is not corrupted
- Try converting file to CSV format

### Missing Value Strategy Errors

**Problem**: Missing value strategy fails.

**Solutions**:
- Verify strategy is one of: drop, mean, median, mode, forward_fill, backward_fill
- Check that numeric columns exist for mean/median strategies
- Ensure sufficient data for chosen strategy
- Review data types in dataset

### Statistical Analysis Errors

**Problem**: Statistical analysis produces errors.

**Solutions**:
- Verify dataset has numeric columns for analysis
- Check that sufficient data points exist
- Ensure data is properly cleaned before analysis
- Review analysis type requirements

### Visualization Errors

**Problem**: Visualization generation fails.

**Solutions**:
- Verify required columns exist (x, y for scatter/line plots)
- Check that data types are appropriate for visualization type
- Ensure dataset is not empty
- Review figure type requirements

### Publication Figure Issues

**Problem**: Publication figures don't meet requirements.

**Solutions**:
- Verify DPI setting (default: 300)
- Check figure size preset matches journal requirements
- Review font settings in configuration
- Ensure output format is supported (PNG, PDF, SVG)

### Common Error Messages

- `File not found`: Verify input file path is correct
- `Unsupported file format`: Use CSV, Excel, or JSON format
- `Column not found`: Verify column names exist in dataset
- `Insufficient data`: Ensure dataset has enough rows/columns
- `Configuration file not found`: Ensure `config.yaml` exists in project root

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

## Data Cleaning Strategies

### Missing Value Handling

- **drop**: Remove rows with missing values
- **mean**: Fill with column mean (numeric columns)
- **median**: Fill with column median (numeric columns)
- **mode**: Fill with column mode
- **forward_fill**: Forward fill missing values
- **backward_fill**: Backward fill missing values

### Outlier Detection

- **IQR Method**: Uses interquartile range with configurable threshold
- **Z-Score Method**: Uses standard deviations from mean

## Statistical Tests

Supported hypothesis tests:

- **t-test**: Compare means of two groups
- **Mann-Whitney U**: Non-parametric alternative to t-test
- **Chi-square**: Test independence of categorical variables
- **ANOVA**: Compare means of multiple groups
- **Kruskal-Wallis**: Non-parametric alternative to ANOVA

## Visualization Types

Supported visualization types:

- **scatter**: Scatter plot for two continuous variables
- **line**: Line plot for time series or sequential data
- **bar**: Bar chart for categorical data
- **histogram**: Distribution visualization
- **boxplot**: Box plot for distribution comparison
- **correlation**: Correlation matrix heatmap
- **heatmap**: General heatmap for matrix data

## Publication Figure Settings

### Figure Sizes

- **single_column**: 3.5" × 2.5" (typical journal single column)
- **double_column**: 7" × 5" (typical journal double column)
- **full_page**: 8.5" × 11" (full page figure)

### Output Formats

- **PNG**: Raster format, high DPI (300+)
- **PDF**: Vector format, scalable
- **SVG**: Vector format, web-friendly

### Font Settings

- **Family**: Arial (configurable)
- **Size**: 10pt (configurable)
- **Weight**: Normal (configurable)

## License

This project is licensed under the MIT License - see the LICENSE file in the repository root for details.
