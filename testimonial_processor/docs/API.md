# Testimonial Processor API Documentation

## Overview

This document describes the public API for the testimonial processing system.

## Configuration Models

### TestimonialDataConfig

Configuration for testimonial data source.

**Fields:**
- `file_path` (str): Path to testimonial data file
- `format` (str): File format (`csv` or `json`)
- `testimonial_id_column` (str): Column name for testimonial ID
- `customer_name_column` (str): Column name for customer name
- `testimonial_text_column` (str): Column name for testimonial text
- `product_column` (Optional[str]): Column name for product name
- `category_column` (Optional[str]): Column name for category
- `rating_column` (Optional[str]): Column name for rating
- `date_column` (Optional[str]): Column name for date

### QuoteExtractionConfig

Configuration for quote extraction.

**Fields:**
- `min_quote_length` (int): Minimum quote length in characters
- `max_quote_length` (int): Maximum quote length in characters
- `extract_full_sentences` (bool): Extract complete sentences only
- `quote_indicators` (List[str]): Indicators that suggest quoted content

### CategorizationConfig

Configuration for categorization.

**Fields:**
- `product_keywords` (Dict[str, List[str]]): Mapping of product names to keyword lists
- `service_keywords` (Dict[str, List[str]]): Mapping of service names to keyword lists
- `auto_categorize` (bool): Automatically categorize based on keywords

### MarketingMaterialConfig

Configuration for marketing material generation.

**Fields:**
- `output_formats` (List[str]): Output formats to generate (`markdown`, `html`)
- `include_customer_name` (bool): Include customer name in materials
- `include_rating` (bool): Include rating if available
- `include_date` (bool): Include testimonial date
- `template_path` (Optional[str]): Path to custom template file

### PermissionConfig

Configuration for permission tracking.

**Fields:**
- `permission_file` (str): Path to permission tracking file
- `default_permission_status` (PermissionStatus): Default permission status
- `require_permission_for_use` (bool): Require granted permission for marketing use

## Data Models

### Quote

Extracted quote from testimonial.

**Fields:**
- `quote_text` (str): The extracted quote text
- `start_position` (int): Start position in original text
- `end_position` (int): End position in original text
- `confidence` (float): Confidence score (default: 1.0)

### TestimonialRecord

Represents a testimonial record.

**Fields:**
- `testimonial_id` (str): Unique testimonial identifier
- `customer_name` (str): Customer name
- `testimonial_text` (str): Full testimonial text
- `product` (Optional[str]): Product name
- `category` (Optional[str]): Category name
- `rating` (Optional[float]): Rating value
- `date` (Optional[datetime]): Testimonial date
- `quotes` (List[Quote]): Extracted quotes
- `permission_status` (PermissionStatus): Permission status

### MarketingMaterial

Generated marketing material.

**Fields:**
- `format` (str): Material format (`markdown` or `html`)
- `content` (str): Material content
- `testimonial_id` (str): Associated testimonial ID
- `category` (Optional[str]): Category name
- `generated_at` (datetime): Generation timestamp

## Enumerations

### PermissionStatus

Permission status enumeration.

**Values:**
- `GRANTED`: Permission granted for use
- `PENDING`: Permission request pending
- `DENIED`: Permission denied
- `EXPIRED`: Permission expired
- `NOT_REQUESTED`: Permission not yet requested

## Functions

### load_config(config_path: Path) -> Config

Load and validate configuration from YAML file.

**Parameters:**
- `config_path` (Path): Path to configuration YAML file

**Returns:**
- `Config`: Validated configuration object

**Raises:**
- `FileNotFoundError`: If config file does not exist
- `ValueError`: If configuration is invalid

### load_testimonial_data(config: TestimonialDataConfig, project_root: Path) -> List[TestimonialRecord]

Load testimonial data from CSV or JSON file.

**Parameters:**
- `config` (TestimonialDataConfig): Testimonial data configuration
- `project_root` (Path): Project root directory

**Returns:**
- `List[TestimonialRecord]`: List of testimonial records

**Raises:**
- `FileNotFoundError`: If data file does not exist
- `ValueError`: If data format is invalid

### extract_quotes(testimonial: TestimonialRecord, config: QuoteExtractionConfig) -> List[Quote]

Extract quotes from testimonial text.

**Parameters:**
- `testimonial` (TestimonialRecord): Testimonial record
- `config` (QuoteExtractionConfig): Quote extraction configuration

**Returns:**
- `List[Quote]`: List of extracted quotes

### categorize_testimonial(testimonial: TestimonialRecord, config: CategorizationConfig) -> Optional[str]

Categorize testimonial by product or service.

**Parameters:**
- `testimonial` (TestimonialRecord): Testimonial record
- `config` (CategorizationConfig): Categorization configuration

**Returns:**
- `Optional[str]`: Category name if found, None otherwise

### generate_markdown_material(testimonial: TestimonialRecord, config: MarketingMaterialConfig) -> str

Generate markdown marketing material.

**Parameters:**
- `testimonial` (TestimonialRecord): Testimonial record
- `config` (MarketingMaterialConfig): Marketing material configuration

**Returns:**
- `str`: Markdown content string

### generate_html_material(testimonial: TestimonialRecord, config: MarketingMaterialConfig) -> str

Generate HTML marketing material.

**Parameters:**
- `testimonial` (TestimonialRecord): Testimonial record
- `config` (MarketingMaterialConfig): Marketing material configuration

**Returns:**
- `str`: HTML content string

### load_permissions(permission_file: Path) -> Dict[str, PermissionStatus]

Load permission statuses from file.

**Parameters:**
- `permission_file` (Path): Path to permission tracking file

**Returns:**
- `Dict[str, PermissionStatus]`: Dictionary mapping testimonial_id to PermissionStatus

### save_permissions(permissions: Dict[str, PermissionStatus], permission_file: Path) -> None

Save permission statuses to file.

**Parameters:**
- `permissions` (Dict[str, PermissionStatus]): Dictionary of permission statuses
- `permission_file` (Path): Path to permission tracking file

### process_testimonials(config_path: Path) -> Dict[str, any]

Process testimonials and generate marketing materials.

**Parameters:**
- `config_path` (Path): Path to configuration file

**Returns:**
- `Dict[str, any]`: Dictionary with processing results

**Raises:**
- `FileNotFoundError`: If config or data files are missing
- `ValueError`: If configuration is invalid

## Example Usage

```python
from pathlib import Path
from testimonial_processor.src.main import process_testimonials

config_path = Path("config.yaml")
results = process_testimonials(config_path)

print(f"Processed {results['testimonials_processed']} testimonials")
print(f"Extracted {results['quotes_extracted']} quotes")
print(f"Generated {results['materials_generated']} marketing materials")
print(f"Categories: {results['categories']}")
```
