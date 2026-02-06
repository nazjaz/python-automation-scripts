"""Monitors backup locations and tracks backup files."""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.database import DatabaseManager, BackupLocation, Backup

logger = logging.getLogger(__name__)


class BackupMonitor:
    """Monitors backup locations and tracks backup files."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize backup monitor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.backup_config = config.get("backups", {})
        self.verification_config = self.backup_config.get("verification", {})

    def scan_backup_location(
        self, location: BackupLocation
    ) -> List[Backup]:
        """Scan backup location for backup files.

        Args:
            location: BackupLocation object.

        Returns:
            List of Backup objects found or created.
        """
        backup_path = Path(location.path)

        if not backup_path.exists():
            logger.warning(
                f"Backup location does not exist: {location.path}",
                extra={"location_id": location.id, "path": location.path},
            )
            return []

        if not backup_path.is_dir():
            logger.warning(
                f"Backup location is not a directory: {location.path}",
                extra={"location_id": location.id, "path": location.path},
            )
            return []

        backups_found = []

        try:
            for file_path in backup_path.iterdir():
                if file_path.is_file():
                    backup = self._process_backup_file(file_path, location)
                    if backup:
                        backups_found.append(backup)
        except PermissionError as e:
            logger.error(
                f"Permission denied accessing backup location: {location.path}",
                extra={"location_id": location.id, "error": str(e)},
            )
        except Exception as e:
            logger.error(
                f"Error scanning backup location: {location.path}",
                extra={"location_id": location.id, "error": str(e)},
            )

        logger.info(
            f"Scanned backup location {location.name}: {len(backups_found)} backups found",
            extra={
                "location_id": location.id,
                "location_name": location.name,
                "backup_count": len(backups_found),
            },
        )

        return backups_found

    def _process_backup_file(
        self, file_path: Path, location: BackupLocation
    ) -> Optional[Backup]:
        """Process a backup file and create or update database record.

        Args:
            file_path: Path to backup file.
            location: BackupLocation object.

        Returns:
            Backup object or None if error.
        """
        try:
            stat = file_path.stat()
            size_bytes = stat.st_size
            backup_timestamp = datetime.fromtimestamp(stat.st_mtime)

            existing_backups = self.db_manager.get_recent_backups(
                location_id=location.id, limit=1000
            )

            existing = None
            for backup in existing_backups:
                if backup.filepath == str(file_path):
                    existing = backup
                    break

            checksum = None
            checksum_algorithm = None

            if self.verification_config.get("enabled", True):
                algorithm = self.verification_config.get("checksum_algorithm", "sha256")
                try:
                    checksum = self._calculate_checksum(file_path, algorithm)
                    checksum_algorithm = algorithm
                except Exception as e:
                    logger.warning(
                        f"Failed to calculate checksum for {file_path}: {e}",
                        extra={"file_path": str(file_path), "error": str(e)},
                    )

            if existing:
                existing.size_bytes = size_bytes
                existing.backup_timestamp = backup_timestamp
                if checksum:
                    existing.checksum = checksum
                    existing.checksum_algorithm = checksum_algorithm
                if existing.status == "pending":
                    existing.status = "completed"
                session = self.db_manager.get_session()
                try:
                    session.merge(existing)
                    session.commit()
                    session.refresh(existing)
                    return existing
                finally:
                    session.close()
            else:
                backup = self.db_manager.add_backup(
                    location_id=location.id,
                    filename=file_path.name,
                    filepath=str(file_path),
                    backup_timestamp=backup_timestamp,
                    size_bytes=size_bytes,
                    checksum=checksum,
                    checksum_algorithm=checksum_algorithm,
                    status="completed",
                )
                return backup

        except Exception as e:
            logger.error(
                f"Error processing backup file {file_path}: {e}",
                extra={"file_path": str(file_path), "error": str(e)},
            )
            return None

    def _calculate_checksum(self, file_path: Path, algorithm: str = "sha256") -> str:
        """Calculate file checksum.

        Args:
            file_path: Path to file.
            algorithm: Hash algorithm (sha256, md5, etc.).

        Returns:
            Hexadecimal checksum string.
        """
        hash_obj = hashlib.new(algorithm)

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    def monitor_all_locations(self) -> Dict[str, List[Backup]]:
        """Monitor all enabled backup locations.

        Returns:
            Dictionary mapping location names to lists of Backup objects.
        """
        locations = self.db_manager.get_backup_locations(enabled_only=True)
        all_backups = {}

        for location in locations:
            backups = self.scan_backup_location(location)
            all_backups[location.name] = backups

        logger.info(
            f"Monitored {len(locations)} backup locations",
            extra={"location_count": len(locations)},
        )

        return all_backups

    def check_backup_health(
        self, location_id: Optional[int] = None, days: int = 7
    ) -> Dict:
        """Check backup health for location(s).

        Args:
            location_id: Optional location ID filter.
            days: Number of days to analyze.

        Returns:
            Dictionary with health metrics.
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        if location_id:
            locations = [self.db_manager.get_session().query(BackupLocation).filter(BackupLocation.id == location_id).first()]
            locations = [l for l in locations if l]
        else:
            locations = self.db_manager.get_backup_locations(enabled_only=True)

        health_data = {}

        for location in locations:
            backups = self.db_manager.get_recent_backups(
                location_id=location.id, days=days
            )

            recent_backups = [b for b in backups if b.created_at >= cutoff_date]

            total = len(recent_backups)
            successful = len([b for b in recent_backups if b.status == "completed"])
            failed = len([b for b in recent_backups if b.status == "failed"])

            total_size = sum(b.size_bytes or 0 for b in recent_backups)

            success_rate = successful / total if total > 0 else 0.0

            health_data[location.name] = {
                "total_backups": total,
                "successful_backups": successful,
                "failed_backups": failed,
                "success_rate": success_rate,
                "total_size_bytes": total_size,
                "location_id": location.id,
            }

        return health_data
