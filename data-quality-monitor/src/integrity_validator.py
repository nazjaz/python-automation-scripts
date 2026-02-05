"""Data integrity validation across databases."""

import logging
from typing import Optional

from src.database_connector import DatabaseConnector

logger = logging.getLogger(__name__)


class IntegrityIssue:
    """Represents a data integrity issue."""

    def __init__(
        self,
        issue_type: str,
        table_name: str,
        column_name: Optional[str],
        description: str,
        severity: str,
        affected_rows: Optional[int] = None,
    ):
        """Initialize integrity issue.

        Args:
            issue_type: Type of integrity issue.
            table_name: Name of the table with the issue.
            column_name: Name of the column with the issue (if applicable).
            description: Description of the issue.
            severity: Severity level (critical, high, medium, low).
            affected_rows: Number of rows affected.
        """
        self.issue_type = issue_type
        self.table_name = table_name
        self.column_name = column_name
        self.description = description
        self.severity = severity
        self.affected_rows = affected_rows


class IntegrityValidator:
    """Validates data integrity across databases."""

    def __init__(self, connector: DatabaseConnector, config: dict):
        """Initialize integrity validator.

        Args:
            connector: Database connector instance.
            config: Integrity validation configuration.
        """
        self.connector = connector
        self.config = config

    def validate_foreign_keys(
        self, table_name: str, foreign_key_config: Optional[list[dict]] = None
    ) -> list[IntegrityIssue]:
        """Validate foreign key constraints.

        Args:
            table_name: Name of the table to validate.
            foreign_key_config: List of foreign key configurations to check.

        Returns:
            List of IntegrityIssue objects for violations found.
        """
        issues = []

        if not self.config.get("check_foreign_keys", True):
            return issues

        try:
            foreign_keys = self.connector.get_foreign_keys(table_name)

            if foreign_key_config:
                for fk_config in foreign_key_config:
                    column = fk_config.get("column")
                    ref_table = fk_config.get("references_table")
                    ref_column = fk_config.get("references_column")

                    if not all([column, ref_table, ref_column]):
                        continue

                    violation_query = (
                        f'SELECT COUNT(*) as violation_count FROM "{table_name}" t '
                        f'LEFT JOIN "{ref_table}" r ON t."{column}" = r."{ref_column}" '
                        f'WHERE t."{column}" IS NOT NULL AND r."{ref_column}" IS NULL'
                    )

                    if self.connector.db_type == "mysql":
                        violation_query = (
                            f"SELECT COUNT(*) as violation_count FROM `{table_name}` t "
                            f"LEFT JOIN `{ref_table}` r ON t.`{column}` = r.`{ref_column}` "
                            f"WHERE t.`{column}` IS NOT NULL AND r.`{ref_column}` IS NULL"
                        )

                    try:
                        result = self.connector.execute_query(violation_query)
                        violation_count = (
                            result[0]["violation_count"] if result else 0
                        )

                        if violation_count > 0:
                            issues.append(
                                IntegrityIssue(
                                    issue_type="foreign_key_violation",
                                    table_name=table_name,
                                    column_name=column,
                                    description=(
                                        f"Foreign key violation: {column} references "
                                        f"{ref_table}.{ref_column} - {violation_count} "
                                        f"orphaned records found"
                                    ),
                                    severity="critical",
                                    affected_rows=violation_count,
                                )
                            )
                    except Exception as e:
                        logger.warning(
                            f"Error validating foreign key {table_name}.{column}: {e}"
                        )
                        issues.append(
                            IntegrityIssue(
                                issue_type="validation_error",
                                table_name=table_name,
                                column_name=column,
                                description=f"Error validating foreign key: {str(e)}",
                                severity="medium",
                            )
                        )

            else:
                for fk in foreign_keys:
                    constrained_cols = fk["constrained_columns"]
                    ref_table = fk["referred_table"]
                    ref_cols = fk["referred_columns"]

                    if len(constrained_cols) == 1 and len(ref_cols) == 1:
                        column = constrained_cols[0]
                        ref_column = ref_cols[0]

                        violation_query = (
                            f'SELECT COUNT(*) as violation_count FROM "{table_name}" t '
                            f'LEFT JOIN "{ref_table}" r ON t."{column}" = r."{ref_column}" '
                            f'WHERE t."{column}" IS NOT NULL AND r."{ref_column}" IS NULL'
                        )

                        if self.connector.db_type == "mysql":
                            violation_query = (
                                f"SELECT COUNT(*) as violation_count FROM `{table_name}` t "
                                f"LEFT JOIN `{ref_table}` r ON t.`{column}` = r.`{ref_column}` "
                                f"WHERE t.`{column}` IS NOT NULL AND r.`{ref_column}` IS NULL"
                            )

                        try:
                            result = self.connector.execute_query(violation_query)
                            violation_count = (
                                result[0]["violation_count"] if result else 0
                            )

                            if violation_count > 0:
                                issues.append(
                                    IntegrityIssue(
                                        issue_type="foreign_key_violation",
                                        table_name=table_name,
                                        column_name=column,
                                        description=(
                                            f"Foreign key violation: {column} references "
                                            f"{ref_table}.{ref_column} - {violation_count} "
                                            f"orphaned records found"
                                        ),
                                        severity="critical",
                                        affected_rows=violation_count,
                                    )
                                )
                        except Exception as e:
                            logger.warning(
                                f"Error validating foreign key {table_name}.{column}: {e}"
                            )

        except Exception as e:
            logger.error(f"Error validating foreign keys for {table_name}: {e}")
            issues.append(
                IntegrityIssue(
                    issue_type="validation_error",
                    table_name=table_name,
                    column_name=None,
                    description=f"Error validating foreign keys: {str(e)}",
                    severity="high",
                )
            )

        return issues

    def validate_referential_integrity(
        self, table_name: str
    ) -> list[IntegrityIssue]:
        """Validate referential integrity.

        Args:
            table_name: Name of the table to validate.

        Returns:
            List of IntegrityIssue objects for violations found.
        """
        issues = []

        if not self.config.get("check_referential_integrity", True):
            return issues

        fk_issues = self.validate_foreign_keys(table_name)
        issues.extend(fk_issues)

        return issues

    def validate_data_types(self, table_name: str) -> list[IntegrityIssue]:
        """Validate data type consistency.

        Args:
            table_name: Name of the table to validate.

        Returns:
            List of IntegrityIssue objects for violations found.
        """
        issues = []

        if not self.config.get("check_data_types", True):
            return issues

        try:
            columns = self.connector.get_table_columns(table_name)
            total_rows = self.connector.get_row_count(table_name)

            if total_rows == 0:
                return issues

            for column in columns:
                column_name = column["name"]
                column_type = str(column["type"]).lower()

                if "int" in column_type or "numeric" in column_type:
                    invalid_query = (
                        f'SELECT COUNT(*) as invalid_count FROM "{table_name}" '
                        f'WHERE "{column_name}" IS NOT NULL '
                        f'AND "{column_name}"::text !~ \'^-?[0-9]+$\''
                    )

                    if self.connector.db_type == "mysql":
                        invalid_query = (
                            f"SELECT COUNT(*) as invalid_count FROM `{table_name}` "
                            f"WHERE `{column_name}` IS NOT NULL "
                            f"AND CAST(`{column_name}` AS CHAR) NOT REGEXP '^-?[0-9]+$'"
                        )

                    try:
                        result = self.connector.execute_query(invalid_query)
                        invalid_count = result[0]["invalid_count"] if result else 0

                        if invalid_count > 0:
                            invalid_percentage = (
                                invalid_count / total_rows if total_rows > 0 else 0
                            )
                            severity = (
                                "critical"
                                if invalid_percentage > 0.1
                                else "high" if invalid_percentage > 0.05 else "medium"
                            )

                            issues.append(
                                IntegrityIssue(
                                    issue_type="data_type_violation",
                                    table_name=table_name,
                                    column_name=column_name,
                                    description=(
                                        f"Data type violation in {column_name}: "
                                        f"{invalid_count} rows with invalid numeric format"
                                    ),
                                    severity=severity,
                                    affected_rows=invalid_count,
                                )
                            )
                    except Exception:
                        pass

        except Exception as e:
            logger.error(f"Error validating data types for {table_name}: {e}")
            issues.append(
                IntegrityIssue(
                    issue_type="validation_error",
                    table_name=table_name,
                    column_name=None,
                    description=f"Error validating data types: {str(e)}",
                    severity="high",
                )
            )

        return issues
