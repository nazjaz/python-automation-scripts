"""Processes event registrations with capacity tracking."""

import logging
from typing import Dict, Optional

from src.database import DatabaseManager, Event, Registration

logger = logging.getLogger(__name__)


class RegistrationProcessor:
    """Processes event registrations and manages capacity."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize registration processor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.events_config = config.get("events", {})
        self.auto_confirm = self.events_config.get("auto_confirm", True)

    def process_registration(
        self,
        event_id: int,
        name: str,
        email: str,
        company: Optional[str] = None,
        phone: Optional[str] = None,
        ticket_type: Optional[str] = None,
        dietary_restrictions: Optional[str] = None,
        special_requests: Optional[str] = None,
    ) -> Dict:
        """Process a new registration.

        Args:
            event_id: Event ID.
            name: Registrant name.
            email: Registrant email.
            company: Optional company name.
            phone: Optional phone number.
            ticket_type: Optional ticket type.
            dietary_restrictions: Optional dietary restrictions.
            special_requests: Optional special requests.

        Returns:
            Dictionary with registration result including status and waitlist info.
        """
        event = self.db_manager.get_event(event_id)

        if not event:
            logger.error(f"Event {event_id} not found", extra={"event_id": event_id})
            return {
                "success": False,
                "error": f"Event {event_id} not found",
            }

        if event.status != "active":
            logger.warning(
                f"Event {event_id} is not active",
                extra={"event_id": event_id, "status": event.status},
            )
            return {
                "success": False,
                "error": f"Event is not accepting registrations (status: {event.status})",
            }

        existing_reg = (
            self.db_manager.get_session()
            .query(Registration)
            .filter(Registration.event_id == event_id)
            .filter(Registration.email == email)
            .first()
        )

        if existing_reg:
            logger.warning(
                f"Registration already exists for {email}",
                extra={"event_id": event_id, "email": email},
            )
            return {
                "success": False,
                "error": "Registration already exists for this email",
                "registration_id": existing_reg.id,
            }

        available_spots = event.capacity - event.current_registrations
        is_waitlist = available_spots <= 0

        if is_waitlist:
            if not event.allow_waitlist:
                logger.warning(
                    f"Event {event_id} is full and waitlist is not allowed",
                    extra={"event_id": event_id, "capacity": event.capacity},
                )
                return {
                    "success": False,
                    "error": "Event is full and waitlist is not available",
                }

            waitlist_regs = self.db_manager.get_waitlist_registrations(event_id)
            waitlist_position = len(waitlist_regs) + 1

            registration = self.db_manager.add_registration(
                event_id=event_id,
                name=name,
                email=email,
                company=company,
                phone=phone,
                ticket_type=ticket_type,
                dietary_restrictions=dietary_restrictions,
                special_requests=special_requests,
                status="pending",
                is_waitlist=True,
            )

            registration.waitlist_position = waitlist_position
            session = self.db_manager.get_session()
            try:
                session.merge(registration)
                session.commit()
            finally:
                session.close()

            logger.info(
                f"Added to waitlist: {email}",
                extra={
                    "event_id": event_id,
                    "registration_id": registration.id,
                    "waitlist_position": waitlist_position,
                },
            )

            return {
                "success": True,
                "registration_id": registration.id,
                "status": "waitlist",
                "waitlist_position": waitlist_position,
                "is_waitlist": True,
            }

        else:
            status = "confirmed" if self.auto_confirm else "pending"

            registration = self.db_manager.add_registration(
                event_id=event_id,
                name=name,
                email=email,
                company=company,
                phone=phone,
                ticket_type=ticket_type,
                dietary_restrictions=dietary_restrictions,
                special_requests=special_requests,
                status=status,
                is_waitlist=False,
            )

            if status == "confirmed":
                from datetime import datetime
                registration.confirmed_at = datetime.utcnow()
                session = self.db_manager.get_session()
                try:
                    session.merge(registration)
                    session.commit()
                finally:
                    session.close()

            self.db_manager.update_event_registration_count(event_id)

            logger.info(
                f"Registration processed: {email}",
                extra={
                    "event_id": event_id,
                    "registration_id": registration.id,
                    "status": status,
                },
            )

            return {
                "success": True,
                "registration_id": registration.id,
                "status": status,
                "is_waitlist": False,
            }

    def confirm_registration(self, registration_id: int) -> Optional[Registration]:
        """Confirm a pending registration.

        Args:
            registration_id: Registration ID.

        Returns:
            Updated Registration object or None if error.
        """
        registration = (
            self.db_manager.get_session()
            .query(Registration)
            .filter(Registration.id == registration_id)
            .first()
        )

        if not registration:
            logger.error(
                f"Registration {registration_id} not found",
                extra={"registration_id": registration_id},
            )
            return None

        if registration.status == "confirmed":
            logger.warning(
                f"Registration {registration_id} already confirmed",
                extra={"registration_id": registration_id},
            )
            return registration

        updated = self.db_manager.update_registration_status(
            registration_id=registration_id,
            status="confirmed",
            is_waitlist=False,
        )

        if updated:
            self.db_manager.update_event_registration_count(registration.event_id)

            logger.info(
                f"Registration confirmed: {registration_id}",
                extra={"registration_id": registration_id},
            )

        return updated

    def cancel_registration(self, registration_id: int) -> Optional[Registration]:
        """Cancel a registration.

        Args:
            registration_id: Registration ID.

        Returns:
            Updated Registration object or None if error.
        """
        registration = (
            self.db_manager.get_session()
            .query(Registration)
            .filter(Registration.id == registration_id)
            .first()
        )

        if not registration:
            return None

        was_confirmed = registration.status == "confirmed"
        was_waitlist = registration.is_waitlist

        updated = self.db_manager.update_registration_status(
            registration_id=registration_id,
            status="cancelled",
        )

        if updated and was_confirmed:
            self.db_manager.update_event_registration_count(registration.event_id)

            if registration.event.allow_waitlist:
                self._promote_from_waitlist(registration.event_id)

        if updated and was_waitlist:
            self.db_manager.update_waitlist_positions(registration.event_id)

        logger.info(
            f"Registration cancelled: {registration_id}",
            extra={"registration_id": registration_id},
        )

        return updated

    def _promote_from_waitlist(self, event_id: int) -> Optional[Registration]:
        """Promote first waitlist registration to confirmed.

        Args:
            event_id: Event ID.

        Returns:
            Promoted Registration object or None if no waitlist.
        """
        event = self.db_manager.get_event(event_id)

        if not event or event.current_registrations >= event.capacity:
            return None

        waitlist_reg = self.db_manager.get_waitlist_registrations(event_id, limit=1)

        if not waitlist_reg:
            return None

        registration = waitlist_reg[0]

        updated = self.db_manager.update_registration_status(
            registration_id=registration.id,
            status="confirmed",
            is_waitlist=False,
            waitlist_position=None,
        )

        if updated:
            self.db_manager.update_event_registration_count(event_id)
            self.db_manager.update_waitlist_positions(event_id)

            logger.info(
                f"Promoted from waitlist: {registration.id}",
                extra={
                    "event_id": event_id,
                    "registration_id": registration.id,
                },
            )

        return updated
