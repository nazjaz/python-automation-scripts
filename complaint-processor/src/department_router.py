"""Route complaints to appropriate departments."""

from typing import Dict, List, Optional

from src.database import DatabaseManager


class DepartmentRouter:
    """Route complaints to appropriate departments."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize department router.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.default_department = config.get("default_department", "Customer Service")

    def route_complaint(
        self, complaint_id: str, category: str, priority: str
    ) -> Dict[str, any]:
        """Route complaint to appropriate department.

        Args:
            complaint_id: Complaint identifier.
            category: Complaint category.
            priority: Complaint priority.

        Returns:
            Dictionary with routing results.
        """
        complaint = self.db_manager.get_complaint(complaint_id)

        if not complaint:
            return {"error": "Complaint not found"}

        department = self._find_department(category, priority, complaint.complaint_text)

        if department:
            self.db_manager.update_complaint_status(
                complaint_id=complaint_id,
                status="assigned",
                department_id=department.id,
            )

            return {
                "complaint_id": complaint_id,
                "department_id": department.id,
                "department_name": department.department_name,
                "status": "assigned",
            }
        else:
            default_dept = self.db_manager.get_department(self.default_department)
            if default_dept:
                self.db_manager.update_complaint_status(
                    complaint_id=complaint_id,
                    status="assigned",
                    department_id=default_dept.id,
                )
                return {
                    "complaint_id": complaint_id,
                    "department_id": default_dept.id,
                    "department_name": default_dept.department_name,
                    "status": "assigned",
                }

        return {"error": "No department found"}

    def _find_department(
        self, category: str, priority: str, complaint_text: str
    ) -> Optional:
        """Find appropriate department for complaint.

        Args:
            category: Complaint category.
            priority: Complaint priority.
            complaint_text: Complaint text.

        Returns:
            Department object or None.
        """
        departments = self.db_manager.get_all_departments()

        for department in departments:
            rules = self._get_department_rules(department.id)

            for rule in rules:
                if self._rule_matches(rule, category, priority, complaint_text):
                    return department

        category_mapping = self.config.get("category_mapping", {
            "product_quality": "Quality Assurance",
            "billing": "Billing",
            "shipping": "Logistics",
            "customer_service": "Customer Service",
            "technical": "Technical Support",
            "account": "Account Management",
        })

        department_name = category_mapping.get(category, self.default_department)
        return self.db_manager.get_department(department_name)

    def _get_department_rules(self, department_id: int) -> List:
        """Get routing rules for department.

        Args:
            department_id: Department ID.

        Returns:
            List of RoutingRule objects.
        """
        session = self.db_manager.get_session()
        try:
            from src.database import RoutingRule

            return (
                session.query(RoutingRule)
                .filter(RoutingRule.department_id == department_id)
                .all()
            )
        finally:
            session.close()

    def _rule_matches(
        self, rule, category: str, priority: str, complaint_text: str
    ) -> bool:
        """Check if routing rule matches complaint.

        Args:
            rule: RoutingRule object.
            category: Complaint category.
            priority: Complaint priority.
            complaint_text: Complaint text.

        Returns:
            True if rule matches, False otherwise.
        """
        if rule.category and rule.category != category:
            return False

        if rule.priority_threshold:
            priority_levels = ["low", "medium", "high", "urgent"]
            rule_priority_index = priority_levels.index(rule.priority_threshold) if rule.priority_threshold in priority_levels else 0
            complaint_priority_index = priority_levels.index(priority) if priority in priority_levels else 0
            if complaint_priority_index < rule_priority_index:
                return False

        if rule.keywords:
            keywords = [k.strip() for k in rule.keywords.split(",")]
            complaint_lower = complaint_text.lower()
            if any(keyword.lower() in complaint_lower for keyword in keywords):
                return True

        if rule.category == category:
            return True

        return False

    def get_department_workload(self, department_id: int) -> Dict[str, any]:
        """Get workload for department.

        Args:
            department_id: Department ID.

        Returns:
            Dictionary with workload information.
        """
        open_complaints = self.db_manager.get_open_complaints(department_id=department_id)

        priority_counts = {}
        for complaint in open_complaints:
            priority_counts[complaint.priority] = priority_counts.get(complaint.priority, 0) + 1

        return {
            "department_id": department_id,
            "open_complaints": len(open_complaints),
            "by_priority": priority_counts,
        }
