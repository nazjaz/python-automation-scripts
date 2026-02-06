"""Process customer complaints."""

from typing import Dict, List, Optional

from src.database import DatabaseManager


class ComplaintProcessor:
    """Process customer complaints."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize complaint processor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def process_complaint(
        self,
        complaint_id: str,
        customer_id: str,
        complaint_text: str,
        customer_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Dict[str, any]:
        """Process a new complaint.

        Args:
            complaint_id: Complaint identifier.
            customer_id: Customer identifier.
            complaint_text: Complaint text.
            customer_name: Customer name.
            email: Customer email.

        Returns:
            Dictionary with processing results.
        """
        from src.issue_categorizer import IssueCategorizer
        from src.department_router import DepartmentRouter

        categorizer = IssueCategorizer(
            self.db_manager, self.config.get("categorization", {})
        )
        router = DepartmentRouter(
            self.db_manager, self.config.get("routing", {})
        )

        customer = self.db_manager.get_customer(customer_id)
        if not customer:
            customer = self.db_manager.add_customer(
                customer_id=customer_id,
                customer_name=customer_name or customer_id,
                email=email,
            )

        categorization = categorizer.categorize_complaint(complaint_text)

        complaint = self.db_manager.add_complaint(
            complaint_id=complaint_id,
            customer_id=customer.id,
            complaint_text=complaint_text,
            category=categorization["category"],
            subcategory=categorization["subcategory"],
            priority=categorization["priority"],
        )

        routing = router.route_complaint(
            complaint_id=complaint_id,
            category=categorization["category"],
            priority=categorization["priority"],
        )

        self.db_manager.add_complaint_update(
            complaint_id=complaint.id,
            update_text=f"Complaint received and categorized as {categorization['category']}",
            status="new",
        )

        return {
            "success": True,
            "complaint_id": complaint_id,
            "category": categorization["category"],
            "subcategory": categorization["subcategory"],
            "priority": categorization["priority"],
            "department": routing.get("department_name"),
            "status": routing.get("status", "new"),
        }

    def get_complaint_summary(self, complaint_id: str) -> Dict[str, any]:
        """Get summary of complaint processing.

        Args:
            complaint_id: Complaint identifier.

        Returns:
            Dictionary with complaint summary.
        """
        from src.resolution_tracker import ResolutionTracker

        tracker = ResolutionTracker(
            self.db_manager, self.config.get("resolution_tracking", {})
        )

        tracking = tracker.track_resolution(complaint_id)

        complaint = self.db_manager.get_complaint(complaint_id)
        if not complaint:
            return {"error": "Complaint not found"}

        return {
            "complaint_id": complaint_id,
            "status": complaint.status,
            "category": complaint.category,
            "priority": complaint.priority,
            "department": complaint.department.department_name if complaint.department else None,
            "assigned_to": complaint.assigned_to,
            "created_at": complaint.created_at,
            "resolved_at": complaint.resolved_at,
            "resolution_time_hours": tracking.get("resolution_time_hours"),
            "is_resolved": tracking.get("is_resolved", False),
            "total_updates": tracking.get("total_updates", 0),
        }
