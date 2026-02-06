"""Newsletter generator automation system.

Automatically generates personalized newsletter content by curating articles,
formatting layouts, personalizing sections, and scheduling distribution to subscriber segments.
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from src.article_curator import ArticleCurator
from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.distribution_scheduler import DistributionScheduler
from src.layout_formatter import LayoutFormatter
from src.personalization_engine import PersonalizationEngine


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/newsletter_generator.log"))
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


def add_subscriber(
    config: dict,
    settings: object,
    subscriber_id: str,
    email: str,
    name: Optional[str] = None,
    segment: Optional[str] = None,
) -> dict:
    """Add a subscriber.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        subscriber_id: Subscriber ID.
        email: Subscriber email.
        name: Optional subscriber name.
        segment: Optional segment.

    Returns:
        Dictionary with subscriber information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    subscriber = db_manager.add_subscriber(
        subscriber_id=subscriber_id,
        email=email,
        name=name,
        segment=segment,
    )

    logger.info(f"Added subscriber: {subscriber.email}", extra={"subscriber_id": subscriber.id, "subscriber_id_str": subscriber_id})

    return {
        "success": True,
        "subscriber_id": subscriber.id,
        "email": subscriber.email,
        "segment": subscriber.segment,
    }


def add_article(
    config: dict,
    settings: object,
    article_id: str,
    title: str,
    content: Optional[str] = None,
    category: Optional[str] = None,
    quality_score: Optional[float] = None,
) -> dict:
    """Add an article.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        article_id: Article ID.
        title: Article title.
        content: Optional article content.
        category: Optional category.
        quality_score: Optional quality score.

    Returns:
        Dictionary with article information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)

    article = db_manager.add_article(
        article_id=article_id,
        title=title,
        content=content,
        category=category,
        quality_score=quality_score,
        published_date=datetime.utcnow(),
    )

    logger.info(f"Added article: {article.title}", extra={"article_id": article.id, "article_id_str": article_id})

    return {
        "success": True,
        "article_id": article.id,
        "title": article.title,
    }


def generate_newsletter(
    config: dict,
    settings: object,
    newsletter_id: str,
    title: str,
    segment: Optional[str] = None,
    article_count: Optional[int] = None,
) -> dict:
    """Generate newsletter.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        newsletter_id: Newsletter ID.
        title: Newsletter title.
        segment: Optional subscriber segment.
        article_count: Optional number of articles.

    Returns:
        Dictionary with newsletter generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    curator = ArticleCurator(db_manager, config)
    formatter = LayoutFormatter(db_manager, config)

    logger.info("Generating newsletter", extra={"newsletter_id": newsletter_id, "segment": segment})

    if segment:
        articles = curator.curate_for_segment(segment, count=article_count)
    else:
        articles = curator.curate_articles(count=article_count)

    if not articles:
        return {"success": False, "error": "No articles available for curation"}

    newsletter = db_manager.add_newsletter(
        newsletter_id=newsletter_id,
        title=title,
        segment=segment,
    )

    for idx, article in enumerate(articles):
        featured = idx == 0
        db_manager.add_newsletter_item(
            newsletter_id=newsletter.id,
            article_id=article.id,
            position=idx + 1,
            featured=featured,
        )

    html_content = formatter.format_newsletter(newsletter, articles)
    text_content = formatter.format_text_version(newsletter, articles)

    newsletter.content_html = html_content
    newsletter.content_text = text_content

    session = db_manager.get_session()
    try:
        session.merge(newsletter)
        session.commit()
        session.refresh(newsletter)
    finally:
        session.close()

    logger.info(
        f"Generated newsletter: {newsletter.newsletter_id}",
        extra={"newsletter_id": newsletter.newsletter_id, "article_count": len(articles)},
    )

    return {
        "success": True,
        "newsletter_id": newsletter.newsletter_id,
        "article_count": len(articles),
    }


def personalize_newsletter(
    config: dict,
    settings: object,
    newsletter_id: str,
    subscriber_id: str,
) -> dict:
    """Personalize newsletter for subscriber.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        newsletter_id: Newsletter ID.
        subscriber_id: Subscriber ID.

    Returns:
        Dictionary with personalization results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    personalizer = PersonalizationEngine(db_manager, config)
    formatter = LayoutFormatter(db_manager, config)

    from src.database import Newsletter, Subscriber
    newsletter = (
        db_manager.get_session()
        .query(Newsletter)
        .filter(Newsletter.newsletter_id == newsletter_id)
        .first()
    )

    subscriber = (
        db_manager.get_session()
        .query(Subscriber)
        .filter(Subscriber.subscriber_id == subscriber_id)
        .first()
    )

    if not newsletter:
        return {"success": False, "error": f"Newsletter {newsletter_id} not found"}

    if not subscriber:
        return {"success": False, "error": f"Subscriber {subscriber_id} not found"}

    logger.info("Personalizing newsletter", extra={"newsletter_id": newsletter_id, "subscriber_id": subscriber_id})

    articles = [item.article for item in newsletter.items if item.article]
    personalized_articles = personalizer.personalize_articles(subscriber.id, articles)
    personalized_sections = personalizer.personalize_sections(newsletter, subscriber)

    personalized_html = formatter.format_newsletter(
        newsletter,
        personalized_articles,
        subscriber_name=subscriber.name,
        personalized=personalized_sections,
    )

    logger.info(
        f"Personalized newsletter for subscriber {subscriber_id}",
        extra={"newsletter_id": newsletter_id, "subscriber_id": subscriber_id},
    )

    return {
        "success": True,
        "personalized_html": personalized_html,
        "article_count": len(personalized_articles),
    }


def schedule_distribution(
    config: dict,
    settings: object,
    newsletter_id: str,
    segment: Optional[str] = None,
    send_time: Optional[str] = None,
) -> dict:
    """Schedule newsletter distribution.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        newsletter_id: Newsletter ID.
        segment: Optional subscriber segment.
        send_time: Optional send time (YYYY-MM-DD HH:MM).

    Returns:
        Dictionary with scheduling results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    scheduler = DistributionScheduler(db_manager, config)

    from src.database import Newsletter
    newsletter = (
        db_manager.get_session()
        .query(Newsletter)
        .filter(Newsletter.newsletter_id == newsletter_id)
        .first()
    )

    if not newsletter:
        return {"success": False, "error": f"Newsletter {newsletter_id} not found"}

    send_datetime = None
    if send_time:
        try:
            send_datetime = datetime.strptime(send_time, "%Y-%m-%d %H:%M")
        except ValueError:
            return {"success": False, "error": "Invalid send time format. Use YYYY-MM-DD HH:MM"}

    logger.info("Scheduling distribution", extra={"newsletter_id": newsletter_id, "segment": segment})

    result = scheduler.schedule_distribution(
        newsletter_id=newsletter.id,
        segment=segment,
        send_time=send_datetime,
    )

    logger.info(
        f"Scheduled distribution for newsletter {newsletter_id}",
        extra={"scheduled_count": result.get("scheduled_count")},
    )

    return result


def send_scheduled(
    config: dict,
    settings: object,
) -> dict:
    """Send scheduled newsletters.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.

    Returns:
        Dictionary with sending results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    scheduler = DistributionScheduler(db_manager, config)

    logger.info("Sending scheduled newsletters")

    ready_newsletters = scheduler.get_scheduled_distributions()

    results = []
    for newsletter in ready_newsletters:
        result = scheduler.send_newsletter(newsletter.id)
        results.append({
            "newsletter_id": newsletter.newsletter_id,
            "sent_count": result.get("sent_count", 0),
            "failed_count": result.get("failed_count", 0),
        })

    logger.info(
        f"Sent {len(results)} scheduled newsletters",
        extra={"newsletter_count": len(results)},
    )

    return {
        "success": True,
        "newsletters_sent": len(results),
        "results": results,
    }


def main() -> None:
    """Main entry point for newsletter generator automation."""
    parser = argparse.ArgumentParser(
        description="Newsletter generator automation system"
    )
    parser.add_argument(
        "--add-subscriber",
        action="store_true",
        help="Add a subscriber",
    )
    parser.add_argument(
        "--subscriber-id", help="Subscriber ID"
    )
    parser.add_argument(
        "--email", help="Subscriber email"
    )
    parser.add_argument(
        "--name", help="Subscriber name"
    )
    parser.add_argument(
        "--segment", help="Subscriber segment"
    )
    parser.add_argument(
        "--add-article",
        action="store_true",
        help="Add an article",
    )
    parser.add_argument(
        "--article-id", help="Article ID"
    )
    parser.add_argument(
        "--title", help="Article title"
    )
    parser.add_argument(
        "--content", help="Article content"
    )
    parser.add_argument(
        "--category", help="Article category"
    )
    parser.add_argument(
        "--quality-score", type=float, help="Quality score (0.0 to 1.0)"
    )
    parser.add_argument(
        "--generate-newsletter",
        action="store_true",
        help="Generate newsletter",
    )
    parser.add_argument(
        "--newsletter-id", help="Newsletter ID"
    )
    parser.add_argument(
        "--article-count", type=int, help="Number of articles"
    )
    parser.add_argument(
        "--personalize",
        action="store_true",
        help="Personalize newsletter for subscriber",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Schedule newsletter distribution",
    )
    parser.add_argument(
        "--send-time", help="Send time (YYYY-MM-DD HH:MM)"
    )
    parser.add_argument(
        "--send-scheduled",
        action="store_true",
        help="Send scheduled newsletters",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([
        args.add_subscriber,
        args.add_article,
        args.generate_newsletter,
        args.personalize,
        args.schedule,
        args.send_scheduled,
    ]):
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
        db_manager = DatabaseManager(settings.database.url)
        db_manager.create_tables()

        if args.add_subscriber:
            if not all([args.subscriber_id, args.email]):
                print(
                    "Error: --subscriber-id and --email are required for --add-subscriber",
                    file=sys.stderr,
                )
                sys.exit(1)

            result = add_subscriber(
                config=config,
                settings=settings,
                subscriber_id=args.subscriber_id,
                email=args.email,
                name=args.name,
                segment=args.segment,
            )

            print(f"\nSubscriber added:")
            print(f"ID: {result['subscriber_id']}")
            print(f"Email: {result['email']}")
            print(f"Segment: {result.get('segment', 'N/A')}")

        elif args.add_article:
            if not all([args.article_id, args.title]):
                print(
                    "Error: --article-id and --title are required for --add-article",
                    file=sys.stderr,
                )
                sys.exit(1)

            result = add_article(
                config=config,
                settings=settings,
                article_id=args.article_id,
                title=args.title,
                content=args.content,
                category=args.category,
                quality_score=args.quality_score,
            )

            print(f"\nArticle added:")
            print(f"ID: {result['article_id']}")
            print(f"Title: {result['title']}")

        elif args.generate_newsletter:
            if not all([args.newsletter_id, args.title]):
                print(
                    "Error: --newsletter-id and --title are required for --generate-newsletter",
                    file=sys.stderr,
                )
                sys.exit(1)

            result = generate_newsletter(
                config=config,
                settings=settings,
                newsletter_id=args.newsletter_id,
                title=args.title,
                segment=args.segment,
                article_count=args.article_count,
            )

            if result["success"]:
                print(f"\nNewsletter generated:")
                print(f"Newsletter ID: {result['newsletter_id']}")
                print(f"Articles: {result['article_count']}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.personalize:
            if not all([args.newsletter_id, args.subscriber_id]):
                print(
                    "Error: --newsletter-id and --subscriber-id are required for --personalize",
                    file=sys.stderr,
                )
                sys.exit(1)

            result = personalize_newsletter(
                config=config,
                settings=settings,
                newsletter_id=args.newsletter_id,
                subscriber_id=args.subscriber_id,
            )

            if result["success"]:
                print(f"\nNewsletter personalized:")
                print(f"Articles: {result['article_count']}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.schedule:
            if not args.newsletter_id:
                print("Error: --newsletter-id is required for --schedule", file=sys.stderr)
                sys.exit(1)

            result = schedule_distribution(
                config=config,
                settings=settings,
                newsletter_id=args.newsletter_id,
                segment=args.segment,
                send_time=args.send_time,
            )

            if result["success"]:
                print(f"\nDistribution scheduled:")
                print(f"Scheduled count: {result['scheduled_count']}")
                print(f"Send time: {result.get('send_time', 'N/A')}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.send_scheduled:
            result = send_scheduled(
                config=config,
                settings=settings,
            )

            print(f"\nScheduled Newsletters Sent:")
            print(f"Newsletters sent: {result['newsletters_sent']}")
            for res in result["results"]:
                print(f"  - {res['newsletter_id']}: {res['sent_count']} sent, {res['failed_count']} failed")

    except Exception as e:
        logger.error(f"Error executing command: {e}", extra={"error": str(e)})
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
