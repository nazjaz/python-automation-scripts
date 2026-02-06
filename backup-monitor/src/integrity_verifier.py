"""Verifies backup integrity using multiple methods."""

import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.database import DatabaseManager, Backup, BackupVerification

logger = logging.getLogger(__name__)


class IntegrityVerifier:
    """Verifies backup integrity using checksums, size validation, and timestamps."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize integrity verifier.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.verification_config = config.get("backups", {}).get("verification", {})
        self.methods = self.verification_config.get("methods", ["checksum", "size_validation"])

    def verify_backup(
        self, backup: Backup
    ) -> List[BackupVerification]:
        """Verify backup integrity using configured methods.

        Args:
            backup: Backup object to verify.

        Returns:
            List of BackupVerification objects.
        """
        file_path = Path(backup.filepath)

        if not file_path.exists():
            verification = self.db_manager.add_verification(
                backup_id=backup.id,
                verification_type="file_existence",
                status="failed",
                error_message=f"Backup file does not exist: {backup.filepath}",
            )
            logger.error(
                f"Backup file does not exist: {backup.filepath}",
                extra={"backup_id": backup.id, "filepath": backup.filepath},
            )
            return [verification]

        verifications = []

        for method in self.methods:
            if method == "checksum":
                verification = self._verify_checksum(backup, file_path)
                if verification:
                    verifications.append(verification)

            elif method == "size_validation":
                verification = self._verify_size(backup, file_path)
                if verification:
                    verifications.append(verification)

            elif method == "timestamp_validation":
                verification = self._verify_timestamp(backup, file_path)
                if verification:
                    verifications.append(verification)

        logger.info(
            f"Verified backup {backup.id} using {len(verifications)} methods",
            extra={"backup_id": backup.id, "verification_count": len(verifications)},
        )

        return verifications

    def _verify_checksum(
        self, backup: Backup, file_path: Path
    ) -> Optional[BackupVerification]:
        """Verify backup checksum.

        Args:
            backup: Backup object.
            file_path: Path to backup file.

        Returns:
            BackupVerification object or None if error.
        """
        if not backup.checksum or not backup.checksum_algorithm:
            return self.db_manager.add_verification(
                backup_id=backup.id,
                verification_type="checksum",
                status="skipped",
                result="No checksum stored for backup",
            )

        try:
            algorithm = backup.checksum_algorithm
            calculated_checksum = self._calculate_checksum(file_path, algorithm)

            if calculated_checksum == backup.checksum:
                status = "passed"
                result = f"Checksum matches ({algorithm})"
            else:
                status = "failed"
                result = f"Checksum mismatch: expected {backup.checksum}, got {calculated_checksum}"

            verification = self.db_manager.add_verification(
                backup_id=backup.id,
                verification_type="checksum",
                status=status,
                result=result,
            )

            if status == "failed":
                logger.error(
                    f"Checksum verification failed for backup {backup.id}",
                    extra={"backup_id": backup.id, "filepath": backup.filepath},
                )

            return verification

        except Exception as e:
            logger.error(
                f"Error verifying checksum for backup {backup.id}: {e}",
                extra={"backup_id": backup.id, "error": str(e)},
            )
            return self.db_manager.add_verification(
                backup_id=backup.id,
                verification_type="checksum",
                status="error",
                error_message=str(e),
            )

    def _verify_size(
        self, backup: Backup, file_path: Path
    ) -> Optional[BackupVerification]:
        """Verify backup file size.

        Args:
            backup: Backup object.
            file_path: Path to backup file.

        Returns:
            BackupVerification object or None if error.
        """
        try:
            actual_size = file_path.stat().st_size
            stored_size = backup.size_bytes

            if stored_size is None:
                return self.db_manager.add_verification(
                    backup_id=backup.id,
                    verification_type="size_validation",
                    status="skipped",
                    result="No size stored for backup",
                )

            if actual_size == stored_size:
                status = "passed"
                result = f"Size matches: {actual_size} bytes"
            else:
                status = "failed"
                result = f"Size mismatch: expected {stored_size}, got {actual_size}"

            verification = self.db_manager.add_verification(
                backup_id=backup.id,
                verification_type="size_validation",
                status=status,
                result=result,
            )

            if status == "failed":
                logger.error(
                    f"Size verification failed for backup {backup.id}",
                    extra={"backup_id": backup.id, "filepath": backup.filepath},
                )

            return verification

        except Exception as e:
            logger.error(
                f"Error verifying size for backup {backup.id}: {e}",
                extra={"backup_id": backup.id, "error": str(e)},
            )
            return self.db_manager.add_verification(
                backup_id=backup.id,
                verification_type="size_validation",
                status="error",
                error_message=str(e),
            )

    def _verify_timestamp(
        self, backup: Backup, file_path: Path
    ) -> Optional[BackupVerification]:
        """Verify backup file timestamp.

        Args:
            backup: Backup object.
            file_path: Path to backup file.

        Returns:
            BackupVerification object or None if error.
        """
        try:
            from datetime import timedelta

            actual_timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
            stored_timestamp = backup.backup_timestamp

            time_diff = abs((actual_timestamp - stored_timestamp).total_seconds())

            if time_diff < 60:
                status = "passed"
                result = f"Timestamp matches (diff: {time_diff:.0f}s)"
            else:
                status = "warning"
                result = f"Timestamp difference: {time_diff:.0f}s"

            verification = self.db_manager.add_verification(
                backup_id=backup.id,
                verification_type="timestamp_validation",
                status=status,
                result=result,
            )

            return verification

        except Exception as e:
            logger.error(
                f"Error verifying timestamp for backup {backup.id}: {e}",
                extra={"backup_id": backup.id, "error": str(e)},
            )
            return self.db_manager.add_verification(
                backup_id=backup.id,
                verification_type="timestamp_validation",
                status="error",
                error_message=str(e),
            )

    def _calculate_checksum(self, file_path: Path, algorithm: str = "sha256") -> str:
        """Calculate file checksum.

        Args:
            file_path: Path to file.
            algorithm: Hash algorithm.

        Returns:
            Hexadecimal checksum string.
        """
        hash_obj = hashlib.new(algorithm)

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    def verify_all_backups(
        self,
        location_id: Optional[int] = None,
        days: Optional[int] = None,
    ) -> Dict[int, List[BackupVerification]]:
        """Verify all backups for location(s).

        Args:
            location_id: Optional location ID filter.
            days: Optional number of days to look back.

        Returns:
            Dictionary mapping backup IDs to verification lists.
        """
        backups = self.db_manager.get_recent_backups(
            location_id=location_id, days=days
        )

        all_verifications = {}

        for backup in backups:
            verifications = self.verify_backup(backup)
            all_verifications[backup.id] = verifications

        logger.info(
            f"Verified {len(backups)} backups",
            extra={"backup_count": len(backups), "location_id": location_id},
        )

        return all_verifications
