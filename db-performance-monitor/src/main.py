"""Database performance monitoring automation system.

Monitors database performance, identifies slow queries, recommends optimizations,
and generates performance reports with indexing suggestions.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.performance_monitor import PerformanceMonitor
from src.slow_query_identifier import SlowQueryIdentifier
from src.optimization_recommender import OptimizationRecommender
from src.report_generator import ReportGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/db_performance_monitor.log"))
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


def monitor_performance(
    config: dict,
    settings: object,
    database_id: str,
) -> dict:
    """Monitor database performance.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        database_id: Database identifier.

    Returns:
        Dictionary with performance monitoring results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    monitor = PerformanceMonitor(db_manager, config.get("performance_monitoring", {}))

    logger.info(f"Monitoring performance for database: {database_id}")

    result = monitor.monitor_performance(database_id)

    logger.info(f"Found {result.get('metrics_count', 0)} metrics")

    return result


def collect_metrics(
    config: dict,
    settings: object,
    database_id: str,
    metrics_file: Path,
) -> dict:
    """Collect performance metrics from file.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        database_id: Database identifier.
        metrics_file: Path to metrics JSON file.

    Returns:
        Dictionary with collection results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    monitor = PerformanceMonitor(db_manager, config.get("performance_monitoring", {}))

    logger.info(f"Collecting metrics for database: {database_id}")

    with open(metrics_file, "r") as f:
        metrics = json.load(f)

    result = monitor.collect_metrics(database_id, metrics)

    logger.info(f"Collected {result.get('metrics_collected', 0)} metrics")

    return result


def identify_slow_queries(
    config: dict,
    settings: object,
    database_id: str,
    queries_file: Path,
) -> dict:
    """Identify slow queries from file.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        database_id: Database identifier.
        queries_file: Path to queries JSON file.

    Returns:
        Dictionary with identification results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    identifier = SlowQueryIdentifier(db_manager, config.get("slow_query_identification", {}))

    logger.info(f"Identifying slow queries for database: {database_id}")

    with open(queries_file, "r") as f:
        queries = json.load(f)

    result = identifier.identify_slow_queries(database_id, queries)

    logger.info(f"Found {result.get('slow_queries_count', 0)} slow queries")

    return result


def recommend_optimizations(
    config: dict,
    settings: object,
    database_id: str,
    query_id: Optional[str] = None,
) -> dict:
    """Recommend optimizations.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        database_id: Database identifier.
        query_id: Optional query ID to optimize specific query.

    Returns:
        Dictionary with optimization recommendations.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    recommender = OptimizationRecommender(
        db_manager, config.get("optimization", {})
    )

    logger.info(f"Recommending optimizations for database: {database_id}")

    result = recommender.recommend_optimizations(database_id, query_id=query_id)

    logger.info(f"Created {result.get('optimizations_created', 0)} optimizations")

    return result


def generate_reports(
    config: dict,
    settings: object,
    database_id: Optional[str] = None,
) -> dict:
    """Generate analysis reports.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        database_id: Optional database ID to filter by.

    Returns:
        Dictionary with report generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    report_generator = ReportGenerator(db_manager, config.get("reporting", {}))

    logger.info("Generating performance reports", extra={"database_id": database_id})

    reports = report_generator.generate_reports(database_id=database_id)

    logger.info(
        f"Reports generated: {len(reports)} report(s) created",
        extra={"report_count": len(reports)},
    )

    return {
        "success": True,
        "reports": {k: str(v) for k, v in reports.items()},
        "database_id": database_id,
    }


def main() -> None:
    """Main entry point for database performance monitoring automation."""
    parser = argparse.ArgumentParser(
        description="Database performance monitoring automation system"
    )
    parser.add_argument(
        "--monitor",
        metavar="DATABASE_ID",
        help="Monitor database performance",
    )
    parser.add_argument(
        "--collect-metrics",
        nargs=2,
        metavar=("DATABASE_ID", "FILE"),
        help="Collect performance metrics from JSON file",
    )
    parser.add_argument(
        "--identify-slow-queries",
        nargs=2,
        metavar=("DATABASE_ID", "FILE"),
        help="Identify slow queries from JSON file",
    )
    parser.add_argument(
        "--recommend-optimizations",
        metavar="DATABASE_ID",
        help="Recommend optimizations",
    )
    parser.add_argument(
        "--query-id",
        help="Query ID for specific optimization",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate performance reports",
    )
    parser.add_argument(
        "--database-id",
        help="Filter by database ID",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([
        args.monitor,
        args.collect_metrics,
        args.identify_slow_queries,
        args.recommend_optimizations,
        args.report,
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
        if args.monitor:
            result = monitor_performance(
                config=config,
                settings=settings,
                database_id=args.monitor,
            )
            print(f"\nPerformance Monitoring:")
            print(f"Database: {result.get('database_name', 'N/A')}")
            print(f"Metrics count: {result.get('metrics_count', 0)}")

        if args.collect_metrics:
            database_id, file_path = args.collect_metrics
            result = collect_metrics(
                config=config,
                settings=settings,
                database_id=database_id,
                metrics_file=Path(file_path),
            )
            if result.get("success"):
                print(f"\nMetrics collected:")
                print(f"Metrics collected: {result.get('metrics_collected', 0)}")

        if args.identify_slow_queries:
            database_id, file_path = args.identify_slow_queries
            result = identify_slow_queries(
                config=config,
                settings=settings,
                database_id=database_id,
                queries_file=Path(file_path),
            )
            if result.get("success"):
                print(f"\nSlow Query Identification:")
                print(f"Total queries: {result.get('total_queries', 0)}")
                print(f"Slow queries: {result.get('slow_queries_count', 0)}")

        if args.recommend_optimizations:
            result = recommend_optimizations(
                config=config,
                settings=settings,
                database_id=args.recommend_optimizations,
                query_id=args.query_id,
            )
            if result.get("success"):
                print(f"\nOptimization Recommendations:")
                print(f"Optimizations created: {result.get('optimizations_created', 0)}")

        if args.report:
            result = generate_reports(
                config=config,
                settings=settings,
                database_id=args.database_id,
            )
            print(f"\nReports generated:")
            for report_type, path in result["reports"].items():
                print(f"  {report_type.upper()}: {path}")

    except Exception as e:
        logger.error(f"Error executing command: {e}", extra={"error": str(e)})
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
