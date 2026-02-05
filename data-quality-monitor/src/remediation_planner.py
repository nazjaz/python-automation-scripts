"""Generates remediation plans for data quality issues."""

import logging
from typing import Optional

from src.integrity_validator import IntegrityIssue
from src.quality_checks import QualityCheckResult

logger = logging.getLogger(__name__)


class RemediationAction:
    """Represents a remediation action."""

    def __init__(
        self,
        action_type: str,
        description: str,
        priority: str,
        estimated_effort: str,
        sql_query: Optional[str] = None,
        manual_steps: Optional[list[str]] = None,
    ):
        """Initialize remediation action.

        Args:
            action_type: Type of action (sql, manual, script).
            description: Description of the action.
            priority: Priority level (high, medium, low).
            estimated_effort: Estimated effort (e.g., "30 minutes", "2 hours").
            sql_query: SQL query to execute (if applicable).
            manual_steps: List of manual steps to perform (if applicable).
        """
        self.action_type = action_type
        self.description = description
        self.priority = priority
        self.estimated_effort = estimated_effort
        self.sql_query = sql_query
        self.manual_steps = manual_steps


class RemediationPlan:
    """Complete remediation plan for data quality issues."""

    def __init__(self, table_name: str):
        """Initialize remediation plan.

        Args:
            table_name: Name of the table this plan addresses.
        """
        self.table_name = table_name
        self.actions: list[RemediationAction] = []

    def add_action(self, action: RemediationAction) -> None:
        """Add a remediation action to the plan.

        Args:
            action: RemediationAction to add.
        """
        self.actions.append(action)

    def get_high_priority_actions(self) -> list[RemediationAction]:
        """Get high priority actions.

        Returns:
            List of high priority remediation actions.
        """
        return [action for action in self.actions if action.priority == "high"]

    def get_total_estimated_effort(self) -> str:
        """Get total estimated effort for all actions.

        Returns:
            Summary of total estimated effort.
        """
        high_priority_count = len(self.get_high_priority_actions())
        total_actions = len(self.actions)

        return f"{total_actions} actions ({high_priority_count} high priority)"


class RemediationPlanner:
    """Generates remediation plans from quality check results and integrity issues."""

    def __init__(self):
        """Initialize remediation planner."""
        pass

    def create_plan_from_quality_result(
        self, result: QualityCheckResult
    ) -> RemediationPlan:
        """Create remediation plan from quality check result.

        Args:
            result: QualityCheckResult to create plan for.

        Returns:
            RemediationPlan with recommended actions.
        """
        plan = RemediationPlan(result.table_name)

        if result.check_type == "completeness":
            for issue in result.issues:
                if issue.get("type") == "high_null_percentage":
                    column = issue.get("column")
                    null_percentage = issue.get("null_percentage", 0)

                    if null_percentage > 0.5:
                        priority = "high"
                        effort = "2-4 hours"
                    elif null_percentage > 0.2:
                        priority = "medium"
                        effort = "1-2 hours"
                    else:
                        priority = "low"
                        effort = "30 minutes"

                    plan.add_action(
                        RemediationAction(
                            action_type="sql",
                            description=(
                                f"Address NULL values in {column}: "
                                f"{null_percentage:.1%} of rows are NULL"
                            ),
                            priority=priority,
                            estimated_effort=effort,
                            sql_query=(
                                f'SELECT * FROM "{result.table_name}" '
                                f'WHERE "{column}" IS NULL LIMIT 100'
                            ),
                            manual_steps=[
                                f"Review NULL values in {result.table_name}.{column}",
                                "Determine appropriate default values or data sources",
                                "Update NULL values with appropriate data",
                                "Implement data validation rules to prevent future NULLs",
                            ],
                        )
                    )

                elif issue.get("type") == "high_empty_strings":
                    column = issue.get("column")
                    empty_percentage = issue.get("empty_percentage", 0)

                    plan.add_action(
                        RemediationAction(
                            action_type="sql",
                            description=(
                                f"Address empty strings in {column}: "
                                f"{empty_percentage:.1%} of rows have empty strings"
                            ),
                            priority="medium",
                            estimated_effort="1 hour",
                            sql_query=(
                                f'SELECT * FROM "{result.table_name}" '
                                f'WHERE "{column}" = \'\' OR TRIM("{column}") = \'\' LIMIT 100'
                            ),
                            manual_steps=[
                                f"Review empty string values in {result.table_name}.{column}",
                                "Determine if empty strings should be NULL or have default values",
                                "Update empty strings appropriately",
                            ],
                        )
                    )

        elif result.check_type == "uniqueness":
            for issue in result.issues:
                if issue.get("type") == "duplicate_values":
                    column = issue.get("column")
                    duplicate_count = issue.get("duplicate_count", 0)

                    plan.add_action(
                        RemediationAction(
                            action_type="sql",
                            description=(
                                f"Resolve duplicate values in {column}: "
                                f"{duplicate_count} duplicate groups found"
                            ),
                            priority="high",
                            estimated_effort="2-4 hours",
                            sql_query=(
                                f'SELECT "{column}", COUNT(*) as count '
                                f'FROM "{result.table_name}" '
                                f'GROUP BY "{column}" HAVING COUNT(*) > 1'
                            ),
                            manual_steps=[
                                f"Identify duplicate records in {result.table_name}.{column}",
                                "Determine which records to keep (most recent, most complete, etc.)",
                                "Delete or merge duplicate records",
                                "Add unique constraint to prevent future duplicates",
                            ],
                        )
                    )

        elif result.check_type == "accuracy":
            for issue in result.issues:
                if issue.get("type") == "pattern_mismatch":
                    column = issue.get("column")
                    pattern = issue.get("pattern")
                    invalid_count = issue.get("invalid_count", 0)

                    plan.add_action(
                        RemediationAction(
                            action_type="manual",
                            description=(
                                f"Fix pattern mismatches in {column}: "
                                f"{invalid_count} rows don't match pattern {pattern}"
                            ),
                            priority="high",
                            estimated_effort="2-3 hours",
                            manual_steps=[
                                f"Review invalid values in {result.table_name}.{column}",
                                f"Validate against expected pattern: {pattern}",
                                "Correct invalid values or update pattern if needed",
                                "Implement validation at data entry point",
                            ],
                        )
                    )

                elif issue.get("type") == "range_violation":
                    column = issue.get("column")
                    min_val = issue.get("min")
                    max_val = issue.get("max")
                    invalid_count = issue.get("invalid_count", 0)

                    range_desc = f"between {min_val} and {max_val}"
                    if min_val is None:
                        range_desc = f"<= {max_val}"
                    elif max_val is None:
                        range_desc = f">= {min_val}"

                    plan.add_action(
                        RemediationAction(
                            action_type="sql",
                            description=(
                                f"Fix range violations in {column}: "
                                f"{invalid_count} rows outside valid range {range_desc}"
                            ),
                            priority="high",
                            estimated_effort="1-2 hours",
                            sql_query=(
                                f'SELECT * FROM "{result.table_name}" '
                                f'WHERE "{column}" IS NOT NULL '
                                f'AND ("{column}" < {min_val if min_val else "NULL"} '
                                f'OR "{column}" > {max_val if max_val else "NULL"}) LIMIT 100'
                            ),
                            manual_steps=[
                                f"Review out-of-range values in {result.table_name}.{column}",
                                f"Validate against expected range: {range_desc}",
                                "Correct invalid values or update range if needed",
                                "Implement range validation at data entry point",
                            ],
                        )
                    )

        return plan

    def create_plan_from_integrity_issue(
        self, issue: IntegrityIssue
    ) -> RemediationPlan:
        """Create remediation plan from integrity issue.

        Args:
            issue: IntegrityIssue to create plan for.

        Returns:
            RemediationPlan with recommended actions.
        """
        plan = RemediationPlan(issue.table_name)

        if issue.issue_type == "foreign_key_violation":
            plan.add_action(
                RemediationAction(
                    action_type="sql",
                    description=issue.description,
                    priority="critical",
                    estimated_effort="2-4 hours",
                    sql_query=(
                        f'SELECT t.* FROM "{issue.table_name}" t '
                        f'LEFT JOIN "{issue.column_name}" r ON t."{issue.column_name}" = r.id '
                        f'WHERE t."{issue.column_name}" IS NOT NULL AND r.id IS NULL'
                    ),
                    manual_steps=[
                        f"Identify orphaned records in {issue.table_name}",
                        "Determine correct reference values or create missing records",
                        "Update foreign key values to valid references",
                        "Add foreign key constraint if not present",
                    ],
                )
            )

        elif issue.issue_type == "data_type_violation":
            plan.add_action(
                RemediationAction(
                    action_type="manual",
                    description=issue.description,
                    priority=issue.severity,
                    estimated_effort="1-2 hours",
                    manual_steps=[
                        f"Review data type violations in {issue.table_name}.{issue.column_name}",
                        "Identify source of invalid data",
                        "Correct data types or convert values appropriately",
                        "Implement data type validation at data entry point",
                    ],
                )
            )

        return plan
