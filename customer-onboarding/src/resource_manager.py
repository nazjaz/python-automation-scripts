"""Resource assignment and management for customer onboarding."""

import logging
from typing import Optional

import requests

from src.database import DatabaseManager, ResourceAssignment

logger = logging.getLogger(__name__)


class ResourceManager:
    """Manages resource assignment for customers."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        """Initialize resource manager.

        Args:
            db_manager: Database manager instance.
            api_url: Optional API URL for external resource assignment.
            api_key: Optional API key for authentication.
            timeout: API request timeout in seconds.
        """
        self.db_manager = db_manager
        self.api_url = api_url
        self.api_key = api_key
        self.timeout = timeout

    def assign_default_resources(
        self, customer_id: int, default_resources: list[dict]
    ) -> list[ResourceAssignment]:
        """Assign default resources to a customer.

        Args:
            customer_id: Customer ID.
            default_resources: List of default resource configurations.

        Returns:
            List of created ResourceAssignment objects.
        """
        assignments = []
        with self.db_manager.get_session() as session:
            for resource in default_resources:
                assignment = ResourceAssignment(
                    customer_id=customer_id,
                    resource_type=resource["type"],
                    resource_name=resource["name"],
                )
                session.add(assignment)
                assignments.append(assignment)

            session.commit()

            for assignment in assignments:
                session.refresh(assignment)

        logger.info(
            f"Assigned {len(assignments)} default resources to customer {customer_id}",
            extra={"customer_id": customer_id, "resource_count": len(assignments)},
        )

        return assignments

    def assign_resource_via_api(
        self, customer_id: int, resource_type: str, resource_name: str
    ) -> bool:
        """Assign resource via external API if configured.

        Args:
            customer_id: Customer ID.
            resource_type: Type of resource to assign.
            resource_name: Name of resource to assign.

        Returns:
            True if assignment successful, False otherwise.
        """
        if not self.api_url or not self.api_key:
            logger.debug(
                "Resource API not configured, skipping API assignment",
                extra={"customer_id": customer_id},
            )
            return False

        try:
            payload = {
                "customer_id": customer_id,
                "resource_type": resource_type,
                "resource_name": resource_name,
            }
            headers = {"Authorization": f"Bearer {self.api_key}"}

            response = requests.post(
                f"{self.api_url}/assign",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()

            logger.info(
                f"Resource assigned via API: {resource_name}",
                extra={
                    "customer_id": customer_id,
                    "resource_type": resource_type,
                    "resource_name": resource_name,
                },
            )
            return True
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Failed to assign resource via API: {e}",
                extra={
                    "customer_id": customer_id,
                    "resource_type": resource_type,
                    "error": str(e),
                },
            )
            return False

    def assign_resources(
        self, customer_id: int, default_resources: list[dict]
    ) -> dict:
        """Assign all resources to a customer.

        Args:
            customer_id: Customer ID.
            default_resources: List of default resource configurations.

        Returns:
            Dictionary with assignment results.
        """
        db_assignments = self.assign_default_resources(customer_id, default_resources)

        api_results = {}
        if self.api_url:
            for resource in default_resources:
                api_results[resource["name"]] = self.assign_resource_via_api(
                    customer_id, resource["type"], resource["name"]
                )

        return {
            "database_assignments": len(db_assignments),
            "api_assignments": api_results,
        }
