"""Performance monitor automation system.

Monitors employee performance metrics, tracks goal completion, generates performance
reviews, and identifies training needs with development plans.
"""

import argparse
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.goal_tracker import GoalTracker
from src.performance_monitor import PerformanceMonitor
from src.review_generator import ReviewGenerator
from src.training_analyzer import TrainingAnalyzer


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/performance_monitor.log"))
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


def add_employee(
    config: dict,
    settings: object,
    employee_id: str,
    name: str,
    email: str,
    department: Optional[str] = None,
    position: Optional[str] = None,
) -> dict:
    """Add an employee.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        employee_id: Employee ID.
        name: Employee name.
        email: Employee email.
        department: Optional department.
        position: Optional position.

    Returns:
        Dictionary with employee information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    employee = db_manager.add_employee(
        employee_id=employee_id,
        name=name,
        email=email,
        department=department,
        position=position,
    )

    logger.info(f"Added employee: {employee.name}", extra={"employee_id": employee.id, "employee_id_str": employee_id})

    return {
        "success": True,
        "employee_id": employee.id,
        "name": employee.name,
        "email": employee.email,
    }


def add_metric(
    config: dict,
    settings: object,
    employee_id: str,
    metric_type: str,
    value: float,
    metric_date: Optional[str] = None,
    target_value: Optional[float] = None,
) -> dict:
    """Add performance metric.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        employee_id: Employee ID.
        metric_type: Metric type.
        value: Metric value.
        metric_date: Optional metric date (YYYY-MM-DD).
        target_value: Optional target value.

    Returns:
        Dictionary with metric information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)

    from src.database import Employee
    employee = (
        db_manager.get_session()
        .query(Employee)
        .filter(Employee.employee_id == employee_id)
        .first()
    )

    if not employee:
        print(f"Error: Employee {employee_id} not found", file=sys.stderr)
        sys.exit(1)

    if metric_date:
        try:
            metric_date_obj = datetime.strptime(metric_date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"Invalid date format: {metric_date}")
            return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}
    else:
        metric_date_obj = date.today()

    metric = db_manager.add_metric(
        employee_id=employee.id,
        metric_type=metric_type,
        metric_date=metric_date_obj,
        value=value,
        target_value=target_value,
    )

    logger.info(f"Added metric: {metric_type}", extra={"metric_id": metric.id, "employee_id": employee.id})

    return {
        "success": True,
        "metric_id": metric.id,
        "metric_type": metric.metric_type,
        "value": metric.value,
    }


def track_goals(
    config: dict,
    settings: object,
    employee_id: Optional[str] = None,
) -> dict:
    """Track goal completion.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        employee_id: Optional employee ID filter.

    Returns:
        Dictionary with goal tracking results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    tracker = GoalTracker(db_manager, config)

    logger.info("Tracking goals", extra={"employee_id": employee_id})

    from src.database import Employee
    if employee_id:
        employee = (
            db_manager.get_session()
            .query(Employee)
            .filter(Employee.employee_id == employee_id)
            .first()
        )
        if employee:
            overdue_goals = tracker.check_overdue_goals(employee_id=employee.id)
            summary = tracker.get_goal_completion_summary(employee.id)
        else:
            return {"success": False, "error": f"Employee {employee_id} not found"}
    else:
        overdue_goals = tracker.check_overdue_goals()
        summary = {"total_employees": len(db_manager.get_employees())}

    logger.info(
        f"Goal tracking completed: {len(overdue_goals)} overdue goals",
        extra={"overdue_count": len(overdue_goals)},
    )

    return {
        "success": True,
        "overdue_goals": len(overdue_goals),
        "summary": summary,
    }


def monitor_performance(
    config: dict,
    settings: object,
    employee_id: str,
) -> dict:
    """Monitor employee performance.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        employee_id: Employee ID.

    Returns:
        Dictionary with performance monitoring results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    monitor = PerformanceMonitor(db_manager, config)

    from src.database import Employee
    employee = (
        db_manager.get_session()
        .query(Employee)
        .filter(Employee.employee_id == employee_id)
        .first()
    )

    if not employee:
        return {"success": False, "error": f"Employee {employee_id} not found"}

    logger.info("Monitoring performance", extra={"employee_id": employee.id})

    performance_score = monitor.calculate_performance_score(employee.id)
    summary = monitor.get_performance_summary(employee.id)

    logger.info(
        f"Performance monitoring completed",
        extra={
            "employee_id": employee.id,
            "overall_score": performance_score.get("overall_score"),
        },
    )

    return {
        "success": True,
        "performance_score": performance_score,
        "summary": summary,
    }


def generate_review(
    config: dict,
    settings: object,
    employee_id: str,
    review_type: str,
    output_path: Optional[str] = None,
) -> dict:
    """Generate performance review.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        employee_id: Employee ID.
        review_type: Review type.
        output_path: Optional output file path.

    Returns:
        Dictionary with review generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    generator = ReviewGenerator(db_manager, config)

    from src.database import Employee
    employee = (
        db_manager.get_session()
        .query(Employee)
        .filter(Employee.employee_id == employee_id)
        .first()
    )

    if not employee:
        return {"success": False, "error": f"Employee {employee_id} not found"}

    logger.info("Generating performance review", extra={"employee_id": employee.id, "review_type": review_type})

    review = generator.generate_review(
        employee_id=employee.id,
        review_type=review_type,
        output_path=output_path,
    )

    logger.info(
        f"Generated performance review: {review.review_id}",
        extra={"review_id": review.review_id, "file_path": review.file_path},
    )

    return {
        "success": True,
        "review_id": review.review_id,
        "file_path": review.file_path,
        "overall_rating": review.overall_rating,
    }


def identify_training_needs(
    config: dict,
    settings: object,
    employee_id: str,
) -> dict:
    """Identify training needs.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        employee_id: Employee ID.

    Returns:
        Dictionary with training needs identification results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    analyzer = TrainingAnalyzer(db_manager, config)

    from src.database import Employee
    employee = (
        db_manager.get_session()
        .query(Employee)
        .filter(Employee.employee_id == employee_id)
        .first()
    )

    if not employee:
        return {"success": False, "error": f"Employee {employee_id} not found"}

    logger.info("Identifying training needs", extra={"employee_id": employee.id})

    training_needs = analyzer.identify_training_needs(employee.id)

    logger.info(
        f"Identified {len(training_needs)} training needs",
        extra={"employee_id": employee.id, "training_needs_count": len(training_needs)},
    )

    return {
        "success": True,
        "training_needs_count": len(training_needs),
        "training_needs": [
            {
                "skill_name": tn.skill_name,
                "skill_category": tn.skill_category,
                "priority": tn.priority,
            }
            for tn in training_needs
        ],
    }


def create_development_plan(
    config: dict,
    settings: object,
    employee_id: str,
    title: Optional[str] = None,
) -> dict:
    """Create development plan.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        employee_id: Employee ID.
        title: Optional plan title.

    Returns:
        Dictionary with development plan creation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    analyzer = TrainingAnalyzer(db_manager, config)

    from src.database import Employee
    employee = (
        db_manager.get_session()
        .query(Employee)
        .filter(Employee.employee_id == employee_id)
        .first()
    )

    if not employee:
        return {"success": False, "error": f"Employee {employee_id} not found"}

    logger.info("Creating development plan", extra={"employee_id": employee.id})

    plan = analyzer.create_development_plan(employee.id, title=title)

    logger.info(
        f"Created development plan: {plan.plan_id}",
        extra={"plan_id": plan.plan_id, "employee_id": employee.id},
    )

    return {
        "success": True,
        "plan_id": plan.plan_id,
        "title": plan.title,
        "start_date": plan.start_date.isoformat(),
        "end_date": plan.end_date.isoformat(),
    }


def main() -> None:
    """Main entry point for performance monitor automation."""
    parser = argparse.ArgumentParser(
        description="Performance monitor automation system"
    )
    parser.add_argument(
        "--add-employee",
        action="store_true",
        help="Add an employee",
    )
    parser.add_argument(
        "--employee-id", help="Employee ID"
    )
    parser.add_argument(
        "--name", help="Employee name"
    )
    parser.add_argument(
        "--email", help="Employee email"
    )
    parser.add_argument(
        "--department", help="Department"
    )
    parser.add_argument(
        "--position", help="Position"
    )
    parser.add_argument(
        "--add-metric",
        action="store_true",
        help="Add performance metric",
    )
    parser.add_argument(
        "--metric-type", help="Metric type"
    )
    parser.add_argument(
        "--value", type=float, help="Metric value"
    )
    parser.add_argument(
        "--metric-date", help="Metric date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--target-value", type=float, help="Target value"
    )
    parser.add_argument(
        "--track-goals",
        action="store_true",
        help="Track goal completion",
    )
    parser.add_argument(
        "--monitor-performance",
        action="store_true",
        help="Monitor employee performance",
    )
    parser.add_argument(
        "--generate-review",
        action="store_true",
        help="Generate performance review",
    )
    parser.add_argument(
        "--review-type",
        choices=["quarterly", "annual", "mid_year", "probationary"],
        help="Review type",
    )
    parser.add_argument(
        "--output", help="Output file path"
    )
    parser.add_argument(
        "--identify-training",
        action="store_true",
        help="Identify training needs",
    )
    parser.add_argument(
        "--create-plan",
        action="store_true",
        help="Create development plan",
    )
    parser.add_argument(
        "--plan-title", help="Development plan title"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    if not any([
        args.add_employee,
        args.add_metric,
        args.track_goals,
        args.monitor_performance,
        args.generate_review,
        args.identify_training,
        args.create_plan,
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

        if args.add_employee:
            if not all([args.employee_id, args.name, args.email]):
                print(
                    "Error: --employee-id, --name, and --email are required for --add-employee",
                    file=sys.stderr,
                )
                sys.exit(1)

            result = add_employee(
                config=config,
                settings=settings,
                employee_id=args.employee_id,
                name=args.name,
                email=args.email,
                department=args.department,
                position=args.position,
            )

            print(f"\nEmployee added:")
            print(f"ID: {result['employee_id']}")
            print(f"Name: {result['name']}")
            print(f"Email: {result['email']}")

        elif args.add_metric:
            if not all([args.employee_id, args.metric_type, args.value is not None]):
                print(
                    "Error: --employee-id, --metric-type, and --value are required for --add-metric",
                    file=sys.stderr,
                )
                sys.exit(1)

            result = add_metric(
                config=config,
                settings=settings,
                employee_id=args.employee_id,
                metric_type=args.metric_type,
                value=args.value,
                metric_date=args.metric_date,
                target_value=args.target_value,
            )

            if result["success"]:
                print(f"\nMetric added:")
                print(f"Type: {result['metric_type']}")
                print(f"Value: {result['value']}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.track_goals:
            result = track_goals(
                config=config,
                settings=settings,
                employee_id=args.employee_id,
            )

            if result["success"]:
                print(f"\nGoal Tracking:")
                print(f"Overdue goals: {result['overdue_goals']}")
                if "summary" in result and "total_goals" in result["summary"]:
                    print(f"Total goals: {result['summary']['total_goals']}")
                    print(f"Completed: {result['summary'].get('completed', 0)}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.monitor_performance:
            if not args.employee_id:
                print("Error: --employee-id is required for --monitor-performance", file=sys.stderr)
                sys.exit(1)

            result = monitor_performance(
                config=config,
                settings=settings,
                employee_id=args.employee_id,
            )

            if result["success"]:
                print(f"\nPerformance Monitoring:")
                print(f"Overall Score: {result['performance_score']['overall_score']:.2f}")
                print(f"Rating: {result['performance_score']['rating']}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.generate_review:
            if not all([args.employee_id, args.review_type]):
                print(
                    "Error: --employee-id and --review-type are required for --generate-review",
                    file=sys.stderr,
                )
                sys.exit(1)

            result = generate_review(
                config=config,
                settings=settings,
                employee_id=args.employee_id,
                review_type=args.review_type,
                output_path=args.output,
            )

            if result["success"]:
                print(f"\nPerformance Review Generated:")
                print(f"Review ID: {result['review_id']}")
                print(f"File: {result['file_path']}")
                print(f"Overall Rating: {result.get('overall_rating', 'N/A')}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.identify_training:
            if not args.employee_id:
                print("Error: --employee-id is required for --identify-training", file=sys.stderr)
                sys.exit(1)

            result = identify_training_needs(
                config=config,
                settings=settings,
                employee_id=args.employee_id,
            )

            if result["success"]:
                print(f"\nTraining Needs Identified: {result['training_needs_count']}")
                for tn in result["training_needs"][:5]:
                    print(f"  - {tn['skill_name']} ({tn['priority']} priority)")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.create_plan:
            if not args.employee_id:
                print("Error: --employee-id is required for --create-plan", file=sys.stderr)
                sys.exit(1)

            result = create_development_plan(
                config=config,
                settings=settings,
                employee_id=args.employee_id,
                title=args.plan_title,
            )

            if result["success"]:
                print(f"\nDevelopment Plan Created:")
                print(f"Plan ID: {result['plan_id']}")
                print(f"Title: {result['title']}")
                print(f"Duration: {result['start_date']} to {result['end_date']}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

    except Exception as e:
        logger.error(f"Error executing command: {e}", extra={"error": str(e)})
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
