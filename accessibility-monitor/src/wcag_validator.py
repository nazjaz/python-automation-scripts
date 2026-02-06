"""Validates web pages against WCAG guidelines."""

import logging
import re
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WCAGValidator:
    """Validates web pages for WCAG compliance."""

    def __init__(
        self,
        db_manager,
        config: Dict,
    ) -> None:
        """Initialize WCAG validator.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.scanning_config = config.get("scanning", {})
        self.violations_config = config.get("violations", {})

    def validate_page(
        self, html_content: str, page_url: str
    ) -> List[Dict]:
        """Validate page for WCAG compliance.

        Args:
            html_content: HTML content to validate.
            page_url: Page URL.

        Returns:
            List of violation dictionaries.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        violations = []

        if self.scanning_config.get("check_images", True):
            violations.extend(self._check_images(soup))

        if self.scanning_config.get("check_forms", True):
            violations.extend(self._check_forms(soup))

        if self.scanning_config.get("check_navigation", True):
            violations.extend(self._check_navigation(soup))

        if self.scanning_config.get("check_keyboard", True):
            violations.extend(self._check_keyboard(soup))

        if self.scanning_config.get("check_color_contrast", True):
            violations.extend(self._check_color_contrast(soup))

        if self.scanning_config.get("check_aria", True):
            violations.extend(self._check_aria(soup))

        if self.scanning_config.get("check_headings", True):
            violations.extend(self._check_headings(soup))

        if self.scanning_config.get("check_links", True):
            violations.extend(self._check_links(soup))

        return violations

    def _check_images(self, soup: BeautifulSoup) -> List[Dict]:
        """Check images for accessibility issues.

        Args:
            soup: BeautifulSoup object.

        Returns:
            List of violation dictionaries.
        """
        violations = []

        for img in soup.find_all("img"):
            if not img.get("alt"):
                violations.append(
                    {
                        "wcag_criterion": "1.1.1",
                        "severity": "high",
                        "violation_type": "missing_alt_text",
                        "description": "Image missing alt text attribute",
                        "element_type": "img",
                        "element_selector": self._get_selector(img),
                        "recommendation": "Add descriptive alt text to all images",
                        "code_example": f'<img src="{img.get("src", "")}" alt="Description of image">',
                    }
                )

            if img.get("alt") == "" and img.get("role") != "presentation":
                violations.append(
                    {
                        "wcag_criterion": "1.1.1",
                        "severity": "medium",
                        "violation_type": "empty_alt_text",
                        "description": "Image has empty alt text but is not marked as decorative",
                        "element_type": "img",
                        "element_selector": self._get_selector(img),
                        "recommendation": "Either add descriptive alt text or set role='presentation' for decorative images",
                    }
                )

        return violations

    def _check_forms(self, soup: BeautifulSoup) -> List[Dict]:
        """Check forms for accessibility issues.

        Args:
            soup: BeautifulSoup object.

        Returns:
            List of violation dictionaries.
        """
        violations = []

        for input_elem in soup.find_all(["input", "textarea", "select"]):
            input_id = input_elem.get("id")
            input_name = input_elem.get("name")

            label = None
            if input_id:
                label = soup.find("label", {"for": input_id})

            if not label and input_elem.get("type") not in ["hidden", "submit", "button"]:
                aria_label = input_elem.get("aria-label")
                aria_labelledby = input_elem.get("aria-labelledby")

                if not aria_label and not aria_labelledby:
                    violations.append(
                        {
                            "wcag_criterion": "1.3.1",
                            "severity": "high",
                            "violation_type": "missing_form_label",
                            "description": f"Form input missing label (id: {input_id}, name: {input_name})",
                            "element_type": input_elem.name,
                            "element_selector": self._get_selector(input_elem),
                            "recommendation": "Add a label element or aria-label attribute",
                            "code_example": f'<label for="{input_id}">Input Label</label>\n<input id="{input_id}" type="text">',
                        }
                    )

        return violations

    def _check_navigation(self, soup: BeautifulSoup) -> List[Dict]:
        """Check navigation for accessibility issues.

        Args:
            soup: BeautifulSoup object.

        Returns:
            List of violation dictionaries.
        """
        violations = []

        nav_elements = soup.find_all("nav")
        if not nav_elements:
            violations.append(
                {
                    "wcag_criterion": "2.4.1",
                    "severity": "medium",
                    "violation_type": "missing_navigation",
                    "description": "Page appears to have navigation but no nav element",
                    "element_type": "page",
                    "recommendation": "Use semantic nav elements for navigation",
                }
            )

        for nav in nav_elements:
            if not nav.get("aria-label") and not nav.get("aria-labelledby"):
                nav_id = nav.get("id")
                if not nav_id or not soup.find(id=nav_id.replace("nav", "label")):
                    violations.append(
                        {
                            "wcag_criterion": "2.4.1",
                            "severity": "low",
                            "violation_type": "unlabeled_navigation",
                            "description": "Navigation element missing accessible label",
                            "element_type": "nav",
                            "element_selector": self._get_selector(nav),
                            "recommendation": "Add aria-label or aria-labelledby to nav element",
                        }
                    )

        return violations

    def _check_keyboard(self, soup: BeautifulSoup) -> List[Dict]:
        """Check keyboard accessibility.

        Args:
            soup: BeautifulSoup object.

        Returns:
            List of violation dictionaries.
        """
        violations = []

        for element in soup.find_all(["a", "button", "input"]):
            if element.get("tabindex") and int(element.get("tabindex", 0)) < 0:
                violations.append(
                    {
                        "wcag_criterion": "2.1.1",
                        "severity": "high",
                        "violation_type": "keyboard_trap",
                        "description": "Element has negative tabindex, removing from keyboard navigation",
                        "element_type": element.name,
                        "element_selector": self._get_selector(element),
                        "recommendation": "Avoid negative tabindex values unless necessary for accessibility",
                    }
                )

        return violations

    def _check_color_contrast(self, soup: BeautifulSoup) -> List[Dict]:
        """Check color contrast (basic check).

        Args:
            soup: BeautifulSoup object.

        Returns:
            List of violation dictionaries.
        """
        violations = []

        for element in soup.find_all(True):
            style = element.get("style", "")
            if style and "color" in style.lower():
                if "background" not in style.lower():
                    violations.append(
                        {
                            "wcag_criterion": "1.4.3",
                            "severity": "medium",
                            "violation_type": "potential_contrast_issue",
                            "description": "Element has color but background may not be specified, potential contrast issue",
                            "element_type": element.name,
                            "element_selector": self._get_selector(element),
                            "recommendation": "Ensure text color contrast ratio meets WCAG AA standards (4.5:1 for normal text)",
                        }
                    )

        return violations

    def _check_aria(self, soup: BeautifulSoup) -> List[Dict]:
        """Check ARIA usage.

        Args:
            soup: BeautifulSoup object.

        Returns:
            List of violation dictionaries.
        """
        violations = []

        for element in soup.find_all(True):
            aria_attrs = [attr for attr in element.attrs if attr.startswith("aria-")]

            if aria_attrs:
                aria_invalid = element.get("aria-invalid")
                if aria_invalid == "true" and not element.get("aria-describedby"):
                    violations.append(
                        {
                            "wcag_criterion": "3.3.1",
                            "severity": "medium",
                            "violation_type": "missing_error_description",
                            "description": "Element marked as invalid but missing error description",
                            "element_type": element.name,
                            "element_selector": self._get_selector(element),
                            "recommendation": "Add aria-describedby pointing to error message",
                        }
                    )

        return violations

    def _check_headings(self, soup: BeautifulSoup) -> List[Dict]:
        """Check heading structure.

        Args:
            soup: BeautifulSoup object.

        Returns:
            List of violation dictionaries.
        """
        violations = []

        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        h1_count = len(soup.find_all("h1"))

        if h1_count == 0:
            violations.append(
                {
                    "wcag_criterion": "1.3.1",
                    "severity": "high",
                    "violation_type": "missing_h1",
                    "description": "Page missing h1 heading",
                    "element_type": "page",
                    "recommendation": "Add a single h1 heading to describe the main content",
                }
            )
        elif h1_count > 1:
            violations.append(
                {
                    "wcag_criterion": "1.3.1",
                    "severity": "medium",
                    "violation_type": "multiple_h1",
                    "description": f"Page has {h1_count} h1 headings, should have only one",
                    "element_type": "page",
                    "recommendation": "Use a single h1 per page for main heading",
                }
            )

        prev_level = 0
        for heading in headings:
            level = int(heading.name[1])
            if level > prev_level + 1:
                violations.append(
                    {
                        "wcag_criterion": "1.3.1",
                        "severity": "medium",
                        "violation_type": "heading_skip",
                        "description": f"Heading level skipped from h{prev_level} to h{level}",
                        "element_type": heading.name,
                        "element_selector": self._get_selector(heading),
                        "recommendation": "Maintain proper heading hierarchy without skipping levels",
                    }
                )
            prev_level = level

        return violations

    def _check_links(self, soup: BeautifulSoup) -> List[Dict]:
        """Check links for accessibility issues.

        Args:
            soup: BeautifulSoup object.

        Returns:
            List of violation dictionaries.
        """
        violations = []

        for link in soup.find_all("a"):
            link_text = link.get_text(strip=True)
            href = link.get("href", "")

            if not link_text or link_text.strip() == "":
                if not link.find(["img", "span", "div"]):
                    violations.append(
                        {
                            "wcag_criterion": "2.4.4",
                            "severity": "high",
                            "violation_type": "empty_link",
                            "description": "Link has no accessible text",
                            "element_type": "a",
                            "element_selector": self._get_selector(link),
                            "recommendation": "Add descriptive link text or accessible content",
                        }
                    )

            if link_text.lower() in ["click here", "read more", "here", "link"]:
                violations.append(
                    {
                        "wcag_criterion": "2.4.4",
                        "severity": "medium",
                        "violation_type": "generic_link_text",
                        "description": f"Link uses generic text: '{link_text}'",
                        "element_type": "a",
                        "element_selector": self._get_selector(link),
                        "recommendation": "Use descriptive link text that makes sense out of context",
                    }
                )

        return violations

    def _get_selector(self, element) -> str:
        """Get CSS selector for element.

        Args:
            element: BeautifulSoup element.

        Returns:
            CSS selector string.
        """
        try:
            if element.get("id"):
                return f"#{element.get('id')}"

            if element.get("class"):
                classes = " ".join(element.get("class", []))
                return f".{classes.replace(' ', '.')}"

            return element.name or "unknown"
        except Exception:
            return "unknown"
