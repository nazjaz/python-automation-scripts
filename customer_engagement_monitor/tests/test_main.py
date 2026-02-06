"""Tests for customer engagement monitoring."""

from datetime import datetime, timedelta

import pytest

from customer_engagement_monitor.src.main import (
    EngagementRecord,
    LTVConfig,
    PurchaseRecord,
    SegmentationConfig,
    SegmentTier,
    TouchpointType,
    calculate_engagement_score,
    calculate_ltv,
    assign_segment,
    generate_segment_strategies,
)


def test_calculate_ltv():
    """Test LTV calculation."""
    now = datetime.now()
    purchases = [
        PurchaseRecord(
            customer_id="cust_001",
            purchase_date=now - timedelta(days=30),
            amount=100.0,
        ),
        PurchaseRecord(
            customer_id="cust_001",
            purchase_date=now - timedelta(days=60),
            amount=150.0,
        ),
        PurchaseRecord(
            customer_id="cust_001",
            purchase_date=now - timedelta(days=90),
            amount=200.0,
        ),
    ]

    config = LTVConfig(
        discount_rate=0.1,
        average_customer_lifespan_years=3.0,
        lookback_months=12,
    )

    ltv, total_revenue, purchase_count = calculate_ltv(
        purchases, "cust_001", config
    )

    assert total_revenue == 450.0
    assert purchase_count == 3
    assert ltv > 0


def test_calculate_ltv_no_purchases():
    """Test LTV calculation with no purchases."""
    config = LTVConfig()

    ltv, total_revenue, purchase_count = calculate_ltv([], "cust_001", config)

    assert ltv == 0.0
    assert total_revenue == 0.0
    assert purchase_count == 0


def test_calculate_engagement_score():
    """Test engagement score calculation."""
    now = datetime.now()
    engagements = [
        EngagementRecord(
            customer_id="cust_001",
            touchpoint=TouchpointType.PURCHASE,
            timestamp=now - timedelta(days=5),
        ),
        EngagementRecord(
            customer_id="cust_001",
            touchpoint=TouchpointType.EMAIL,
            timestamp=now - timedelta(days=2),
        ),
        EngagementRecord(
            customer_id="cust_001",
            touchpoint=TouchpointType.WEB,
            timestamp=now - timedelta(days=1),
        ),
    ]

    score, touchpoint_counts, last_engagement = calculate_engagement_score(
        engagements, "cust_001"
    )

    assert score > 0
    assert score <= 1.0
    assert TouchpointType.PURCHASE in touchpoint_counts
    assert last_engagement is not None


def test_calculate_engagement_score_with_scores():
    """Test engagement score calculation with explicit scores."""
    now = datetime.now()
    engagements = [
        EngagementRecord(
            customer_id="cust_001",
            touchpoint=TouchpointType.EMAIL,
            timestamp=now,
            engagement_score=0.8,
        ),
        EngagementRecord(
            customer_id="cust_001",
            touchpoint=TouchpointType.WEB,
            timestamp=now,
            engagement_score=0.6,
        ),
    ]

    score, _, _ = calculate_engagement_score(engagements, "cust_001")

    assert score > 0
    assert score <= 1.0


def test_assign_segment_champion():
    """Test segment assignment for champion customers."""
    from customer_engagement_monitor.src.main import CustomerMetrics

    config = SegmentationConfig(
        ltv_threshold_high=1000.0,
        engagement_threshold_high=0.7,
    )

    metrics = CustomerMetrics(
        customer_id="cust_001",
        lifetime_value=1500.0,
        total_revenue=5000.0,
        purchase_count=10,
        engagement_score=0.8,
        touchpoint_count={},
    )

    segment = assign_segment(metrics, config)

    assert segment == SegmentTier.CHAMPION


def test_assign_segment_at_risk():
    """Test segment assignment for at-risk customers."""
    from customer_engagement_monitor.src.main import CustomerMetrics

    config = SegmentationConfig(
        ltv_threshold_medium=500.0,
        recency_threshold_days=90,
    )

    metrics = CustomerMetrics(
        customer_id="cust_001",
        lifetime_value=300.0,
        total_revenue=1000.0,
        purchase_count=5,
        engagement_score=0.4,
        touchpoint_count={},
        days_since_last_engagement=60,
    )

    segment = assign_segment(metrics, config)

    assert segment == SegmentTier.AT_RISK


def test_assign_segment_lost():
    """Test segment assignment for lost customers."""
    from customer_engagement_monitor.src.main import CustomerMetrics

    config = SegmentationConfig(
        ltv_threshold_medium=500.0,
        recency_threshold_days=90,
    )

    metrics = CustomerMetrics(
        customer_id="cust_001",
        lifetime_value=200.0,
        total_revenue=500.0,
        purchase_count=2,
        engagement_score=0.2,
        touchpoint_count={},
        days_since_last_engagement=120,
    )

    segment = assign_segment(metrics, config)

    assert segment == SegmentTier.LOST


def test_generate_segment_strategies():
    """Test strategy generation for segments."""
    from customer_engagement_monitor.src.main import SegmentAnalysis

    segment_analysis = SegmentAnalysis(
        segment=SegmentTier.CHAMPION,
        customer_count=100,
        avg_ltv=1500.0,
        avg_engagement_score=0.8,
        total_revenue=150000.0,
        recommendations=[],
    )

    strategies = generate_segment_strategies(
        SegmentTier.CHAMPION, segment_analysis
    )

    assert len(strategies) > 0
    assert all(isinstance(s, str) for s in strategies)


def test_engagement_score_normalization():
    """Test that engagement scores are normalized."""
    now = datetime.now()
    many_engagements = [
        EngagementRecord(
            customer_id="cust_001",
            touchpoint=TouchpointType.PURCHASE,
            timestamp=now - timedelta(days=i),
        )
        for i in range(20)
    ]

    score, _, _ = calculate_engagement_score(many_engagements, "cust_001")

    assert score <= 1.0
    assert score > 0
