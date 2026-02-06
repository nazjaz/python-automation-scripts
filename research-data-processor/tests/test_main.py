"""Test suite for research data processor system."""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np

from src.config import load_config, get_settings
from src.database import (
    DatabaseManager,
    Dataset,
    Analysis,
    Figure,
)
from src.data_cleaner import DataCleaner
from src.statistical_analyzer import StatisticalAnalyzer
from src.visualization_generator import VisualizationGenerator
from src.figure_creator import FigureCreator


@pytest.fixture
def test_db():
    """Create test database."""
    db_manager = DatabaseManager("sqlite:///:memory:")
    db_manager.create_tables()
    return db_manager


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        "data_cleaning": {
            "missing_value_strategies": ["drop", "mean"],
            "outlier_detection": {
                "method": "iqr",
                "threshold": 1.5,
            },
            "duplicate_handling": "drop",
        },
        "statistical_analysis": {
            "descriptive_stats": True,
            "correlation_analysis": True,
            "significance_level": 0.05,
        },
        "visualization": {
            "figure_size": {"width": 8, "height": 6},
            "dpi": 300,
        },
        "publication": {
            "dpi": 300,
            "figure_size": {
                "single_column": [3.5, 2.5],
            },
        },
    }


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame for testing."""
    return pd.DataFrame({
        "x": np.random.randn(100),
        "y": np.random.randn(100),
        "category": np.random.choice(["A", "B", "C"], 100),
    })


class TestDatabaseManager:
    """Test database manager functionality."""

    def test_create_tables(self, test_db):
        """Test table creation."""
        session = test_db.get_session()
        try:
            datasets = session.query(Dataset).all()
            assert len(datasets) == 0
        finally:
            session.close()

    def test_add_dataset(self, test_db):
        """Test adding dataset."""
        dataset = test_db.add_dataset(
            dataset_id="DS001",
            name="Test Dataset",
            file_path="/path/to/data.csv",
            row_count=100,
            column_count=5,
        )
        assert dataset.id is not None
        assert dataset.dataset_id == "DS001"


class TestDataCleaner:
    """Test data cleaner functionality."""

    def test_clean_dataset(self, test_db, sample_config, sample_dataframe):
        """Test dataset cleaning."""
        cleaner = DataCleaner(test_db, sample_config)
        df_cleaned, report = cleaner.clean_dataset(sample_dataframe)

        assert isinstance(df_cleaned, pd.DataFrame)
        assert "original_rows" in report
        assert "final_rows" in report


class TestStatisticalAnalyzer:
    """Test statistical analyzer functionality."""

    def test_descriptive_statistics(self, test_db, sample_config, sample_dataframe):
        """Test descriptive statistics calculation."""
        analyzer = StatisticalAnalyzer(test_db, sample_config)
        stats = analyzer.descriptive_statistics(sample_dataframe)

        assert isinstance(stats, dict)
        assert "x" in stats or "y" in stats

    def test_correlation_analysis(self, test_db, sample_config, sample_dataframe):
        """Test correlation analysis."""
        analyzer = StatisticalAnalyzer(test_db, sample_config)
        corr = analyzer.correlation_analysis(sample_dataframe)

        assert isinstance(corr, pd.DataFrame)


class TestVisualizationGenerator:
    """Test visualization generator functionality."""

    def test_scatter_plot(self, test_db, sample_config, sample_dataframe):
        """Test scatter plot creation."""
        viz_gen = VisualizationGenerator(test_db, sample_config)
        fig = viz_gen.scatter_plot(
            sample_dataframe["x"],
            sample_dataframe["y"],
            title="Test Scatter",
        )

        assert fig is not None
        plt.close(fig)


class TestConfig:
    """Test configuration management."""

    def test_load_config(self):
        """Test loading configuration file."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            config = load_config(config_path)
            assert "data_cleaning" in config
            assert "statistical_analysis" in config

    def test_get_settings(self):
        """Test getting application settings."""
        settings = get_settings()
        assert settings.database.url is not None
        assert settings.app.name is not None
