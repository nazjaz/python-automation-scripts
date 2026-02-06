"""Warranty Claims Processor.

Automatically processes customer warranty claims by validating coverage, tracking
claim status, coordinating with service providers, and generating warranty analytics.
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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


class ClaimStatus(str, Enum):
    """Warranty claim status enumeration."""

    SUBMITTED = "submitted"
    VALIDATED = "validated"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DENIED = "denied"
    CANCELLED = "cancelled"


class CoverageStatus(str, Enum):
    """Warranty coverage status."""

    COVERED = "covered"
    NOT_COVERED = "not_covered"
    EXPIRED = "expired"
    INVALID = "invalid"


class WarrantyDataConfig(BaseModel):
    """Configuration for warranty data source."""

    file_path: str = Field(..., description="Path to warranty data file")
    format: str = Field(default="csv", description="File format: csv or json")
    warranty_id_column: str = Field(
        default="warranty_id", description="Column name for warranty ID"
    )
    customer_id_column: str = Field(
        default="customer_id", description="Column name for customer ID"
    )
    product_id_column: str = Field(
        default="product_id", description="Column name for product ID"
    )
    purchase_date_column: str = Field(
        default="purchase_date", description="Column name for purchase date"
    )
    warranty_start_date_column: str = Field(
        default="warranty_start_date",
        description="Column name for warranty start date",
    )
    warranty_duration_months_column: str = Field(
        default="warranty_duration_months",
        description="Column name for warranty duration in months",
    )
    coverage_type_column: Optional[str] = Field(
        default=None, description="Column name for coverage type"
    )


class ClaimDataConfig(BaseModel):
    """Configuration for claim data source."""

    file_path: str = Field(..., description="Path to claim data file")
    format: str = Field(default="csv", description="File format: csv or json")
    claim_id_column: str = Field(
        default="claim_id", description="Column name for claim ID"
    )
    warranty_id_column: str = Field(
        default="warranty_id", description="Column name for warranty ID"
    )
    claim_date_column: str = Field(
        default="claim_date", description="Column name for claim date"
    )
    issue_description_column: str = Field(
        default="issue_description",
        description="Column name for issue description",
    )
    status_column: Optional[str] = Field(
        default=None, description="Column name for claim status"
    )
    service_provider_column: Optional[str] = Field(
        default=None, description="Column name for service provider"
    )
    claim_amount_column: Optional[str] = Field(
        default=None, description="Column name for claim amount"
    )


class ServiceProviderConfig(BaseModel):
    """Configuration for service provider data source."""

    file_path: Optional[str] = Field(
        default=None, description="Path to service provider file"
    )
    format: str = Field(default="csv", description="File format: csv or json")
    provider_id_column: str = Field(
        default="provider_id", description="Column name for provider ID"
    )
    provider_name_column: str = Field(
        default="provider_name", description="Column name for provider name"
    )
    service_areas_column: Optional[str] = Field(
        default=None, description="Column name for service areas"
    )
    capacity_column: Optional[str] = Field(
        default=None, description="Column name for capacity"
    )


class ValidationConfig(BaseModel):
    """Configuration for coverage validation."""

    require_active_warranty: bool = Field(
        default=True, description="Require warranty to be active"
    )
    validate_coverage_type: bool = Field(
        default=False, description="Validate coverage type matches issue"
    )
    auto_approve_threshold: float = Field(
        default=500.0, description="Auto-approve claims below this amount"
    )


class AnalyticsConfig(BaseModel):
    """Configuration for analytics generation."""

    output_format: str = Field(
        default="markdown", description="Report format: markdown or html"
    )
    output_path: str = Field(
        default="logs/warranty_analytics.md",
        description="Path for analytics report",
    )


class Config(BaseModel):
    """Main configuration model."""

    warranty_data: WarrantyDataConfig = Field(
        ..., description="Warranty data source configuration"
    )
    claim_data: ClaimDataConfig = Field(
        ..., description="Claim data source configuration"
    )
    service_provider: ServiceProviderConfig = Field(
        default_factory=ServiceProviderConfig,
        description="Service provider configuration",
    )
    validation: ValidationConfig = Field(
        default_factory=ValidationConfig,
        description="Validation settings",
    )
    analytics: AnalyticsConfig = Field(
        default_factory=AnalyticsConfig,
        description="Analytics generation settings",
    )
    claims_output_file: str = Field(
        default="logs/processed_claims.json",
        description="Path to save processed claims",
    )


class AppSettings(BaseSettings):
    """Application settings from environment variables."""

    config_path: str = "config.yaml"


@dataclass
class WarrantyRecord:
    """Represents a warranty record."""

    warranty_id: str
    customer_id: str
    product_id: str
    purchase_date: datetime
    warranty_start_date: datetime
    warranty_duration_months: int
    coverage_type: Optional[str] = None

    def is_active(self, check_date: datetime) -> bool:
        """Check if warranty is active on given date."""
        end_date = self.warranty_start_date + timedelta(
            days=self.warranty_duration_months * 30
        )
        return self.warranty_start_date <= check_date <= end_date


@dataclass
class ClaimRecord:
    """Represents a warranty claim record."""

    claim_id: str
    warranty_id: str
    claim_date: datetime
    issue_description: str
    status: ClaimStatus = ClaimStatus.SUBMITTED
    service_provider: Optional[str] = None
    claim_amount: Optional[float] = None
    coverage_status: Optional[CoverageStatus] = None
    validation_notes: Optional[str] = None


@dataclass
class ServiceProvider:
    """Represents a service provider."""

    provider_id: str
    provider_name: str
    service_areas: List[str] = field(default_factory=list)
    capacity: Optional[int] = None
    active_claims: int = 0


@dataclass
class WarrantyAnalytics:
    """Warranty analytics summary."""

    total_claims: int
    total_warranties: int
    claims_by_status: Dict[str, int]
    coverage_validation_results: Dict[str, int]
    total_claim_amount: float
    avg_claim_amount: float
    approval_rate: float
    provider_performance: Dict[str, Dict[str, float]]
    claims_by_month: Dict[str, int]
    generated_at: datetime


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


def load_warranty_data(
    config: WarrantyDataConfig, project_root: Path
) -> Dict[str, WarrantyRecord]:
    """Load warranty data from file.

    Args:
        config: Warranty data configuration
        project_root: Project root directory

    Returns:
        Dictionary mapping warranty_id to WarrantyRecord

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        raise FileNotFoundError(f"Warranty data file not found: {data_path}")

    warranties = {}

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        required_columns = [
            config.warranty_id_column,
            config.customer_id_column,
            config.product_id_column,
            config.purchase_date_column,
            config.warranty_start_date_column,
            config.warranty_duration_months_column,
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df[config.purchase_date_column] = pd.to_datetime(
            df[config.purchase_date_column]
        )
        df[config.warranty_start_date_column] = pd.to_datetime(
            df[config.warranty_start_date_column]
        )

        for _, row in df.iterrows():
            warranty = WarrantyRecord(
                warranty_id=str(row[config.warranty_id_column]),
                customer_id=str(row[config.customer_id_column]),
                product_id=str(row[config.product_id_column]),
                purchase_date=row[config.purchase_date_column],
                warranty_start_date=row[config.warranty_start_date_column],
                warranty_duration_months=int(
                    row[config.warranty_duration_months_column]
                ),
            )

            if (
                config.coverage_type_column
                and config.coverage_type_column in df.columns
            ):
                if pd.notna(row[config.coverage_type_column]):
                    warranty.coverage_type = str(row[config.coverage_type_column])

            warranties[warranty.warranty_id] = warranty

        logger.info(f"Loaded {len(warranties)} warranty records")
        return warranties

    except pd.errors.EmptyDataError:
        logger.warning(f"Warranty data file is empty: {data_path}")
        return {}
    except Exception as e:
        logger.error(f"Failed to load warranty data: {e}")
        raise


def load_claim_data(
    config: ClaimDataConfig, project_root: Path
) -> List[ClaimRecord]:
    """Load claim data from file.

    Args:
        config: Claim data configuration
        project_root: Project root directory

    Returns:
        List of ClaimRecord objects

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        raise FileNotFoundError(f"Claim data file not found: {data_path}")

    claims = []

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        required_columns = [
            config.claim_id_column,
            config.warranty_id_column,
            config.claim_date_column,
            config.issue_description_column,
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df[config.claim_date_column] = pd.to_datetime(df[config.claim_date_column])

        for _, row in df.iterrows():
            claim = ClaimRecord(
                claim_id=str(row[config.claim_id_column]),
                warranty_id=str(row[config.warranty_id_column]),
                claim_date=row[config.claim_date_column],
                issue_description=str(row[config.issue_description_column]),
            )

            if config.status_column and config.status_column in df.columns:
                if pd.notna(row[config.status_column]):
                    try:
                        claim.status = ClaimStatus(
                            str(row[config.status_column]).lower()
                        )
                    except ValueError:
                        pass

            if (
                config.service_provider_column
                and config.service_provider_column in df.columns
            ):
                if pd.notna(row[config.service_provider_column]):
                    claim.service_provider = str(
                        row[config.service_provider_column]
                    )

            if (
                config.claim_amount_column
                and config.claim_amount_column in df.columns
            ):
                if pd.notna(row[config.claim_amount_column]):
                    claim.claim_amount = float(row[config.claim_amount_column])

            claims.append(claim)

        logger.info(f"Loaded {len(claims)} claim records")
        return claims

    except pd.errors.EmptyDataError:
        logger.warning(f"Claim data file is empty: {data_path}")
        return []
    except Exception as e:
        logger.error(f"Failed to load claim data: {e}")
        raise


def load_service_providers(
    config: ServiceProviderConfig, project_root: Path
) -> Dict[str, ServiceProvider]:
    """Load service provider data from file.

    Args:
        config: Service provider configuration
        project_root: Project root directory

    Returns:
        Dictionary mapping provider_id to ServiceProvider

    Raises:
        FileNotFoundError: If data file does not exist
        ValueError: If data format is invalid
    """
    if not config.file_path:
        return {}

    data_path = Path(config.file_path)
    if not data_path.is_absolute():
        data_path = project_root / data_path

    if not data_path.exists():
        logger.warning(f"Service provider file not found: {data_path}")
        return {}

    providers = {}

    try:
        if config.format.lower() == "csv":
            df = pd.read_csv(data_path)
        elif config.format.lower() == "json":
            df = pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported format: {config.format}")

        required_columns = [
            config.provider_id_column,
            config.provider_name_column,
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        for _, row in df.iterrows():
            provider = ServiceProvider(
                provider_id=str(row[config.provider_id_column]),
                provider_name=str(row[config.provider_name_column]),
            )

            if (
                config.service_areas_column
                and config.service_areas_column in df.columns
            ):
                if pd.notna(row[config.service_areas_column]):
                    areas_str = str(row[config.service_areas_column])
                    provider.service_areas = [
                        area.strip() for area in areas_str.split(",")
                    ]

            if config.capacity_column and config.capacity_column in df.columns:
                if pd.notna(row[config.capacity_column]):
                    provider.capacity = int(row[config.capacity_column])

            providers[provider.provider_id] = provider

        logger.info(f"Loaded {len(providers)} service providers")
        return providers

    except Exception as e:
        logger.warning(f"Failed to load service providers: {e}")
        return {}


def validate_coverage(
    claim: ClaimRecord,
    warranty: Optional[WarrantyRecord],
    config: ValidationConfig,
) -> Tuple[CoverageStatus, str]:
    """Validate warranty coverage for a claim.

    Args:
        claim: Claim record to validate
        warranty: Warranty record (optional)
        config: Validation configuration

    Returns:
        Tuple of (coverage_status, validation_notes)
    """
    if not warranty:
        return CoverageStatus.INVALID, "Warranty not found"

    if config.require_active_warranty:
        if not warranty.is_active(claim.claim_date):
            end_date = warranty.warranty_start_date + timedelta(
                days=warranty.warranty_duration_months * 30
            )
            return (
                CoverageStatus.EXPIRED,
                f"Warranty expired on {end_date.strftime('%Y-%m-%d')}",
            )

    if config.validate_coverage_type and warranty.coverage_type:
        if "accidental" in claim.issue_description.lower():
            if "accidental" not in warranty.coverage_type.lower():
                return (
                    CoverageStatus.NOT_COVERED,
                    "Issue type not covered by warranty",
                )

    return CoverageStatus.COVERED, "Coverage validated"


def assign_service_provider(
    claim: ClaimRecord,
    providers: Dict[str, ServiceProvider],
) -> Optional[str]:
    """Assign service provider to claim.

    Args:
        claim: Claim record
        providers: Dictionary of available providers

    Returns:
        Provider ID if assigned, None otherwise
    """
    if not providers:
        return None

    available_providers = [
        p
        for p in providers.values()
        if p.capacity is None or p.active_claims < p.capacity
    ]

    if not available_providers:
        return None

    available_providers.sort(key=lambda x: x.active_claims)
    assigned = available_providers[0]
    assigned.active_claims += 1

    return assigned.provider_id


def process_claims(
    claims: List[ClaimRecord],
    warranties: Dict[str, WarrantyRecord],
    providers: Dict[str, ServiceProvider],
    config: ValidationConfig,
) -> List[ClaimRecord]:
    """Process claims through validation and assignment workflow.

    Args:
        claims: List of claim records
        warranties: Dictionary of warranty records
        providers: Dictionary of service providers
        config: Validation configuration

    Returns:
        List of processed claim records
    """
    processed_claims = []

    for claim in claims:
        warranty = warranties.get(claim.warranty_id)

        coverage_status, validation_notes = validate_coverage(
            claim, warranty, config
        )
        claim.coverage_status = coverage_status
        claim.validation_notes = validation_notes

        if coverage_status == CoverageStatus.COVERED:
            if claim.status == ClaimStatus.SUBMITTED:
                claim.status = ClaimStatus.VALIDATED

            if claim.claim_amount and claim.claim_amount <= config.auto_approve_threshold:
                if claim.status == ClaimStatus.VALIDATED:
                    claim.status = ClaimStatus.APPROVED

            if claim.status == ClaimStatus.APPROVED and not claim.service_provider:
                provider_id = assign_service_provider(claim, providers)
                if provider_id:
                    claim.service_provider = provider_id
                    claim.status = ClaimStatus.IN_PROGRESS

        elif coverage_status in [
            CoverageStatus.EXPIRED,
            CoverageStatus.NOT_COVERED,
            CoverageStatus.INVALID,
        ]:
            if claim.status == ClaimStatus.SUBMITTED:
                claim.status = ClaimStatus.DENIED

        processed_claims.append(claim)

    logger.info(f"Processed {len(processed_claims)} claims")
    return processed_claims


def generate_analytics(
    claims: List[ClaimRecord],
    warranties: Dict[str, WarrantyRecord],
    providers: Dict[str, ServiceProvider],
) -> WarrantyAnalytics:
    """Generate warranty analytics.

    Args:
        claims: List of processed claim records
        warranties: Dictionary of warranty records
        providers: Dictionary of service providers

    Returns:
        WarrantyAnalytics object
    """
    total_claims = len(claims)
    total_warranties = len(warranties)

    claims_by_status = defaultdict(int)
    coverage_results = defaultdict(int)
    claim_amounts = []

    for claim in claims:
        claims_by_status[claim.status.value] += 1
        if claim.coverage_status:
            coverage_results[claim.coverage_status.value] += 1
        if claim.claim_amount:
            claim_amounts.append(claim.claim_amount)

    total_claim_amount = sum(claim_amounts) if claim_amounts else 0.0
    avg_claim_amount = (
        total_claim_amount / len(claim_amounts) if claim_amounts else 0.0
    )

    approved_count = claims_by_status.get(ClaimStatus.APPROVED.value, 0)
    completed_count = claims_by_status.get(ClaimStatus.COMPLETED.value, 0)
    denied_count = claims_by_status.get(ClaimStatus.DENIED.value, 0)
    total_processed = approved_count + completed_count + denied_count
    approval_rate = (
        (approved_count + completed_count) / total_processed
        if total_processed > 0
        else 0.0
    )

    provider_performance = {}
    for provider_id, provider in providers.items():
        provider_claims = [
            c for c in claims if c.service_provider == provider_id
        ]
        if provider_claims:
            completed = sum(
                1
                for c in provider_claims
                if c.status == ClaimStatus.COMPLETED
            )
            provider_performance[provider_id] = {
                "name": provider.provider_name,
                "total_claims": len(provider_claims),
                "completed_claims": completed,
                "completion_rate": completed / len(provider_claims),
            }

    claims_by_month = defaultdict(int)
    for claim in claims:
        month_key = claim.claim_date.strftime("%Y-%m")
        claims_by_month[month_key] += 1

    return WarrantyAnalytics(
        total_claims=total_claims,
        total_warranties=total_warranties,
        claims_by_status=dict(claims_by_status),
        coverage_validation_results=dict(coverage_results),
        total_claim_amount=total_claim_amount,
        avg_claim_amount=avg_claim_amount,
        approval_rate=approval_rate,
        provider_performance=provider_performance,
        claims_by_month=dict(claims_by_month),
        generated_at=datetime.now(),
    )


def write_markdown_report(
    analytics: WarrantyAnalytics, output_path: Path
) -> None:
    """Write warranty analytics report to markdown file.

    Args:
        analytics: Warranty analytics data
        output_path: Path to write the report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Warranty Claims Analytics Report\n\n")
        f.write(
            f"**Generated:** {analytics.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        f.write("## Summary\n\n")
        f.write(f"- **Total Claims:** {analytics.total_claims}\n")
        f.write(f"- **Total Warranties:** {analytics.total_warranties}\n")
        f.write(f"- **Total Claim Amount:** ${analytics.total_claim_amount:,.2f}\n")
        f.write(f"- **Average Claim Amount:** ${analytics.avg_claim_amount:,.2f}\n")
        f.write(f"- **Approval Rate:** {analytics.approval_rate:.1%}\n")
        f.write("\n")

        f.write("## Claims by Status\n\n")
        if analytics.claims_by_status:
            f.write("| Status | Count |\n")
            f.write("|--------|-------|\n")
            for status, count in sorted(
                analytics.claims_by_status.items(), key=lambda x: -x[1]
            ):
                f.write(f"| {status.replace('_', ' ').title()} | {count} |\n")
        f.write("\n")

        f.write("## Coverage Validation Results\n\n")
        if analytics.coverage_validation_results:
            f.write("| Coverage Status | Count |\n")
            f.write("|-----------------|-------|\n")
            for status, count in sorted(
                analytics.coverage_validation_results.items(),
                key=lambda x: -x[1],
            ):
                f.write(f"| {status.replace('_', ' ').title()} | {count} |\n")
        f.write("\n")

        f.write("## Service Provider Performance\n\n")
        if analytics.provider_performance:
            f.write(
                "| Provider | Total Claims | Completed | Completion Rate |\n"
            )
            f.write("|----------|--------------|-----------|-----------------|\n")
            for provider_id, perf in analytics.provider_performance.items():
                f.write(
                    f"| {perf['name']} | {perf['total_claims']} | "
                    f"{perf['completed_claims']} | "
                    f"{perf['completion_rate']:.1%} |\n"
                )
        f.write("\n")

        f.write("## Claims by Month\n\n")
        if analytics.claims_by_month:
            f.write("| Month | Claim Count |\n")
            f.write("|-------|-------------|\n")
            for month, count in sorted(analytics.claims_by_month.items()):
                f.write(f"| {month} | {count} |\n")

    logger.info(f"Report written to {output_path}")


def process_warranty_claims(config_path: Path) -> Dict[str, any]:
    """Process warranty claims and generate analytics.

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

    warranties = load_warranty_data(config.warranty_data, project_root)
    claims = load_claim_data(config.claim_data, project_root)
    providers = load_service_providers(
        config.service_provider, project_root
    )

    if not claims:
        logger.warning("No claims available for processing")
        return {
            "claims_processed": 0,
            "analytics": None,
        }

    processed_claims = process_claims(
        claims, warranties, providers, config.validation
    )

    analytics = generate_analytics(processed_claims, warranties, providers)

    report_path = Path(config.analytics.output_path)
    if not report_path.is_absolute():
        report_path = project_root / report_path

    write_markdown_report(analytics, report_path)

    claims_output = Path(config.claims_output_file)
    if not claims_output.is_absolute():
        claims_output = project_root / claims_output

    claims_output.parent.mkdir(parents=True, exist_ok=True)
    claims_data = [
        {
            "claim_id": claim.claim_id,
            "warranty_id": claim.warranty_id,
            "status": claim.status.value,
            "coverage_status": (
                claim.coverage_status.value if claim.coverage_status else None
            ),
            "service_provider": claim.service_provider,
            "claim_amount": claim.claim_amount,
            "validation_notes": claim.validation_notes,
        }
        for claim in processed_claims
    ]

    with open(claims_output, "w", encoding="utf-8") as f:
        json.dump(claims_data, f, indent=2)

    logger.info(f"Processed claims saved to {claims_output}")

    return {
        "claims_processed": len(processed_claims),
        "analytics": analytics,
    }


def main() -> None:
    """Main entry point for the warranty claims processor."""
    settings = AppSettings()
    config_path = Path(settings.config_path)

    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent
        config_path = project_root / config_path

    try:
        logger.info("Starting warranty claims processing")
        results = process_warranty_claims(config_path)
        logger.info(
            f"Processing complete. Processed {results['claims_processed']} claims."
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
