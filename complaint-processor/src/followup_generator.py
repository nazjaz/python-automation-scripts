"""Generate customer satisfaction follow-ups."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class FollowUpGenerator:
    """Generate customer satisfaction follow-ups."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize follow-up generator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.followup_templates = config.get("followup_templates", {})
        self.followup_delay_hours = config.get("followup_delay_hours", 24)

    def generate_followup(self, complaint_id: str) -> Dict[str, any]:
        """Generate follow-up for resolved complaint.

        Args:
            complaint_id: Complaint identifier.

        Returns:
            Dictionary with follow-up information.
        """
        complaint = self.db_manager.get_complaint(complaint_id)

        if not complaint:
            return {"error": "Complaint not found"}

        if complaint.status != "resolved":
            return {"error": "Complaint not resolved"}

        resolution = self.db_manager.get_resolution(complaint.id)
        if not resolution:
            return {"error": "No resolution found"}

        followup_type = "satisfaction_survey"
        message = self._generate_followup_message(complaint, resolution, followup_type)

        followup = self.db_manager.add_followup(
            complaint_id=complaint.id,
            customer_id=complaint.customer_id,
            followup_type=followup_type,
            message=message,
        )

        return {
            "success": True,
            "followup_id": followup.id,
            "complaint_id": complaint_id,
            "customer_id": complaint.customer.customer_id,
            "followup_type": followup_type,
            "message": message,
        }

    def _generate_followup_message(
        self, complaint, resolution, followup_type: str
    ) -> str:
        """Generate follow-up message.

        Args:
            complaint: Complaint object.
            resolution: Resolution object.
            followup_type: Follow-up type.

        Returns:
            Follow-up message string.
        """
        template = self.followup_templates.get(followup_type, {})

        if template and "message" in template:
            message = template["message"]
            message = message.replace("{customer_name}", complaint.customer.customer_name or "Customer")
            message = message.replace("{complaint_id}", complaint.complaint_id)
            return message

        default_message = (
            f"Dear {complaint.customer.customer_name or 'Customer'},\n\n"
            f"Thank you for bringing your concern to our attention. "
            f"We have resolved your complaint (ID: {complaint.complaint_id}).\n\n"
            f"Resolution: {resolution.resolution_text}\n\n"
            f"We would appreciate your feedback on how we handled your complaint. "
            f"Please let us know if you are satisfied with the resolution.\n\n"
            f"Best regards,\nCustomer Service Team"
        )

        return default_message

    def generate_followups_for_resolved(
        self, hours_since_resolution: int = 24, limit: int = 50
    ) -> List[Dict[str, any]]:
        """Generate follow-ups for recently resolved complaints.

        Args:
            hours_since_resolution: Hours since resolution to generate follow-up.
            limit: Maximum number of follow-ups to generate.

        Returns:
            List of follow-up dictionaries.
        """
        session = self.db_manager.get_session()
        try:
            from src.database import Complaint, FollowUp

            cutoff = datetime.utcnow() - timedelta(hours=hours_since_resolution)

            resolved_complaints = (
                session.query(Complaint)
                .filter(
                    Complaint.status == "resolved",
                    Complaint.resolved_at >= cutoff,
                )
                .all()
            )

            followups_generated = []

            for complaint in resolved_complaints[:limit]:
                existing_followup = (
                    session.query(FollowUp)
                    .filter(FollowUp.complaint_id == complaint.id)
                    .first()
                )

                if not existing_followup:
                    followup = self.generate_followup(complaint.complaint_id)
                    if followup.get("success"):
                        followups_generated.append(followup)

            return followups_generated
        finally:
            session.close()

    def send_followup(self, followup_id: int) -> Dict[str, any]:
        """Mark follow-up as sent.

        Args:
            followup_id: Follow-up ID.

        Returns:
            Dictionary with send results.
        """
        self.db_manager.update_followup_sent(followup_id)

        return {
            "success": True,
            "followup_id": followup_id,
            "sent_at": datetime.utcnow(),
        }

    def get_pending_followups(self, limit: Optional[int] = None) -> List[Dict[str, any]]:
        """Get pending follow-ups.

        Args:
            limit: Maximum number of follow-ups to return.

        Returns:
            List of pending follow-up dictionaries.
        """
        followups = self.db_manager.get_pending_followups(limit=limit)

        return [
            {
                "id": f.id,
                "complaint_id": f.complaint.complaint_id if f.complaint else None,
                "customer_id": f.customer.customer_id if f.customer else None,
                "followup_type": f.followup_type,
                "message": f.message,
                "created_at": f.created_at,
            }
            for f in followups
        ]

    def record_followup_response(
        self, followup_id: int, satisfaction_score: float
    ) -> Dict[str, any]:
        """Record follow-up response with satisfaction score.

        Args:
            followup_id: Follow-up ID.
            satisfaction_score: Satisfaction score (1.0 to 5.0).

        Returns:
            Dictionary with response recording results.
        """
        self.db_manager.update_followup_sent(followup_id, satisfaction_score=satisfaction_score)

        session = self.db_manager.get_session()
        try:
            from src.database import FollowUp

            followup = session.query(FollowUp).filter(FollowUp.id == followup_id).first()
            if followup and followup.complaint:
                resolution = self.db_manager.get_resolution(followup.complaint.id)
                if resolution:
                    resolution.customer_satisfaction_score = satisfaction_score
                    session.commit()

        finally:
            session.close()

        return {
            "success": True,
            "followup_id": followup_id,
            "satisfaction_score": satisfaction_score,
        }
