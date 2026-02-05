"""License data collection from various sources."""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from src.database import DatabaseManager, License

logger = logging.getLogger(__name__)


class LicenseCollector:
    """Collects license data from multiple sources."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize license collector.

        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager

    def collect_from_source(self, source_config: dict, settings: object) -> int:
        """Collect licenses from a configured source.

        Args:
            source_config: Source configuration dictionary.
            settings: Application settings.

        Returns:
            Number of licenses collected.
        """
        source_type = source_config.get("type", "").lower()
        source_name = source_config.get("name", "unknown")

        if not source_config.get("enabled", True):
            logger.info(f"Source {source_name} is disabled, skipping")
            return 0

        try:
            if source_type == "ldap":
                return self._collect_from_ldap(source_config, settings)
            elif source_type == "api":
                return self._collect_from_api(source_config, settings)
            elif source_type == "csv":
                return self._collect_from_csv(source_config)
            else:
                logger.warning(f"Unsupported source type: {source_type}")
                return 0
        except Exception as e:
            logger.error(f"Error collecting from {source_name}: {e}")
            return 0

    def _collect_from_ldap(
        self, source_config: dict, settings: object
    ) -> int:
        """Collect licenses from LDAP/Active Directory.

        Args:
            source_config: Source configuration.
            settings: Application settings.

        Returns:
            Number of licenses collected.
        """
        connection_string = (
            source_config.get("connection_string")
            or settings.ad_connection_string
        )

        if not connection_string:
            logger.warning("LDAP connection string not configured")
            return 0

        logger.info(f"Collecting licenses from LDAP: {connection_string}")

        collected = 0
        try:
            licenses_data = self._query_ldap(connection_string)
            for license_data in licenses_data:
                self.db_manager.create_license(
                    license_type=license_data.get("type", "Unknown"),
                    license_key=license_data.get("key", ""),
                    source=source_config.get("name", "ldap"),
                    assigned_to=license_data.get("user"),
                    assigned_email=license_data.get("email"),
                )
                collected += 1
        except Exception as e:
            logger.error(f"LDAP collection error: {e}")

        return collected

    def _query_ldap(self, connection_string: str) -> list[dict]:
        """Query LDAP for license information (mock implementation).

        Args:
            connection_string: LDAP connection string.

        Returns:
            List of license dictionaries.
        """
        return []

    def _collect_from_api(self, source_config: dict, settings: object) -> int:
        """Collect licenses from API source.

        Args:
            source_config: Source configuration.
            settings: Application settings.

        Returns:
            Number of licenses collected.
        """
        api_url = source_config.get("api_url") or settings.snow_api_url
        api_key = source_config.get("api_key") or settings.snow_api_key

        if not api_url or not api_key:
            logger.warning("API URL or key not configured")
            return 0

        logger.info(f"Collecting licenses from API: {api_url}")

        collected = 0
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(f"{api_url}/licenses", headers=headers, timeout=30)
            response.raise_for_status()

            licenses_data = response.json().get("result", [])
            for license_data in licenses_data:
                self.db_manager.create_license(
                    license_type=license_data.get("type", "Unknown"),
                    license_key=license_data.get("key", ""),
                    source=source_config.get("name", "api"),
                    assigned_to=license_data.get("user"),
                    assigned_email=license_data.get("email"),
                    cost=license_data.get("cost"),
                    currency=license_data.get("currency", "USD"),
                )
                collected += 1
        except requests.exceptions.RequestException as e:
            logger.error(f"API collection error: {e}")

        return collected

    def _collect_from_csv(self, source_config: dict) -> int:
        """Collect licenses from CSV file.

        Args:
            source_config: Source configuration.

        Returns:
            Number of licenses collected.
        """
        file_path = Path(source_config.get("file_path", "data/licenses.csv"))

        if not file_path.exists():
            logger.warning(f"CSV file not found: {file_path}")
            return 0

        logger.info(f"Collecting licenses from CSV: {file_path}")

        collected = 0
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.db_manager.create_license(
                        license_type=row.get("type", "Unknown"),
                        license_key=row.get("key", ""),
                        source=source_config.get("name", "csv"),
                        assigned_to=row.get("user"),
                        assigned_email=row.get("email"),
                        cost=float(row.get("cost", 0)) if row.get("cost") else None,
                        currency=row.get("currency", "USD"),
                    )
                    collected += 1
        except Exception as e:
            logger.error(f"CSV collection error: {e}")

        return collected
