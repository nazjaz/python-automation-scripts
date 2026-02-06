"""Calculates reimbursable amounts for expenses."""

import logging
from typing import Dict, List, Optional

from src.database import DatabaseManager, ExpenseReport, Expense

logger = logging.getLogger(__name__)


class ReimbursementCalculator:
    """Calculates reimbursable amounts for expense reports."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize reimbursement calculator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.reimbursement_config = config.get("reimbursement", {})
        self.calculation_method = self.reimbursement_config.get("calculation_method", "full")
        self.tax_rate = self.reimbursement_config.get("tax_rate", 0.0)
        self.rounding_precision = self.reimbursement_config.get("rounding_precision", 2)

    def calculate_reimbursement(
        self,
        report_id: int,
    ) -> Dict:
        """Calculate reimbursable amount for expense report.

        Args:
            report_id: Report ID.

        Returns:
            Dictionary with reimbursement calculation results.
        """
        report = (
            self.db_manager.get_session()
            .query(ExpenseReport)
            .filter(ExpenseReport.id == report_id)
            .first()
        )

        if not report:
            return {"error": "Report not found"}

        total_amount = sum(expense.amount for expense in report.expenses)
        reimbursable_amount = 0.0

        for expense in report.expenses:
            if expense.validated:
                expense_reimbursable = self._calculate_expense_reimbursement(expense)
                reimbursable_amount += expense_reimbursable
            else:
                logger.warning(
                    f"Expense {expense.id} not validated, excluding from reimbursement",
                    extra={"expense_id": expense.id, "report_id": report_id},
                )

        reimbursable_amount = round(reimbursable_amount, self.rounding_precision)

        report.total_amount = total_amount
        report.reimbursable_amount = reimbursable_amount

        session = self.db_manager.get_session()
        try:
            session.merge(report)
            session.commit()
        finally:
            session.close()

        logger.info(
            f"Calculated reimbursement for report {report_id}",
            extra={
                "report_id": report_id,
                "total_amount": total_amount,
                "reimbursable_amount": reimbursable_amount,
            },
        )

        return {
            "report_id": report_id,
            "total_amount": total_amount,
            "reimbursable_amount": reimbursable_amount,
            "non_reimbursable": total_amount - reimbursable_amount,
        }

    def _calculate_expense_reimbursement(self, expense: Expense) -> float:
        """Calculate reimbursable amount for individual expense.

        Args:
            expense: Expense object.

        Returns:
            Reimbursable amount.
        """
        if self.calculation_method == "full":
            return expense.amount

        if self.calculation_method == "tax_excluded":
            return expense.amount / (1.0 + self.tax_rate)

        return expense.amount
