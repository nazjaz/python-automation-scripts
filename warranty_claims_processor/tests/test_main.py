"""Tests for warranty claims processing."""

from datetime import datetime, timedelta

import pytest

from warranty_claims_processor.src.main import (
    ClaimRecord,
    ClaimStatus,
    CoverageStatus,
    ServiceProvider,
    ValidationConfig,
    WarrantyRecord,
    assign_service_provider,
    process_claims,
    validate_coverage,
)


def test_validate_coverage_active():
    """Test coverage validation for active warranty."""
    warranty = WarrantyRecord(
        warranty_id="warr_001",
        customer_id="cust_001",
        product_id="prod_001",
        purchase_date=datetime.now() - timedelta(days=365),
        warranty_start_date=datetime.now() - timedelta(days=365),
        warranty_duration_months=24,
    )

    claim = ClaimRecord(
        claim_id="claim_001",
        warranty_id="warr_001",
        claim_date=datetime.now() - timedelta(days=100),
        issue_description="Product defect",
    )

    config = ValidationConfig(require_active_warranty=True)

    status, notes = validate_coverage(claim, warranty, config)

    assert status == CoverageStatus.COVERED
    assert "validated" in notes.lower()


def test_validate_coverage_expired():
    """Test coverage validation for expired warranty."""
    warranty = WarrantyRecord(
        warranty_id="warr_002",
        customer_id="cust_002",
        product_id="prod_002",
        purchase_date=datetime.now() - timedelta(days=1000),
        warranty_start_date=datetime.now() - timedelta(days=1000),
        warranty_duration_months=12,
    )

    claim = ClaimRecord(
        claim_id="claim_002",
        warranty_id="warr_002",
        claim_date=datetime.now(),
        issue_description="Product defect",
    )

    config = ValidationConfig(require_active_warranty=True)

    status, notes = validate_coverage(claim, warranty, config)

    assert status == CoverageStatus.EXPIRED
    assert "expired" in notes.lower()


def test_validate_coverage_not_found():
    """Test coverage validation when warranty not found."""
    claim = ClaimRecord(
        claim_id="claim_003",
        warranty_id="warr_999",
        claim_date=datetime.now(),
        issue_description="Product defect",
    )

    config = ValidationConfig()

    status, notes = validate_coverage(claim, None, config)

    assert status == CoverageStatus.INVALID
    assert "not found" in notes.lower()


def test_validate_coverage_type():
    """Test coverage type validation."""
    warranty = WarrantyRecord(
        warranty_id="warr_003",
        customer_id="cust_003",
        product_id="prod_003",
        purchase_date=datetime.now() - timedelta(days=100),
        warranty_start_date=datetime.now() - timedelta(days=100),
        warranty_duration_months=24,
        coverage_type="manufacturing_defect",
    )

    claim = ClaimRecord(
        claim_id="claim_004",
        warranty_id="warr_003",
        claim_date=datetime.now(),
        issue_description="Accidental damage occurred",
    )

    config = ValidationConfig(
        require_active_warranty=True, validate_coverage_type=True
    )

    status, notes = validate_coverage(claim, warranty, config)

    assert status == CoverageStatus.NOT_COVERED
    assert "not covered" in notes.lower()


def test_assign_service_provider():
    """Test service provider assignment."""
    providers = {
        "prov_001": ServiceProvider(
            provider_id="prov_001",
            provider_name="Provider A",
            capacity=10,
            active_claims=5,
        ),
        "prov_002": ServiceProvider(
            provider_id="prov_002",
            provider_name="Provider B",
            capacity=10,
            active_claims=3,
        ),
    }

    claim = ClaimRecord(
        claim_id="claim_005",
        warranty_id="warr_001",
        claim_date=datetime.now(),
        issue_description="Product defect",
    )

    provider_id = assign_service_provider(claim, providers)

    assert provider_id == "prov_002"
    assert providers["prov_002"].active_claims == 4


def test_assign_service_provider_no_capacity():
    """Test provider assignment when all providers at capacity."""
    providers = {
        "prov_001": ServiceProvider(
            provider_id="prov_001",
            provider_name="Provider A",
            capacity=5,
            active_claims=5,
        ),
    }

    claim = ClaimRecord(
        claim_id="claim_006",
        warranty_id="warr_001",
        claim_date=datetime.now(),
        issue_description="Product defect",
    )

    provider_id = assign_service_provider(claim, providers)

    assert provider_id is None


def test_process_claims_workflow():
    """Test claim processing workflow."""
    warranty = WarrantyRecord(
        warranty_id="warr_001",
        customer_id="cust_001",
        product_id="prod_001",
        purchase_date=datetime.now() - timedelta(days=100),
        warranty_start_date=datetime.now() - timedelta(days=100),
        warranty_duration_months=24,
    )

    warranties = {"warr_001": warranty}

    providers = {
        "prov_001": ServiceProvider(
            provider_id="prov_001",
            provider_name="Provider A",
            capacity=10,
        ),
    }

    claim = ClaimRecord(
        claim_id="claim_001",
        warranty_id="warr_001",
        claim_date=datetime.now(),
        issue_description="Product defect",
        status=ClaimStatus.SUBMITTED,
        claim_amount=300.0,
    )

    config = ValidationConfig(
        require_active_warranty=True, auto_approve_threshold=500.0
    )

    processed = process_claims([claim], warranties, providers, config)

    assert len(processed) == 1
    assert processed[0].status == ClaimStatus.IN_PROGRESS
    assert processed[0].coverage_status == CoverageStatus.COVERED
    assert processed[0].service_provider == "prov_001"


def test_process_claims_denied():
    """Test claim denial workflow."""
    warranty = WarrantyRecord(
        warranty_id="warr_002",
        customer_id="cust_002",
        product_id="prod_002",
        purchase_date=datetime.now() - timedelta(days=1000),
        warranty_start_date=datetime.now() - timedelta(days=1000),
        warranty_duration_months=12,
    )

    warranties = {"warr_002": warranty}

    claim = ClaimRecord(
        claim_id="claim_002",
        warranty_id="warr_002",
        claim_date=datetime.now(),
        issue_description="Product defect",
        status=ClaimStatus.SUBMITTED,
    )

    config = ValidationConfig(require_active_warranty=True)

    processed = process_claims([claim], warranties, {}, config)

    assert len(processed) == 1
    assert processed[0].status == ClaimStatus.DENIED
    assert processed[0].coverage_status == CoverageStatus.EXPIRED
