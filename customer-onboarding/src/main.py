"""Customer onboarding automation system.

Automates the customer onboarding process by sending welcome emails,
setting up accounts, assigning resources, and tracking progress with metrics.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.account_manager import AccountManager
from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.email_service import EmailService
from src.onboarding_tracker import OnboardingTracker
from src.resource_manager import ResourceManager


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/onboarding.log"))
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


def process_onboarding(
    email: str,
    name: str,
    company_name: Optional[str] = None,
    config: Optional[dict] = None,
    settings: Optional[object] = None,
) -> dict:
    """Process complete onboarding workflow for a customer.

    Args:
        email: Customer email address.
        name: Customer full name.
        company_name: Optional company name.
        config: Configuration dictionary.
        settings: Application settings object.

    Returns:
        Dictionary with onboarding results and metrics.
    """
    logger = logging.getLogger(__name__)

    if config is None:
        config = load_config()

    if settings is None:
        settings = get_settings()

    db_manager = DatabaseManager(settings.database_url)
    db_manager.create_tables()

    email_config = config.get("email", {})
    onboarding_config = config.get("onboarding", {})
    resources_config = config.get("resources", {})

    email_service = EmailService(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        from_email=settings.smtp_from_email,
        from_name=settings.smtp_from_name,
        retry_attempts=email_config.get("retry_attempts", 3),
        retry_delay_seconds=email_config.get("retry_delay_seconds", 5),
    )

    account_manager = AccountManager(db_manager)
    resource_manager = ResourceManager(
        db_manager,
        api_url=settings.resource_api_url,
        api_key=settings.resource_api_key,
        timeout=resources_config.get("assignment_api_timeout", 30),
    )

    tracker = OnboardingTracker(db_manager)

    try:
        customer = db_manager.create_customer(email, name, company_name)
        logger.info(
            f"Created customer record: {customer.id}",
            extra={"customer_id": customer.id, "email": email},
        )
    except ValueError as e:
        logger.error(f"Failed to create customer: {e}", extra={"email": email})
        return {"success": False, "error": str(e)}

    results = {
        "customer_id": customer.id,
        "email": email,
        "steps_completed": [],
        "errors": [],
    }

    onboarding_steps = onboarding_config.get("steps", [])
    tracker.initialize_steps(customer.id, onboarding_steps)

    for step in sorted(onboarding_steps, key=lambda x: x["order"]):
        step_name = step["name"]
        try:
            if step_name == "welcome_email":
                success = email_service.send_welcome_email(
                    to_email=email,
                    customer_name=name,
                    company_name=company_name,
                    template_path=email_config.get("welcome_template"),
                    subject_template=email_config.get("subject"),
                )
                if success:
                    tracker.complete_step(customer.id, step_name)
                    results["steps_completed"].append(step_name)
                else:
                    results["errors"].append(f"Failed to send welcome email")

            elif step_name == "account_setup":
                account_id = account_manager.setup_account(customer.id)
                tracker.complete_step(customer.id, step_name)
                results["steps_completed"].append(step_name)
                results["account_id"] = account_id

            elif step_name == "resource_assignment":
                default_resources = resources_config.get("default_assignments", [])
                assignment_results = resource_manager.assign_resources(
                    customer.id, default_resources
                )
                tracker.complete_step(customer.id, step_name)
                results["steps_completed"].append(step_name)
                results["resource_assignments"] = assignment_results

            else:
                logger.warning(
                    f"Unknown onboarding step: {step_name}",
                    extra={"step_name": step_name, "customer_id": customer.id},
                )

        except Exception as e:
            logger.error(
                f"Error processing step {step_name}: {e}",
                extra={"step_name": step_name, "customer_id": customer.id, "error": str(e)},
            )
            results["errors"].append(f"Error in {step_name}: {str(e)}")

    metrics = tracker.get_completion_metrics(customer.id)
    results["completion_metrics"] = metrics
    results["success"] = len(results["errors"]) == 0

    logger.info(
        f"Onboarding completed for customer {customer.id}",
        extra={
            "customer_id": customer.id,
            "completion": metrics.get("completion_percentage", 0.0),
            "steps_completed": len(results["steps_completed"]),
        },
    )

    return results


def main() -> None:
    """Main entry point for customer onboarding automation."""
    parser = argparse.ArgumentParser(
        description="Customer onboarding automation system"
    )
    parser.add_argument(
        "--email", required=True, help="Customer email address"
    )
    parser.add_argument("--name", required=True, help="Customer full name")
    parser.add_argument("--company", help="Company name (optional)")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Display completion metrics for all customers",
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config) if args.config else load_config()
        settings = get_settings()
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    setup_logging(config.get("logging", {}))

    if args.metrics:
        db_manager = DatabaseManager(settings.database_url)
        tracker = OnboardingTracker(db_manager)
        metrics = tracker.get_all_metrics(
            completion_threshold=config.get("onboarding", {}).get(
                "completion_threshold", 0.75
            )
        )
        print("\nOnboarding Metrics:")
        print(f"Total Customers: {metrics['total_customers']}")
        print(f"Completed: {metrics['completed_customers']}")
        print(f"In Progress: {metrics['in_progress_customers']}")
        print(f"Average Completion: {metrics['average_completion_percentage']:.2%}")
    else:
        results = process_onboarding(
            email=args.email, name=args.name, company_name=args.company, config=config, settings=settings
        )

        if results["success"]:
            print(f"\nOnboarding completed successfully for {args.email}")
            print(f"Customer ID: {results['customer_id']}")
            if "account_id" in results:
                print(f"Account ID: {results['account_id']}")
            print(f"Steps Completed: {', '.join(results['steps_completed'])}")
            print(
                f"Completion: {results['completion_metrics']['completion_percentage']:.2%}"
            )
        else:
            print(f"\nOnboarding completed with errors for {args.email}")
            print(f"Errors: {', '.join(results['errors'])}")
            sys.exit(1)


if __name__ == "__main__":
    main()
