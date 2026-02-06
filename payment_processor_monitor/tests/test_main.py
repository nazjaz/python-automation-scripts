"""Tests for payment processor monitoring."""

from datetime import datetime, timedelta

import pytest

from payment_processor_monitor.src.main import (
    FailedPayment,
    FailureReason,
    PaymentAnalytics,
    PaymentRecord,
    PaymentStatus,
    RetryConfig,
    calculate_analytics,
    identify_failed_payments,
)


def test_identify_failed_payments():
    """Test failed payment identification."""
    now = datetime.now()
    payments = [
        PaymentRecord(
            payment_id="pay_001",
            customer_id="cust_001",
            amount=100.0,
            status=PaymentStatus.SUCCESS,
            timestamp=now - timedelta(days=1),
        ),
        PaymentRecord(
            payment_id="pay_002",
            customer_id="cust_002",
            amount=50.0,
            status=PaymentStatus.FAILED,
            timestamp=now - timedelta(days=5),
            failure_reason=FailureReason.INSUFFICIENT_FUNDS,
            retry_count=0,
        ),
        PaymentRecord(
            payment_id="pay_003",
            customer_id="cust_003",
            amount=200.0,
            status=PaymentStatus.FAILED,
            timestamp=now - timedelta(days=1),
            failure_reason=FailureReason.EXPIRED_CARD,
            retry_count=2,
        ),
    ]

    retry_config = RetryConfig(max_retries=3, retry_delay_days=3)

    failed = identify_failed_payments(payments, retry_config)

    assert len(failed) == 2
    assert failed[0].payment_id == "pay_002"
    assert failed[0].requires_reminder is True
    assert failed[1].payment_id == "pay_003"
    assert failed[1].requires_reminder is False


def test_calculate_analytics_basic():
    """Test basic analytics calculation."""
    now = datetime.now()
    payments = [
        PaymentRecord(
            payment_id="pay_001",
            customer_id="cust_001",
            amount=100.0,
            status=PaymentStatus.SUCCESS,
            timestamp=now,
        ),
        PaymentRecord(
            payment_id="pay_002",
            customer_id="cust_002",
            amount=50.0,
            status=PaymentStatus.SUCCESS,
            timestamp=now - timedelta(days=1),
        ),
        PaymentRecord(
            payment_id="pay_003",
            customer_id="cust_003",
            amount=75.0,
            status=PaymentStatus.FAILED,
            timestamp=now - timedelta(days=2),
            failure_reason=FailureReason.INSUFFICIENT_FUNDS,
        ),
    ]

    from payment_processor_monitor.src.main import ForecastingConfig

    forecasting_config = ForecastingConfig(forecast_days=7, lookback_days=30)

    analytics = calculate_analytics(payments, forecasting_config)

    assert analytics.total_payments == 3
    assert analytics.successful_payments == 2
    assert analytics.failed_payments == 1
    assert analytics.success_rate == pytest.approx(0.6667, abs=0.01)
    assert analytics.total_revenue == 150.0
    assert analytics.failed_revenue == 75.0
    assert analytics.avg_payment_amount == pytest.approx(75.0, abs=0.01)
    assert FailureReason.INSUFFICIENT_FUNDS.value in analytics.failure_reasons


def test_calculate_analytics_empty():
    """Test analytics calculation with empty data."""
    from payment_processor_monitor.src.main import ForecastingConfig

    forecasting_config = ForecastingConfig()

    analytics = calculate_analytics([], forecasting_config)

    assert analytics.total_payments == 0
    assert analytics.successful_payments == 0
    assert analytics.success_rate == 0.0
    assert analytics.total_revenue == 0.0


def test_calculate_analytics_forecast():
    """Test revenue forecasting."""
    now = datetime.now()
    payments = []
    for i in range(14):
        payments.append(
            PaymentRecord(
                payment_id=f"pay_{i:03d}",
                customer_id=f"cust_{i:03d}",
                amount=100.0 + (i * 10),
                status=PaymentStatus.SUCCESS,
                timestamp=now - timedelta(days=14 - i),
            )
        )

    from payment_processor_monitor.src.main import ForecastingConfig

    forecasting_config = ForecastingConfig(
        forecast_days=7, lookback_days=30, method="moving_average"
    )

    analytics = calculate_analytics(payments, forecasting_config)

    assert len(analytics.revenue_forecast) == 7
    assert all("date" in f for f in analytics.revenue_forecast)
    assert all("forecasted_revenue" in f for f in analytics.revenue_forecast)


def test_failed_payment_requires_reminder():
    """Test reminder requirement logic."""
    now = datetime.now()
    retry_config = RetryConfig(max_retries=3, retry_delay_days=3)

    payment_old = PaymentRecord(
        payment_id="pay_001",
        customer_id="cust_001",
        amount=100.0,
        status=PaymentStatus.FAILED,
        timestamp=now - timedelta(days=5),
        retry_count=0,
    )

    payment_recent = PaymentRecord(
        payment_id="pay_002",
        customer_id="cust_002",
        amount=50.0,
        status=PaymentStatus.FAILED,
        timestamp=now - timedelta(days=1),
        retry_count=0,
    )

    payment_max_retries = PaymentRecord(
        payment_id="pay_003",
        customer_id="cust_003",
        amount=75.0,
        status=PaymentStatus.FAILED,
        timestamp=now - timedelta(days=5),
        retry_count=3,
    )

    failed = identify_failed_payments(
        [payment_old, payment_recent, payment_max_retries], retry_config
    )

    assert len(failed) == 3
    assert failed[0].requires_reminder is True
    assert failed[1].requires_reminder is False
    assert failed[2].requires_reminder is False
