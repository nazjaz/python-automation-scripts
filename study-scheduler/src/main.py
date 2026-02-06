"""Study scheduler automation system.

Automatically generates personalized study schedules based on exam dates,
course load, and learning preferences, with progress tracking and adjustment recommendations.
"""

import argparse
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.progress_tracker import ProgressTracker
from src.recommendation_engine import RecommendationEngine
from src.report_generator import ReportGenerator
from src.schedule_generator import ScheduleGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/study_scheduler.log"))
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


def add_course(
    config: dict,
    settings: object,
    name: str,
    code: str,
    difficulty: str = "medium",
    priority: str = "medium",
    total_hours: float = 0.0,
) -> dict:
    """Add a course.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        name: Course name.
        code: Course code.
        difficulty: Course difficulty.
        priority: Course priority.
        total_hours: Total hours required.

    Returns:
        Dictionary with course information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    course = db_manager.add_course(
        name=name,
        code=code,
        difficulty=difficulty,
        priority=priority,
        total_hours_required=total_hours,
    )

    logger.info(f"Added course: {course.name}", extra={"course_id": course.id, "code": code})

    return {
        "success": True,
        "course_id": course.id,
        "name": course.name,
        "code": course.code,
    }


def add_exam(
    config: dict,
    settings: object,
    course_id: int,
    name: str,
    exam_date: str,
    exam_type: Optional[str] = None,
    weight: Optional[float] = None,
    prep_hours: Optional[float] = None,
) -> dict:
    """Add an exam.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        course_id: Course ID.
        name: Exam name.
        exam_date: Exam date (YYYY-MM-DD).
        exam_type: Optional exam type.
        weight: Optional weight percentage.
        prep_hours: Optional preparation hours required.

    Returns:
        Dictionary with exam information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)

    try:
        exam_date_obj = datetime.strptime(exam_date, "%Y-%m-%d").date()
    except ValueError:
        logger.error(f"Invalid date format: {exam_date}")
        return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}

    exam = db_manager.add_exam(
        course_id=course_id,
        name=name,
        exam_date=exam_date_obj,
        exam_type=exam_type,
        weight_percentage=weight,
        preparation_hours_required=prep_hours,
    )

    logger.info(f"Added exam: {exam.name}", extra={"exam_id": exam.id, "course_id": course_id})

    return {
        "success": True,
        "exam_id": exam.id,
        "name": exam.name,
        "exam_date": exam.exam_date.isoformat(),
    }


def set_preferences(
    config: dict,
    settings: object,
    study_style: Optional[str] = None,
    daily_hours: Optional[float] = None,
    preferred_times: Optional[str] = None,
    break_frequency: Optional[int] = None,
    review_frequency: Optional[int] = None,
) -> dict:
    """Set learning preferences.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        study_style: Optional study style.
        daily_hours: Optional daily study hours.
        preferred_times: Optional preferred study times (comma-separated).
        break_frequency: Optional break frequency in minutes.
        review_frequency: Optional review frequency in days.

    Returns:
        Dictionary with preference information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    preference = db_manager.update_learning_preference(
        study_style=study_style,
        daily_study_hours=daily_hours,
        preferred_study_times=preferred_times,
        break_frequency_minutes=break_frequency,
        review_frequency_days=review_frequency,
    )

    logger.info("Updated learning preferences", extra={"preference_id": preference.id})

    return {
        "success": True,
        "study_style": preference.study_style,
        "daily_study_hours": preference.daily_study_hours,
    }


def generate_schedule(
    config: dict,
    settings: object,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    course_ids: Optional[list] = None,
) -> dict:
    """Generate study schedule.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        start_date: Optional start date (YYYY-MM-DD).
        end_date: Optional end date (YYYY-MM-DD).
        course_ids: Optional list of course IDs.

    Returns:
        Dictionary with schedule generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    generator = ScheduleGenerator(db_manager, config)

    start_date_obj = None
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"Invalid start date format: {start_date}")
            return {"success": False, "error": "Invalid start date format"}

    end_date_obj = None
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"Invalid end date format: {end_date}")
            return {"success": False, "error": "Invalid end date format"}

    logger.info("Generating study schedule", extra={"start_date": start_date, "end_date": end_date})

    schedule = generator.generate_schedule(
        start_date=start_date_obj,
        end_date=end_date_obj,
        course_ids=course_ids,
    )

    logger.info(
        f"Generated study schedule: {len(schedule)} sessions",
        extra={"session_count": len(schedule)},
    )

    return {
        "success": True,
        "session_count": len(schedule),
    }


def track_progress(
    config: dict,
    settings: object,
    session_id: int,
    hours_studied: float,
    completion_percentage: Optional[float] = None,
    topics_mastered: int = 0,
    topics_reviewed: int = 0,
) -> dict:
    """Record study session progress.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        session_id: Study session ID.
        hours_studied: Hours studied.
        completion_percentage: Optional completion percentage.
        topics_mastered: Number of topics mastered.
        topics_reviewed: Number of topics reviewed.

    Returns:
        Dictionary with progress recording results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    tracker = ProgressTracker(db_manager, config)

    logger.info("Recording session progress", extra={"session_id": session_id})

    try:
        progress = tracker.record_session_progress(
            session_id=session_id,
            hours_studied=hours_studied,
            completion_percentage=completion_percentage,
            topics_mastered=topics_mastered,
            topics_reviewed=topics_reviewed,
        )

        logger.info(
            f"Progress recorded for session {session_id}",
            extra={"session_id": session_id, "progress_id": progress.id},
        )

        return {
            "success": True,
            "progress_id": progress.id,
            "completion_percentage": progress.completion_percentage,
        }
    except ValueError as e:
        logger.error(f"Error recording progress: {e}", extra={"session_id": session_id, "error": str(e)})
        return {"success": False, "error": str(e)}


def get_recommendations(
    config: dict,
    settings: object,
    course_id: Optional[int] = None,
    days: int = 7,
) -> dict:
    """Get adjustment recommendations.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        course_id: Optional course ID filter.
        days: Number of days to analyze.

    Returns:
        Dictionary with recommendations.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    engine = RecommendationEngine(db_manager, config)

    logger.info("Generating recommendations", extra={"course_id": course_id, "days": days})

    recommendations = engine.generate_recommendations(course_id=course_id, days=days)

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
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    course_id: Optional[int] = None,
    format: str = "html",
) -> dict:
    """Generate study schedule report.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        start_date: Optional start date (YYYY-MM-DD).
        end_date: Optional end date (YYYY-MM-DD).
        course_id: Optional course ID filter.
        format: Report format (html or csv).

    Returns:
        Dictionary with report path.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    generator = ReportGenerator(db_manager, output_dir="reports")

    start_date_obj = None
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            return {"success": False, "error": "Invalid start date format"}

    end_date_obj = None
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return {"success": False, "error": "Invalid end date format"}

    logger.info("Generating study schedule report", extra={"format": format, "course_id": course_id})

    if format == "html":
        report_path = generator.generate_html_schedule(
            start_date=start_date_obj,
            end_date=end_date_obj,
            course_id=course_id,
        )
    else:
        report_path = generator.generate_csv_schedule(
            start_date=start_date_obj,
            end_date=end_date_obj,
            course_id=course_id,
        )

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
    """Main entry point for study scheduler automation."""
    parser = argparse.ArgumentParser(
        description="Study scheduler automation system"
    )
    parser.add_argument(
        "--add-course",
        action="store_true",
        help="Add a course",
    )
    parser.add_argument(
        "--name", help="Course name or exam name"
    )
    parser.add_argument(
        "--code", help="Course code"
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default="medium",
        help="Course difficulty (default: medium)",
    )
    parser.add_argument(
        "--priority",
        choices=["low", "medium", "high", "critical"],
        default="medium",
        help="Course priority (default: medium)",
    )
    parser.add_argument(
        "--total-hours", type=float, help="Total hours required for course"
    )
    parser.add_argument(
        "--add-exam",
        action="store_true",
        help="Add an exam",
    )
    parser.add_argument(
        "--course-id", type=int, help="Course ID"
    )
    parser.add_argument(
        "--exam-date", help="Exam date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--exam-type", help="Exam type"
    )
    parser.add_argument(
        "--weight", type=float, help="Exam weight percentage"
    )
    parser.add_argument(
        "--prep-hours", type=float, help="Preparation hours required"
    )
    parser.add_argument(
        "--set-preferences",
        action="store_true",
        help="Set learning preferences",
    )
    parser.add_argument(
        "--study-style",
        choices=["visual", "auditory", "kinesthetic", "reading_writing"],
        help="Study style",
    )
    parser.add_argument(
        "--daily-hours", type=float, help="Daily study hours"
    )
    parser.add_argument(
        "--preferred-times", help="Preferred study times (comma-separated, e.g., '09:00,14:00,19:00')"
    )
    parser.add_argument(
        "--break-frequency", type=int, help="Break frequency in minutes"
    )
    parser.add_argument(
        "--review-frequency", type=int, help="Review frequency in days"
    )
    parser.add_argument(
        "--generate-schedule",
        action="store_true",
        help="Generate study schedule",
    )
    parser.add_argument(
        "--start-date", help="Start date for schedule (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date", help="End date for schedule (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--track-progress",
        action="store_true",
        help="Record study session progress",
    )
    parser.add_argument(
        "--session-id", type=int, help="Study session ID"
    )
    parser.add_argument(
        "--hours-studied", type=float, help="Hours studied"
    )
    parser.add_argument(
        "--completion-percentage", type=float, help="Completion percentage (0.0 to 1.0)"
    )
    parser.add_argument(
        "--topics-mastered", type=int, default=0, help="Number of topics mastered"
    )
    parser.add_argument(
        "--topics-reviewed", type=int, default=0, help="Number of topics reviewed"
    )
    parser.add_argument(
        "--get-recommendations",
        action="store_true",
        help="Get adjustment recommendations",
    )
    parser.add_argument(
        "--recommendation-days", type=int, default=7, help="Days to analyze for recommendations"
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate study schedule report",
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
        args.add_course,
        args.add_exam,
        args.set_preferences,
        args.generate_schedule,
        args.track_progress,
        args.get_recommendations,
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
        if args.add_course:
            if not args.name or not args.code:
                print("Error: --name and --code are required for --add-course", file=sys.stderr)
                sys.exit(1)

            result = add_course(
                config=config,
                settings=settings,
                name=args.name,
                code=args.code,
                difficulty=args.difficulty,
                priority=args.priority,
                total_hours=args.total_hours or 0.0,
            )

            print(f"\nCourse added successfully:")
            print(f"ID: {result['course_id']}")
            print(f"Name: {result['name']}")
            print(f"Code: {result['code']}")

        elif args.add_exam:
            if not all([args.course_id, args.name, args.exam_date]):
                print(
                    "Error: --course-id, --name, and --exam-date are required for --add-exam",
                    file=sys.stderr,
                )
                sys.exit(1)

            result = add_exam(
                config=config,
                settings=settings,
                course_id=args.course_id,
                name=args.name,
                exam_date=args.exam_date,
                exam_type=args.exam_type,
                weight=args.weight,
                prep_hours=args.prep_hours,
            )

            if result["success"]:
                print(f"\nExam added successfully:")
                print(f"ID: {result['exam_id']}")
                print(f"Name: {result['name']}")
                print(f"Date: {result['exam_date']}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.set_preferences:
            result = set_preferences(
                config=config,
                settings=settings,
                study_style=args.study_style,
                daily_hours=args.daily_hours,
                preferred_times=args.preferred_times,
                break_frequency=args.break_frequency,
                review_frequency=args.review_frequency,
            )

            print(f"\nPreferences updated:")
            print(f"Study Style: {result.get('study_style', 'Not set')}")
            print(f"Daily Hours: {result.get('daily_study_hours', 'Not set')}")

        elif args.generate_schedule:
            result = generate_schedule(
                config=config,
                settings=settings,
                start_date=args.start_date,
                end_date=args.end_date,
            )

            if result["success"]:
                print(f"\nStudy schedule generated:")
                print(f"Sessions created: {result['session_count']}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.track_progress:
            if not all([args.session_id, args.hours_studied is not None]):
                print(
                    "Error: --session-id and --hours-studied are required for --track-progress",
                    file=sys.stderr,
                )
                sys.exit(1)

            result = track_progress(
                config=config,
                settings=settings,
                session_id=args.session_id,
                hours_studied=args.hours_studied,
                completion_percentage=args.completion_percentage,
                topics_mastered=args.topics_mastered,
                topics_reviewed=args.topics_reviewed,
            )

            if result["success"]:
                print(f"\nProgress recorded:")
                print(f"Completion: {result.get('completion_percentage', 0):.1%}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.get_recommendations:
            result = get_recommendations(
                config=config,
                settings=settings,
                course_id=args.course_id,
                days=args.recommendation_days,
            )

            print(f"\nRecommendations ({result['recommendation_count']}):")
            for rec in result["recommendations"][:5]:
                print(f"  [{rec['priority'].upper()}] {rec['title']}")
                print(f"    {rec['description']}")

        elif args.generate_report:
            result = generate_report(
                config=config,
                settings=settings,
                start_date=args.start_date,
                end_date=args.end_date,
                course_id=args.course_id,
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
