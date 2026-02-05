"""Account setup and management for customer onboarding."""

import logging
import uuid
from typing import Optional

from src.database import DatabaseManager, Customer

logger = logging.getLogger(__name__)


class AccountManager:
    """Manages customer account setup and configuration."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize account manager.

        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager

    def setup_account(self, customer_id: int, account_prefix: str = "ACC") -> str:
        """Set up account for a customer.

        Args:
            customer_id: Customer ID.
            account_prefix: Prefix for account ID generation.

        Returns:
            Generated account ID.

        Raises:
            ValueError: If customer not found.
        """
        with self.db_manager.get_session() as session:
            customer = session.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise ValueError(f"Customer with ID {customer_id} not found")

            account_id = f"{account_prefix}-{uuid.uuid4().hex[:8].upper()}"

            customer.account_id = account_id
            session.commit()
            session.refresh(customer)

            logger.info(
                f"Account setup completed for customer {customer_id}",
                extra={"customer_id": customer_id, "account_id": account_id},
            )

            return account_id

    def get_account_info(self, customer_id: int) -> Optional[dict]:
        """Get account information for a customer.

        Args:
            customer_id: Customer ID.

        Returns:
            Dictionary with account information or None if not found.
        """
        with self.db_manager.get_session() as session:
            customer = session.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return None

            return {
                "customer_id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "company_name": customer.company_name,
                "account_id": customer.account_id,
                "is_active": customer.is_active,
                "created_at": customer.created_at.isoformat() if customer.created_at else None,
            }
