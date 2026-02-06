"""Gift recommendation automation system.

Automatically generates personalized gift recommendations by analyzing
recipient preferences, purchase history, and special occasions with price range filtering.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.recommendation_engine import RecommendationEngine
from src.report_generator import ReportGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/gift_recommender.log"))
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


def add_recipient(
    config: dict,
    settings: object,
    name: str,
    email: Optional[str] = None,
    age: Optional[int] = None,
    relationship: Optional[str] = None,
) -> dict:
    """Add recipient to system.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        name: Recipient name.
        email: Optional email address.
        age: Optional age.
        relationship: Optional relationship type.

    Returns:
        Dictionary with recipient information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    recipient = db_manager.add_recipient(
        name=name, email=email, age=age, relationship=relationship
    )

    logger.info(
        f"Added recipient: {recipient.name}",
        extra={"recipient_id": recipient.id, "name": name},
    )

    return {
        "success": True,
        "recipient_id": recipient.id,
        "name": recipient.name,
        "email": recipient.email,
    }


def add_preference(
    config: dict,
    settings: object,
    recipient_id: int,
    category: str,
    interest: Optional[str] = None,
    priority: int = 1,
) -> dict:
    """Add preference for recipient.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        recipient_id: Recipient ID.
        category: Preference category.
        interest: Optional interest description.
        priority: Priority level (1-10).

    Returns:
        Dictionary with preference information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    preference = db_manager.add_preference(
        recipient_id=recipient_id,
        category=category,
        interest=interest,
        priority=priority,
    )

    logger.info(
        f"Added preference for recipient {recipient_id}",
        extra={
            "recipient_id": recipient_id,
            "category": category,
            "preference_id": preference.id,
        },
    )

    return {
        "success": True,
        "preference_id": preference.id,
        "category": category,
    }


def generate_recommendations(
    config: dict,
    settings: object,
    recipient_id: int,
    occasion: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    price_range: Optional[str] = None,
    categories: Optional[list] = None,
    max_recommendations: Optional[int] = None,
    generate_report: bool = True,
) -> dict:
    """Generate gift recommendations for recipient.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        recipient_id: Recipient ID.
        occasion: Optional occasion type.
        min_price: Optional minimum price.
        max_price: Optional maximum price.
        price_range: Optional price range category.
        categories: Optional list of category filters.
        max_recommendations: Optional maximum number of recommendations.
        generate_report: Whether to generate report files.

    Returns:
        Dictionary with recommendations and report paths.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    recommendation_engine = RecommendationEngine(db_manager, config)

    logger.info(
        "Generating gift recommendations",
        extra={
            "recipient_id": recipient_id,
            "occasion": occasion,
            "price_range": price_range,
        },
    )

    recommendations = recommendation_engine.generate_recommendations(
        recipient_id=recipient_id,
        occasion=occasion,
        min_price=min_price,
        max_price=max_price,
        price_range=price_range,
        categories=categories,
        max_recommendations=max_recommendations,
    )

    reports = {}
    if generate_report and recommendations:
        report_generator = ReportGenerator(
            db_manager, recommendation_engine, output_dir="reports"
        )

        reports["html"] = str(
            report_generator.generate_html_report(
                recipient_id, recommendations, occasion=occasion
            )
        )
        reports["csv"] = str(
            report_generator.generate_csv_report(
                recipient_id, recommendations, occasion=occasion
            )
        )

    logger.info(
        f"Generated {len(recommendations)} recommendations",
        extra={
            "recipient_id": recipient_id,
            "recommendation_count": len(recommendations),
        },
    )

    return {
        "success": True,
        "recipient_id": recipient_id,
        "recommendation_count": len(recommendations),
        "recommendations": [
            {
                "item_id": rec["item"].id,
                "name": rec["item"].name,
                "category": rec["item"].category,
                "price": rec["item"].price,
                "score": rec["score"],
            }
            for rec in recommendations
        ],
        "reports": reports,
    }


def main() -> None:
    """Main entry point for gift recommendation automation."""
    parser = argparse.ArgumentParser(
        description="Gift recommendation automation system"
    )
    parser.add_argument(
        "--add-recipient",
        action="store_true",
        help="Add a new recipient",
    )
    parser.add_argument(
        "--name", required=False, help="Recipient name"
    )
    parser.add_argument(
        "--email", help="Recipient email address"
    )
    parser.add_argument(
        "--age", type=int, help="Recipient age"
    )
    parser.add_argument(
        "--relationship", help="Relationship type"
    )
    parser.add_argument(
        "--add-preference",
        action="store_true",
        help="Add preference for recipient",
    )
    parser.add_argument(
        "--recipient-id", type=int, help="Recipient ID"
    )
    parser.add_argument(
        "--category", help="Preference category"
    )
    parser.add_argument(
        "--interest", help="Interest description"
    )
    parser.add_argument(
        "--priority", type=int, default=1, help="Priority level (1-10)"
    )
    parser.add_argument(
        "--recommend",
        action="store_true",
        help="Generate gift recommendations",
    )
    parser.add_argument(
        "--occasion",
        help="Occasion type (birthday, anniversary, wedding, etc.)",
    )
    parser.add_argument(
        "--min-price", type=float, help="Minimum price filter"
    )
    parser.add_argument(
        "--max-price", type=float, help="Maximum price filter"
    )
    parser.add_argument(
        "--price-range",
        help="Price range category (budget, low, medium, high, premium)",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        help="Category filters",
    )
    parser.add_argument(
        "--max-recommendations",
        type=int,
        help="Maximum number of recommendations",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([args.add_recipient, args.add_preference, args.recommend]):
        parser.print_help()
        sys.exit(1)

    try:
        config = load_config(args.config) if args.config else load_config()
        settings = get_settings()
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    setup_logging(config.get("logging", {}))

    logger = logging.getLogger(__name__)

    try:
        if args.add_recipient:
            if not args.name:
                print("Error: --name is required for --add-recipient", file=sys.stderr)
                sys.exit(1)

            result = add_recipient(
                config=config,
                settings=settings,
                name=args.name,
                email=args.email,
                age=args.age,
                relationship=args.relationship,
            )
            print(f"\nRecipient added successfully:")
            print(f"ID: {result['recipient_id']}")
            print(f"Name: {result['name']}")
            if result.get("email"):
                print(f"Email: {result['email']}")

        elif args.add_preference:
            if not args.recipient_id or not args.category:
                print(
                    "Error: --recipient-id and --category are required for --add-preference",
                    file=sys.stderr,
                )
                sys.exit(1)

            result = add_preference(
                config=config,
                settings=settings,
                recipient_id=args.recipient_id,
                category=args.category,
                interest=args.interest,
                priority=args.priority,
            )
            print(f"\nPreference added successfully:")
            print(f"Category: {result['category']}")

        elif args.recommend:
            if not args.recipient_id:
                print(
                    "Error: --recipient-id is required for --recommend",
                    file=sys.stderr,
                )
                sys.exit(1)

            result = generate_recommendations(
                config=config,
                settings=settings,
                recipient_id=args.recipient_id,
                occasion=args.occasion,
                min_price=args.min_price,
                max_price=args.max_price,
                price_range=args.price_range,
                categories=args.categories,
                max_recommendations=args.max_recommendations,
            )

            print(f"\nGenerated {result['recommendation_count']} recommendations:")
            for i, rec in enumerate(result["recommendations"][:5], 1):
                print(
                    f"{i}. {rec['name']} ({rec['category']}) - "
                    f"${rec['price']:.2f} (Score: {rec['score']:.2%})"
                )

            if result.get("reports"):
                print(f"\nReports generated:")
                for report_type, path in result["reports"].items():
                    print(f"  {report_type.upper()}: {path}")

    except Exception as e:
        logger.error(f"Error executing command: {e}", extra={"error": str(e)})
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
