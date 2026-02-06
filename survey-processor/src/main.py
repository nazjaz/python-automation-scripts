"""Customer survey processing automation system.

Processes customer surveys by analyzing responses, identifying trends,
calculating satisfaction scores, and generating executive summaries with insights.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.response_processor import ResponseProcessor
from src.survey_analyzer import SurveyAnalyzer
from src.trend_identifier import TrendIdentifier
from src.satisfaction_calculator import SatisfactionCalculator
from src.summary_generator import SummaryGenerator
from src.report_generator import ReportGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/survey_processor.log"))
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


def create_survey(
    config: dict,
    settings: object,
    survey_name: str,
    description: Optional[str] = None,
    survey_type: Optional[str] = None,
) -> dict:
    """Create a new survey.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        survey_name: Survey name.
        description: Survey description.
        survey_type: Survey type.

    Returns:
        Dictionary with survey information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    logger.info(f"Creating survey: {survey_name}")

    survey = db_manager.add_survey(
        survey_name=survey_name,
        description=description,
        survey_type=survey_type,
    )

    logger.info(f"Survey created: ID {survey.id}")

    return {
        "success": True,
        "survey_id": survey.id,
        "survey_name": survey.survey_name,
    }


def import_responses(
    config: dict,
    settings: object,
    survey_id: int,
    file_path: Path,
    file_format: str = "csv",
) -> dict:
    """Import responses from file.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        survey_id: Survey ID.
        file_path: Path to response file.
        file_format: File format (csv or json).

    Returns:
        Dictionary with import results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    response_processor = ResponseProcessor(db_manager, config.get("import", {}))

    logger.info(f"Importing responses from {file_format} file: {file_path}")

    if file_format.lower() == "json":
        result = response_processor.import_responses_from_json(survey_id, file_path)
    else:
        result = response_processor.import_responses_from_csv(survey_id, file_path)

    logger.info(f"Imported {result['imported_count']} responses")

    return result


def analyze_survey(
    config: dict,
    settings: object,
    survey_id: int,
) -> dict:
    """Analyze survey responses.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        survey_id: Survey ID.

    Returns:
        Dictionary with analysis results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    analyzer = SurveyAnalyzer(db_manager, config.get("analysis", {}))

    logger.info(f"Analyzing survey {survey_id}")

    analysis_results = analyzer.analyze_survey(survey_id)

    summary_generator = SummaryGenerator(db_manager, config.get("summary", {}))
    insights = summary_generator.generate_insights(survey_id, analysis_results)

    logger.info(f"Analysis completed: {len(analysis_results.get('question_analyses', []))} questions analyzed, {len(insights)} insights generated")

    return {
        "success": True,
        "total_responses": analysis_results.get("total_responses", 0),
        "questions_analyzed": len(analysis_results.get("question_analyses", [])),
        "insights_generated": len(insights),
    }


def identify_trends(
    config: dict,
    settings: object,
    survey_id: int,
) -> dict:
    """Identify trends in survey responses.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        survey_id: Survey ID.

    Returns:
        Dictionary with trend identification results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    trend_identifier = TrendIdentifier(db_manager, config.get("trends", {}))

    logger.info(f"Identifying trends for survey {survey_id}")

    trends = trend_identifier.identify_trends(survey_id)

    logger.info(f"Identified {len(trends)} trends")

    return {
        "success": True,
        "trends_identified": len(trends),
        "trends": trends,
    }


def calculate_satisfaction(
    config: dict,
    settings: object,
    survey_id: int,
) -> dict:
    """Calculate satisfaction scores.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        survey_id: Survey ID.

    Returns:
        Dictionary with satisfaction calculation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    calculator = SatisfactionCalculator(db_manager, config.get("satisfaction", {}))

    logger.info(f"Calculating satisfaction scores for survey {survey_id}")

    result = calculator.calculate_satisfaction_scores(survey_id)
    stats = calculator.get_satisfaction_statistics(survey_id)

    logger.info(f"Satisfaction scores calculated: average {stats.get('average', 0.0):.2f}")

    return {
        "success": True,
        "calculated_count": result.get("calculated_count", 0),
        "average_satisfaction": stats.get("average", 0.0),
        "statistics": stats,
    }


def generate_summary(
    config: dict,
    settings: object,
    survey_id: int,
) -> dict:
    """Generate executive summary.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        survey_id: Survey ID.

    Returns:
        Dictionary with summary generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    summary_generator = SummaryGenerator(db_manager, config.get("summary", {}))

    logger.info(f"Generating executive summary for survey {survey_id}")

    summary = summary_generator.generate_summary(survey_id)

    logger.info("Executive summary generated")

    return {
        "success": True,
        "summary_id": summary.get("id"),
        "satisfaction_score": summary.get("satisfaction_score", 0.0),
        "response_count": summary.get("response_count", 0),
        "key_insights_count": len(summary.get("key_insights", [])),
        "recommendations_count": len(summary.get("recommendations", [])),
    }


def generate_reports(
    config: dict,
    settings: object,
    survey_id: Optional[int] = None,
) -> dict:
    """Generate analysis reports.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        survey_id: Optional survey ID to filter by.

    Returns:
        Dictionary with report generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    report_generator = ReportGenerator(db_manager, config.get("reporting", {}))

    logger.info("Generating survey analysis reports", extra={"survey_id": survey_id})

    reports = report_generator.generate_reports(survey_id=survey_id)

    logger.info(
        f"Reports generated: {len(reports)} report(s) created",
        extra={"report_count": len(reports)},
    )

    return {
        "success": True,
        "reports": {k: str(v) for k, v in reports.items()},
        "survey_id": survey_id,
    }


def main() -> None:
    """Main entry point for survey processing automation."""
    parser = argparse.ArgumentParser(
        description="Customer survey processing automation system"
    )
    parser.add_argument(
        "--create-survey",
        nargs=2,
        metavar=("NAME", "DESCRIPTION"),
        help="Create a new survey",
    )
    parser.add_argument(
        "--import",
        nargs=2,
        metavar=("SURVEY_ID", "FILE"),
        help="Import responses from CSV or JSON file",
    )
    parser.add_argument(
        "--analyze",
        type=int,
        metavar="SURVEY_ID",
        help="Analyze survey responses",
    )
    parser.add_argument(
        "--identify-trends",
        type=int,
        metavar="SURVEY_ID",
        help="Identify trends in survey responses",
    )
    parser.add_argument(
        "--calculate-satisfaction",
        type=int,
        metavar="SURVEY_ID",
        help="Calculate satisfaction scores",
    )
    parser.add_argument(
        "--generate-summary",
        type=int,
        metavar="SURVEY_ID",
        help="Generate executive summary",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate analysis reports",
    )
    parser.add_argument(
        "--survey-id",
        type=int,
        help="Filter by survey ID",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="File format for import (default: csv)",
    )
    parser.add_argument(
        "--survey-type",
        help="Survey type",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([
        args.create_survey,
        args.import,
        args.analyze,
        args.identify_trends,
        args.calculate_satisfaction,
        args.generate_summary,
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
        if args.create_survey:
            name, description = args.create_survey
            result = create_survey(
                config=config,
                settings=settings,
                survey_name=name,
                description=description,
                survey_type=args.survey_type,
            )
            print(f"\nSurvey created:")
            print(f"ID: {result['survey_id']}")
            print(f"Name: {result['survey_name']}")

        if args.import:
            survey_id, file_path = args.import
            result = import_responses(
                config=config,
                settings=settings,
                survey_id=int(survey_id),
                file_path=Path(file_path),
                file_format=args.format,
            )
            print(f"\nResponse import completed:")
            print(f"Imported responses: {result['imported_count']}")
            print(f"File: {result['file_path']}")

        if args.analyze:
            result = analyze_survey(
                config=config,
                settings=settings,
                survey_id=args.analyze,
            )
            print(f"\nSurvey analysis completed:")
            print(f"Total responses: {result['total_responses']}")
            print(f"Questions analyzed: {result['questions_analyzed']}")
            print(f"Insights generated: {result['insights_generated']}")

        if args.identify_trends:
            result = identify_trends(
                config=config,
                settings=settings,
                survey_id=args.identify_trends,
            )
            print(f"\nTrend identification completed:")
            print(f"Trends identified: {result['trends_identified']}")

        if args.calculate_satisfaction:
            result = calculate_satisfaction(
                config=config,
                settings=settings,
                survey_id=args.calculate_satisfaction,
            )
            print(f"\nSatisfaction calculation completed:")
            print(f"Calculated scores: {result['calculated_count']}")
            print(f"Average satisfaction: {result['average_satisfaction']:.2f}/5.0")

        if args.generate_summary:
            result = generate_summary(
                config=config,
                settings=settings,
                survey_id=args.generate_summary,
            )
            print(f"\nExecutive summary generated:")
            print(f"Satisfaction score: {result['satisfaction_score']:.2f}/5.0")
            print(f"Response count: {result['response_count']}")
            print(f"Key insights: {result['key_insights_count']}")
            print(f"Recommendations: {result['recommendations_count']}")

        if args.report:
            result = generate_reports(
                config=config,
                settings=settings,
                survey_id=args.survey_id,
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
