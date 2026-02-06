"""Scans websites for accessibility issues."""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.database import DatabaseManager, AccessibilityScan, Violation

logger = logging.getLogger(__name__)


class AccessibilityScanner:
    """Scans websites for accessibility compliance issues."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize accessibility scanner.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.accessibility_config = config.get("accessibility", {})
        self.scanning_config = config.get("scanning", {})
        self.timeout = self.accessibility_config.get("timeout_seconds", 30)
        self.user_agent = self.accessibility_config.get("user_agent", "Mozilla/5.0")
        self.max_pages = self.accessibility_config.get("max_pages", 50)
        self.scan_depth = self.accessibility_config.get("scan_depth", 10)

    def scan_website(
        self,
        website_id: int,
        start_url: str,
        max_pages: Optional[int] = None,
    ) -> List[AccessibilityScan]:
        """Scan website for accessibility issues.

        Args:
            website_id: Website ID.
            start_url: Starting URL to scan.
            max_pages: Optional maximum pages to scan.

        Returns:
            List of AccessibilityScan objects.
        """
        if max_pages is None:
            max_pages = self.max_pages

        from src.wcag_validator import WCAGValidator

        validator = WCAGValidator(self.db_manager, self.config)

        scanned_urls: Set[str] = set()
        urls_to_scan: List[str] = [start_url]
        scans = []

        while urls_to_scan and len(scanned_urls) < max_pages:
            current_url = urls_to_scan.pop(0)

            if current_url in scanned_urls:
                continue

            scanned_urls.add(current_url)

            logger.info(f"Scanning: {current_url}", extra={"url": current_url})

            try:
                scan_start = time.time()
                html_content = self._fetch_page(current_url)

                if not html_content:
                    continue

                violations = validator.validate_page(html_content, current_url)

                scan_duration = time.time() - scan_start

                violation_counts = self._count_violations_by_severity(violations)
                compliance_score = self._calculate_compliance_score(violation_counts)

                scan = self.db_manager.add_scan(
                    website_id=website_id,
                    page_url=current_url,
                    wcag_version=self.accessibility_config.get("wcag_version", "2.1"),
                    compliance_level=self.accessibility_config.get("target_level", "AA"),
                    total_violations=len(violations),
                    critical_violations=violation_counts.get("critical", 0),
                    high_violations=violation_counts.get("high", 0),
                    medium_violations=violation_counts.get("medium", 0),
                    low_violations=violation_counts.get("low", 0),
                    compliance_score=compliance_score,
                    scan_duration_seconds=scan_duration,
                )

                for violation_data in violations:
                    self.db_manager.add_violation(
                        scan_id=scan.id,
                        **violation_data,
                    )

                scans.append(scan)

                new_urls = self._extract_links(html_content, current_url, scanned_urls)
                urls_to_scan.extend(new_urls[:self.scan_depth])

            except Exception as e:
                logger.error(
                    f"Error scanning {current_url}: {e}",
                    extra={"url": current_url, "error": str(e)},
                )

        logger.info(
            f"Scan completed: {len(scans)} pages scanned",
            extra={"pages_scanned": len(scans), "website_id": website_id},
        )

        return scans

    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch page content.

        Args:
            url: URL to fetch.

        Returns:
            HTML content or None if error.
        """
        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(url, headers=headers, timeout=self.timeout, allow_redirects=self.scanning_config.get("follow_redirects", True))

            if response.status_code == 200:
                return response.text

            logger.warning(
                f"Non-200 status code: {response.status_code}",
                extra={"url": url, "status_code": response.status_code},
            )
            return None

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error fetching page: {e}",
                extra={"url": url, "error": str(e)},
            )
            return None

    def _extract_links(
        self, html_content: str, base_url: str, scanned_urls: Set[str]
    ) -> List[str]:
        """Extract links from HTML content.

        Args:
            html_content: HTML content.
            base_url: Base URL for resolving relative links.
            scanned_urls: Set of already scanned URLs.

        Returns:
            List of URLs to scan.
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            links = []

            for link in soup.find_all("a", href=True):
                href = link["href"]
                absolute_url = urljoin(base_url, href)

                parsed = urlparse(absolute_url)
                base_parsed = urlparse(base_url)

                if parsed.netloc == base_parsed.netloc:
                    if absolute_url not in scanned_urls:
                        links.append(absolute_url)

            return links

        except Exception as e:
            logger.error(
                f"Error extracting links: {e}",
                extra={"base_url": base_url, "error": str(e)},
            )
            return []

    def _count_violations_by_severity(
        self, violations: List[Dict]
    ) -> Dict[str, int]:
        """Count violations by severity.

        Args:
            violations: List of violation dictionaries.

        Returns:
            Dictionary mapping severity to count.
        """
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for violation in violations:
            severity = violation.get("severity", "medium")
            counts[severity] = counts.get(severity, 0) + 1

        return counts

    def _calculate_compliance_score(
        self, violation_counts: Dict[str, int]
    ) -> float:
        """Calculate compliance score.

        Args:
            violation_counts: Dictionary of violation counts by severity.

        Returns:
            Compliance score (0.0 to 1.0).
        """
        total_violations = sum(violation_counts.values())

        if total_violations == 0:
            return 1.0

        weighted_score = (
            violation_counts.get("critical", 0) * 0.5
            + violation_counts.get("high", 0) * 0.3
            + violation_counts.get("medium", 0) * 0.15
            + violation_counts.get("low", 0) * 0.05
        )

        max_possible_score = total_violations * 0.5

        if max_possible_score == 0:
            return 1.0

        score = 1.0 - (weighted_score / max_possible_score)
        return max(0.0, min(1.0, score))
