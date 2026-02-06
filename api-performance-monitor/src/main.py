"""API performance monitoring automation system.

Monitors API endpoint performance, tracks response times, identifies slow endpoints,
and generates optimization recommendations with bottleneck analysis.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.api_monitor import APIMonitor
from src.bottleneck_analyzer import BottleneckAnalyzer
from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.recommendation_engine import RecommendationEngine
from src.report_generator import ReportGenerator
from src.response_time_tracker import ResponseTimeTracker


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/api_performance.log"))
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


def add_endpoint(
    config: dict,
    settings: object,
    base_url: str,
    path: str,
    method: str = "GET",
    description: Optional[str] = None,
) -> dict:
    """Add an API endpoint to monitor.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        base_url: Base URL of the API.
        path: Endpoint path.
        method: HTTP method.
        description: Optional description.

    Returns:
        Dictionary with endpoint information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    endpoint = db_manager.add_endpoint(
        base_url=base_url,
        path=path,
        method=method,
        description=description,
    )

    logger.info(f"Added endpoint: {endpoint.full_url}", extra={"endpoint_id": endpoint.id, "url": endpoint.full_url})

    return {
        "success": True,
        "endpoint_id": endpoint.id,
        "full_url": endpoint.full_url,
        "method": endpoint.method,
    }


def monitor_endpoint(
    config: dict,
    settings: object,
    endpoint_id: int,
    headers: Optional[dict] = None,
) -> dict:
    """Monitor an API endpoint.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        endpoint_id: Endpoint ID.
        headers: Optional request headers.

    Returns:
        Dictionary with monitoring results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    monitor = APIMonitor(db_manager, config)

    logger.info("Monitoring endpoint", extra={"endpoint_id": endpoint_id})

    request = monitor.monitor_endpoint(endpoint_id=endpoint_id, headers=headers)

    logger.info(
        f"Endpoint monitored: {request.response_time_ms:.2f}ms",
        extra={
            "endpoint_id": endpoint_id,
            "response_time_ms": request.response_time_ms,
            "status_code": request.status_code,
        },
    )

    return {
        "success": True,
        "request_id": request.id,
        "response_time_ms": request.response_time_ms,
        "status_code": request.status_code,
    }


def analyze_performance(
    config: dict,
    settings: object,
    endpoint_id: Optional[int] = None,
    hours: int = 24,
) -> dict:
    """Analyze endpoint performance.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        endpoint_id: Optional endpoint ID filter.
        hours: Number of hours to analyze.

    Returns:
        Dictionary with analysis results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    tracker = ResponseTimeTracker(db_manager, config)

    logger.info("Analyzing performance", extra={"endpoint_id": endpoint_id, "hours": hours})

    if endpoint_id:
        from src.database import APIEndpoint
        endpoint = (
            db_manager.get_session()
            .query(APIEndpoint)
            .filter(APIEndpoint.id == endpoint_id)
            .first()
        )
        if endpoint:
            metrics = tracker.calculate_metrics(endpoint_id)
            slow_endpoints = tracker.identify_slow_endpoints()
            slow_endpoints = [e for e in slow_endpoints if e["endpoint_id"] == endpoint_id]
        else:
            return {"success": False, "error": f"Endpoint {endpoint_id} not found"}
    else:
        endpoints = db_manager.get_endpoints(active_only=True)
        for endpoint in endpoints:
            tracker.calculate_metrics(endpoint.id)
        slow_endpoints = tracker.identify_slow_endpoints()

    logger.info(
        f"Performance analysis completed: {len(slow_endpoints)} slow endpoints",
        extra={"slow_endpoint_count": len(slow_endpoints)},
    )

    return {
        "success": True,
        "slow_endpoints": slow_endpoints,
    }


def identify_bottlenecks(
    config: dict,
    settings: object,
    endpoint_id: Optional[int] = None,
    hours: int = 24,
) -> dict:
    """Identify performance bottlenecks.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        endpoint_id: Optional endpoint ID filter.
        hours: Number of hours to analyze.

    Returns:
        Dictionary with bottleneck identification results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    analyzer = BottleneckAnalyzer(db_manager, config)

    logger.info("Identifying bottlenecks", extra={"endpoint_id": endpoint_id, "hours": hours})

    if endpoint_id:
        bottlenecks = analyzer.analyze_endpoint(endpoint_id, hours=hours)
    else:
        bottlenecks = analyzer.analyze_all_endpoints(hours=hours)

    logger.info(
        f"Bottleneck identification completed: {len(bottlenecks)} bottlenecks found",
        extra={"bottleneck_count": len(bottlenecks)},
    )

    return {
        "success": True,
        "bottleneck_count": len(bottlenecks),
        "bottlenecks": [
            {
                "type": b.bottleneck_type,
                "severity": b.severity,
                "description": b.description,
            }
            for b in bottlenecks
        ],
    }


def generate_recommendations(
    config: dict,
    settings: object,
    endpoint_id: Optional[int] = None,
) -> dict:
    """Generate optimization recommendations.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        endpoint_id: Optional endpoint ID filter.

    Returns:
        Dictionary with recommendation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    engine = RecommendationEngine(db_manager, config)

    logger.info("Generating recommendations", extra={"endpoint_id": endpoint_id})

    if endpoint_id:
        recommendations = engine.generate_recommendations(endpoint_id)
    else:
        endpoints = db_manager.get_endpoints(active_only=True)
        recommendations = []
        for endpoint in endpoints:
            recommendations.extend(engine.generate_recommendations(endpoint.id))

    logger.info(
        f"Generated {len(recommendations)} recommendations",
        extra={"recommendation_count": len(recommendations)},
    )

    return {
        "success": True,
        "recommendation_count": len(recommendations),
        "recommendations": [
            {
                "type": r.recommendation_type,
                "title": r.title,
                "description": r.description,
                "priority": r.priority,
            }
            for r in recommendations
        ],
    }


def generate_report(
    config: dict,
    settings: object,
    endpoint_id: Optional[int] = None,
    hours: int = 24,
    format: str = "html",
) -> dict:
    """Generate performance report.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        endpoint_id: Optional endpoint ID filter.
        hours: Number of hours to analyze.
        format: Report format (html, csv, json).

    Returns:
        Dictionary with report path.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    generator = ReportGenerator(
        db_manager,
        config,
        output_dir=config.get("reporting", {}).get("output_directory", "reports"),
    )

    logger.info("Generating performance report", extra={"format": format, "endpoint_id": endpoint_id})

    if format == "html":
        report_path = generator.generate_html_report(
            endpoint_id=endpoint_id,
            hours=hours,
        )
    elif format == "csv":
        report_path = generator.generate_csv_report(
            endpoint_id=endpoint_id,
            hours=hours,
        )
    else:
        return {"success": False, "error": f"Unsupported format: {format}"}

    logger.info(
        f"Report generated: {report_path}",
        extra={"report_path": str(report_path)},
    )

    return {
        "success": True,
        "report_path": str(report_path),
        "format": format,
    }


def main() -> None:
    """Main entry point for API performance monitoring automation."""
    parser = argparse.ArgumentParser(
        description="API performance monitoring automation system"
    )
    parser.add_argument(
        "--add-endpoint",
        action="store_true",
        help="Add an API endpoint to monitor",
    )
    parser.add_argument(
        "--base-url", help="Base URL of the API"
    )
    parser.add_argument(
        "--path", help="Endpoint path"
    )
    parser.add_argument(
        "--method",
        choices=["GET", "POST", "PUT", "DELETE", "PATCH"],
        default="GET",
        help="HTTP method (default: GET)",
    )
    parser.add_argument(
        "--description", help="Endpoint description"
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Monitor an API endpoint",
    )
    parser.add_argument(
        "--endpoint-id", type=int, help="Endpoint ID"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze endpoint performance",
    )
    parser.add_argument(
        "--analyze-hours", type=int, default=24, help="Hours to analyze (default: 24)"
    )
    parser.add_argument(
        "--identify-bottlenecks",
        action="store_true",
        help="Identify performance bottlenecks",
    )
    parser.add_argument(
        "--bottleneck-hours", type=int, default=24, help="Hours to analyze for bottlenecks (default: 24)"
    )
    parser.add_argument(
        "--generate-recommendations",
        action="store_true",
        help="Generate optimization recommendations",
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate performance report",
    )
    parser.add_argument(
        "--format",
        choices=["html", "csv"],
        default="html",
        help="Report format (default: html)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([
        args.add_endpoint,
        args.monitor,
        args.analyze,
        args.identify_bottlenecks,
        args.generate_recommendations,
        args.generate_report,
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
        if args.add_endpoint:
            if not all([args.base_url, args.path]):
                print(
                    "Error: --base-url and --path are required for --add-endpoint",
                    file=sys.stderr,
                )
                sys.exit(1)

            result = add_endpoint(
                config=config,
                settings=settings,
                base_url=args.base_url,
                path=args.path,
                method=args.method,
                description=args.description,
            )

            print(f"\nEndpoint added:")
            print(f"ID: {result['endpoint_id']}")
            print(f"URL: {result['full_url']}")
            print(f"Method: {result['method']}")

        elif args.monitor:
            if not args.endpoint_id:
                print("Error: --endpoint-id is required for --monitor", file=sys.stderr)
                sys.exit(1)

            result = monitor_endpoint(
                config=config,
                settings=settings,
                endpoint_id=args.endpoint_id,
            )

            print(f"\nEndpoint monitored:")
            print(f"Response Time: {result['response_time_ms']:.2f} ms")
            print(f"Status Code: {result.get('status_code', 'N/A')}")

        elif args.analyze:
            result = analyze_performance(
                config=config,
                settings=settings,
                endpoint_id=args.endpoint_id,
                hours=args.analyze_hours,
            )

            if result["success"]:
                print(f"\nPerformance analysis:")
                print(f"Slow endpoints: {len(result['slow_endpoints'])}")
                for endpoint in result["slow_endpoints"][:5]:
                    print(f"  - {endpoint['full_url']}: {endpoint['p95_response_time_ms']:.2f}ms ({endpoint['severity']})")

        elif args.identify_bottlenecks:
            result = identify_bottlenecks(
                config=config,
                settings=settings,
                endpoint_id=args.endpoint_id,
                hours=args.bottleneck_hours,
            )

            print(f"\nBottleneck identification:")
            print(f"Bottlenecks found: {result['bottleneck_count']}")
            for bottleneck in result["bottlenecks"][:5]:
                print(f"  - {bottleneck['type']}: {bottleneck['description']} ({bottleneck['severity']})")

        elif args.generate_recommendations:
            result = generate_recommendations(
                config=config,
                settings=settings,
                endpoint_id=args.endpoint_id,
            )

            print(f"\nRecommendations ({result['recommendation_count']}):")
            for rec in result["recommendations"][:5]:
                print(f"  [{rec['priority'].upper()}] {rec['title']}")
                print(f"    {rec['description']}")

        elif args.generate_report:
            result = generate_report(
                config=config,
                settings=settings,
                endpoint_id=args.endpoint_id,
                hours=args.analyze_hours,
                format=args.format,
            )

            if result["success"]:
                print(f"\nReport generated:")
                print(f"Format: {result['format'].upper()}")
                print(f"Path: {result['report_path']}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

    except Exception as e:
        logger.error(f"Error executing command: {e}", extra={"error": str(e)})
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
