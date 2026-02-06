"""Portfolio generator automation system.

Automatically generates personalized investment portfolios based on risk tolerance,
financial goals, and market conditions, with rebalancing recommendations.
"""

import argparse
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.goal_calculator import GoalCalculator
from src.portfolio_generator import PortfolioGenerator
from src.rebalancing_engine import RebalancingEngine
from src.report_generator import ReportGenerator
from src.risk_analyzer import RiskAnalyzer


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/portfolio_generator.log"))
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


def add_investor(
    config: dict,
    settings: object,
    investor_id: str,
    name: str,
    email: str,
    risk_tolerance: str,
    age: Optional[int] = None,
    horizon_years: Optional[int] = None,
) -> dict:
    """Add an investor.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        investor_id: Investor ID.
        name: Investor name.
        email: Investor email.
        risk_tolerance: Risk tolerance level.
        age: Optional age.
        horizon_years: Optional investment horizon in years.

    Returns:
        Dictionary with investor information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    db_manager.create_tables()

    investor = db_manager.add_investor(
        investor_id=investor_id,
        name=name,
        email=email,
        risk_tolerance=risk_tolerance,
        age=age,
        investment_horizon_years=horizon_years,
    )

    logger.info(f"Added investor: {investor.name}", extra={"investor_id": investor.id, "investor_id_str": investor_id})

    return {
        "success": True,
        "investor_id": investor.id,
        "name": investor.name,
        "risk_tolerance": investor.risk_tolerance,
    }


def add_goal(
    config: dict,
    settings: object,
    investor_id: int,
    goal_type: str,
    target_amount: float,
    target_date: str,
    description: Optional[str] = None,
    priority: str = "medium",
) -> dict:
    """Add a financial goal.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        investor_id: Investor ID.
        goal_type: Goal type.
        target_amount: Target amount.
        target_date: Target date (YYYY-MM-DD).
        description: Optional description.
        priority: Priority level.

    Returns:
        Dictionary with goal information.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)

    try:
        target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        logger.error(f"Invalid date format: {target_date}")
        return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}

    goal = db_manager.add_goal(
        investor_id=investor_id,
        goal_type=goal_type,
        target_amount=target_amount,
        target_date=target_date_obj,
        description=description,
        priority=priority,
    )

    logger.info(f"Added goal: {goal.goal_type}", extra={"goal_id": goal.id, "investor_id": investor_id})

    return {
        "success": True,
        "goal_id": goal.id,
        "goal_type": goal.goal_type,
        "target_amount": goal.target_amount,
    }


def generate_portfolio(
    config: dict,
    settings: object,
    investor_id: int,
    portfolio_name: str,
    initial_investment: float,
    risk_tolerance: Optional[str] = None,
) -> dict:
    """Generate personalized portfolio.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        investor_id: Investor ID.
        portfolio_name: Portfolio name.
        initial_investment: Initial investment amount.
        risk_tolerance: Optional risk tolerance.

    Returns:
        Dictionary with portfolio generation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    generator = PortfolioGenerator(db_manager, config)

    logger.info("Generating portfolio", extra={"investor_id": investor_id, "initial_investment": initial_investment})

    portfolio = generator.generate_portfolio(
        investor_id=investor_id,
        portfolio_name=portfolio_name,
        initial_investment=initial_investment,
        risk_tolerance=risk_tolerance,
    )

    logger.info(
        f"Generated portfolio: {portfolio.name}",
        extra={"portfolio_id": portfolio.id, "total_value": portfolio.total_value},
    )

    return {
        "success": True,
        "portfolio_id": portfolio.id,
        "name": portfolio.name,
        "total_value": portfolio.total_value,
    }


def analyze_risk(
    config: dict,
    settings: object,
    investor_id: int,
) -> dict:
    """Analyze investor risk tolerance.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        investor_id: Investor ID.

    Returns:
        Dictionary with risk analysis results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    analyzer = RiskAnalyzer(db_manager, config)

    logger.info("Analyzing risk tolerance", extra={"investor_id": investor_id})

    result = analyzer.analyze_risk_tolerance(investor_id)

    logger.info(
        f"Risk analysis completed",
        extra={
            "investor_id": investor_id,
            "recommended_tolerance": result.get("recommended_risk_tolerance"),
        },
    )

    return result


def calculate_goals(
    config: dict,
    settings: object,
    investor_id: int,
) -> dict:
    """Calculate portfolio requirements for goals.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        investor_id: Investor ID.

    Returns:
        Dictionary with goal calculation results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    calculator = GoalCalculator(db_manager, config)

    logger.info("Calculating goal requirements", extra={"investor_id": investor_id})

    result = calculator.calculate_portfolio_requirements(investor_id)

    logger.info(
        f"Goal calculation completed",
        extra={
            "investor_id": investor_id,
            "total_required": result.get("total_required_investment"),
        },
    )

    return result


def check_rebalancing(
    config: dict,
    settings: object,
    portfolio_id: int,
) -> dict:
    """Check if portfolio needs rebalancing.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        portfolio_id: Portfolio ID.

    Returns:
        Dictionary with rebalancing check results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    engine = RebalancingEngine(db_manager, config)

    logger.info("Checking rebalancing needs", extra={"portfolio_id": portfolio_id})

    needs_rebalancing = engine.check_rebalancing_needed(portfolio_id)

    if needs_rebalancing:
        recommendations = engine.generate_rebalancing_recommendations(portfolio_id)
    else:
        recommendations = []

    logger.info(
        f"Rebalancing check completed",
        extra={
            "portfolio_id": portfolio_id,
            "needs_rebalancing": needs_rebalancing,
            "recommendation_count": len(recommendations),
        },
    )

    return {
        "success": True,
        "needs_rebalancing": needs_rebalancing,
        "recommendation_count": len(recommendations),
        "recommendations": [
            {
                "id": r.id,
                "asset_symbol": r.asset_symbol,
                "action_type": r.action_type,
                "recommended_action": r.recommended_action,
                "amount_change": r.amount_change,
            }
            for r in recommendations
        ],
    }


def generate_report(
    config: dict,
    settings: object,
    portfolio_id: int,
    format: str = "html",
) -> dict:
    """Generate portfolio report.

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        portfolio_id: Portfolio ID.
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

    logger.info("Generating portfolio report", extra={"format": format, "portfolio_id": portfolio_id})

    if format == "html":
        report_path = generator.generate_html_report(portfolio_id)
    else:
        report_path = generator.generate_csv_report(portfolio_id)

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
    """Main entry point for portfolio generator automation."""
    parser = argparse.ArgumentParser(
        description="Portfolio generator automation system"
    )
    parser.add_argument(
        "--add-investor",
        action="store_true",
        help="Add an investor",
    )
    parser.add_argument(
        "--investor-id", help="Investor ID"
    )
    parser.add_argument(
        "--name", help="Investor name"
    )
    parser.add_argument(
        "--email", help="Investor email"
    )
    parser.add_argument(
        "--risk-tolerance",
        choices=["conservative", "moderate", "aggressive"],
        help="Risk tolerance level",
    )
    parser.add_argument(
        "--age", type=int, help="Investor age"
    )
    parser.add_argument(
        "--horizon-years", type=int, help="Investment horizon in years"
    )
    parser.add_argument(
        "--add-goal",
        action="store_true",
        help="Add a financial goal",
    )
    parser.add_argument(
        "--goal-type",
        choices=["retirement", "education", "house_purchase", "emergency_fund", "wealth_building"],
        help="Goal type",
    )
    parser.add_argument(
        "--target-amount", type=float, help="Target amount"
    )
    parser.add_argument(
        "--target-date", help="Target date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--priority",
        choices=["low", "medium", "high"],
        default="medium",
        help="Goal priority",
    )
    parser.add_argument(
        "--generate-portfolio",
        action="store_true",
        help="Generate personalized portfolio",
    )
    parser.add_argument(
        "--portfolio-name", help="Portfolio name"
    )
    parser.add_argument(
        "--initial-investment", type=float, help="Initial investment amount"
    )
    parser.add_argument(
        "--analyze-risk",
        action="store_true",
        help="Analyze investor risk tolerance",
    )
    parser.add_argument(
        "--calculate-goals",
        action="store_true",
        help="Calculate portfolio requirements for goals",
    )
    parser.add_argument(
        "--check-rebalancing",
        action="store_true",
        help="Check if portfolio needs rebalancing",
    )
    parser.add_argument(
        "--portfolio-id", type=int, help="Portfolio ID"
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate portfolio report",
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
        args.add_investor,
        args.add_goal,
        args.generate_portfolio,
        args.analyze_risk,
        args.calculate_goals,
        args.check_rebalancing,
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

        if args.add_investor:
            if not all([args.investor_id, args.name, args.email, args.risk_tolerance]):
                print(
                    "Error: --investor-id, --name, --email, and --risk-tolerance are required for --add-investor",
                    file=sys.stderr,
                )
                sys.exit(1)

            result = add_investor(
                config=config,
                settings=settings,
                investor_id=args.investor_id,
                name=args.name,
                email=args.email,
                risk_tolerance=args.risk_tolerance,
                age=args.age,
                horizon_years=args.horizon_years,
            )

            print(f"\nInvestor added:")
            print(f"ID: {result['investor_id']}")
            print(f"Name: {result['name']}")
            print(f"Risk Tolerance: {result['risk_tolerance']}")

        elif args.add_goal:
            if not all([args.investor_id, args.goal_type, args.target_amount, args.target_date]):
                print(
                    "Error: --investor-id, --goal-type, --target-amount, and --target-date are required for --add-goal",
                    file=sys.stderr,
                )
                sys.exit(1)

            from src.database import Investor
            investor = (
                db_manager.get_session()
                .query(Investor)
                .filter(Investor.investor_id == args.investor_id)
                .first()
            )

            if not investor:
                print(f"Error: Investor {args.investor_id} not found", file=sys.stderr)
                sys.exit(1)

            result = add_goal(
                config=config,
                settings=settings,
                investor_id=investor.id,
                goal_type=args.goal_type,
                target_amount=args.target_amount,
                target_date=args.target_date,
                description=None,
                priority=args.priority,
            )

            if result["success"]:
                print(f"\nGoal added:")
                print(f"Goal ID: {result['goal_id']}")
                print(f"Type: {result['goal_type']}")
                print(f"Target: ${result['target_amount']:.2f}")
            else:
                print(f"Error: {result.get('error')}", file=sys.stderr)
                sys.exit(1)

        elif args.generate_portfolio:
            if not all([args.investor_id, args.portfolio_name, args.initial_investment]):
                print(
                    "Error: --investor-id, --portfolio-name, and --initial-investment are required for --generate-portfolio",
                    file=sys.stderr,
                )
                sys.exit(1)

            from src.database import Investor
            investor = (
                db_manager.get_session()
                .query(Investor)
                .filter(Investor.investor_id == args.investor_id)
                .first()
            )

            if not investor:
                print(f"Error: Investor {args.investor_id} not found", file=sys.stderr)
                sys.exit(1)

            result = generate_portfolio(
                config=config,
                settings=settings,
                investor_id=investor.id,
                portfolio_name=args.portfolio_name,
                initial_investment=args.initial_investment,
                risk_tolerance=args.risk_tolerance,
            )

            print(f"\nPortfolio generated:")
            print(f"Portfolio ID: {result['portfolio_id']}")
            print(f"Name: {result['name']}")
            print(f"Total Value: ${result['total_value']:.2f}")

        elif args.analyze_risk:
            if not args.investor_id:
                print("Error: --investor-id is required for --analyze-risk", file=sys.stderr)
                sys.exit(1)

            from src.database import Investor
            investor = (
                db_manager.get_session()
                .query(Investor)
                .filter(Investor.investor_id == args.investor_id)
                .first()
            )

            if not investor:
                print(f"Error: Investor {args.investor_id} not found", file=sys.stderr)
                sys.exit(1)

            result = analyze_risk(
                config=config,
                settings=settings,
                investor_id=investor.id,
            )

            print(f"\nRisk Analysis:")
            print(f"Current Tolerance: {result.get('current_risk_tolerance')}")
            print(f"Recommended Tolerance: {result.get('recommended_risk_tolerance')}")
            print(f"Risk Score: {result.get('risk_score', 0):.2f}")

        elif args.calculate_goals:
            if not args.investor_id:
                print("Error: --investor-id is required for --calculate-goals", file=sys.stderr)
                sys.exit(1)

            from src.database import Investor
            investor = (
                db_manager.get_session()
                .query(Investor)
                .filter(Investor.investor_id == args.investor_id)
                .first()
            )

            if not investor:
                print(f"Error: Investor {args.investor_id} not found", file=sys.stderr)
                sys.exit(1)

            result = calculate_goals(
                config=config,
                settings=settings,
                investor_id=investor.id,
            )

            if "error" in result:
                print(f"Error: {result['error']}", file=sys.stderr)
                sys.exit(1)

            print(f"\nGoal Requirements:")
            print(f"Total Required: ${result.get('total_required_investment', 0):.2f}")
            for goal in result.get("goals", []):
                print(f"  {goal['goal_type']}: ${goal['required_investment']:.2f}")

        elif args.check_rebalancing:
            if not args.portfolio_id:
                print("Error: --portfolio-id is required for --check-rebalancing", file=sys.stderr)
                sys.exit(1)

            result = check_rebalancing(
                config=config,
                settings=settings,
                portfolio_id=args.portfolio_id,
            )

            print(f"\nRebalancing Check:")
            print(f"Needs Rebalancing: {result['needs_rebalancing']}")
            print(f"Recommendations: {result['recommendation_count']}")
            for rec in result["recommendations"][:5]:
                print(f"  - {rec['recommended_action']}")

        elif args.generate_report:
            if not args.portfolio_id:
                print("Error: --portfolio-id is required for --generate-report", file=sys.stderr)
                sys.exit(1)

            result = generate_report(
                config=config,
                settings=settings,
                portfolio_id=args.portfolio_id,
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
