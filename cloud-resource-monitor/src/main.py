"""Cloud resource monitor automation system.

Monitors cloud resource utilization, identifies idle resources, recommends
right-sizing, and automatically scales resources based on demand patterns.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.auto_scaler import AutoScaler
from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.idle_detector import IdleDetector
from src.report_generator import ReportGenerator
from src.resource_monitor import ResourceMonitor
from src.right_sizing_analyzer import RightSizingAnalyzer


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/cloud_resource_monitor.log"))
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


def add_resource(
    config: dict,
    settings: object,
    resource_id: str,
    resource_name: str,
    resource_type: str,
    cloud_provider: str,
    instance_type: Optional[str] = None,
    cost_per_hour: Optional[float] = None,
) -> dict:
    """Add a cloud resource.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        resource_id: Resource ID.
        resource_name: Resource name.
        resource_type: Resource type.
        cloud_provider: Cloud provider.
        instance_type: Optional instance type.
        cost_per_hour: Optional cost per hour.

    Returns:
        Dictionary with resource information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    resource = db_manager.add_resource(
        resource_id=resource_id,
        resource_name=resource_name,
        resource_type=resource_type,
        cloud_provider=cloud_provider,
        instance_type=instance_type,
        cost_per_hour=cost_per_hour,
    )

    logger.info(f"Added resource: {resource.resource_name}", extra={"resource_id": resource.id, "resource_id_str": resource_id})

    return {
        "success": True,
        "resource_id": resource.id,
        "resource_name": resource.resource_name,
        "resource_type": resource.resource_type,
    }


def collect_metrics(
    config: dict,
    settings: object,
    resource_id: str,
    cpu_utilization: Optional[float] = None,
    memory_utilization: Optional[float] = None,
    disk_utilization: Optional[float] = None,
) -> dict:
    """Collect metrics for a resource.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        resource_id: Resource ID.
        cpu_utilization: Optional CPU utilization percentage.
        memory_utilization: Optional memory utilization percentage.
        disk_utilization: Optional disk utilization percentage.

    Returns:
        Dictionary with metrics collection results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    monitor = ResourceMonitor(db_manager, config)

    from src.database import CloudResource
    resource = (
        db_manager.get_session()
        .query(CloudResource)
        .filter(CloudResource.resource_id == resource_id)
        .first()
    )

    if not resource:
        return {"success": False, "error": f"Resource {resource_id} not found"}

    metrics = {}
    if cpu_utilization is not None:
        metrics["cpu_utilization"] = cpu_utilization
    if memory_utilization is not None:
        metrics["memory_utilization"] = memory_utilization
    if disk_utilization is not None:
        metrics["disk_utilization"] = disk_utilization

    if not metrics:
        return {"success": False, "error": "No metrics provided"}

    collected = monitor.collect_metrics(resource.id, metrics)

    logger.info(
        f"Collected {len(collected)} metrics for resource {resource_id}",
        extra={"resource_id": resource.id, "metric_count": len(collected)},
    )

    return {
        "success": True,
        "metrics_collected": len(collected),
    }


def detect_idle(
    config: dict,
    settings: object,
    resource_id: Optional[str] = None,
) -> dict:
    """Detect idle resources.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        resource_id: Optional resource ID filter.

    Returns:
        Dictionary with idle detection results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    detector = IdleDetector(db_manager, config)

    logger.info("Detecting idle resources", extra={"resource_id": resource_id})

    from src.database import CloudResource
    resource_id_int = None
    if resource_id:
        resource = (
            db_manager.get_session()
            .query(CloudResource)
            .filter(CloudResource.resource_id == resource_id)
            .first()
        )
        if resource:
            resource_id_int = resource.id
        else:
            return {"success": False, "error": f"Resource {resource_id} not found"}

    idle_resources = detector.detect_idle_resources(resource_id=resource_id_int)

    logger.info(
        f"Detected {len(idle_resources)} idle resources",
        extra={"idle_count": len(idle_resources)},
    )

    return {
        "success": True,
        "idle_count": len(idle_resources),
        "idle_resources": [
            {
                "resource_id": ir.resource_id,
                "idle_duration_hours": ir.idle_duration_hours,
            }
            for ir in idle_resources
        ],
    }


def recommend_right_sizing(
    config: dict,
    settings: object,
    resource_id: Optional[str] = None,
) -> dict:
    """Recommend right-sizing for resources.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        resource_id: Optional resource ID filter.

    Returns:
        Dictionary with right-sizing recommendation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    analyzer = RightSizingAnalyzer(db_manager, config)

    logger.info("Analyzing right-sizing", extra={"resource_id": resource_id})

    from src.database import CloudResource
    if resource_id:
        resource = (
            db_manager.get_session()
            .query(CloudResource)
            .filter(CloudResource.resource_id == resource_id)
            .first()
        )
        if resource:
            recommendation = analyzer.analyze_resource(resource.id)
            recommendations = [recommendation] if recommendation else []
        else:
            return {"success": False, "error": f"Resource {resource_id} not found"}
    else:
        recommendations = analyzer.analyze_all_resources()

    logger.info(
        f"Generated {len(recommendations)} right-sizing recommendations",
        extra={"recommendation_count": len(recommendations)},
    )

    return {
        "success": True,
        "recommendation_count": len(recommendations),
        "recommendations": [
            {
                "resource_id": r.resource_id,
                "recommendation_type": r.recommendation_type,
                "priority": r.priority,
                "estimated_cost_savings": r.estimated_cost_savings,
            }
            for r in recommendations
        ],
    }


def check_scaling(
    config: dict,
    settings: object,
    resource_id: str,
) -> dict:
    """Check if resource needs scaling.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        resource_id: Resource ID.

    Returns:
        Dictionary with scaling check results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    scaler = AutoScaler(db_manager, config)

    from src.database import CloudResource
    resource = (
        db_manager.get_session()
        .query(CloudResource)
        .filter(CloudResource.resource_id == resource_id)
        .first()
    )

    if not resource:
        return {"success": False, "error": f"Resource {resource_id} not found"}

    logger.info("Checking scaling needs", extra={"resource_id": resource.id})

    action = scaler.check_scaling_needed(resource.id)

    if action:
        logger.info(
            f"Scaling action needed: {action.action_type}",
            extra={"action_type": action.action_type, "resource_id": resource.id},
        )
    else:
        logger.info("No scaling action needed", extra={"resource_id": resource.id})

    return {
        "success": True,
        "scaling_needed": action is not None,
        "action": {
            "action_type": action.action_type,
            "scaling_reason": action.scaling_reason,
            "target_capacity": action.target_capacity,
        } if action else None,
    }


def analyze_demand_patterns(
    config: dict,
    settings: object,
    resource_id: str,
) -> dict:
    """Analyze demand patterns for resource.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        resource_id: Resource ID.

    Returns:
        Dictionary with demand pattern analysis results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    scaler = AutoScaler(db_manager, config)

    from src.database import CloudResource
    resource = (
        db_manager.get_session()
        .query(CloudResource)
        .filter(CloudResource.resource_id == resource_id)
        .first()
    )

    if not resource:
        return {"success": False, "error": f"Resource {resource_id} not found"}

    logger.info("Analyzing demand patterns", extra={"resource_id": resource.id})

    pattern = scaler.analyze_demand_patterns(resource.id)

    if pattern:
        logger.info(
            f"Detected demand pattern: {pattern.pattern_type}",
            extra={"pattern_type": pattern.pattern_type, "resource_id": resource.id},
        )

    return {
        "success": True,
        "pattern_detected": pattern is not None,
        "pattern": {
            "pattern_type": pattern.pattern_type,
            "pattern_description": pattern.pattern_description,
            "predicted_demand": pattern.predicted_demand,
        } if pattern else None,
    }


def generate_report(
    config: dict,
    settings: object,
    format: str = "html",
) -> dict:
    """Generate resource monitoring report.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        format: Report format (html or csv).

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

    logger.info("Generating resource report", extra={"format": format})

    if format == "html":
        report_path = generator.generate_html_report()
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
    """Main entry point for cloud resource monitor automation."""
    parser = argparse.ArgumentParser(
        description="Cloud resource monitor automation system"
    )
    parser.add_argument(
        "--add-resource",
        action="store_true",
        help="Add a cloud resource",
    )
    parser.add_argument(
        "--resource-id", help="Resource ID"
    )
    parser.add_argument(
        "--resource-name", help="Resource name"
    )
    parser.add_argument(
        "--resource-type",
        choices=["compute", "storage", "database", "network", "container"],
        help="Resource type",
    )
    parser.add_argument(
        "--cloud-provider",
        choices=["aws", "azure", "gcp"],
        help="Cloud provider",
    )
    parser.add_argument(
        "--instance-type", help="Instance type"
    )
    parser.add_argument(
        "--cost-per-hour", type=float, help="Cost per hour"
    )
    parser.add_argument(
        "--collect-metrics",
        action="store_true",
        help="Collect metrics for resource",
    )
    parser.add_argument(
        "--cpu-utilization", type=float, help="CPU utilization percentage"
    )
    parser.add_argument(
        "--memory-utilization", type=float, help="Memory utilization percentage"
    )
    parser.add_argument(
        "--disk-utilization", type=float, help="Disk utilization percentage"
    )
    parser.add_argument(
        "--detect-idle",
        action="store_true",
        help="Detect idle resources",
    )
    parser.add_argument(
        "--recommend-right-sizing",
        action="store_true",
        help="Recommend right-sizing",
    )
    parser.add_argument(
        "--check-scaling",
        action="store_true",
        help="Check if resource needs scaling",
    )
    parser.add_argument(
        "--analyze-patterns",
        action="store_true",
        help="Analyze demand patterns",
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate resource monitoring report",
    )
    parser.add_argument(
        "--format",
        choices=["html"],
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
        args.add_resource,
        args.collect_metrics,
        args.detect_idle,
        args.recommend_right_sizing,
        args.check_scaling,
        args.analyze_patterns,
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
        db_manager = DatabaseManager(settings.database.url)
        db_manager.create_tables()

        if args.add_resource:
            if not all([args.resource_id, args.resource_name, args.resource_type, args.cloud_provider]):
                print(
                    "Error: --resource-id, --resource-name, --resource-type, and --cloud-provider are required for --add-resource",
                    file=sys.stderr,
                )
                sys.exit(1)

            result = add_resource(
                config=config,
                settings=settings,
                resource_id=args.resource_id,
                resource_name=args.resource_name,
                resource_type=args.resource_type,
                cloud_provider=args.cloud_provider,
                instance_type=args.instance_type,
                cost_per_hour=args.cost_per_hour,
            )

            print(f"\nResource added:")
            print(f"ID: {result['resource_id']}")
            print(f"Name: {result['resource_name']}")
            print(f"Type: {result['resource_type']}")

        elif args.collect_metrics:
            if not args.resource_id:
                print("Error: --resource-id is required for --collect-metrics", file=sys.stderr)
                sys.exit(1)

            result = collect_metrics(
                config=config,
                settings=settings,
                resource_id=args.resource_id,
                cpu_utilization=args.cpu_utilization,
                memory_utilization=args.memory_utilization,
                disk_utilization=args.disk_utilization,
            )

            if result["success"]:
                print(f"\nMetrics collected:")
                print(f"Metrics: {result['metrics_collected']}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.detect_idle:
            result = detect_idle(
                config=config,
                settings=settings,
                resource_id=args.resource_id,
            )

            if result["success"]:
                print(f"\nIdle Detection:")
                print(f"Idle resources: {result['idle_count']}")
                for ir in result["idle_resources"][:5]:
                    print(f"  - Resource {ir['resource_id']}: idle for {ir['idle_duration_hours']:.1f} hours")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.recommend_right_sizing:
            result = recommend_right_sizing(
                config=config,
                settings=settings,
                resource_id=args.resource_id,
            )

            if result["success"]:
                print(f"\nRight-Sizing Recommendations:")
                print(f"Recommendations: {result['recommendation_count']}")
                for rec in result["recommendations"][:5]:
                    print(f"  - Resource {rec['resource_id']}: {rec['recommendation_type']} ({rec['priority']} priority)")
                    if rec.get("estimated_cost_savings"):
                        print(f"    Estimated savings: ${rec['estimated_cost_savings']:.2f}/hour")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.check_scaling:
            if not args.resource_id:
                print("Error: --resource-id is required for --check-scaling", file=sys.stderr)
                sys.exit(1)

            result = check_scaling(
                config=config,
                settings=settings,
                resource_id=args.resource_id,
            )

            if result["success"]:
                print(f"\nScaling Check:")
                print(f"Scaling needed: {result['scaling_needed']}")
                if result.get("action"):
                    print(f"Action: {result['action']['action_type']}")
                    print(f"Reason: {result['action']['scaling_reason']}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.analyze_patterns:
            if not args.resource_id:
                print("Error: --resource-id is required for --analyze-patterns", file=sys.stderr)
                sys.exit(1)

            result = analyze_demand_patterns(
                config=config,
                settings=settings,
                resource_id=args.resource_id,
            )

            if result["success"]:
                print(f"\nDemand Pattern Analysis:")
                print(f"Pattern detected: {result['pattern_detected']}")
                if result.get("pattern"):
                    print(f"Type: {result['pattern']['pattern_type']}")
                    print(f"Description: {result['pattern']['pattern_description']}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.generate_report:
            result = generate_report(
                config=config,
                settings=settings,
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
