"""Tracks customer support response times."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, SupportTicket, TicketResponse, TicketMetrics

logger = logging.getLogger(__name__)


class ResponseTimeTracker:
    """Tracks and calculates response times for support tickets."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize response time tracker.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.support_config = config.get("support", {})
        self.thresholds = self.support_config.get("response_time_thresholds", {})
        self.first_response_threshold = self.thresholds.get("first_response_minutes", 60)

    def calculate_first_response_time(
        self, ticket: SupportTicket
    ) -> Optional[float]:
        """Calculate first response time for ticket.

        Args:
            ticket: SupportTicket object.

        Returns:
            First response time in minutes or None if no response yet.
        """
        if not ticket.first_response_at:
            return None

        time_diff = ticket.first_response_at - ticket.created_at
        return time_diff.total_seconds() / 60.0

    def calculate_resolution_time(
        self, ticket: SupportTicket
    ) -> Optional[float]:
        """Calculate resolution time for ticket.

        Args:
            ticket: SupportTicket object.

        Returns:
            Resolution time in hours or None if not resolved.
        """
        if not ticket.resolved_at:
            return None

        time_diff = ticket.resolved_at - ticket.created_at
        return time_diff.total_seconds() / 3600.0

    def track_response_time(
        self, ticket_id: int, response_id: int
    ) -> Optional[float]:
        """Track response time for a specific response.

        Args:
            ticket_id: Ticket ID.
            response_id: Response ID.

        Returns:
            Response time in minutes or None if error.
        """
        ticket = (
            self.db_manager.get_session()
            .query(SupportTicket)
            .filter(SupportTicket.id == ticket_id)
            .first()
        )

        response = (
            self.db_manager.get_session()
            .query(TicketResponse)
            .filter(TicketResponse.id == response_id)
            .first()
        )

        if not ticket or not response:
            return None

        if response.response_type == "agent":
            if not ticket.first_response_at:
                ticket.first_response_at = response.created_at
                self.db_manager.update_ticket_status(
                    ticket_id=ticket_id,
                    status=ticket.status,
                    first_response_at=response.created_at,
                )

            time_diff = response.created_at - ticket.created_at
            response_time_minutes = time_diff.total_seconds() / 60.0

            response.response_time_minutes = response_time_minutes
            session = self.db_manager.get_session()
            try:
                session.merge(response)
                session.commit()
            finally:
                session.close()

            return response_time_minutes

        return None

    def update_ticket_metrics(self, ticket_id: int) -> Optional[TicketMetrics]:
        """Update metrics for a ticket.

        Args:
            ticket_id: Ticket ID.

        Returns:
            TicketMetrics object or None if error.
        """
        ticket = (
            self.db_manager.get_session()
            .query(SupportTicket)
            .filter(SupportTicket.id == ticket_id)
            .first()
        )

        if not ticket:
            return None

        first_response_time = self.calculate_first_response_time(ticket)
        resolution_time = self.calculate_resolution_time(ticket)

        responses = (
            self.db_manager.get_session()
            .query(TicketResponse)
            .filter(TicketResponse.ticket_id == ticket_id)
            .all()
        )

        response_count = len(responses)

        sla_met = None
        if first_response_time is not None:
            sla_met = first_response_time <= self.first_response_threshold

        existing_metrics = (
            self.db_manager.get_session()
            .query(TicketMetrics)
            .filter(TicketMetrics.ticket_id == ticket_id)
            .first()
        )

        if existing_metrics:
            existing_metrics.first_response_time_minutes = first_response_time
            existing_metrics.resolution_time_hours = resolution_time
            existing_metrics.response_count = response_count
            existing_metrics.sla_met = sla_met
            session = self.db_manager.get_session()
            try:
                session.merge(existing_metrics)
                session.commit()
                session.refresh(existing_metrics)
                return existing_metrics
            finally:
                session.close()
        else:
            return self.db_manager.add_metrics(
                ticket_id=ticket_id,
                first_response_time_minutes=first_response_time,
                resolution_time_hours=resolution_time,
                response_count=response_count,
                sla_met=sla_met,
            )

    def get_average_response_time(
        self,
        days: int = 30,
        category: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> Optional[float]:
        """Calculate average first response time.

        Args:
            days: Number of days to analyze.
            category: Optional category filter.
            agent: Optional agent filter.

        Returns:
            Average response time in minutes or None if no data.
        """
        tickets = self.db_manager.get_tickets(
            status="resolved", category=category, agent=agent, days=days
        )

        response_times = []

        for ticket in tickets:
            first_response_time = self.calculate_first_response_time(ticket)
            if first_response_time is not None:
                response_times.append(first_response_time)

        if not response_times:
            return None

        return sum(response_times) / len(response_times)

    def get_sla_compliance_rate(
        self,
        days: int = 30,
        category: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> Optional[float]:
        """Calculate SLA compliance rate.

        Args:
            days: Number of days to analyze.
            category: Optional category filter.
            agent: Optional agent filter.

        Returns:
            SLA compliance rate (0.0 to 1.0) or None if no data.
        """
        tickets = self.db_manager.get_tickets(
            category=category, agent=agent, days=days
        )

        tickets_with_response = 0
        sla_met_count = 0

        for ticket in tickets:
            first_response_time = self.calculate_first_response_time(ticket)
            if first_response_time is not None:
                tickets_with_response += 1
                if first_response_time <= self.first_response_threshold:
                    sla_met_count += 1

        if tickets_with_response == 0:
            return None

        return sla_met_count / float(tickets_with_response)

    def track_all_tickets(self, days: Optional[int] = None) -> int:
        """Track response times for all tickets.

        Args:
            days: Optional number of days to look back.

        Returns:
            Number of tickets processed.
        """
        tickets = self.db_manager.get_tickets(days=days)

        tracked_count = 0

        for ticket in tickets:
            try:
                self.update_ticket_metrics(ticket.id)
                tracked_count += 1
            except Exception as e:
                logger.error(
                    f"Error tracking ticket {ticket.id}: {e}",
                    extra={"ticket_id": ticket.id, "error": str(e)},
                )

        logger.info(
            f"Tracked response times for {tracked_count} tickets",
            extra={"tracked_count": tracked_count, "days": days},
        )

        return tracked_count
