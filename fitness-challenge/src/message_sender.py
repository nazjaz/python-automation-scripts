"""Send motivational messages to participants."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager


class MessageSender:
    """Send motivational messages to participants."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize message sender.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.message_templates = config.get("message_templates", {})
        self.email_enabled = config.get("email_enabled", False)
        self.sms_enabled = config.get("sms_enabled", False)

    def send_motivational_message(
        self, participant_id: int, message_type: str = "motivational"
    ) -> Dict[str, any]:
        """Send motivational message to participant.

        Args:
            participant_id: Participant ID.
            message_type: Message type (motivational, reminder, achievement, etc.).

        Returns:
            Dictionary with message information.
        """
        participant = self.db_manager.get_participant(participant_id)
        if not participant:
            return {}

        template = self.message_templates.get(message_type, {})
        content = self._generate_message_content(participant, message_type, template)

        subject = template.get("subject", "Keep up the great work!")

        message = self.db_manager.add_message(
            participant_id=participant_id,
            message_type=message_type,
            content=content,
            subject=subject,
        )

        if self.email_enabled and participant.email:
            self._send_email(participant.email, subject, content)

        if self.sms_enabled and participant.phone:
            self._send_sms(participant.phone, content)

        return {
            "id": message.id,
            "participant_id": participant_id,
            "message_type": message_type,
            "subject": subject,
            "content": content,
            "sent_at": message.sent_at,
        }

    def _generate_message_content(
        self, participant, message_type: str, template: Dict
    ) -> str:
        """Generate message content.

        Args:
            participant: Participant object.
            message_type: Message type.
            template: Message template.

        Returns:
            Generated message content.
        """
        base_content = template.get("content", "Keep up the great work!")

        progress_stats = self._get_participant_progress_stats(participant.id)

        content = base_content.replace("{name}", participant.name)
        content = content.replace("{progress}", str(progress_stats.get("total_progress", 0)))
        content = content.replace(
            "{active_challenges}", str(progress_stats.get("active_challenges", 0))
        )
        content = content.replace(
            "{completed_goals}", str(progress_stats.get("completed_goals", 0))
        )

        return content

    def _get_participant_progress_stats(self, participant_id: int) -> Dict[str, any]:
        """Get participant progress statistics.

        Args:
            participant_id: Participant ID.

        Returns:
            Dictionary with progress statistics.
        """
        from src.progress_tracker import ProgressTracker

        tracker = ProgressTracker(self.db_manager, self.config)
        stats = tracker.get_participant_statistics(participant_id, days=7)

        return {
            "total_progress": stats.get("total_progress", 0),
            "active_challenges": stats.get("active_challenges", 0),
            "completed_goals": stats.get("completed_goals", 0),
        }

    def send_achievement_message(
        self, participant_id: int, achievement_type: str, achievement_details: str
    ) -> Dict[str, any]:
        """Send achievement message.

        Args:
            participant_id: Participant ID.
            achievement_type: Achievement type (goal_completed, milestone_reached, etc.).
            achievement_details: Achievement details.

        Returns:
            Dictionary with message information.
        """
        participant = self.db_manager.get_participant(participant_id)
        if not participant:
            return {}

        template = self.message_templates.get("achievement", {})
        content = template.get("content", "Congratulations on your achievement!")
        content = content.replace("{name}", participant.name)
        content = content.replace("{achievement}", achievement_details)

        subject = template.get("subject", "Achievement Unlocked!")

        message = self.db_manager.add_message(
            participant_id=participant_id,
            message_type="achievement",
            content=content,
            subject=subject,
        )

        if self.email_enabled and participant.email:
            self._send_email(participant.email, subject, content)

        return {
            "id": message.id,
            "participant_id": participant_id,
            "message_type": "achievement",
            "subject": subject,
            "content": content,
            "sent_at": message.sent_at,
        }

    def send_reminder_message(
        self, participant_id: int, reminder_type: str = "progress_update"
    ) -> Dict[str, any]:
        """Send reminder message.

        Args:
            participant_id: Participant ID.
            reminder_type: Reminder type.

        Returns:
            Dictionary with message information.
        """
        participant = self.db_manager.get_participant(participant_id)
        if not participant:
            return {}

        template = self.message_templates.get("reminder", {})
        content = template.get("content", "Don't forget to log your progress!")
        content = content.replace("{name}", participant.name)

        subject = template.get("subject", "Progress Reminder")

        message = self.db_manager.add_message(
            participant_id=participant_id,
            message_type="reminder",
            content=content,
            subject=subject,
        )

        if self.email_enabled and participant.email:
            self._send_email(participant.email, subject, content)

        return {
            "id": message.id,
            "participant_id": participant_id,
            "message_type": "reminder",
            "subject": subject,
            "content": content,
            "sent_at": message.sent_at,
        }

    def send_bulk_messages(
        self, message_type: str = "motivational", participant_ids: Optional[List[int]] = None
    ) -> List[Dict[str, any]]:
        """Send messages to multiple participants.

        Args:
            message_type: Message type.
            participant_ids: Optional list of participant IDs. If None, sends to all.

        Returns:
            List of message dictionaries.
        """
        if participant_ids is None:
            participants = self.db_manager.get_all_participants()
            participant_ids = [p.id for p in participants]

        messages = []
        for participant_id in participant_ids:
            try:
                message = self.send_motivational_message(participant_id, message_type)
                if message:
                    messages.append(message)
            except Exception:
                continue

        return messages

    def _send_email(self, email: str, subject: str, content: str) -> None:
        """Send email message.

        Args:
            email: Recipient email.
            subject: Email subject.
            content: Email content.
        """
        if not self.email_enabled:
            return

    def _send_sms(self, phone: str, content: str) -> None:
        """Send SMS message.

        Args:
            phone: Recipient phone number.
            content: SMS content.
        """
        if not self.sms_enabled:
            return
