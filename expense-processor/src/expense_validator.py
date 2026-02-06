"""Validates expenses against company policies."""

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, Expense, Policy, ExpenseReport

logger = logging.getLogger(__name__)


class ExpenseValidator:
    """Validates expenses against company policies."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize expense validator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.policies_config = config.get("expense_policies", {})
        self.validation_config = config.get("validation", {})

    def validate_expense(
        self,
        expense_id: int,
    ) -> Dict:
        """Validate expense against policies.

        Args:
            expense_id: Expense ID.

        Returns:
            Dictionary with validation results.
        """
        expense = (
            self.db_manager.get_session()
            .query(Expense)
            .filter(Expense.id == expense_id)
            .first()
        )

        if not expense:
            return {"valid": False, "error": "Expense not found"}

        policy = self.db_manager.get_policy(expense.category)

        validation_results = {
            "valid": True,
            "violations": [],
            "warnings": [],
            "notes": [],
        }

        if policy:
            validation_results.update(self._validate_against_policy(expense, policy))
        else:
            validation_results.update(self._validate_against_defaults(expense))

        validation_results.update(self._check_receipt_requirement(expense))

        if self.validation_config.get("check_duplicates", True):
            validation_results.update(self._check_duplicates(expense))

        expense.validated = validation_results["valid"]
        expense.validation_notes = "; ".join(validation_results["violations"] + validation_results["warnings"])

        session = self.db_manager.get_session()
        try:
            session.merge(expense)
            session.commit()
        finally:
            session.close()

        logger.info(
            f"Validated expense {expense_id}: {validation_results['valid']}",
            extra={"expense_id": expense_id, "valid": validation_results["valid"]},
        )

        return validation_results

    def _validate_against_policy(
        self, expense: Expense, policy: Policy
    ) -> Dict:
        """Validate expense against specific policy.

        Args:
            expense: Expense object.
            policy: Policy object.

        Returns:
            Dictionary with validation results.
        """
        violations = []
        warnings = []

        if policy.max_amount and expense.amount > policy.max_amount:
            violations.append(
                f"Amount ${expense.amount:.2f} exceeds policy maximum ${policy.max_amount:.2f} for {expense.category}"
            )

        if policy.max_daily_amount:
            daily_total = self._get_daily_total(expense)
            if daily_total > policy.max_daily_amount:
                violations.append(
                    f"Daily total ${daily_total:.2f} exceeds policy maximum ${policy.max_daily_amount:.2f} for {expense.category}"
                )

        if policy.require_receipt:
            receipts = expense.receipts
            if not receipts:
                violations.append(f"Receipt required for {expense.category} expenses")

        return {
            "violations": violations,
            "warnings": warnings,
        }

    def _validate_against_defaults(self, expense: Expense) -> Dict:
        """Validate expense against default policies.

        Args:
            expense: Expense object.

        Returns:
            Dictionary with validation results.
        """
        violations = []
        warnings = []

        max_daily = self.policies_config.get(f"max_daily_{expense.category}", None)
        if max_daily and expense.amount > max_daily:
            violations.append(
                f"Amount ${expense.amount:.2f} exceeds default maximum ${max_daily:.2f} for {expense.category}"
            )

        require_receipt_threshold = self.policies_config.get("require_receipt_threshold", 25.0)
        if expense.amount >= require_receipt_threshold:
            receipts = expense.receipts
            if not receipts:
                violations.append(
                    f"Receipt required for expenses over ${require_receipt_threshold:.2f}"
                )

        allowed_categories = self.policies_config.get("allowed_categories", [])
        if expense.category not in allowed_categories:
            violations.append(f"Category '{expense.category}' not in allowed categories")

        return {
            "violations": violations,
            "warnings": warnings,
        }

    def _check_receipt_requirement(self, expense: Expense) -> Dict:
        """Check receipt requirement.

        Args:
            expense: Expense object.

        Returns:
            Dictionary with validation results.
        """
        violations = []

        require_receipt_threshold = self.policies_config.get("require_receipt_threshold", 25.0)
        if expense.amount >= require_receipt_threshold:
            receipts = expense.receipts
            if not receipts:
                violations.append(
                    f"Receipt required for expenses over ${require_receipt_threshold:.2f}"
                )

        return {"violations": violations}

    def _check_duplicates(self, expense: Expense) -> Dict:
        """Check for duplicate expenses.

        Args:
            expense: Expense object.

        Returns:
            Dictionary with validation results.
        """
        warnings = []

        similar_expenses = (
            self.db_manager.get_session()
            .query(Expense)
            .filter(
                Expense.id != expense.id,
                Expense.report_id == expense.report_id,
                Expense.category == expense.category,
                Expense.amount == expense.amount,
                Expense.expense_date == expense.expense_date,
            )
            .all()
        )

        if similar_expenses:
            warnings.append(
                f"Potential duplicate expense: {len(similar_expenses)} similar expenses found"
            )

        return {"warnings": warnings}

    def _get_daily_total(self, expense: Expense) -> float:
        """Get daily total for expense category.

        Args:
            expense: Expense object.

        Returns:
            Daily total amount.
        """
        report = (
            self.db_manager.get_session()
            .query(ExpenseReport)
            .filter(ExpenseReport.id == expense.report_id)
            .first()
        )

        if not report:
            return expense.amount

        daily_expenses = [
            e for e in report.expenses
            if e.expense_date == expense.expense_date and e.category == expense.category
        ]

        return sum(e.amount for e in daily_expenses)

    def validate_report(
        self,
        report_id: int,
    ) -> Dict:
        """Validate all expenses in a report.

        Args:
            report_id: Report ID.

        Returns:
            Dictionary with validation results.
        """
        report = (
            self.db_manager.get_session()
            .query(ExpenseReport)
            .filter(ExpenseReport.id == report_id)
            .first()
        )

        if not report:
            return {"valid": False, "error": "Report not found"}

        all_valid = True
        all_violations = []
        all_warnings = []

        for expense in report.expenses:
            validation = self.validate_expense(expense.id)
            if not validation["valid"]:
                all_valid = False
            all_violations.extend(validation.get("violations", []))
            all_warnings.extend(validation.get("warnings", []))

        return {
            "valid": all_valid,
            "violations": all_violations,
            "warnings": all_warnings,
            "expenses_validated": len(report.expenses),
        }
