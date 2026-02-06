"""Testimonial Processor.

Automatically processes customer testimonials by extracting quotes, categorizing
by product or service, and generating marketing materials with permission tracking.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

import pandas as pd
import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class PermissionStatus(str, Enum):
    """Permission status enumeration."""

    GRANTED = "granted"
    PENDING = "pending"
    DENIED = "denied"
    EXPIRED = "expired"
    NOT_REQUESTED = "not_requested"


class TestimonialDataConfig(BaseModel):
    """Configuration for testimonial data source."""

    file_path: str = Field(..., description="Path to testimonial data file")
    format: str = Field(default="csv", description="File format: csv or json")
    testimonial_id_column: str = Field(
        default="testimonial_id", description="Column name for testimonial ID"
    )
    customer_name_column: str = Field(
        default="customer_name", description="Column name for customer name"
    )
    testimonial_text_column: str = Field(
        default="testimonial_text", description="Column name for testimonial text"
    )
    product_column: Optional[str] = Field(
        default=None, description="Column name for product/service name"
    )
    category_column: Optional[str] = Field(
        default=None, description="Column name for category"
    )
    rating_column: Optional[str] = Field(
        default=None, description="Column name for rating"
    )
    date_column: Optional[str] = Field(
        default=None, description="Column name for testimonial date"
    )


class QuoteExtractionConfig(BaseModel):
    """Configuration for quote extraction."""

    min_quote_length: int = Field(
        default=20, description="Minimum quote length in characters"
    )
    max_quote_length: int = Field(
        default=500, description="Maximum quote length in characters"
    )
    extract_full_sentences: bool = Field(
        default=True, description="Extract complete sentences only"
    )
    quote_indicators: List[str] = Field(
        default_factory=lambda: ['"', "'", "said", "says", "stated"],
        description="Indicators that suggest quoted content",
    )


class CategorizationConfig(BaseModel):
    """Configuration for categorization."""

    product_keywords: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Mapping of product names to keyword lists",
    )
    service_keywords: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Mapping of service names to keyword lists",
    )
    auto_categorize: bool = Field(
        default=True, description="Automatically categorize based on keywords"
    )


class MarketingMaterialConfig(BaseModel):
    """Configuration for marketing material generation."""

    output_formats: List[str] = Field(
        default_factory=lambda: ["markdown", "html"],
        description="Output formats to generate",
    )
    include_customer_name: bool = Field(
        default=True, description="Include customer name in materials"
    )
    include_rating: bool = Field(
        default=True, description="Include rating if available"
    )
    include_date: bool = Field(
        default=False, description="Include testimonial date"
    )
    template_path: Optional[str] = Field(
        default=None, description="Path to custom template file"
    )


class PermissionConfig(BaseModel):
    """Configuration for permission tracking."""

    permission_file: str = Field(
        default="logs/permissions.json",
        description="Path to permission tracking file",
    )
    default_permission_status: PermissionStatus = Field(
        default=PermissionStatus.NOT_REQUESTED,
        description="Default permission status for new testimonials",
    )
    require_permission_for_use: bool = Field(
        default=True, description="Require granted permission for marketing use"
    )


class Config(BaseModel):
    """Main configuration model."""

    testimonial_data: TestimonialDataConfig = Field(
        ..., description="Testimonial data source configuration"
    )
    quote_extraction: QuoteExtractionConfig = Field(
        default_factory=QuoteExtractionConfig,
        description="Quote extraction settings",
    )
    categorization: CategorizationConfig = Field(
        default_factory=CategorizationConfig,
        description="Categorization settings",
    )
    marketing: MarketingMaterialConfig = Field(
        default_factory=MarketingMaterialConfig,
        description="Marketing material generation settings",
    )
    permission: PermissionConfig = Field(
        default_factory=PermissionConfig,
        description="Permission tracking settings",
    )
    output_directory: str = Field(
        default="logs/marketing_materials",
        description="Directory for generated marketing materials",
    )


class AppSettings(BaseSettings):
    """Application settings from environment variables."""

    config_path: str = "config.yaml"


@dataclass
class Quote:
    """Extracted quote from testimonial."""

    quote_text: str
    start_position: int
    end_position: int
    confidence: float = 1.0


@dataclass
class TestimonialRecord:
    """Represents a testimonial record."""

    testimonial_id: str
    customer_name: str
    testimonial_text: str
    product: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[float] = None
    date: Optional[datetime] = None
    quotes: List[Quote] = field(default_factory=list)
    permission_status: PermissionStatus = PermissionStatus.NOT_REQUESTED


@dataclass
class MarketingMaterial:
    """Generated marketing material."""

    format: str
    content: str
    testimonial_id: str
    category: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.now)


def load_config(config_path: Path) -> Config:
    """Load and validate configuration from YAML file.

    Args:
        config_path: Path to configuration YAML file

    Returns:
        Validated configuration object

    Raises:
        FileNotFoundError: If config file does not exist
        ValueError: If configuration is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        config = Config(**config_data)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in configuration file: {e}")
        raise ValueError(f"Invalid YAML configuration: {e}") from e
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


def load_testimonial_data(
    config: TestimonialDataConfig, project_root: Path
) -> List[TestimonialRecord]:
    """Load testimonial data from CSV or JSON file.

    Args:
        config: Testimonial data configuration
        project_root: Project root directory

    Returns:
        List of TestimonialRecord objects

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        raise FileNotFoundError(f"Testimonial data file not found: {data_path}")

    testimonials = []

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        required_columns = [
            config.testimonial_id_column,
            config.customer_name_column,
            config.testimonial_text_column,
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        for _, row in df.iterrows():
            testimonial = TestimonialRecord(
                testimonial_id=str(row[config.testimonial_id_column]),
                customer_name=str(row[config.customer_name_column]),
                testimonial_text=str(row[config.testimonial_text_column]),
            )

            if config.product_column and config.product_column in df.columns:
                if pd.notna(row[config.product_column]):
                    testimonial.product = str(row[config.product_column])

            if config.category_column and config.category_column in df.columns:
                if pd.notna(row[config.category_column]):
                    testimonial.category = str(row[config.category_column])

            if config.rating_column and config.rating_column in df.columns:
                if pd.notna(row[config.rating_column]):
                    testimonial.rating = float(row[config.rating_column])

            if config.date_column and config.date_column in df.columns:
                if pd.notna(row[config.date_column]):
                    testimonial.date = pd.to_datetime(row[config.date_column])

            testimonials.append(testimonial)

        logger.info(f"Loaded {len(testimonials)} testimonials")
        return testimonials

    except pd.errors.EmptyDataError:
        logger.warning(f"Testimonial data file is empty: {data_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to load testimonial data: {e}")
        raise


def extract_quotes(
    testimonial: TestimonialRecord, config: QuoteExtractionConfig
) -> List[Quote]:
    """Extract quotes from testimonial text.

    Args:
        testimonial: Testimonial record
        config: Quote extraction configuration

    Returns:
        List of extracted quotes
    """
    quotes = []
    text = testimonial.testimonial_text

    if config.extract_full_sentences:
        sentence_pattern = r"[^.!?]*[.!?]"
        sentences = re.findall(sentence_pattern, text)

        for sentence in sentences:
            sentence = sentence.strip()
            if (
                config.min_quote_length
                <= len(sentence)
                <= config.max_quote_length
            ):
                has_indicator = any(
                    indicator.lower() in sentence.lower()
                    for indicator in config.quote_indicators
                )
                if has_indicator or len(sentences) == 1:
                    quote = Quote(
                        quote_text=sentence,
                        start_position=text.find(sentence),
                        end_position=text.find(sentence) + len(sentence),
                    )
                    quotes.append(quote)
    else:
        quoted_pattern = r'["\']([^"\']+)["\']'
        matches = re.finditer(quoted_pattern, text)
        for match in matches:
            quote_text = match.group(1).strip()
            if (
                config.min_quote_length
                <= len(quote_text)
                <= config.max_quote_length
            ):
                quote = Quote(
                    quote_text=quote_text,
                    start_position=match.start(),
                    end_position=match.end(),
                )
                quotes.append(quote)

    if not quotes and len(text) >= config.min_quote_length:
        truncated = text[: config.max_quote_length]
        if len(text) > config.max_quote_length:
            last_period = truncated.rfind(".")
            if last_period > config.min_quote_length:
                truncated = truncated[: last_period + 1]
        quotes.append(
            Quote(
                quote_text=truncated,
                start_position=0,
                end_position=len(truncated),
            )
        )

    return quotes


def categorize_testimonial(
    testimonial: TestimonialRecord, config: CategorizationConfig
) -> Optional[str]:
    """Categorize testimonial by product or service.

    Args:
        testimonial: Testimonial record
        config: Categorization configuration

    Returns:
        Category name if found, None otherwise
    """
    if testimonial.category:
        return testimonial.category

    if testimonial.product:
        return testimonial.product

    if not config.auto_categorize:
        return None

    text_lower = testimonial.testimonial_text.lower()

    for product, keywords in config.product_keywords.items():
        if any(keyword.lower() in text_lower for keyword in keywords):
            return product

    for service, keywords in config.service_keywords.items():
        if any(keyword.lower() in text_lower for keyword in keywords):
            return service

    return None


def load_permissions(permission_file: Path) -> Dict[str, PermissionStatus]:
    """Load permission statuses from file.

    Args:
        permission_file: Path to permission tracking file

    Returns:
        Dictionary mapping testimonial_id to PermissionStatus
    """
    if not permission_file.exists():
        return {}

    try:
        with open(permission_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return {
                tid: PermissionStatus(status)
                for tid, status in data.items()
            }

    except Exception as e:
        logger.warning(f"Failed to load permissions: {e}")

    return {}


def save_permissions(
    permissions: Dict[str, PermissionStatus], permission_file: Path
) -> None:
    """Save permission statuses to file.

    Args:
        permissions: Dictionary of permission statuses
        permission_file: Path to permission tracking file
    """
    permission_file.parent.mkdir(parents=True, exist_ok=True)

    data = {tid: status.value for tid, status in permissions.items()}

    try:
        with open(permission_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Permissions saved to {permission_file}")
    except Exception as e:
        logger.error(f"Failed to save permissions: {e}")


def generate_markdown_material(
    testimonial: TestimonialRecord, config: MarketingMaterialConfig
) -> str:
    """Generate markdown marketing material.

    Args:
        testimonial: Testimonial record
        config: Marketing material configuration

    Returns:
        Markdown content string
    """
    content_parts = []

    if testimonial.quotes:
        quote_text = testimonial.quotes[0].quote_text
    else:
        quote_text = testimonial.testimonial_text[:500]

    content_parts.append(f'> {quote_text}')

    if config.include_customer_name:
        content_parts.append(f"\n**— {testimonial.customer_name}**")

    if config.include_rating and testimonial.rating:
        stars = "★" * int(testimonial.rating) + "☆" * (
            5 - int(testimonial.rating)
        )
        content_parts.append(f"\nRating: {stars} ({testimonial.rating}/5)")

    if config.include_date and testimonial.date:
        content_parts.append(
            f"\nDate: {testimonial.date.strftime('%B %Y')}"
        )

    if testimonial.category:
        content_parts.append(f"\nCategory: {testimonial.category}")

    return "\n".join(content_parts)


def generate_html_material(
    testimonial: TestimonialRecord, config: MarketingMaterialConfig
) -> str:
    """Generate HTML marketing material.

    Args:
        testimonial: Testimonial record
        config: Marketing material configuration

    Returns:
        HTML content string
    """
    if testimonial.quotes:
        quote_text = testimonial.quotes[0].quote_text
    else:
        quote_text = testimonial.testimonial_text[:500]

    html_parts = ['<div class="testimonial">']
    html_parts.append(f'  <blockquote>{quote_text}</blockquote>')

    if config.include_customer_name:
        html_parts.append(f'  <p class="author">— {testimonial.customer_name}</p>')

    if config.include_rating and testimonial.rating:
        stars = "★" * int(testimonial.rating) + "☆" * (
            5 - int(testimonial.rating)
        )
        html_parts.append(f'  <p class="rating">{stars} ({testimonial.rating}/5)</p>')

    if config.include_date and testimonial.date:
        html_parts.append(
            f'  <p class="date">{testimonial.date.strftime("%B %Y")}</p>'
        )

    if testimonial.category:
        html_parts.append(f'  <p class="category">Category: {testimonial.category}</p>')

    html_parts.append("</div>")

    return "\n".join(html_parts)


def generate_marketing_materials(
    testimonials: List[TestimonialRecord],
    config: MarketingMaterialConfig,
    output_dir: Path,
) -> List[MarketingMaterial]:
    """Generate marketing materials for testimonials.

    Args:
        testimonials: List of testimonial records
        config: Marketing material configuration
        output_dir: Output directory for materials

    Returns:
        List of generated marketing materials
    """
    materials = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for testimonial in testimonials:
        for format_type in config.output_formats:
            if format_type.lower() == "markdown":
                content = generate_markdown_material(testimonial, config)
                extension = "md"
            elif format_type.lower() == "html":
                content = generate_html_material(testimonial, config)
                extension = "html"
            else:
                logger.warning(f"Unsupported format: {format_type}")
                continue

            material = MarketingMaterial(
                format=format_type,
                content=content,
                testimonial_id=testimonial.testimonial_id,
                category=testimonial.category,
            )
            materials.append(material)

            filename = f"{testimonial.testimonial_id}.{extension}"
            filepath = output_dir / filename

            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.debug(f"Generated {format_type} material: {filepath}")
            except Exception as e:
                logger.error(f"Failed to write material to {filepath}: {e}")

    logger.info(f"Generated {len(materials)} marketing materials")
    return materials


def process_testimonials(config_path: Path) -> Dict[str, any]:
    """Process testimonials and generate marketing materials.

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary with processing results

    Raises:
        FileNotFoundError: If config or data files are missing
        ValueError: If configuration is invalid
    """
    config = load_config(config_path)
    project_root = config_path.parent

    testimonials = load_testimonial_data(config.testimonial_data, project_root)

    if not testimonials:
        logger.warning("No testimonials available for processing")
        return {
            "testimonials_processed": 0,
            "quotes_extracted": 0,
            "materials_generated": 0,
        }

    permissions = {}
    permission_file = Path(config.permission.permission_file)
    if not permission_file.is_absolute():
        permission_file = project_root / permission_file

    permissions = load_permissions(permission_file)

    quotes_count = 0
    for testimonial in testimonials:
        quotes = extract_quotes(testimonial, config.quote_extraction)
        testimonial.quotes = quotes
        quotes_count += len(quotes)

        category = categorize_testimonial(testimonial, config.categorization)
        if category:
            testimonial.category = category

        if testimonial.testimonial_id not in permissions:
            permissions[testimonial.testimonial_id] = (
                config.permission.default_permission_status
            )
        testimonial.permission_status = permissions[testimonial.testimonial_id]

    save_permissions(permissions, permission_file)

    eligible_testimonials = [
        t
        for t in testimonials
        if not config.permission.require_permission_for_use
        or t.permission_status == PermissionStatus.GRANTED
    ]

    output_dir = Path(config.output_directory)
    if not output_dir.is_absolute():
        output_dir = project_root / output_dir

    materials = generate_marketing_materials(
        eligible_testimonials, config.marketing, output_dir
    )

    return {
        "testimonials_processed": len(testimonials),
        "quotes_extracted": quotes_count,
        "materials_generated": len(materials),
        "categories": {
            t.category
            for t in testimonials
            if t.category
        },
    }


def main() -> None:
    """Main entry point for the testimonial processor."""
    settings = AppSettings()
    config_path = Path(settings.config_path)

    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent
        config_path = project_root / config_path

    try:
        logger.info("Starting testimonial processing")
        results = process_testimonials(config_path)
        logger.info(
            f"Processing complete. Processed {results['testimonials_processed']} "
            f"testimonials, extracted {results['quotes_extracted']} quotes, "
            f"and generated {results['materials_generated']} marketing materials."
        )
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
