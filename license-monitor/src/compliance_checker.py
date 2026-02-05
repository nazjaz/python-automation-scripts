"""License compliance checking service."""

import logging
from datetime import datetime

from src.database import DatabaseManager, ComplianceRecord, License

logger = logging.getLogger(__name__)


class ComplianceChecker:
    """Checks license compliance status."""

    def __init__(self, db_manager: DatabaseManager, threshold: float = 0.95):
        """Initialize compliance checker.

        Args:
            db_manager: Database manager instance.
            threshold: Minimum compliance percentage (0.0 to 1.0).
        """
        self.db_manager = db_manager
        self.threshold = threshold

    def check_compliance(self, license_type: str) -> ComplianceRecord:
        """Check compliance for a specific license type.

        Args:
            license_type: License type name.

        Returns:
            ComplianceRecord with compliance status.
        """
        licenses = self.db_manager.get_licenses_by_type(license_type)
        total_licenses = len(licenses)
        assigned_licenses = sum(1 for l in licenses if l.assigned_to)
        unused_licenses = len(self.db_manager.get_unused_licenses(threshold_days=90))

        if total_licenses > 0:
            compliance_percentage = assigned_licenses / total_licenses
        else:
            compliance_percentage = 1.0

        status = "compliant" if compliance_percentage >= self.threshold else "non_compliant"

        with self.db_manager.get_session() as session:
            record = ComplianceRecord(
                license_type=license_type,
                total_licenses=total_licenses,
                assigned_licenses=assigned_licenses,
                unused_licenses=unused_licenses,
                compliance_percentage=compliance_percentage,
                status=status,
            )
            session.add(record)
            session.commit()
            session.refresh(record)

        logger.info(
            f"Compliance check for {license_type}: {compliance_percentage:.2%} "
            f"({status})"
        )

        return record

    def check_all_compliance(self, license_types: list[str]) -> list[ComplianceRecord]:
        """Check compliance for all license types.

        Args:
            license_types: List of license type names.

        Returns:
            List of ComplianceRecord objects.
        """
        records = []
        for license_type in license_types:
            try:
                record = self.check_compliance(license_type)
                records.append(record)
            except Exception as e:
                logger.error(f"Error checking compliance for {license_type}: {e}")

        return records
