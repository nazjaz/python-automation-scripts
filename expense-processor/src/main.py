"""Expense report processing automation system.

Automatically processes expense reports by extracting receipts, validating expenses
against policies, calculating reimbursements, and routing for approvals.
"""

import argparse
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from src.approval_router import ApprovalRouter
from src.config import get_settings, load_config
from src.database import DatabaseManager
from src.expense_validator import ExpenseValidator
from src.receipt_extractor import ReceiptExtractor
from src.reimbursement_calculator import ReimbursementCalculator
from src.report_generator import ReportGenerator


def setup_logging(log_config: dict) -> None:
    """Configure application logging.

    Args:
        log_config: Logging configuration dictionary.
    """
    from logging.handlers import RotatingFileHandler

    log_file = Path(log_config.get("file", "logs/expense_processor.log"))
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


def process_expense_report(
    config: dict,
    settings: object,
    report_id: int,
) -> dict:
    """Process expense report (validate, calculate, route).

    Args:
        config: Configuration dictionary.
        settings: Application settings object.
        report_id: Report ID.

    Returns:
        Dictionary with processing results.
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager(settings.database.url)
    validator = ExpenseValidator(db_manager, config)
    calculator = ReimbursementCalculator(db_manager, config)
    router = ApprovalRouter(db_manager, config)

    logger.info("Processing expense report", extra={"report_id": report_id})

    validation_result = validator.validate_report(report_id)
    calculation_result = calculator.calculate_reimbursement(report_id)
    approvals = router.route_for_approval(report_id)

    logger.info(
        f"Expense report processed: {report_id}",
        extra={
            "report_id": report_id,
            "valid": validation_result.get("valid"),
            "reimbursable_amount": calculation_result.get("reimbursable_amount"),
        },
    )

    return {
        "success": True,
        "validation": validation_result,
        "calculation": calculation_result,
        "approvals": [{"id": a.id, "status": a.status} for a in approvals],
    }


def main() -> None:
    """Main entry point for expense processor automation."""
    parser = argparse.ArgumentParser(
        description="Expense report processing automation system"
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
        "--manager-id", type=int, help="Manager employee ID"
    )
    parser.add_argument(
        "--role",
        choices=["employee", "manager", "director", "vp"],
        default="employee",
        help="Employee role",
    )
    parser.add_argument(
        "--create-report",
        action="store_true",
        help="Create expense report",
    )
    parser.add_argument(
        "--report-date", help="Report date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--description", help="Report description"
    )
    parser.add_argument(
        "--add-expense",
        action="store_true",
        help="Add expense to report",
    )
    parser.add_argument(
        "--report-id", type=int, help="Report ID"
    )
    parser.add_argument(
        "--expense-date", help="Expense date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--category",
        choices=["meals", "lodging", "transportation", "office_supplies", "training", "other"],
        help="Expense category",
    )
    parser.add_argument(
        "--amount", type=float, help="Expense amount"
    )
    parser.add_argument(
        "--merchant", help="Merchant name"
    )
    parser.add_argument(
        "--extract-receipt",
        action="store_true",
        help="Extract receipt data",
    )
    parser.add_argument(
        "--receipt-file", help="Path to receipt file"
    )
    parser.add_argument(
        "--process-report",
        action="store_true",
        help="Process expense report (validate, calculate, route)",
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate expense report",
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
        args.add_employee,
        args.create_report,
        args.add_expense,
        args.extract_receipt,
        args.process_report,
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

        if args.add_employee:
            if not all([args.employee_id, args.name, args.email]):
                print(
                    "Error: --employee-id, --name, and --email are required for --add-employee",
                    file=sys.stderr,
                )
                sys.exit(1)

            employee = db_manager.add_employee(
                employee_id=args.employee_id,
                name=args.name,
                email=args.email,
                department=args.department,
                manager_id=args.manager_id,
                role=args.role,
            )

            print(f"\nEmployee added:")
            print(f"ID: {employee.id}")
            print(f"Employee ID: {employee.employee_id}")
            print(f"Name: {employee.name}")

        elif args.create_report:
            if not all([args.employee_id, args.report_date]):
                print(
                    "Error: --employee-id and --report-date are required for --create-report",
                    file=sys.stderr,
                )
                sys.exit(1)

            from src.database import Employee
            employee = (
                db_manager.get_session()
                .query(Employee)
                .filter(Employee.employee_id == args.employee_id)
                .first()
            )

            if not employee:
                print(f"Error: Employee {args.employee_id} not found", file=sys.stderr)
                sys.exit(1)

            try:
                report_date = datetime.strptime(args.report_date, "%Y-%m-%d").date()
            except ValueError:
                print("Error: Invalid date format. Use YYYY-MM-DD", file=sys.stderr)
                sys.exit(1)

            report = db_manager.add_expense_report(
                employee_id=employee.id,
                report_date=report_date,
                description=args.description,
            )

            print(f"\nExpense report created:")
            print(f"Report ID: {report.id}")
            print(f"Date: {report.report_date}")

        elif args.add_expense:
            if not all([args.report_id, args.expense_date, args.category, args.amount]):
                print(
                    "Error: --report-id, --expense-date, --category, and --amount are required for --add-expense",
                    file=sys.stderr,
                )
                sys.exit(1)

            try:
                expense_date = datetime.strptime(args.expense_date, "%Y-%m-%d").date()
            except ValueError:
                print("Error: Invalid date format. Use YYYY-MM-DD", file=sys.stderr)
                sys.exit(1)

            expense = db_manager.add_expense(
                report_id=args.report_id,
                expense_date=expense_date,
                category=args.category,
                amount=args.amount,
                description=args.description,
                merchant=args.merchant,
            )

            print(f"\nExpense added:")
            print(f"Expense ID: {expense.id}")
            print(f"Amount: ${expense.amount:.2f}")

        elif args.extract_receipt:
            if not all([args.report_id, args.receipt_file]):
                print(
                    "Error: --report-id and --receipt-file are required for --extract-receipt",
                    file=sys.stderr,
                )
                sys.exit(1)

            from src.database import Expense
            expenses = (
                db_manager.get_session()
                .query(Expense)
                .filter(Expense.report_id == args.report_id)
                .all()
            )

            if not expenses:
                print(f"Error: No expenses found for report {args.report_id}", file=sys.stderr)
                sys.exit(1)

            extractor = ReceiptExtractor(db_manager, config)
            receipt = extractor.extract_from_file(args.receipt_file, expenses[-1].id)

            print(f"\nReceipt extracted:")
            print(f"Receipt ID: {receipt.id}")
            if receipt.extracted_amount:
                print(f"Extracted Amount: ${receipt.extracted_amount:.2f}")
            if receipt.extracted_merchant:
                print(f"Extracted Merchant: {receipt.extracted_merchant}")

        elif args.process_report:
            if not args.report_id:
                print("Error: --report-id is required for --process-report", file=sys.stderr)
                sys.exit(1)

            result = process_expense_report(
                config=config,
                settings=settings,
                report_id=args.report_id,
            )

            print(f"\nReport processed:")
            print(f"Valid: {result['validation'].get('valid')}")
            print(f"Reimbursable: ${result['calculation'].get('reimbursable_amount', 0):.2f}")
            print(f"Approvals: {len(result['approvals'])}")

        elif args.generate_report:
            if not args.report_id:
                print("Error: --report-id is required for --generate-report", file=sys.stderr)
                sys.exit(1)

            generator = ReportGenerator(
                db_manager,
                config,
                output_dir=config.get("reporting", {}).get("output_directory", "reports"),
            )

            if args.format == "html":
                report_path = generator.generate_html_report(args.report_id)
            else:
                report_path = generator.generate_csv_report(args.report_id)

            print(f"\nReport generated:")
            print(f"Format: {args.format.upper()}")
            print(f"Path: {report_path}")

    except Exception as e:
        logger.error(f"Error executing command: {e}", extra={"error": str(e)})
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
