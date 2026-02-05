"""License usage tracking service."""

import logging
from datetime import datetime
from typing import Optional

from src.database import DatabaseManager, License, LicenseUsage

logger = logging.getLogger(__name__)


class UsageTracker:
    """Tracks license usage over time."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize usage tracker.

        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager

    def record_usage(
        self,
        license_id: int,
        user_email: str,
        usage_duration_minutes: int = 0,
        is_active: bool = True,
    ) -> LicenseUsage:
        """Record license usage.

        Args:
            license_id: License ID.
            user_email: User email address.
            usage_duration_minutes: Duration of usage in minutes.
            is_active: Whether usage is currently active.

        Returns:
            Created LicenseUsage object.
        """
        with self.db_manager.get_session() as session:
            usage = LicenseUsage(
                license_id=license_id,
                user_email=user_email,
                usage_duration_minutes=usage_duration_minutes,
                is_active=is_active,
            )
            session.add(usage)
            session.commit()
            session.refresh(usage)

        logger.debug(f"Recorded usage for license {license_id} by {user_email}")
        return usage

    def get_usage_stats(
        self, license_id: Optional[int] = None, license_type: Optional[str] = None
    ) -> dict:
        """Get usage statistics.

        Args:
            license_id: Specific license ID (optional).
            license_type: License type (optional).

        Returns:
            Dictionary with usage statistics.
        """
        with self.db_manager.get_session() as session:
            query = session.query(LicenseUsage)

            if license_id:
                query = query.filter(LicenseUsage.license_id == license_id)
            elif license_type:
                licenses = (
                    session.query(License.id)
                    .join(License)
                    .filter(License.license_type == license_type)
                    .all()
                )
                license_ids = [l[0] for l in licenses]
                query = query.filter(LicenseUsage.license_id.in_(license_ids))

            total_usage = query.count()
            active_usage = query.filter(LicenseUsage.is_active == True).count()
            unique_users = query.distinct(LicenseUsage.user_email).count()

            return {
                "total_usage_records": total_usage,
                "active_usage": active_usage,
                "unique_users": unique_users,
            }

    def get_last_usage_date(self, license_id: int) -> Optional[datetime]:
        """Get last usage date for a license.

        Args:
            license_id: License ID.

        Returns:
            Last usage date or None if never used.
        """
        with self.db_manager.get_session() as session:
            last_usage = (
                session.query(LicenseUsage)
                .filter(LicenseUsage.license_id == license_id)
                .order_by(LicenseUsage.usage_date.desc())
                .first()
            )

            return last_usage.usage_date if last_usage else None
