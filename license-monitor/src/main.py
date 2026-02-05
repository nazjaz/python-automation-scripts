"""Software license monitoring automation system.

Monitors software license usage, tracks compliance, identifies unused
licenses, and generates optimization reports for cost reduction.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.compliance_checker import ComplianceChecker
from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.license_collector import LicenseCollector
from src.optimizer import LicenseOptimizer
from src.report_generator import ReportGenerator
from src.usage_tracker import UsageTracker


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/license_monitor.log"))
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


def collect_licenses(config: dict, settings: object) -> int:
    """Collect licenses from all configured sources.

    Args:
        config: Configuration dictionary.
        settings: Application settings.

    Returns:
        Total number of licenses collected.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(config.get("database", {}).get("url", "sqlite:///license_monitor.db"))
    db_manager.create_tables()

    collector = LicenseCollector(db_manager)
    license_sources = config.get("license_sources", [])

    total_collected = 0
    for source_config in license_sources:
        collected = collector.collect_from_source(source_config, settings)
        total_collected += collected
        logger.info(
            f"Collected {collected} licenses from {source_config.get('name')}"
        )

    logger.info(f"Total licenses collected: {total_collected}")
    return total_collected


def check_compliance(config: dict) -> list:
    """Check compliance for all license types.

    Args:
        config: Configuration dictionary.

    Returns:
        List of ComplianceRecord objects.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(config.get("database", {}).get("url", "sqlite:///license_monitor.db"))
    monitoring_config = config.get("monitoring", {})

    checker = ComplianceChecker(
        db_manager,
        threshold=monitoring_config.get("compliance_threshold_percentage", 0.95),
    )

    license_types = [lt["name"] for lt in config.get("license_types", [])]
    compliance_records = checker.check_all_compliance(license_types)

    logger.info(f"Checked compliance for {len(compliance_records)} license types")
    return compliance_records


def generate_optimization_report(config: dict) -> dict:
    """Generate optimization report with recommendations.

    Args:
        config: Configuration dictionary.

    Returns:
        Dictionary with report generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(config.get("database", {}).get("url", "sqlite:///license_monitor.db"))
    monitoring_config = config.get("monitoring", {})
    optimization_config = config.get("optimization", {})
    reporting_config = config.get("reporting", {})

    optimizer = LicenseOptimizer(
        db_manager,
        config.get("license_types", []),
        cost_savings_threshold=optimization_config.get("cost_savings_threshold", 100.00),
    )

    recommendations = optimizer.generate_all_recommendations(
        threshold_days=monitoring_config.get("unused_license_threshold_days", 90)
    )

    compliance_records = check_compliance(config)

    generator = ReportGenerator(
        db_manager,
        output_directory=reporting_config.get("output_directory", "reports"),
        template_path=reporting_config.get("report_template"),
    )

    output_formats = reporting_config.get("output_format", ["html", "json"])
    generated_files = []

    if "json" in output_formats:
        json_path = generator.generate_json(compliance_records, recommendations)
        generated_files.append(str(json_path))

    if "html" in output_formats:
        html_path = generator.generate_html(compliance_records, recommendations)
        generated_files.append(str(html_path))

    if "excel" in output_formats:
        excel_path = generator.generate_excel(compliance_records, recommendations)
        generated_files.append(str(excel_path))

    total_savings = sum(r.estimated_savings for r in recommendations)

    logger.info(
        f"Generated optimization report with {len(recommendations)} recommendations "
        f"and ${total_savings:.2f} potential savings"
    )

    return {
        "compliance_records": len(compliance_records),
        "recommendations": len(recommendations),
        "total_savings": total_savings,
        "generated_files": generated_files,
    }


def main() -> None:
    """Main entry point for license monitoring automation."""
    parser = argparse.ArgumentParser(description="Software license monitoring system")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--collect", action="store_true", help="Collect licenses from sources"
    )
    parser.add_argument(
        "--compliance", action="store_true", help="Check compliance status"
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate optimization report"
    )

    args = parser.parse_args()

    try:
        config = load_config(args.config) if args.config else load_config()
        settings = get_settings()
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    setup_logging(config.get("logging", {}))

    logger = logging.getLogger(__name__)
    logger.info("Starting license monitoring")

    if args.collect:
        total_collected = collect_licenses(config, settings)
        print(f"Collected {total_collected} licenses from all sources")

    elif args.compliance:
        records = check_compliance(config)
        print(f"\nCompliance Check Results:")
        for record in records:
            status_icon = "✓" if record.status == "compliant" else "✗"
            print(
                f"{status_icon} {record.license_type}: "
                f"{record.compliance_percentage:.2%} "
                f"({record.assigned_licenses}/{record.total_licenses} assigned)"
            )

    elif args.report:
        result = generate_optimization_report(config)
        print(f"\nOptimization Report Generated:")
        print(f"Compliance Records: {result['compliance_records']}")
        print(f"Recommendations: {result['recommendations']}")
        print(f"Total Potential Savings: ${result['total_savings']:.2f}")
        print(f"Generated Files: {', '.join(result['generated_files'])}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
