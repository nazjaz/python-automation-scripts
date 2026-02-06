"""Monitor application security scans."""

from datetime import datetime
from typing import Dict, List, Optional

from src.database import DatabaseManager


class ScanMonitor:
    """Monitor application security scans."""

    def __init__(self, db_manager: DatabaseManager, config: Dict):
        """Initialize scan monitor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config

    def monitor_scan(self, scan_id: str) -> Dict[str, any]:
        """Monitor security scan status.

        Args:
            scan_id: Scan identifier.

        Returns:
            Dictionary with scan monitoring information.
        """
        scan = self.db_manager.get_security_scan(scan_id)

        if not scan:
            return {"error": "Scan not found"}

        vulnerabilities = []
        if scan.vulnerabilities:
            vulnerabilities = [
                {
                    "vulnerability_id": v.vulnerability_id,
                    "title": v.title,
                    "severity": v.severity,
                    "cvss_score": v.cvss_score,
                }
                for v in scan.vulnerabilities
            ]

        return {
            "scan_id": scan_id,
            "status": scan.status,
            "scan_type": scan.scan_type,
            "scan_tool": scan.scan_tool,
            "started_at": scan.started_at,
            "completed_at": scan.completed_at,
            "vulnerabilities_found": scan.vulnerabilities_found,
            "critical_count": scan.critical_count,
            "high_count": scan.high_count,
            "medium_count": scan.medium_count,
            "low_count": scan.low_count,
            "vulnerabilities": vulnerabilities,
        }

    def process_scan_results(
        self,
        scan_id: str,
        vulnerabilities: List[Dict[str, any]],
    ) -> Dict[str, any]:
        """Process scan results and create vulnerabilities.

        Args:
            scan_id: Scan identifier.
            vulnerabilities: List of vulnerability dictionaries.

        Returns:
            Dictionary with processing results.
        """
        scan = self.db_manager.get_security_scan(scan_id)

        if not scan:
            return {"error": "Scan not found"}

        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0

        created_vulnerabilities = []

        for vuln_data in vulnerabilities:
            severity = vuln_data.get("severity", "low").lower()

            if severity == "critical":
                critical_count += 1
            elif severity == "high":
                high_count += 1
            elif severity == "medium":
                medium_count += 1
            else:
                low_count += 1

            vulnerability = self.db_manager.add_vulnerability(
                vulnerability_id=vuln_data.get("vulnerability_id", f"VULN-{len(created_vulnerabilities) + 1}"),
                application_id=scan.application_id,
                scan_id=scan.id,
                title=vuln_data.get("title", "Unknown Vulnerability"),
                severity=severity,
                cve_id=vuln_data.get("cve_id"),
                description=vuln_data.get("description"),
                cvss_score=vuln_data.get("cvss_score"),
                component=vuln_data.get("component"),
                affected_version=vuln_data.get("affected_version"),
            )

            created_vulnerabilities.append(vulnerability.vulnerability_id)

        self.db_manager.update_scan_results(
            scan_id=scan_id,
            completed_at=datetime.utcnow(),
            vulnerabilities_found=len(vulnerabilities),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
        )

        return {
            "success": True,
            "scan_id": scan_id,
            "vulnerabilities_created": len(created_vulnerabilities),
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
        }

    def get_scan_statistics(
        self, application_id: Optional[int] = None, days: int = 30
    ) -> Dict[str, any]:
        """Get scan statistics.

        Args:
            application_id: Optional application ID to filter by.
            days: Number of days to analyze.

        Returns:
            Dictionary with scan statistics.
        """
        from datetime import timedelta

        scans = self.db_manager.get_recent_scans(
            application_id=application_id, limit=1000
        )

        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_scans = [s for s in scans if s.started_at >= cutoff]

        if not recent_scans:
            return {
                "total_scans": 0,
                "completed_scans": 0,
                "average_vulnerabilities": 0.0,
            }

        completed_scans = [s for s in recent_scans if s.status == "completed"]

        total_vulnerabilities = sum(s.vulnerabilities_found for s in completed_scans)
        average_vulnerabilities = (
            total_vulnerabilities / len(completed_scans)
            if completed_scans
            else 0.0
        )

        return {
            "total_scans": len(recent_scans),
            "completed_scans": len(completed_scans),
            "average_vulnerabilities": average_vulnerabilities,
            "total_vulnerabilities_found": total_vulnerabilities,
        }
