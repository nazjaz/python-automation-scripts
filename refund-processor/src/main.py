"""Customer refund processing automation system.

Automatically processes customer refunds by validating requests,
checking policies, calculating refund amounts, and updating payment
systems with confirmation emails.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.email_service import EmailService
from src.payment_integrator import PaymentIntegrator, PaymentIntegrationError
from src.policy_checker import PolicyChecker, PolicyError
from src.refund_calculator import RefundCalculator
from src.refund_validator import RefundValidator, ValidationError


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/refund_processor.log"))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_file,
        maxBytes=log_config.get("max_bytes", 10485760),
        backupCount=log_config.get("backup_count", 5),
    )

    formatter = logging.Formatter(log_config.get("format"))
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def process_refund(
    order_id: str,
    customer_email: str,
    requested_amount: float,
    refund_reason: str,
    description: Optional[str] = None,
    config: Optional[dict] = None,
    settings: Optional[object] = None,
) -> dict:
    """Process a complete refund request.

    Args:
        order_id: Order identifier.
        customer_email: Customer email address.
        requested_amount: Requested refund amount.
        refund_reason: Reason for refund.
        description: Additional description (optional).
        config: Configuration dictionary.
        settings: Application settings.

    Returns:
        Dictionary with refund processing results.
    """
    logger = logging.getLogger(__name__)

    if config is None:
        from src.config import load_config

        config = load_config()

    if settings is None:
        from src.config import get_settings

        settings = get_settings()

    db_manager = DatabaseManager(config.get("database", {}).get("url", "sqlite:///refunds.db"))
    db_manager.create_tables()

    order = db_manager.get_order_by_id(order_id)
    if not order:
        return {
            "success": False,
            "error": f"Order {order_id} not found",
        }

    validation_config = config.get("validation", {})
    policy_config = config.get("refund_policies", {})
    email_config = config.get("email", {})
    payment_config = config.get("payment_systems", {}).get("primary", {})

    validator = RefundValidator(db_manager, validation_config)
    policy_checker = PolicyChecker(db_manager, policy_config)
    calculator = RefundCalculator(db_manager, policy_config)

    try:
        validator.validate_request(
            order_id, customer_email, requested_amount, refund_reason
        )
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")
        return {"success": False, "error": str(e)}

    try:
        is_partial = requested_amount < order.total_amount
        policy_result = policy_checker.check_policy(
            order_id, requested_amount, refund_reason, is_partial
        )
    except PolicyError as e:
        logger.error(f"Policy check failed: {e}")
        return {"success": False, "error": str(e), "requires_approval": True}

    if policy_result.get("requires_approval"):
        refund_request = db_manager.create_refund_request(
            order_id, customer_email, requested_amount, refund_reason, description
        )
        return {
            "success": False,
            "error": "Refund requires manual approval",
            "refund_request_id": refund_request.id,
            "approval_status": "requires_approval",
        }

    refund_calculation = calculator.calculate_refund(
        order_id, requested_amount, refund_reason
    )

    refund_request = db_manager.create_refund_request(
        order_id, customer_email, requested_amount, refund_reason, description
    )

    payment_integrator = PaymentIntegrator(
        provider=payment_config.get("provider", "stripe"),
        api_key=settings.stripe_api_key,
        api_secret=settings.stripe_secret_key,
    )

    try:
        payment_result = payment_integrator.process_refund(
            transaction_id=order.payment_transaction_id,
            amount=refund_calculation["net_refund_amount"],
            currency=refund_calculation["currency"],
            reason=refund_reason,
        )

        refund = db_manager.create_refund(
            refund_request_id=refund_request.id,
            order_id=order_id,
            customer_email=customer_email,
            refund_amount=refund_calculation["refund_amount"],
            restocking_fee=refund_calculation["restocking_fee"],
            net_refund_amount=refund_calculation["net_refund_amount"],
            currency=refund_calculation["currency"],
            refund_reason=refund_reason,
            payment_provider=order.payment_provider,
            payment_refund_id=payment_result.get("refund_id"),
        )

        db_manager.update_refund_status(
            refund.id, "completed", payment_result.get("refund_id")
        )

        email_service = EmailService(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_username=settings.smtp_username,
            smtp_password=settings.smtp_password,
            from_email=email_config.get("from_email", settings.smtp_from_email),
            from_name=email_config.get("from_name", "Refund Processing Team"),
            retry_attempts=email_config.get("retry_attempts", 3),
            retry_delay_seconds=email_config.get("retry_delay_seconds", 5),
        )

        email_sent = email_service.send_refund_confirmation(
            to_email=customer_email,
            customer_name=order.customer_name,
            order_id=order_id,
            refund_amount=refund_calculation["refund_amount"],
            net_refund_amount=refund_calculation["net_refund_amount"],
            restocking_fee=refund_calculation["restocking_fee"],
            currency=refund_calculation["currency"],
            refund_reason=refund_reason,
            template_path=email_config.get("confirmation_template"),
            subject_template=email_config.get("subject"),
        )

        if email_sent:
            refund.confirmation_sent = True
            with db_manager.get_session() as session:
                session.add(refund)
                session.commit()

        logger.info(
            f"Refund processed successfully for order {order_id}: "
            f"${refund_calculation['net_refund_amount']:.2f}"
        )

        return {
            "success": True,
            "refund_id": refund.id,
            "order_id": order_id,
            "refund_amount": refund_calculation["refund_amount"],
            "restocking_fee": refund_calculation["restocking_fee"],
            "net_refund_amount": refund_calculation["net_refund_amount"],
            "currency": refund_calculation["currency"],
            "payment_refund_id": payment_result.get("refund_id"),
            "email_sent": email_sent,
        }

    except PaymentIntegrationError as e:
        logger.error(f"Payment processing failed: {e}")
        return {
            "success": False,
            "error": f"Payment processing failed: {str(e)}",
            "refund_request_id": refund_request.id,
        }


def main() -> None:
    """Main entry point for refund processing automation."""
    parser = argparse.ArgumentParser(description="Customer refund processing system")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument("--order-id", required=True, help="Order identifier")
    parser.add_argument("--email", required=True, help="Customer email address")
    parser.add_argument("--amount", type=float, required=True, help="Refund amount")
    parser.add_argument("--reason", required=True, help="Refund reason")
    parser.add_argument("--description", help="Additional description (optional)")

    args = parser.parse_args()

    try:
        config = load_config(args.config) if args.config else load_config()
        settings = get_settings()
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    setup_logging(config.get("logging", {}))

    result = process_refund(
        order_id=args.order_id,
        customer_email=args.email,
        requested_amount=args.amount,
        refund_reason=args.reason,
        description=args.description,
        config=config,
        settings=settings,
    )

    if result["success"]:
        print(f"\nRefund processed successfully!")
        print(f"Refund ID: {result['refund_id']}")
        print(f"Order ID: {result['order_id']}")
        print(f"Net Refund Amount: {result['currency']}{result['net_refund_amount']:.2f}")
        if result.get("restocking_fee", 0) > 0:
            print(f"Restocking Fee: {result['currency']}{result['restocking_fee']:.2f}")
        print(f"Payment Refund ID: {result.get('payment_refund_id', 'N/A')}")
        print(f"Confirmation Email: {'Sent' if result.get('email_sent') else 'Failed'}")
    else:
        print(f"\nRefund processing failed: {result.get('error', 'Unknown error')}")
        if result.get("requires_approval"):
            print("This refund requires manual approval.")
        sys.exit(1)


if __name__ == "__main__":
    main()
