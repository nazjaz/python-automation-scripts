"""Performs statistical analysis on research data."""

import json
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.preprocessing import StandardScaler

from src.database import DatabaseManager

logger = logging.getLogger(__name__)


class StatisticalAnalyzer:
    """Performs statistical analysis on research data."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize statistical analyzer.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.analysis_config = config.get("statistical_analysis", {})
        self.significance_level = self.analysis_config.get("significance_level", 0.05)
        self.confidence_level = self.analysis_config.get("confidence_interval", 0.95)

    def descriptive_statistics(
        self,
        df: pd.DataFrame,
    ) -> Dict:
        """Calculate descriptive statistics.

        Args:
            df: Input DataFrame.

        Returns:
            Dictionary with descriptive statistics.
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        stats_dict = {}

        for col in numeric_cols:
            stats_dict[col] = {
                "count": df[col].count(),
                "mean": df[col].mean(),
                "std": df[col].std(),
                "min": df[col].min(),
                "25%": df[col].quantile(0.25),
                "50%": df[col].median(),
                "75%": df[col].quantile(0.75),
                "max": df[col].max(),
                "skewness": df[col].skew(),
                "kurtosis": df[col].kurtosis(),
            }

        logger.info(
            f"Calculated descriptive statistics for {len(numeric_cols)} columns",
            extra={"column_count": len(numeric_cols)},
        )

        return stats_dict

    def correlation_analysis(
        self,
        df: pd.DataFrame,
        method: str = "pearson",
    ) -> pd.DataFrame:
        """Perform correlation analysis.

        Args:
            df: Input DataFrame.
            method: Correlation method (pearson, spearman, kendall).

        Returns:
            Correlation matrix DataFrame.
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) < 2:
            return pd.DataFrame()

        correlation_matrix = df[numeric_cols].corr(method=method)

        logger.info(
            f"Calculated correlation matrix using {method} method",
            extra={"method": method, "columns": len(numeric_cols)},
        )

        return correlation_matrix

    def t_test(
        self,
        group1: pd.Series,
        group2: pd.Series,
        alternative: str = "two-sided",
    ) -> Dict:
        """Perform t-test.

        Args:
            group1: First group data.
            group2: Second group data.
            alternative: Alternative hypothesis (two-sided, less, greater).

        Returns:
            Dictionary with test results.
        """
        statistic, p_value = stats.ttest_ind(group1, group2, alternative=alternative)

        result = {
            "test": "t_test",
            "statistic": float(statistic),
            "p_value": float(p_value),
            "significant": p_value < self.significance_level,
            "significance_level": self.significance_level,
            "alternative": alternative,
        }

        logger.info(
            f"Performed t-test: p={p_value:.4f}, significant={result['significant']}",
            extra=result,
        )

        return result

    def mann_whitney_test(
        self,
        group1: pd.Series,
        group2: pd.Series,
        alternative: str = "two-sided",
    ) -> Dict:
        """Perform Mann-Whitney U test.

        Args:
            group1: First group data.
            group2: Second group data.
            alternative: Alternative hypothesis.

        Returns:
            Dictionary with test results.
        """
        statistic, p_value = stats.mannwhitneyu(group1, group2, alternative=alternative)

        result = {
            "test": "mann_whitney",
            "statistic": float(statistic),
            "p_value": float(p_value),
            "significant": p_value < self.significance_level,
            "significance_level": self.significance_level,
            "alternative": alternative,
        }

        logger.info(
            f"Performed Mann-Whitney test: p={p_value:.4f}, significant={result['significant']}",
            extra=result,
        )

        return result

    def chi_square_test(
        self,
        observed: pd.DataFrame,
    ) -> Dict:
        """Perform chi-square test.

        Args:
            observed: Observed frequencies DataFrame.

        Returns:
            Dictionary with test results.
        """
        chi2, p_value, dof, expected = stats.chi2_contingency(observed)

        result = {
            "test": "chi_square",
            "chi2": float(chi2),
            "p_value": float(p_value),
            "degrees_of_freedom": int(dof),
            "significant": p_value < self.significance_level,
            "significance_level": self.significance_level,
        }

        logger.info(
            f"Performed chi-square test: p={p_value:.4f}, significant={result['significant']}",
            extra=result,
        )

        return result

    def anova_test(
        self,
        groups: List[pd.Series],
    ) -> Dict:
        """Perform ANOVA test.

        Args:
            groups: List of group data Series.

        Returns:
            Dictionary with test results.
        """
        f_statistic, p_value = stats.f_oneway(*groups)

        result = {
            "test": "anova",
            "f_statistic": float(f_statistic),
            "p_value": float(p_value),
            "significant": p_value < self.significance_level,
            "significance_level": self.significance_level,
            "groups": len(groups),
        }

        logger.info(
            f"Performed ANOVA test: p={p_value:.4f}, significant={result['significant']}",
            extra=result,
        )

        return result

    def linear_regression(
        self,
        X: pd.DataFrame,
        y: pd.Series,
    ) -> Dict:
        """Perform linear regression.

        Args:
            X: Independent variables DataFrame.
            y: Dependent variable Series.

        Returns:
            Dictionary with regression results.
        """
        from sklearn.linear_model import LinearRegression

        model = LinearRegression()
        model.fit(X, y)

        y_pred = model.predict(X)
        r_squared = model.score(X, y)

        result = {
            "test": "linear_regression",
            "coefficients": model.coef_.tolist(),
            "intercept": float(model.intercept_),
            "r_squared": float(r_squared),
            "feature_names": X.columns.tolist(),
        }

        logger.info(
            f"Performed linear regression: R²={r_squared:.4f}",
            extra=result,
        )

        return result

    def perform_analysis(
        self,
        df: pd.DataFrame,
        analysis_types: Optional[List[str]] = None,
    ) -> Dict:
        """Perform comprehensive statistical analysis.

        Args:
            df: Input DataFrame.
            analysis_types: Optional list of analysis types to perform.

        Returns:
            Dictionary with all analysis results.
        """
        results = {}

        if analysis_types is None:
            analysis_types = []

            if self.analysis_config.get("descriptive_stats", True):
                analysis_types.append("descriptive")
            if self.analysis_config.get("correlation_analysis", True):
                analysis_types.append("correlation")

        if "descriptive" in analysis_types:
            results["descriptive"] = self.descriptive_statistics(df)

        if "correlation" in analysis_types:
            results["correlation"] = self.correlation_analysis(df).to_dict()

        logger.info(
            f"Performed statistical analysis",
            extra={"analysis_types": analysis_types},
        )

        return results
