"""Analyzes resolution rates for support tickets."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, SupportTicket, PerformanceMetric

logger = logging.getLogger(__name__)


class ResolutionRateAnalyzer:
    """Analyzes resolution rates and performance metrics."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize resolution rate analyzer.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.performance_config = config.get("performance", {})
        self.resolution_target = self.performance_config.get("resolution_rate_target", 0.85)

    def calculate_resolution_rate(
        self,
        days: int = 30,
        category: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> Dict:
        """Calculate resolution rate for tickets.

        Args:
            days: Number of days to analyze.
            category: Optional category filter.
            agent: Optional agent filter.

        Returns:
            Dictionary with resolution rate and related metrics.
        """
        tickets = self.db_manager.get_tickets(
            category=category, agent=agent, days=days
        )

        total_tickets = len(tickets)
        resolved_tickets = len([t for t in tickets if t.status in ["resolved", "closed"]])

        resolution_rate = resolved_tickets / float(total_tickets) if total_tickets > 0 else 0.0

        resolved_tickets_list = [t for t in tickets if t.status in ["resolved", "closed"]]
        resolution_times = []

        for ticket in resolved_tickets_list:
            if ticket.resolved_at:
                time_diff = ticket.resolved_at - ticket.created_at
                resolution_times.append(time_diff.total_seconds() / 3600.0)

        average_resolution_time = (
            sum(resolution_times) / len(resolution_times)
            if resolution_times
            else None
        )

        return {
            "total_tickets": total_tickets,
            "resolved_tickets": resolved_tickets,
            "resolution_rate": resolution_rate,
            "average_resolution_time_hours": average_resolution_time,
        }

    def calculate_average_resolution_time(
        self,
        days: int = 30,
        category: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> Optional[float]:
        """Calculate average resolution time.

        Args:
            days: Number of days to analyze.
            category: Optional category filter.
            agent: Optional agent filter.

        Returns:
            Average resolution time in hours or None if no resolved tickets.
        """
        tickets = self.db_manager.get_tickets(
            status="resolved", category=category, agent=agent, days=days
        )

        resolution_times = []

        for ticket in tickets:
            if ticket.resolved_at:
                time_diff = ticket.resolved_at - ticket.created_at
                resolution_times.append(time_diff.total_seconds() / 3600.0)

        if not resolution_times:
            return None

        return sum(resolution_times) / len(resolution_times)

    def generate_performance_metrics(
        self,
        days: int = 30,
        category: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> PerformanceMetric:
        """Generate and store performance metrics.

        Args:
            days: Number of days to analyze.
            category: Optional category filter.
            agent: Optional agent filter.

        Returns:
            PerformanceMetric object.
        """
        from src.response_time_tracker import ResponseTimeTracker

        response_tracker = ResponseTimeTracker(self.db_manager, self.config)

        resolution_data = self.calculate_resolution_rate(
            days=days, category=category, agent=agent
        )

        average_response_time = response_tracker.get_average_response_time(
            days=days, category=category, agent=agent
        )

        sla_compliance = response_tracker.get_sla_compliance_rate(
            days=days, category=category, agent=agent
        )

        sla_compliance_percentage = (
            sla_compliance * 100.0 if sla_compliance is not None else None
        )

        metric = self.db_manager.add_performance_metric(
            metric_date=datetime.utcnow(),
            category=category,
            agent=agent,
            total_tickets=resolution_data["total_tickets"],
            resolved_tickets=resolution_data["resolved_tickets"],
            resolution_rate=resolution_data["resolution_rate"],
            average_response_time_minutes=average_response_time,
            average_resolution_time_hours=resolution_data["average_resolution_time_hours"],
            sla_compliance_percentage=sla_compliance_percentage,
        )

        logger.info(
            f"Generated performance metrics",
            extra={
                "category": category,
                "agent": agent,
                "resolution_rate": resolution_data["resolution_rate"],
            },
        )

        return metric

    def get_resolution_rate_by_category(
        self, days: int = 30
    ) -> Dict[str, float]:
        """Get resolution rates by category.

        Args:
            days: Number of days to analyze.

        Returns:
            Dictionary mapping category names to resolution rates.
        """
        categories = self.config.get("support", {}).get("ticket_categories", [])

        rates_by_category = {}

        for category in categories:
            data = self.calculate_resolution_rate(days=days, category=category)
            rates_by_category[category] = data["resolution_rate"]

        return rates_by_category

    def get_resolution_rate_by_agent(
        self, days: int = 30
    ) -> Dict[str, float]:
        """Get resolution rates by agent.

        Args:
            days: Number of days to analyze.

        Returns:
            Dictionary mapping agent names to resolution rates.
        """
        tickets = self.db_manager.get_tickets(days=days)

        agents = set(t.assigned_agent for t in tickets if t.assigned_agent)

        rates_by_agent = {}

        for agent in agents:
            data = self.calculate_resolution_rate(days=days, agent=agent)
            rates_by_agent[agent] = data["resolution_rate"]

        return rates_by_agent

    def identify_low_performance_areas(
        self, days: int = 30, threshold: Optional[float] = None
    ) -> List[Dict]:
        """Identify areas with low resolution rates.

        Args:
            days: Number of days to analyze.
            threshold: Optional threshold (defaults to target rate).

        Returns:
            List of dictionaries with low performance areas.
        """
        if threshold is None:
            threshold = self.resolution_target

        low_performance = []

        categories = self.config.get("support", {}).get("ticket_categories", [])
        for category in categories:
            data = self.calculate_resolution_rate(days=days, category=category)
            if data["resolution_rate"] < threshold:
                low_performance.append(
                    {
                        "type": "category",
                        "identifier": category,
                        "resolution_rate": data["resolution_rate"],
                        "total_tickets": data["total_tickets"],
                        "resolved_tickets": data["resolved_tickets"],
                    }
                )

        tickets = self.db_manager.get_tickets(days=days)
        agents = set(t.assigned_agent for t in tickets if t.assigned_agent)

        for agent in agents:
            data = self.calculate_resolution_rate(days=days, agent=agent)
            if data["resolution_rate"] < threshold:
                low_performance.append(
                    {
                        "type": "agent",
                        "identifier": agent,
                        "resolution_rate": data["resolution_rate"],
                        "total_tickets": data["total_tickets"],
                        "resolved_tickets": data["resolved_tickets"],
                    }
                )

        return low_performance
