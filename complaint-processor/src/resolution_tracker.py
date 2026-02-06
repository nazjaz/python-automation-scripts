"""Track complaint resolution."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class ResolutionTracker:
    """Track complaint resolution."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize resolution tracker.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def track_resolution(self, complaint_id: str) -> Dict[str, any]:
        """Track resolution status for complaint.

        Args:
            complaint_id: Complaint identifier.

        Returns:
            Dictionary with resolution tracking information.
        """
        complaint = self.db_manager.get_complaint(complaint_id)

        if not complaint:
            return {"error": "Complaint not found"}

        resolution = self.db_manager.get_resolution(complaint.id)
        updates = self._get_complaint_updates(complaint.id)

        resolution_time = None
        if complaint.resolution_time_hours:
            resolution_time = complaint.resolution_time_hours
        elif complaint.resolved_at and complaint.created_at:
            resolution_time = (
                complaint.resolved_at - complaint.created_at
            ).total_seconds() / 3600

        return {
            "complaint_id": complaint_id,
            "status": complaint.status,
            "is_resolved": complaint.status == "resolved",
            "resolution_time_hours": resolution_time,
            "resolution": {
                "resolution_text": resolution.resolution_text if resolution else None,
                "resolved_by": resolution.resolved_by if resolution else None,
                "resolved_at": resolution.resolved_at if resolution else None,
            } if resolution else None,
            "total_updates": len(updates),
            "updates": [
                {
                    "update_text": u.update_text,
                    "status": u.status,
                    "updated_by": u.updated_by,
                    "updated_at": u.updated_at,
                }
                for u in updates[:5]
            ],
        }

    def _get_complaint_updates(self, complaint_id: int) -> List:
        """Get updates for complaint.

        Args:
            complaint_id: Complaint ID.

        Returns:
            List of ComplaintUpdate objects.
        """
        session = self.db_manager.get_session()
        try:
            from src.database import ComplaintUpdate

            return (
                session.query(ComplaintUpdate)
                .filter(ComplaintUpdate.complaint_id == complaint_id)
                .order_by(ComplaintUpdate.updated_at.desc())
                .all()
            )
        finally:
            session.close()

    def add_resolution(
        self,
        complaint_id: str,
        resolution_text: str,
        resolution_type: str,
        resolved_by: str,
    ) -> Dict[str, any]:
        """Add resolution for complaint.

        Args:
            complaint_id: Complaint identifier.
            resolution_text: Resolution text.
            resolution_type: Resolution type.
            resolved_by: Person who resolved.

        Returns:
            Dictionary with resolution information.
        """
        complaint = self.db_manager.get_complaint(complaint_id)

        if not complaint:
            return {"error": "Complaint not found"}

        resolution = self.db_manager.add_resolution(
            complaint_id=complaint.id,
            resolution_text=resolution_text,
            resolution_type=resolution_type,
            resolved_by=resolved_by,
        )

        self.db_manager.add_complaint_update(
            complaint_id=complaint.id,
            update_text=f"Complaint resolved: {resolution_text}",
            status="resolved",
            updated_by=resolved_by,
        )

        return {
            "success": True,
            "complaint_id": complaint_id,
            "resolution_id": resolution.id,
            "status": "resolved",
            "resolution_time_hours": complaint.resolution_time_hours,
        }

    def get_resolution_statistics(self, days: int = 30) -> Dict[str, any]:
        """Get resolution statistics.

        Args:
            days: Number of days to analyze.

        Returns:
            Dictionary with resolution statistics.
        """
        session = self.db_manager.get_session()
        try:
            from src.database import Complaint
            from datetime import timedelta

            cutoff = datetime.utcnow() - timedelta(days=days)
            complaints = (
                session.query(Complaint)
                .filter(Complaint.created_at >= cutoff)
                .all()
            )

            total_complaints = len(complaints)
            resolved = [c for c in complaints if c.status == "resolved"]

            resolution_times = [
                c.resolution_time_hours
                for c in resolved
                if c.resolution_time_hours is not None
            ]

            average_resolution_time = (
                sum(resolution_times) / len(resolution_times)
                if resolution_times
                else None
            )

            return {
                "days": days,
                "total_complaints": total_complaints,
                "resolved_complaints": len(resolved),
                "resolution_rate": (
                    len(resolved) / total_complaints * 100
                    if total_complaints > 0
                    else 0.0
                ),
                "average_resolution_time_hours": average_resolution_time,
            }
        finally:
            session.close()

    def get_overdue_complaints(self, hours: int = 48) -> List[Dict[str, any]]:
        """Get complaints that are overdue.

        Args:
            hours: Hours threshold for overdue.

        Returns:
            List of overdue complaint dictionaries.
        """
        open_complaints = self.db_manager.get_open_complaints()

        overdue = []
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        for complaint in open_complaints:
            if complaint.created_at < cutoff:
                hours_open = (datetime.utcnow() - complaint.created_at).total_seconds() / 3600
                overdue.append({
                    "complaint_id": complaint.complaint_id,
                    "status": complaint.status,
                    "hours_open": hours_open,
                    "priority": complaint.priority,
                    "department": complaint.department.department_name if complaint.department else None,
                })

        return sorted(overdue, key=lambda x: x["hours_open"], reverse=True)
