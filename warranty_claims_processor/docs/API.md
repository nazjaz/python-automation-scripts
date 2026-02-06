# Warranty Claims Processor API Documentation

## Overview

This document describes the public API for the warranty claims processing system.

## Configuration Models

### WarrantyDataConfig

Configuration for warranty data source.

**Fields:**
- `file_path` (str): Path to warranty data file
- `format` (str): File format (`csv` or `json`)
- `warranty_id_column` (str): Column name for warranty ID
- `customer_id_column` (str): Column name for customer ID
- `product_id_column` (str): Column name for product ID
- `purchase_date_column` (str): Column name for purchase date
- `warranty_start_date_column` (str): Column name for warranty start date
- `warranty_duration_months_column` (str): Column name for warranty duration
- `coverage_type_column` (Optional[str]): Column name for coverage type

### ClaimDataConfig

Configuration for claim data source.

**Fields:**
- `file_path` (str): Path to claim data file
- `format` (str): File format (`csv` or `json`)
- `claim_id_column` (str): Column name for claim ID
- `warranty_id_column` (str): Column name for warranty ID
- `claim_date_column` (str): Column name for claim date
- `issue_description_column` (str): Column name for issue description
- `status_column` (Optional[str]): Column name for claim status
- `service_provider_column` (Optional[str]): Column name for service provider
- `claim_amount_column` (Optional[str]): Column name for claim amount

### ServiceProviderConfig

Configuration for service provider data source.

**Fields:**
- `file_path` (Optional[str]): Path to service provider file
- `format` (str): File format (`csv` or `json`)
- `provider_id_column` (str): Column name for provider ID
- `provider_name_column` (str): Column name for provider name
- `service_areas_column` (Optional[str]): Column name for service areas
- `capacity_column` (Optional[str]): Column name for capacity

### ValidationConfig

Configuration for coverage validation.

**Fields:**
- `require_active_warranty` (bool): Require warranty to be active
- `validate_coverage_type` (bool): Validate coverage type matches issue
- `auto_approve_threshold` (float): Auto-approve claims below this amount

## Data Models

### WarrantyRecord

Represents a warranty record.

**Fields:**
- `warranty_id` (str): Unique warranty identifier
- `customer_id` (str): Customer identifier
- `product_id` (str): Product identifier
- `purchase_date` (datetime): Purchase date
- `warranty_start_date` (datetime): Warranty start date
- `warranty_duration_months` (int): Warranty duration in months
- `coverage_type` (Optional[str]): Coverage type

**Methods:**
- `is_active(check_date: datetime) -> bool`: Check if warranty is active

### ClaimRecord

Represents a warranty claim record.

**Fields:**
- `claim_id` (str): Unique claim identifier
- `warranty_id` (str): Warranty identifier
- `claim_date` (datetime): Claim submission date
- `issue_description` (str): Description of the issue
- `status` (ClaimStatus): Current claim status
- `service_provider` (Optional[str]): Assigned service provider ID
- `claim_amount` (Optional[float]): Claim amount
- `coverage_status` (Optional[CoverageStatus]): Coverage validation status
- `validation_notes` (Optional[str]): Validation notes

### ServiceProvider

Represents a service provider.

**Fields:**
- `provider_id` (str): Provider identifier
- `provider_name` (str): Provider name
- `service_areas` (List[str]): List of service areas
- `capacity` (Optional[int]): Maximum capacity
- `active_claims` (int): Current active claims count

### WarrantyAnalytics

Warranty analytics summary.

**Fields:**
- `total_claims` (int): Total number of claims
- `total_warranties` (int): Total number of warranties
- `claims_by_status` (Dict[str, int]): Claims count by status
- `coverage_validation_results` (Dict[str, int]): Coverage validation results
- `total_claim_amount` (float): Total claim amount
- `avg_claim_amount` (float): Average claim amount
- `approval_rate` (float): Approval rate (0.0 to 1.0)
- `provider_performance` (Dict[str, Dict[str, float]]): Provider performance metrics
- `claims_by_month` (Dict[str, int]): Claims count by month
- `generated_at` (datetime): Generation timestamp

## Enumerations

### ClaimStatus

Warranty claim status enumeration.

**Values:**
- `SUBMITTED`: Claim submitted
- `VALIDATED`: Coverage validated
- `APPROVED`: Claim approved
- `IN_PROGRESS`: Service in progress
- `COMPLETED`: Claim completed
- `DENIED`: Claim denied
- `CANCELLED`: Claim cancelled

### CoverageStatus

Warranty coverage status.

**Values:**
- `COVERED`: Coverage validated
- `NOT_COVERED`: Issue not covered
- `EXPIRED`: Warranty expired
- `INVALID`: Invalid warranty

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

### load_warranty_data(config: WarrantyDataConfig, project_root: Path) -> Dict[str, WarrantyRecord]

Load warranty data from file.

**Parameters:**
- `config` (WarrantyDataConfig): Warranty data configuration
- `project_root` (Path): Project root directory

**Returns:**
- `Dict[str, WarrantyRecord]`: Dictionary mapping warranty_id to WarrantyRecord

**Raises:**
- `FileNotFoundError`: If data file does not exist
- `ValueError`: If data format is invalid

### validate_coverage(claim: ClaimRecord, warranty: Optional[WarrantyRecord], config: ValidationConfig) -> Tuple[CoverageStatus, str]

Validate warranty coverage for a claim.

**Parameters:**
- `claim` (ClaimRecord): Claim record to validate
- `warranty` (Optional[WarrantyRecord]): Warranty record
- `config` (ValidationConfig): Validation configuration

**Returns:**
- `Tuple[CoverageStatus, str]`: (coverage_status, validation_notes)

### assign_service_provider(claim: ClaimRecord, providers: Dict[str, ServiceProvider]) -> Optional[str]

Assign service provider to claim.

**Parameters:**
- `claim` (ClaimRecord): Claim record
- `providers` (Dict[str, ServiceProvider]): Dictionary of available providers

**Returns:**
- `Optional[str]`: Provider ID if assigned, None otherwise

### process_claims(claims: List[ClaimRecord], warranties: Dict[str, WarrantyRecord], providers: Dict[str, ServiceProvider], config: ValidationConfig) -> List[ClaimRecord]

Process claims through validation and assignment workflow.

**Parameters:**
- `claims` (List[ClaimRecord]): List of claim records
- `warranties` (Dict[str, WarrantyRecord]): Dictionary of warranty records
- `providers` (Dict[str, ServiceProvider]): Dictionary of service providers
- `config` (ValidationConfig): Validation configuration

**Returns:**
- `List[ClaimRecord]`: List of processed claim records

### generate_analytics(claims: List[ClaimRecord], warranties: Dict[str, WarrantyRecord], providers: Dict[str, ServiceProvider]) -> WarrantyAnalytics

Generate warranty analytics.

**Parameters:**
- `claims` (List[ClaimRecord]): List of processed claim records
- `warranties` (Dict[str, WarrantyRecord]): Dictionary of warranty records
- `providers` (Dict[str, ServiceProvider]): Dictionary of service providers

**Returns:**
- `WarrantyAnalytics`: Warranty analytics object

### process_warranty_claims(config_path: Path) -> Dict[str, any]

Process warranty claims and generate analytics.

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
from warranty_claims_processor.src.main import process_warranty_claims

config_path = Path("config.yaml")
results = process_warranty_claims(config_path)

print(f"Processed {results['claims_processed']} claims")

analytics = results['analytics']
if analytics:
    print(f"Total Claims: {analytics.total_claims}")
    print(f"Approval Rate: {analytics.approval_rate:.1%}")
    print(f"Average Claim Amount: ${analytics.avg_claim_amount:,.2f}")
```
