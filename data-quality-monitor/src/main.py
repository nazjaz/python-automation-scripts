"""Data quality monitoring automation system.

Monitors data quality across databases, identifies inconsistencies,
validates data integrity, and generates scorecards with remediation plans.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database_connector import DatabaseConnector
from src.integrity_validator import IntegrityValidator
from src.quality_checks import AccuracyChecker, CompletenessChecker, UniquenessChecker
from src.remediation_planner import RemediationPlanner
from src.scorecard_generator import Scorecard, ScorecardGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/data_quality.log"))
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


def process_database_quality(
    db_config: dict,
    table_configs: list[dict],
    quality_config: dict,
    reporting_config: dict,
    settings: object,
) -> Scorecard:
    """Process data quality monitoring for a database.

    Args:
        db_config: Database configuration.
        table_configs: List of table configurations to check.
        quality_config: Quality checks configuration.
        reporting_config: Reporting configuration.
        settings: Application settings.

    Returns:
        Scorecard with quality results.
    """
    logger = logging.getLogger(__name__)

    connector = DatabaseConnector(
        name=db_config["name"],
        connection_string=db_config["connection_string"],
        db_type=db_config["type"],
    )

    if not connector.connect():
        logger.error(f"Failed to connect to database: {db_config['name']}")
        raise ConnectionError(f"Failed to connect to database: {db_config['name']}")

    try:
        scorecard = Scorecard(database_name=db_config["name"])

        completeness_checker = CompletenessChecker(
            connector, quality_config.get("completeness", {})
        )
        uniqueness_checker = UniquenessChecker(
            connector, quality_config.get("uniqueness", {})
        )
        accuracy_checker = AccuracyChecker(
            connector, quality_config.get("accuracy", {})
        )
        integrity_validator = IntegrityValidator(
            connector, quality_config.get("consistency", {})
        )
        remediation_planner = RemediationPlanner()

        for table_config in table_configs:
            table_name = table_config["name"]
            logger.info(f"Processing table: {table_name}")

            table_checks = table_config.get("checks", [])
            results = []

            for check_config in table_checks:
                check_type = check_config.get("type")

                if check_type == "completeness" and quality_config.get(
                    "completeness", {}
                ).get("enabled", True):
                    columns = check_config.get("columns")
                    result = completeness_checker.check_table(table_name, columns)
                    results.append(result)

                elif check_type == "uniqueness" and quality_config.get(
                    "uniqueness", {}
                ).get("enabled", True):
                    columns = check_config.get("columns")
                    result = uniqueness_checker.check_table(table_name, columns)
                    results.append(result)

                elif check_type == "accuracy" and quality_config.get(
                    "accuracy", {}
                ).get("enabled", True):
                    column_checks = check_config.get("columns", [])
                    result = accuracy_checker.check_table(table_name, column_checks)
                    results.append(result)

                elif check_type == "consistency" and quality_config.get(
                    "consistency", {}
                ).get("enabled", True):
                    fk_config = check_config.get("foreign_keys", [])
                    integrity_issues = integrity_validator.validate_foreign_keys(
                        table_name, fk_config
                    )
                    scorecard.add_integrity_issues(integrity_issues)

                    for issue in integrity_issues:
                        plan = remediation_planner.create_plan_from_integrity_issue(
                            issue
                        )
                        scorecard.remediation_plans[f"{table_name}_{issue.issue_type}"] = (
                            plan
                        )

            scorecard.add_table_result(table_name, results)

            for result in results:
                if not result.passed:
                    plan = remediation_planner.create_plan_from_quality_result(result)
                    scorecard.remediation_plans[f"{table_name}_{result.check_type}"] = plan

        scorecard.calculate_overall_score()

        logger.info(
            f"Completed quality monitoring for {db_config['name']}: "
            f"Overall score: {scorecard.overall_score:.2%}"
        )

        return scorecard

    finally:
        connector.disconnect()


def main() -> None:
    """Main entry point for data quality monitoring automation."""
    parser = argparse.ArgumentParser(description="Data quality monitoring system")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--database",
        help="Specific database to monitor (default: all enabled databases)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for reports (default: from config)",
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
    logger.info("Starting data quality monitoring")

    databases = config.get("databases", [])
    tables = config.get("tables", [])
    quality_config = config.get("quality_checks", {})
    reporting_config = config.get("reporting", {})

    output_dir = args.output_dir or reporting_config.get("output_directory", "reports")
    generator = ScorecardGenerator(
        output_directory=str(output_dir),
        template_path=reporting_config.get("scorecard_template"),
    )

    scorecards = []

    for db_config in databases:
        if not db_config.get("enabled", True):
            continue

        if args.database and db_config["name"] != args.database:
            continue

        db_tables = [
            t for t in tables if t.get("database") == db_config["name"]
        ]

        if not db_tables:
            logger.warning(f"No tables configured for database: {db_config['name']}")
            continue

        try:
            scorecard = process_database_quality(
                db_config, db_tables, quality_config, reporting_config, settings
            )
            scorecards.append(scorecard)

            output_formats = reporting_config.get("output_format", ["html", "json"])

            if "json" in output_formats:
                generator.generate_json(scorecard)

            if "html" in output_formats:
                generator.generate_html(
                    scorecard,
                    include_remediation=reporting_config.get(
                        "include_remediation", True
                    ),
                )

            if "excel" in output_formats:
                generator.generate_excel(scorecard)

            print(f"\nDatabase: {scorecard.database_name}")
            print(f"Overall Score: {scorecard.overall_score:.2%}")
            print(f"Tables Checked: {len(scorecard.table_results)}")
            print(f"Integrity Issues: {len(scorecard.integrity_issues)}")
            print(f"Reports generated in: {output_dir}")

        except Exception as e:
            logger.error(f"Error processing database {db_config['name']}: {e}")
            print(f"Error processing database {db_config['name']}: {e}", file=sys.stderr)
            continue

    if not scorecards:
        print("No databases processed successfully", file=sys.stderr)
        sys.exit(1)

    overall_avg = sum(s.overall_score for s in scorecards) / len(scorecards)
    print(f"\nOverall Average Score: {overall_avg:.2%}")


if __name__ == "__main__":
    main()
