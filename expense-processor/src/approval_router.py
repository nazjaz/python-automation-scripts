"""Routes expense reports for approval."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from src.database import DatabaseManager, ExpenseReport, Employee, Approval

logger = logging.getLogger(__name__)


class ApprovalRouter:
    """Routes expense reports for approval based on amount and policies."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize approval router.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.approval_config = config.get("approval", {})
        self.routing_enabled = self.approval_config.get("routing_enabled", True)
        self.auto_approve_threshold = self.approval_config.get("auto_approve_under", 25.0)
        self.approval_levels = self.approval_config.get("approval_levels", [])

    def route_for_approval(
        self,
        report_id: int,
    ) -> List[Approval]:
        """Route expense report for approval.

        Args:
            report_id: Report ID.

        Returns:
            List of Approval objects created.
        """
        if not self.routing_enabled:
            logger.info("Approval routing disabled", extra={"report_id": report_id})
            return []

        report = (
            self.db_manager.get_session()
            .query(ExpenseReport)
            .filter(ExpenseReport.id == report_id)
            .first()
        )

        if not report:
            logger.error(f"Report {report_id} not found", extra={"report_id": report_id})
            return []

        if report.reimbursable_amount <= self.auto_approve_threshold:
            logger.info(
                f"Report {report_id} auto-approved (under threshold)",
                extra={"report_id": report_id, "amount": report.reimbursable_amount},
            )
            report.status = "approved"
            session = self.db_manager.get_session()
            try:
                session.merge(report)
                session.commit()
            finally:
                session.close()
            return []

        required_level = self._determine_approval_level(report.reimbursable_amount)
        approver = self._find_approver(report.employee_id, required_level)

        if not approver:
            logger.warning(
                f"No approver found for level {required_level}",
                extra={"report_id": report_id, "level": required_level},
            )
            return []

        approval = self.db_manager.add_approval(
            report_id=report_id,
            approver_id=approver.id,
            approval_level=required_level,
            status="pending",
        )

        report.status = "pending_approval"
        session = self.db_manager.get_session()
        try:
            session.merge(report)
            session.commit()
        finally:
            session.close()

        logger.info(
            f"Routed report {report_id} for approval",
            extra={
                "report_id": report_id,
                "approver_id": approver.id,
                "approval_level": required_level,
            },
        )

        return [approval]

    def _determine_approval_level(self, amount: float) -> int:
        """Determine required approval level based on amount.

        Args:
            amount: Reimbursable amount.

        Returns:
            Approval level (1, 2, 3, etc.).
        """
        for level_config in sorted(self.approval_levels, key=lambda x: x.get("max_amount", 0)):
            max_amount = level_config.get("max_amount", 0)
            if amount <= max_amount:
                return level_config.get("level", 1)

        return len(self.approval_levels)

    def _find_approver(
        self, employee_id: int, approval_level: int
    ) -> Optional[Employee]:
        """Find appropriate approver for approval level.

        Args:
            employee_id: Employee ID submitting report.
            approval_level: Required approval level.

        Returns:
            Employee object (approver) or None.
        """
        employee = (
            self.db_manager.get_session()
            .query(Employee)
            .filter(Employee.id == employee_id)
            .first()
        )

        if not employee:
            return None

        level_config = next(
            (l for l in self.approval_levels if l.get("level") == approval_level),
            None,
        )

        if not level_config:
            return None

        required_role = level_config.get("approver_role", "manager")

        if employee.manager_id:
            manager = (
                self.db_manager.get_session()
                .query(Employee)
                .filter(Employee.id == employee.manager_id)
                .first()
            )

            if manager and manager.role == required_role:
                return manager

        approver = (
            self.db_manager.get_session()
            .query(Employee)
            .filter(Employee.role == required_role)
            .first()
        )

        return approver

    def approve_report(
        self,
        approval_id: int,
        approver_id: int,
        approved: bool = True,
        comments: Optional[str] = None,
    ) -> Dict:
        """Approve or reject expense report.

        Args:
            approval_id: Approval ID.
            approver_id: Approver employee ID.
            approved: Whether to approve (True) or reject (False).
            comments: Optional comments.

        Returns:
            Dictionary with approval result.
        """
        approval = (
            self.db_manager.get_session()
            .query(Approval)
            .filter(Approval.id == approval_id)
            .first()
        )

        if not approval:
            return {"success": False, "error": "Approval not found"}

        if approval.approver_id != approver_id:
            return {"success": False, "error": "Unauthorized approver"}

        approval.status = "approved" if approved else "rejected"
        approval.comments = comments
        approval.approved_at = datetime.utcnow()

        report = (
            self.db_manager.get_session()
            .query(ExpenseReport)
            .filter(ExpenseReport.id == approval.report_id)
            .first()
        )

        if report:
            report.status = approval.status

        session = self.db_manager.get_session()
        try:
            session.merge(approval)
            if report:
                session.merge(report)
            session.commit()
        finally:
            session.close()

        logger.info(
            f"Report {approval.report_id} {approval.status}",
            extra={
                "report_id": approval.report_id,
                "approval_id": approval_id,
                "status": approval.status,
            },
        )

        return {
            "success": True,
            "report_id": approval.report_id,
            "status": approval.status,
        }
