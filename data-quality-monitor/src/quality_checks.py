"""Data quality check implementations."""

import logging
import re
from typing import Optional

import pandas as pd
from sqlalchemy import text

from src.database_connector import DatabaseConnector

logger = logging.getLogger(__name__)


class QualityCheckResult:
    """Result of a quality check."""

    def __init__(
        self,
        check_type: str,
        table_name: str,
        column_name: Optional[str],
        score: float,
        passed: bool,
        issues: list[dict],
        threshold: float,
    ):
        """Initialize quality check result.

        Args:
            check_type: Type of quality check.
            table_name: Name of the table checked.
            column_name: Name of the column checked (if applicable).
            score: Quality score (0.0 to 1.0).
            passed: Whether check passed threshold.
            issues: List of identified issues.
            threshold: Minimum acceptable score.
        """
        self.check_type = check_type
        self.table_name = table_name
        self.column_name = column_name
        self.score = score
        self.passed = passed
        self.issues = issues
        self.threshold = threshold


class CompletenessChecker:
    """Checks data completeness."""

    def __init__(self, connector: DatabaseConnector, config: dict):
        """Initialize completeness checker.

        Args:
            connector: Database connector instance.
            config: Completeness check configuration.
        """
        self.connector = connector
        self.config = config
        self.threshold = config.get("threshold", 0.95)

    def check_table(
        self, table_name: str, columns: Optional[list[str]] = None
    ) -> QualityCheckResult:
        """Check completeness for a table.

        Args:
            table_name: Name of the table to check.
            columns: List of columns to check. If None, checks all columns.

        Returns:
            QualityCheckResult with completeness metrics.
        """
        issues = []
        total_rows = self.connector.get_row_count(table_name)

        if total_rows == 0:
            return QualityCheckResult(
                check_type="completeness",
                table_name=table_name,
                column_name=None,
                score=0.0,
                passed=False,
                issues=[{"type": "empty_table", "message": "Table is empty"}],
                threshold=self.threshold,
            )

        if columns is None:
            column_info = self.connector.get_table_columns(table_name)
            columns = [col["name"] for col in column_info]

        null_counts = {}
        empty_counts = {}

        for column in columns:
            try:
                if self.config.get("check_null_percentage", True):
                    null_query = (
                        f'SELECT COUNT(*) as null_count FROM "{table_name}" '
                        f'WHERE "{column}" IS NULL'
                    )
                    if self.connector.db_type == "mysql":
                        null_query = (
                            f"SELECT COUNT(*) as null_count FROM `{table_name}` "
                            f"WHERE `{column}` IS NULL"
                        )

                    result = self.connector.execute_query(null_query)
                    null_count = result[0]["null_count"] if result else 0
                    null_percentage = null_count / total_rows if total_rows > 0 else 0

                    if null_percentage > (1 - self.threshold):
                        issues.append(
                            {
                                "type": "high_null_percentage",
                                "column": column,
                                "null_percentage": null_percentage,
                                "null_count": null_count,
                            }
                        )

                    null_counts[column] = null_percentage

                if self.config.get("check_empty_strings", True):
                    empty_query = (
                        f'SELECT COUNT(*) as empty_count FROM "{table_name}" '
                        f'WHERE "{column}" = \'\' OR TRIM("{column}") = \'\''
                    )
                    if self.connector.db_type == "mysql":
                        empty_query = (
                            f"SELECT COUNT(*) as empty_count FROM `{table_name}` "
                            f"WHERE `{column}` = '' OR TRIM(`{column}`) = ''"
                        )

                    result = self.connector.execute_query(empty_query)
                    empty_count = result[0]["empty_count"] if result else 0
                    empty_percentage = empty_count / total_rows if total_rows > 0 else 0

                    if empty_percentage > (1 - self.threshold):
                        issues.append(
                            {
                                "type": "high_empty_strings",
                                "column": column,
                                "empty_percentage": empty_percentage,
                                "empty_count": empty_count,
                            }
                        )

                    empty_counts[column] = empty_percentage

            except Exception as e:
                logger.warning(
                    f"Error checking completeness for {table_name}.{column}: {e}"
                )
                issues.append(
                    {
                        "type": "check_error",
                        "column": column,
                        "error": str(e),
                    }
                )

        avg_completeness = 1.0 - (
            sum(null_counts.values()) + sum(empty_counts.values())
        ) / (len(columns) * 2) if columns else 1.0

        score = max(0.0, min(1.0, avg_completeness))

        return QualityCheckResult(
            check_type="completeness",
            table_name=table_name,
            column_name=None,
            score=score,
            passed=score >= self.threshold,
            issues=issues,
            threshold=self.threshold,
        )


class UniquenessChecker:
    """Checks data uniqueness."""

    def __init__(self, connector: DatabaseConnector, config: dict):
        """Initialize uniqueness checker.

        Args:
            connector: Database connector instance.
            config: Uniqueness check configuration.
        """
        self.connector = connector
        self.config = config
        self.threshold = config.get("threshold", 0.98)

    def check_table(
        self, table_name: str, columns: Optional[list[str]] = None
    ) -> QualityCheckResult:
        """Check uniqueness for a table.

        Args:
            table_name: Name of the table to check.
            columns: List of columns to check. If None, checks primary keys.

        Returns:
            QualityCheckResult with uniqueness metrics.
        """
        issues = []
        total_rows = self.connector.get_row_count(table_name)

        if total_rows == 0:
            return QualityCheckResult(
                check_type="uniqueness",
                table_name=table_name,
                column_name=None,
                score=1.0,
                passed=True,
                issues=[],
                threshold=self.threshold,
            )

        if columns is None:
            column_info = self.connector.get_table_columns(table_name)
            primary_key_cols = [col["name"] for col in column_info if col["primary_key"]]
            if primary_key_cols:
                columns = primary_key_cols
            else:
                columns = [col["name"] for col in column_info[:1]]

        for column in columns:
            try:
                if self.config.get("check_duplicate_records", True):
                    duplicate_query = (
                        f'SELECT "{column}", COUNT(*) as count FROM "{table_name}" '
                        f'GROUP BY "{column}" HAVING COUNT(*) > 1'
                    )
                    if self.connector.db_type == "mysql":
                        duplicate_query = (
                            f"SELECT `{column}`, COUNT(*) as count FROM `{table_name}` "
                            f"GROUP BY `{column}` HAVING COUNT(*) > 1"
                        )

                    result = self.connector.execute_query(duplicate_query)
                    duplicate_count = len(result)
                    duplicate_percentage = (
                        duplicate_count / total_rows if total_rows > 0 else 0
                    )

                    if duplicate_percentage > (1 - self.threshold):
                        issues.append(
                            {
                                "type": "duplicate_values",
                                "column": column,
                                "duplicate_count": duplicate_count,
                                "duplicate_percentage": duplicate_percentage,
                            }
                        )

            except Exception as e:
                logger.warning(
                    f"Error checking uniqueness for {table_name}.{column}: {e}"
                )
                issues.append(
                    {
                        "type": "check_error",
                        "column": column,
                        "error": str(e),
                    }
                )

        uniqueness_score = 1.0 - (len(issues) / len(columns)) if columns else 1.0
        score = max(0.0, min(1.0, uniqueness_score))

        return QualityCheckResult(
            check_type="uniqueness",
            table_name=table_name,
            column_name=None,
            score=score,
            passed=score >= self.threshold,
            issues=issues,
            threshold=self.threshold,
        )


class AccuracyChecker:
    """Checks data accuracy."""

    def __init__(self, connector: DatabaseConnector, config: dict):
        """Initialize accuracy checker.

        Args:
            connector: Database connector instance.
            config: Accuracy check configuration.
        """
        self.connector = connector
        self.config = config
        self.threshold = config.get("threshold", 0.85)

    def check_table(
        self, table_name: str, column_checks: Optional[list[dict]] = None
    ) -> QualityCheckResult:
        """Check accuracy for a table.

        Args:
            table_name: Name of the table to check.
            column_checks: List of column-specific checks with patterns, ranges, etc.

        Returns:
            QualityCheckResult with accuracy metrics.
        """
        issues = []
        total_rows = self.connector.get_row_count(table_name)

        if total_rows == 0 or not column_checks:
            return QualityCheckResult(
                check_type="accuracy",
                table_name=table_name,
                column_name=None,
                score=1.0,
                passed=True,
                issues=[],
                threshold=self.threshold,
            )

        for check in column_checks:
            column_name = check.get("name")
            if not column_name:
                continue

            try:
                if "pattern" in check and self.config.get("check_pattern_matching", True):
                    pattern = check["pattern"]
                    invalid_query = (
                        f'SELECT COUNT(*) as invalid_count FROM "{table_name}" '
                        f'WHERE "{column_name}" IS NOT NULL '
                        f'AND "{column_name}" NOT SIMILAR TO \'{pattern}\''
                    )
                    if self.connector.db_type == "mysql":
                        invalid_query = (
                            f"SELECT COUNT(*) as invalid_count FROM `{table_name}` "
                            f"WHERE `{column_name}` IS NOT NULL "
                            f"AND `{column_name}` NOT REGEXP '{pattern}'"
                        )

                    result = self.connector.execute_query(invalid_query)
                    invalid_count = result[0]["invalid_count"] if result else 0
                    invalid_percentage = invalid_count / total_rows if total_rows > 0 else 0

                    if invalid_percentage > (1 - self.threshold):
                        issues.append(
                            {
                                "type": "pattern_mismatch",
                                "column": column_name,
                                "pattern": pattern,
                                "invalid_count": invalid_count,
                                "invalid_percentage": invalid_percentage,
                            }
                        )

                if "min" in check or "max" in check:
                    min_val = check.get("min")
                    max_val = check.get("max")
                    min_inclusive = check.get("min_inclusive", True)
                    max_inclusive = check.get("max_inclusive", True)

                    conditions = []
                    if min_val is not None:
                        op = ">=" if min_inclusive else ">"
                        conditions.append(f'"{column_name}" {op} {min_val}')
                    if max_val is not None:
                        op = "<=" if max_inclusive else "<"
                        conditions.append(f'"{column_name}" {op} {max_val}')

                    if conditions:
                        invalid_query = (
                            f'SELECT COUNT(*) as invalid_count FROM "{table_name}" '
                            f'WHERE "{column_name}" IS NOT NULL '
                            f'AND NOT ({") AND (".join(conditions)})'
                        )
                        if self.connector.db_type == "mysql":
                            conditions_mysql = []
                            if min_val is not None:
                                op = ">=" if min_inclusive else ">"
                                conditions_mysql.append(f"`{column_name}` {op} {min_val}")
                            if max_val is not None:
                                op = "<=" if max_inclusive else "<"
                                conditions_mysql.append(f"`{column_name}` {op} {max_val}")
                            invalid_query = (
                                f"SELECT COUNT(*) as invalid_count FROM `{table_name}` "
                                f"WHERE `{column_name}` IS NOT NULL "
                                f"AND NOT ({') AND ('.join(conditions_mysql)})"
                            )

                        result = self.connector.execute_query(invalid_query)
                        invalid_count = result[0]["invalid_count"] if result else 0
                        invalid_percentage = (
                            invalid_count / total_rows if total_rows > 0 else 0
                        )

                        if invalid_percentage > (1 - self.threshold):
                            issues.append(
                                {
                                    "type": "range_violation",
                                    "column": column_name,
                                    "min": min_val,
                                    "max": max_val,
                                    "invalid_count": invalid_count,
                                    "invalid_percentage": invalid_percentage,
                                }
                            )

            except Exception as e:
                logger.warning(
                    f"Error checking accuracy for {table_name}.{column_name}: {e}"
                )
                issues.append(
                    {
                        "type": "check_error",
                        "column": column_name,
                        "error": str(e),
                    }
                )

        accuracy_score = 1.0 - (len(issues) / len(column_checks)) if column_checks else 1.0
        score = max(0.0, min(1.0, accuracy_score))

        return QualityCheckResult(
            check_type="accuracy",
            table_name=table_name,
            column_name=None,
            score=score,
            passed=score >= self.threshold,
            issues=issues,
            threshold=self.threshold,
        )
