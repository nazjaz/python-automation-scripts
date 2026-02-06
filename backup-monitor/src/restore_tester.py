"""Tests restore procedures for backups."""

import logging
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.database import DatabaseManager, Backup, RestoreTest

logger = logging.getLogger(__name__)


class RestoreTester:
    """Tests restore procedures for backups."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize restore tester.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.restore_config = config.get("backups", {}).get("restore_testing", {})
        self.test_location = Path(self.restore_config.get("test_location", "test_backups"))
        self.cleanup_after_test = self.restore_config.get("cleanup_after_test", True)

    def test_restore(
        self, backup: Backup
    ) -> Optional[RestoreTest]:
        """Test restore procedure for backup.

        Args:
            backup: Backup object to test.

        Returns:
            RestoreTest object or None if error.
        """
        file_path = Path(backup.filepath)

        if not file_path.exists():
            logger.error(
                f"Backup file does not exist for restore test: {backup.filepath}",
                extra={"backup_id": backup.id, "filepath": backup.filepath},
            )
            return self.db_manager.add_restore_test(
                backup_id=backup.id,
                status="failed",
                error_message=f"Backup file does not exist: {backup.filepath}",
            )

        test_start = datetime.utcnow()
        test_dir = None

        try:
            self.test_location.mkdir(parents=True, exist_ok=True)

            test_dir = self.test_location / f"restore_test_{backup.id}_{test_start.strftime('%Y%m%d_%H%M%S')}"
            test_dir.mkdir(parents=True, exist_ok=True)

            restore_result = self._perform_restore(backup, file_path, test_dir)

            test_end = datetime.utcnow()
            duration = (test_end - test_start).total_seconds()

            if restore_result["success"]:
                status = "passed"
                result = restore_result.get("message", "Restore test completed successfully")
                error_message = None
            else:
                status = "failed"
                result = restore_result.get("message", "Restore test failed")
                error_message = restore_result.get("error", "Unknown error")

            restore_test = self.db_manager.add_restore_test(
                backup_id=backup.id,
                status=status,
                test_location=str(test_dir),
                duration_seconds=duration,
                result=result,
                error_message=error_message,
            )

            if self.cleanup_after_test and test_dir.exists():
                try:
                    shutil.rmtree(test_dir)
                    logger.debug(
                        f"Cleaned up test directory: {test_dir}",
                        extra={"test_dir": str(test_dir)},
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to cleanup test directory: {test_dir}",
                        extra={"test_dir": str(test_dir), "error": str(e)},
                    )

            logger.info(
                f"Restore test completed for backup {backup.id}: {status}",
                extra={
                    "backup_id": backup.id,
                    "status": status,
                    "duration_seconds": duration,
                },
            )

            return restore_test

        except Exception as e:
            logger.error(
                f"Error during restore test for backup {backup.id}: {e}",
                extra={"backup_id": backup.id, "error": str(e)},
            )

            if test_dir and test_dir.exists() and self.cleanup_after_test:
                try:
                    shutil.rmtree(test_dir)
                except Exception:
                    pass

            return self.db_manager.add_restore_test(
                backup_id=backup.id,
                status="error",
                error_message=str(e),
            )

    def _perform_restore(
        self, backup: Backup, file_path: Path, test_dir: Path
    ) -> Dict:
        """Perform actual restore operation.

        Args:
            backup: Backup object.
            file_path: Path to backup file.
            test_dir: Test directory for restore.

        Returns:
            Dictionary with success status and message.
        """
        backup_type = backup.location.backup_type.lower()

        if backup_type == "file":
            return self._restore_file_backup(file_path, test_dir)
        elif backup_type == "database":
            return self._restore_database_backup(file_path, test_dir)
        else:
            return {
                "success": False,
                "error": f"Unknown backup type: {backup_type}",
                "message": f"Cannot test restore for backup type: {backup_type}",
            }

    def _restore_file_backup(
        self, file_path: Path, test_dir: Path
    ) -> Dict:
        """Restore file backup (extract or copy).

        Args:
            file_path: Path to backup file.
            test_dir: Test directory for restore.

        Returns:
            Dictionary with success status and message.
        """
        try:
            if file_path.suffix in [".zip", ".tar", ".tar.gz", ".tgz"]:
                import tarfile
                import zipfile

                if file_path.suffix == ".zip":
                    with zipfile.ZipFile(file_path, "r") as zip_ref:
                        zip_ref.extractall(test_dir)
                else:
                    with tarfile.open(file_path, "r:*") as tar_ref:
                        tar_ref.extractall(test_dir)

                extracted_files = list(test_dir.rglob("*"))
                file_count = len([f for f in extracted_files if f.is_file()])

                return {
                    "success": True,
                    "message": f"Extracted {file_count} files from archive",
                }
            else:
                shutil.copy2(file_path, test_dir / file_path.name)
                return {
                    "success": True,
                    "message": f"Copied backup file to test directory",
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to restore file backup: {e}",
            }

    def _restore_database_backup(
        self, file_path: Path, test_dir: Path
    ) -> Dict:
        """Restore database backup (simulated).

        Args:
            file_path: Path to backup file.
            test_dir: Test directory for restore.

        Returns:
            Dictionary with success status and message.
        """
        try:
            if file_path.suffix == ".sql":
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(1024)
                    if "CREATE TABLE" in content or "INSERT INTO" in content:
                        return {
                            "success": True,
                            "message": "SQL backup file appears valid",
                        }
                    else:
                        return {
                            "success": False,
                            "error": "SQL file does not contain expected database statements",
                            "message": "SQL backup validation failed",
                        }
            elif file_path.suffix in [".dump", ".sqlite", ".db"]:
                test_file = test_dir / file_path.name
                shutil.copy2(file_path, test_file)
                if test_file.exists() and test_file.stat().st_size > 0:
                    return {
                        "success": True,
                        "message": f"Database backup file copied and validated ({test_file.stat().st_size} bytes)",
                    }
                else:
                    return {
                        "success": False,
                        "error": "Database backup file is empty or invalid",
                        "message": "Database backup validation failed",
                    }
            else:
                return {
                    "success": False,
                    "error": f"Unknown database backup format: {file_path.suffix}",
                    "message": f"Cannot validate database backup format: {file_path.suffix}",
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to restore database backup: {e}",
            }

    def test_all_backups(
        self,
        location_id: Optional[int] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[RestoreTest]:
        """Test restore for all backups.

        Args:
            location_id: Optional location ID filter.
            days: Optional number of days to look back.
            limit: Optional limit on number of tests.

        Returns:
            List of RestoreTest objects.
        """
        backups = self.db_manager.get_recent_backups(
            location_id=location_id, days=days, limit=limit
        )

        locations = self.db_manager.get_backup_locations(enabled_only=True)
        testable_locations = {loc.id for loc in locations if loc.test_restore}

        testable_backups = [
            b for b in backups
            if b.location_id in testable_locations
        ]

        all_tests = []

        for backup in testable_backups:
            test = self.test_restore(backup)
            if test:
                all_tests.append(test)

        logger.info(
            f"Tested restore for {len(all_tests)} backups",
            extra={"test_count": len(all_tests), "location_id": location_id},
        )

        return all_tests
