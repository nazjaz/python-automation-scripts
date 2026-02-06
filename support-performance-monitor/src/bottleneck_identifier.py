"""Identifies bottlenecks in support operations."""

import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.database import DatabaseManager, SupportTicket, Bottleneck

logger = logging.getLogger(__name__)


class BottleneckIdentifier:
    """Identifies bottlenecks in support ticket processing."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize bottleneck identifier.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.bottleneck_config = config.get("bottleneck_detection", {})
        self.threshold_percentage = config.get("performance", {}).get(
            "bottleneck_threshold_percentage", 20.0
        )
        self.min_tickets = self.bottleneck_config.get("min_tickets_for_analysis", 10)

    def identify_category_bottlenecks(
        self, days: int = 30
    ) -> List[Bottleneck]:
        """Identify bottlenecks by category.

        Args:
            days: Number of days to analyze.

        Returns:
            List of Bottleneck objects.
        """
        if not self.bottleneck_config.get("check_categories", True):
            return []

        from src.resolution_rate_analyzer import ResolutionRateAnalyzer

        analyzer = ResolutionRateAnalyzer(self.db_manager, self.config)

        categories = self.config.get("support", {}).get("ticket_categories", [])
        bottlenecks = []

        for category in categories:
            tickets = self.db_manager.get_tickets(category=category, days=days)

            if len(tickets) < self.min_tickets:
                continue

            open_tickets = [t for t in tickets if t.status not in ["resolved", "closed"]]
            open_percentage = len(open_tickets) / float(len(tickets)) * 100.0

            if open_percentage > self.threshold_percentage:
                resolution_data = analyzer.calculate_resolution_rate(
                    days=days, category=category
                )

                severity = self._determine_severity(open_percentage)

                bottleneck = self.db_manager.add_bottleneck(
                    bottleneck_type="category",
                    identifier=category,
                    severity=severity,
                    description=f"Category '{category}' has {open_percentage:.1f}% open tickets. "
                    f"Resolution rate: {resolution_data['resolution_rate']:.1%}",
                    impact_percentage=open_percentage,
                    ticket_count=len(open_tickets),
                )

                bottlenecks.append(bottleneck)

                logger.info(
                    f"Identified category bottleneck: {category}",
                    extra={
                        "category": category,
                        "open_percentage": open_percentage,
                        "severity": severity,
                    },
                )

        return bottlenecks

    def identify_agent_bottlenecks(
        self, days: int = 30
    ) -> List[Bottleneck]:
        """Identify bottlenecks by agent.

        Args:
            days: Number of days to analyze.

        Returns:
            List of Bottleneck objects.
        """
        if not self.bottleneck_config.get("check_agents", True):
            return []

        from src.resolution_rate_analyzer import ResolutionRateAnalyzer

        analyzer = ResolutionRateAnalyzer(self.db_manager, self.config)

        tickets = self.db_manager.get_tickets(days=days)
        agents = set(t.assigned_agent for t in tickets if t.assigned_agent)

        bottlenecks = []

        for agent in agents:
            agent_tickets = [t for t in tickets if t.assigned_agent == agent]

            if len(agent_tickets) < self.min_tickets:
                continue

            open_tickets = [
                t for t in agent_tickets if t.status not in ["resolved", "closed"]
            ]
            open_percentage = len(open_tickets) / float(len(agent_tickets)) * 100.0

            if open_percentage > self.threshold_percentage:
                resolution_data = analyzer.calculate_resolution_rate(
                    days=days, agent=agent
                )

                severity = self._determine_severity(open_percentage)

                bottleneck = self.db_manager.add_bottleneck(
                    bottleneck_type="agent",
                    identifier=agent,
                    severity=severity,
                    description=f"Agent '{agent}' has {open_percentage:.1f}% open tickets. "
                    f"Resolution rate: {resolution_data['resolution_rate']:.1%}",
                    impact_percentage=open_percentage,
                    ticket_count=len(open_tickets),
                )

                bottlenecks.append(bottleneck)

                logger.info(
                    f"Identified agent bottleneck: {agent}",
                    extra={
                        "agent": agent,
                        "open_percentage": open_percentage,
                        "severity": severity,
                    },
                )

        return bottlenecks

    def identify_time_period_bottlenecks(
        self, days: int = 30
    ) -> List[Bottleneck]:
        """Identify bottlenecks by time period.

        Args:
            days: Number of days to analyze.

        Returns:
            List of Bottleneck objects.
        """
        if not self.bottleneck_config.get("check_time_periods", True):
            return []

        tickets = self.db_manager.get_tickets(days=days)

        if len(tickets) < self.min_tickets:
            return []

        hour_counts = Counter()

        for ticket in tickets:
            if ticket.status not in ["resolved", "closed"]:
                hour = ticket.created_at.hour
                hour_counts[hour] += 1

        total_open = sum(hour_counts.values())
        if total_open == 0:
            return []

        bottlenecks = []

        for hour, count in hour_counts.items():
            percentage = (count / float(total_open)) * 100.0

            if percentage > self.threshold_percentage:
                severity = self._determine_severity(percentage)

                bottleneck = self.db_manager.add_bottleneck(
                    bottleneck_type="time_period",
                    identifier=f"{hour:02d}:00",
                    severity=severity,
                    description=f"Time period {hour:02d}:00 has {percentage:.1f}% of open tickets",
                    impact_percentage=percentage,
                    ticket_count=count,
                )

                bottlenecks.append(bottleneck)

        return bottlenecks

    def identify_all_bottlenecks(
        self, days: int = 30
    ) -> List[Bottleneck]:
        """Identify all types of bottlenecks.

        Args:
            days: Number of days to analyze.

        Returns:
            List of all Bottleneck objects identified.
        """
        all_bottlenecks = []

        all_bottlenecks.extend(self.identify_category_bottlenecks(days=days))
        all_bottlenecks.extend(self.identify_agent_bottlenecks(days=days))
        all_bottlenecks.extend(self.identify_time_period_bottlenecks(days=days))

        logger.info(
            f"Identified {len(all_bottlenecks)} bottlenecks",
            extra={"bottleneck_count": len(all_bottlenecks), "days": days},
        )

        return all_bottlenecks

    def _determine_severity(self, percentage: float) -> str:
        """Determine bottleneck severity based on percentage.

        Args:
            percentage: Impact percentage.

        Returns:
            Severity level string.
        """
        if percentage >= 50.0:
            return "critical"
        elif percentage >= 30.0:
            return "high"
        elif percentage >= 20.0:
            return "medium"
        else:
            return "low"
