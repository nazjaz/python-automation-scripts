"""Tests for shopping recommendation engine."""

from datetime import datetime, timedelta

import pytest

from shopping_recommendation_engine.src.main import (
    BrowsingRecord,
    InventoryItem,
    PurchaseRecord,
    RecommendationConfig,
    RecommendationPriority,
    SeasonalTrendsConfig,
    analyze_browsing_behavior,
    analyze_purchase_history,
    generate_recommendations,
    identify_seasonal_products,
)


def test_analyze_purchase_history():
    """Test purchase history analysis."""
    now = datetime.now()
    purchases = [
        PurchaseRecord(
            customer_id="cust_001",
            product_id="prod_001",
            purchase_date=now - timedelta(days=10),
            quantity=2,
        ),
        PurchaseRecord(
            customer_id="cust_001",
            product_id="prod_002",
            purchase_date=now - timedelta(days=100),
            quantity=1,
        ),
        PurchaseRecord(
            customer_id="cust_002",
            product_id="prod_001",
            purchase_date=now - timedelta(days=5),
            quantity=1,
        ),
    ]

    scores = analyze_purchase_history(purchases, "cust_001")

    assert "prod_001" in scores
    assert "prod_002" in scores
    assert scores["prod_001"] > scores["prod_002"]


def test_analyze_browsing_behavior():
    """Test browsing behavior analysis."""
    now = datetime.now()
    browsing_records = [
        BrowsingRecord(
            customer_id="cust_001",
            product_id="prod_001",
            timestamp=now - timedelta(days=5),
            action_type="view",
            view_duration=120.0,
        ),
        BrowsingRecord(
            customer_id="cust_001",
            product_id="prod_002",
            timestamp=now - timedelta(days=2),
            action_type="add_to_cart",
            view_duration=60.0,
        ),
        BrowsingRecord(
            customer_id="cust_002",
            product_id="prod_001",
            timestamp=now - timedelta(days=1),
            action_type="view",
        ),
    ]

    scores = analyze_browsing_behavior(browsing_records, "cust_001")

    assert "prod_001" in scores
    assert "prod_002" in scores
    assert scores["prod_002"] > scores["prod_001"]


def test_identify_seasonal_products():
    """Test seasonal product identification."""
    now = datetime.now()
    current_month = now.month

    purchases = []
    for month in range(1, 13):
        for day in range(1, 8):
            date = datetime(now.year, month, day)
            if month in [12, 1, 2]:
                purchases.append(
                    PurchaseRecord(
                        customer_id="cust_001",
                        product_id="winter_product",
                        purchase_date=date,
                        quantity=2,
                    )
                )
            else:
                purchases.append(
                    PurchaseRecord(
                        customer_id="cust_001",
                        product_id="winter_product",
                        purchase_date=date,
                        quantity=1,
                    )
                )

    seasonal_config = SeasonalTrendsConfig(
        enable_seasonal_boost=True,
        seasonal_categories={
            "winter": [12, 1, 2],
            "spring": [3, 4, 5],
            "summer": [6, 7, 8],
            "fall": [9, 10, 11],
        },
    )

    seasonal_products = identify_seasonal_products(purchases, seasonal_config)

    if current_month in [12, 1, 2]:
        assert "winter_product" in seasonal_products


def test_generate_recommendations():
    """Test recommendation generation."""
    purchase_scores = {"prod_001": 5.0, "prod_002": 3.0}
    browsing_scores = {"prod_003": 4.0, "prod_004": 2.0}
    seasonal_products = {"prod_005"}
    inventory = {
        "prod_001": InventoryItem(product_id="prod_001", quantity=10, in_stock=True),
        "prod_003": InventoryItem(product_id="prod_003", quantity=5, in_stock=True),
        "prod_005": InventoryItem(product_id="prod_005", quantity=0, in_stock=False),
    }

    purchases = [
        PurchaseRecord(
            customer_id="cust_001",
            product_id="prod_001",
            purchase_date=datetime.now(),
            category="electronics",
        )
    ]

    config = RecommendationConfig(
        max_recommendations=10,
        min_score_threshold=0.1,
        purchase_history_weight=0.4,
        browsing_weight=0.3,
        seasonal_weight=0.3,
        require_in_stock=True,
    )

    seasonal_config = SeasonalTrendsConfig()

    recommendations = generate_recommendations(
        "cust_001",
        purchase_scores,
        browsing_scores,
        seasonal_products,
        inventory,
        purchases,
        config,
        seasonal_config,
    )

    assert len(recommendations) > 0
    assert all(rec.in_stock for rec in recommendations)
    assert all(rec.score >= config.min_score_threshold for rec in recommendations)


def test_generate_recommendations_priority():
    """Test recommendation priority classification."""
    purchase_scores = {"prod_001": 10.0}
    browsing_scores = {}
    seasonal_products = set()
    inventory = {
        "prod_001": InventoryItem(product_id="prod_001", quantity=10, in_stock=True),
    }

    config = RecommendationConfig(
        max_recommendations=10,
        min_score_threshold=0.1,
    )

    seasonal_config = SeasonalTrendsConfig()

    recommendations = generate_recommendations(
        "cust_001",
        purchase_scores,
        browsing_scores,
        seasonal_products,
        inventory,
        [],
        config,
        seasonal_config,
    )

    assert len(recommendations) > 0
    high_priority = [r for r in recommendations if r.priority == RecommendationPriority.HIGH]
    assert len(high_priority) > 0


def test_inventory_filtering():
    """Test inventory-based filtering."""
    purchase_scores = {"prod_001": 5.0}
    browsing_scores = {}
    seasonal_products = set()
    inventory = {
        "prod_001": InventoryItem(product_id="prod_001", quantity=0, in_stock=False),
    }

    config = RecommendationConfig(
        max_recommendations=10,
        min_score_threshold=0.1,
        require_in_stock=True,
    )

    seasonal_config = SeasonalTrendsConfig()

    recommendations = generate_recommendations(
        "cust_001",
        purchase_scores,
        browsing_scores,
        seasonal_products,
        inventory,
        [],
        config,
        seasonal_config,
    )

    assert len(recommendations) == 0


def test_seasonal_boost():
    """Test seasonal boost application."""
    purchase_scores = {}
    browsing_scores = {"prod_001": 1.0}
    seasonal_products = {"prod_001"}
    inventory = {
        "prod_001": InventoryItem(product_id="prod_001", quantity=10, in_stock=True),
    }

    config = RecommendationConfig(
        max_recommendations=10,
        min_score_threshold=0.1,
        seasonal_weight=0.5,
    )

    seasonal_config = SeasonalTrendsConfig(seasonal_boost_multiplier=2.0)

    recommendations = generate_recommendations(
        "cust_001",
        purchase_scores,
        browsing_scores,
        seasonal_products,
        inventory,
        [],
        config,
        seasonal_config,
    )

    assert len(recommendations) > 0
    seasonal_rec = next((r for r in recommendations if r.product_id == "prod_001"), None)
    assert seasonal_rec is not None
    assert "Seasonal trend" in seasonal_rec.reasons
