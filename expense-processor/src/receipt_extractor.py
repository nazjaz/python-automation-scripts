"""Extracts data from receipt images and PDFs."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from PIL import Image
import pytesseract
from pdf2image import convert_from_path

from src.database import DatabaseManager, Receipt

logger = logging.getLogger(__name__)


class ReceiptExtractor:
    """Extracts expense data from receipt files."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize receipt extractor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.extraction_config = config.get("receipt_extraction", {})
        self.supported_formats = self.extraction_config.get("supported_formats", ["pdf", "jpg", "jpeg", "png"])
        self.ocr_enabled = self.extraction_config.get("ocr_enabled", True)
        self.confidence_threshold = self.extraction_config.get("confidence_threshold", 0.7)

    def extract_from_file(
        self,
        file_path: str,
        expense_id: int,
    ) -> Receipt:
        """Extract data from receipt file.

        Args:
            file_path: Path to receipt file.
            expense_id: Expense ID to associate receipt with.

        Returns:
            Receipt object with extracted data.
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"Receipt file not found: {file_path}")

        file_extension = file_path_obj.suffix.lower().lstrip(".")
        if file_extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_extension}")

        logger.info(f"Extracting data from receipt: {file_path}", extra={"file_path": file_path, "expense_id": expense_id})

        ocr_text = None
        if self.ocr_enabled:
            ocr_text = self._perform_ocr(file_path, file_extension)

        extracted_data = self._parse_receipt_data(ocr_text or "")

        receipt = self.db_manager.add_receipt(
            expense_id=expense_id,
            file_path=file_path,
            file_type=file_extension,
            extracted_merchant=extracted_data.get("merchant"),
            extracted_date=extracted_data.get("date"),
            extracted_amount=extracted_data.get("amount"),
            extracted_category=extracted_data.get("category"),
            extraction_confidence=extracted_data.get("confidence", 0.0),
            ocr_text=ocr_text,
        )

        logger.info(
            f"Extracted receipt data: amount={extracted_data.get('amount')}, merchant={extracted_data.get('merchant')}",
            extra={"receipt_id": receipt.id, "extracted_amount": extracted_data.get("amount")},
        )

        return receipt

    def _perform_ocr(self, file_path: str, file_extension: str) -> Optional[str]:
        """Perform OCR on receipt file.

        Args:
            file_path: Path to receipt file.
            file_extension: File extension.

        Returns:
            Extracted text or None if error.
        """
        try:
            if file_extension == "pdf":
                images = convert_from_path(file_path)
                if not images:
                    return None
                image = images[0]
            else:
                image = Image.open(file_path)

            text = pytesseract.image_to_string(image)
            return text

        except Exception as e:
            logger.error(
                f"OCR error: {e}",
                extra={"file_path": file_path, "error": str(e)},
            )
            return None

    def _parse_receipt_data(self, ocr_text: str) -> Dict:
        """Parse receipt data from OCR text.

        Args:
            ocr_text: OCR extracted text.

        Returns:
            Dictionary with extracted data.
        """
        extracted = {
            "merchant": None,
            "date": None,
            "amount": None,
            "category": None,
            "confidence": 0.0,
        }

        if not ocr_text:
            return extracted

        amount = self._extract_amount(ocr_text)
        date = self._extract_date(ocr_text)
        merchant = self._extract_merchant(ocr_text)
        category = self._extract_category(ocr_text, merchant)

        confidence = 0.0
        if amount:
            confidence += 0.4
        if date:
            confidence += 0.3
        if merchant:
            confidence += 0.2
        if category:
            confidence += 0.1

        extracted.update(
            {
                "merchant": merchant,
                "date": date,
                "amount": amount,
                "category": category,
                "confidence": confidence,
            }
        )

        return extracted

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract amount from text.

        Args:
            text: Text to search.

        Returns:
            Extracted amount or None.
        """
        patterns = [
            r"total[:\s]*\$?(\d+\.?\d*)",
            r"amount[:\s]*\$?(\d+\.?\d*)",
            r"\$(\d+\.?\d{2})",
            r"(\d+\.?\d{2})\s*USD",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return float(matches[-1])
                except ValueError:
                    continue

        return None

    def _extract_date(self, text: str) -> Optional[datetime]:
        """Extract date from text.

        Args:
            text: Text to search.

        Returns:
            Extracted date or None.
        """
        patterns = [
            r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})",
            r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    date_str = "/".join(matches[0])
                    return datetime.strptime(date_str, "%m/%d/%Y").date()
                except (ValueError, IndexError):
                    try:
                        date_str = "/".join(matches[0])
                        return datetime.strptime(date_str, "%Y/%m/%d").date()
                    except (ValueError, IndexError):
                        continue

        return None

    def _extract_merchant(self, text: str) -> Optional[str]:
        """Extract merchant name from text.

        Args:
            text: Text to search.

        Returns:
            Extracted merchant name or None.
        """
        lines = text.split("\n")
        if lines:
            first_line = lines[0].strip()
            if len(first_line) > 3 and len(first_line) < 100:
                return first_line

        return None

    def _extract_category(
        self, text: str, merchant: Optional[str]
    ) -> Optional[str]:
        """Extract category from text.

        Args:
            text: Text to search.
            merchant: Optional merchant name.

        Returns:
            Extracted category or None.
        """
        text_lower = text.lower()
        merchant_lower = (merchant or "").lower()

        category_keywords = {
            "meals": ["restaurant", "cafe", "food", "dining", "meal"],
            "lodging": ["hotel", "inn", "lodge", "accommodation"],
            "transportation": ["taxi", "uber", "lyft", "airline", "train", "bus"],
            "office_supplies": ["office", "supplies", "stationery"],
            "training": ["training", "course", "seminar", "conference"],
        }

        for category, keywords in category_keywords.items():
            if any(keyword in text_lower or keyword in merchant_lower for keyword in keywords):
                return category

        return None
