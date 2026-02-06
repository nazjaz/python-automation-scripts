"""Customer review processing automation system.

Processes customer reviews by extracting key themes, calculating sentiment scores,
identifying product issues, and generating improvement recommendations.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.issue_identifier import IssueIdentifier
from src.recommendation_generator import RecommendationGenerator
from src.report_generator import ReportGenerator
from src.sentiment_analyzer import SentimentAnalyzer
from src.theme_extractor import ThemeExtractor


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/review_processor.log"))
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


def process_reviews(
    config: dict,
    settings: object,
    limit: Optional[int] = None,
    product_id: Optional[str] = None,
) -> dict:
    """Process customer reviews.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        limit: Maximum number of reviews to process.
        product_id: Optional product ID to filter by.

    Returns:
        Dictionary with processing results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    sentiment_analyzer = SentimentAnalyzer(config.get("sentiment", {}))
    theme_extractor = ThemeExtractor(config.get("themes", {}))
    issue_identifier = IssueIdentifier(config.get("issues", {}))
    recommendation_generator = RecommendationGenerator(
        config.get("recommendations", {})
    )

    reviews = db_manager.get_unprocessed_reviews(limit=limit)
    if product_id:
        reviews = [r for r in reviews if r.product_id == product_id]

    if not reviews:
        logger.warning("No unprocessed reviews found")
        return {"success": True, "processed_count": 0}

    logger.info(f"Processing {len(reviews)} reviews")

    processed_count = 0
    total_issues = 0
    total_recommendations = 0

    for review in reviews:
        try:
            sentiment_score, sentiment_label = sentiment_analyzer.analyze_sentiment(
                review.review_text, review.rating
            )

            db_manager.update_review_sentiment(
                review.id, sentiment_score, sentiment_label
            )

            themes = theme_extractor.extract_themes(review.review_text)
            for theme in themes:
                db_manager.add_theme(
                    review.id,
                    theme["theme_text"],
                    theme["relevance_score"],
                    theme["category"],
                )

            issues = issue_identifier.identify_issues(
                review.review_text, sentiment_score, sentiment_label
            )
            for issue in issues:
                db_manager.add_issue(
                    review.id,
                    issue["issue_text"],
                    issue["severity"],
                    issue["category"],
                )
                total_issues += 1

            processed_count += 1

        except Exception as e:
            logger.error(f"Error processing review {review.id}: {e}")

    all_issues = db_manager.get_all_issues()
    aggregated_issues = issue_identifier.aggregate_issues(
        [
            {
                "issue_text": issue.issue_text,
                "severity": issue.severity,
                "category": issue.category,
            }
            for issue in all_issues
        ]
    )

    recommendations = recommendation_generator.generate_recommendations(
        [
            {
                "issue_text": issue.issue_text,
                "severity": issue.severity,
                "category": issue.category,
            }
            for issue in all_issues
        ],
        aggregated_issues,
    )

    for recommendation in recommendations:
        db_manager.add_recommendation(
            recommendation["recommendation_text"],
            recommendation["priority"],
            recommendation["category"],
            recommendation["impact_score"],
        )
        total_recommendations += 1

    logger.info(
        f"Review processing completed: {processed_count} reviews processed, "
        f"{total_issues} issues identified, {total_recommendations} recommendations generated"
    )

    return {
        "success": True,
        "processed_count": processed_count,
        "issues_identified": total_issues,
        "recommendations_generated": total_recommendations,
    }


def generate_reports(config: dict, settings: object, product_id: Optional[str] = None) -> dict:
    """Generate analysis reports.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        product_id: Optional product ID to filter by.

    Returns:
        Dictionary with report generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    report_generator = ReportGenerator(db_manager, config.get("reporting", {}))

    logger.info("Generating review analysis reports", extra={"product_id": product_id})

    reports = report_generator.generate_reports(product_id=product_id)

    logger.info(
        f"Reports generated: {len(reports)} report(s) created",
        extra={"report_count": len(reports), "product_id": product_id},
    )

    return {
        "success": True,
        "reports": {k: str(v) for k, v in reports.items()},
        "product_id": product_id,
    }


def add_reviews_from_file(
    config: dict,
    settings: object,
    file_path: Path,
    source: str = "file",
) -> dict:
    """Add reviews from a text file.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        file_path: Path to file containing reviews.
        source: Review source identifier.

    Returns:
        Dictionary with import results.
    """
    logger = logging.getLogger(__name__)

    if not file_path.exists():
        raise FileNotFoundError(f"Review file not found: {file_path}")

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    logger.info(f"Importing reviews from file: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    imported_count = 0
    for line in lines:
        line = line.strip()
        if line and len(line) > 10:
            try:
                db_manager.add_review(review_text=line, source=source)
                imported_count += 1
            except Exception as e:
                logger.error(f"Error importing review: {e}")

    logger.info(f"Imported {imported_count} reviews from file")

    return {
        "success": True,
        "imported_count": imported_count,
        "file_path": str(file_path),
    }


def main() -> None:
    """Main entry point for customer review processing automation."""
    parser = argparse.ArgumentParser(
        description="Customer review processing automation system"
    )
    parser.add_argument(
        "--process",
        action="store_true",
        help="Process customer reviews",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate analysis reports",
    )
    parser.add_argument(
        "--import",
        type=Path,
        metavar="FILE",
        help="Import reviews from text file",
    )
    parser.add_argument(
        "--product-id",
        help="Filter by specific product ID",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of reviews to process",
    )
    parser.add_argument(
        "--source",
        default="file",
        help="Review source identifier (default: file)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([args.process, args.report, args.import]):
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
        if args.import:
            result = add_reviews_from_file(
                config=config,
                settings=settings,
                file_path=args.import,
                source=args.source,
            )
            print(f"\nReview import completed:")
            print(f"Imported reviews: {result['imported_count']}")
            print(f"File: {result['file_path']}")

        if args.process:
            result = process_reviews(
                config=config,
                settings=settings,
                limit=args.limit,
                product_id=args.product_id,
            )
            print(f"\nReview processing completed:")
            print(f"Processed reviews: {result['processed_count']}")
            print(f"Issues identified: {result['issues_identified']}")
            print(f"Recommendations generated: {result['recommendations_generated']}")

        if args.report:
            result = generate_reports(
                config=config,
                settings=settings,
                product_id=args.product_id,
            )
            print(f"\nReports generated:")
            for report_type, path in result["reports"].items():
                print(f"  {report_type.upper()}: {path}")
            if args.product_id:
                print(f"Product ID: {args.product_id}")

    except Exception as e:
        logger.error(f"Error executing command: {e}", extra={"error": str(e)})
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
