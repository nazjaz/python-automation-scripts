"""Database models and operations for expense processing data."""

from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Date,
    Float,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

Base = declarative_base()


class Employee(Base):
    """Database model for employees."""

    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    department = Column(String(100))
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True, index=True)
    role = Column(String(100), default="employee")
    created_at = Column(DateTime, default=datetime.utcnow)

    expense_reports = relationship("ExpenseReport", back_populates="employee", cascade="all, delete-orphan")
    manager = relationship("Employee", remote_side=[id])

    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, employee_id={self.employee_id}, name={self.name})>"


class ExpenseReport(Base):
    """Database model for expense reports."""

    __tablename__ = "expense_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    report_date = Column(Date, nullable=False, index=True)
    submission_date = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(50), default="pending", index=True)
    total_amount = Column(Float, default=0.0)
    reimbursable_amount = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = relationship("Employee", back_populates="expense_reports")
    expenses = relationship("Expense", back_populates="report", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="report", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<ExpenseReport(id={self.id}, employee_id={self.employee_id}, "
            f"status={self.status}, total_amount={self.total_amount})>"
        )


class Expense(Base):
    """Database model for individual expenses."""

    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("expense_reports.id"), nullable=False, index=True)
    expense_date = Column(Date, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    description = Column(Text)
    merchant = Column(String(255))
    validated = Column(Boolean, default=False, index=True)
    validation_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("ExpenseReport", back_populates="expenses")
    receipts = relationship("Receipt", back_populates="expense", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<Expense(id={self.id}, report_id={self.report_id}, "
            f"category={self.category}, amount={self.amount})>"
        )


class Receipt(Base):
    """Database model for receipts."""

    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))
    extracted_merchant = Column(String(255))
    extracted_date = Column(Date)
    extracted_amount = Column(Float)
    extracted_category = Column(String(100))
    extraction_confidence = Column(Float)
    ocr_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    expense = relationship("Expense", back_populates="receipts")

    def __repr__(self) -> str:
        return (
            f"<Receipt(id={self.id}, expense_id={self.expense_id}, "
            f"file_path={self.file_path}, extracted_amount={self.extracted_amount})>"
        )


class Policy(Base):
    """Database model for expense policies."""

    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(100), nullable=False, index=True)
    max_amount = Column(Float)
    max_daily_amount = Column(Float)
    require_receipt = Column(Boolean, default=True)
    require_approval = Column(Boolean, default=False)
    approval_threshold = Column(Float)
    description = Column(Text)
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<Policy(id={self.id}, category={self.category}, "
            f"max_amount={self.max_amount}, active={self.active})>"
        )


class Approval(Base):
    """Database model for approvals."""

    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("expense_reports.id"), nullable=False, index=True)
    approver_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    approval_level = Column(Integer, default=1)
    status = Column(String(50), default="pending", index=True)
    comments = Column(Text)
    approved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    report = relationship("ExpenseReport", back_populates="approvals")
    approver = relationship("Employee")

    def __repr__(self) -> str:
        return (
            f"<Approval(id={self.id}, report_id={self.report_id}, "
            f"approver_id={self.approver_id}, status={self.status})>"
        )


class DatabaseManager:
    """Manages database operations for expense processing data."""

    def __init__(self, database_url: str) -> None:
        """Initialize database manager.

        Args:
            database_url: SQLAlchemy database URL.
        """
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        """Create all database tables if they don't exist."""
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get database session.

        Returns:
            SQLAlchemy session object.
        """
        return self.SessionLocal()

    def add_employee(
        self,
        employee_id: str,
        name: str,
        email: str,
        department: Optional[str] = None,
        manager_id: Optional[int] = None,
        role: str = "employee",
    ) -> Employee:
        """Add or update employee.

        Args:
            employee_id: Employee ID.
            name: Employee name.
            email: Employee email.
            department: Optional department.
            manager_id: Optional manager ID.
            role: Employee role.

        Returns:
            Employee object.
        """
        session = self.get_session()
        try:
            employee = (
                session.query(Employee)
                .filter(Employee.employee_id == employee_id)
                .first()
            )

            if employee is None:
                employee = Employee(
                    employee_id=employee_id,
                    name=name,
                    email=email,
                    department=department,
                    manager_id=manager_id,
                    role=role,
                )
                session.add(employee)
            else:
                employee.name = name
                employee.email = email
                employee.department = department
                employee.manager_id = manager_id
                employee.role = role

            session.commit()
            session.refresh(employee)
            return employee
        finally:
            session.close()

    def add_expense_report(
        self,
        employee_id: int,
        report_date: date,
        description: Optional[str] = None,
        currency: str = "USD",
    ) -> ExpenseReport:
        """Add expense report.

        Args:
            employee_id: Employee ID.
            report_date: Report date.
            description: Optional description.
            currency: Currency code.

        Returns:
            ExpenseReport object.
        """
        session = self.get_session()
        try:
            report = ExpenseReport(
                employee_id=employee_id,
                report_date=report_date,
                description=description,
                currency=currency,
            )
            session.add(report)
            session.commit()
            session.refresh(report)
            return report
        finally:
            session.close()

    def add_expense(
        self,
        report_id: int,
        expense_date: date,
        category: str,
        amount: float,
        description: Optional[str] = None,
        merchant: Optional[str] = None,
        currency: str = "USD",
    ) -> Expense:
        """Add expense.

        Args:
            report_id: Report ID.
            expense_date: Expense date.
            category: Expense category.
            amount: Expense amount.
            description: Optional description.
            merchant: Optional merchant name.
            currency: Currency code.

        Returns:
            Expense object.
        """
        session = self.get_session()
        try:
            expense = Expense(
                report_id=report_id,
                expense_date=expense_date,
                category=category,
                amount=amount,
                description=description,
                merchant=merchant,
                currency=currency,
            )
            session.add(expense)
            session.commit()
            session.refresh(expense)
            return expense
        finally:
            session.close()

    def add_receipt(
        self,
        expense_id: int,
        file_path: str,
        file_type: Optional[str] = None,
        extracted_merchant: Optional[str] = None,
        extracted_date: Optional[date] = None,
        extracted_amount: Optional[float] = None,
        extracted_category: Optional[str] = None,
        extraction_confidence: Optional[float] = None,
        ocr_text: Optional[str] = None,
    ) -> Receipt:
        """Add receipt.

        Args:
            expense_id: Expense ID.
            file_path: Receipt file path.
            file_type: Optional file type.
            extracted_merchant: Optional extracted merchant.
            extracted_date: Optional extracted date.
            extracted_amount: Optional extracted amount.
            extracted_category: Optional extracted category.
            extraction_confidence: Optional extraction confidence.
            ocr_text: Optional OCR text.

        Returns:
            Receipt object.
        """
        session = self.get_session()
        try:
            receipt = Receipt(
                expense_id=expense_id,
                file_path=file_path,
                file_type=file_type,
                extracted_merchant=extracted_merchant,
                extracted_date=extracted_date,
                extracted_amount=extracted_amount,
                extracted_category=extracted_category,
                extraction_confidence=extraction_confidence,
                ocr_text=ocr_text,
            )
            session.add(receipt)
            session.commit()
            session.refresh(receipt)
            return receipt
        finally:
            session.close()

    def add_policy(
        self,
        category: str,
        max_amount: Optional[float] = None,
        max_daily_amount: Optional[float] = None,
        require_receipt: bool = True,
        require_approval: bool = False,
        approval_threshold: Optional[float] = None,
        description: Optional[str] = None,
    ) -> Policy:
        """Add or update policy.

        Args:
            category: Expense category.
            max_amount: Optional maximum amount.
            max_daily_amount: Optional maximum daily amount.
            require_receipt: Whether receipt is required.
            require_approval: Whether approval is required.
            approval_threshold: Optional approval threshold.
            description: Optional description.

        Returns:
            Policy object.
        """
        session = self.get_session()
        try:
            policy = (
                session.query(Policy)
                .filter(Policy.category == category, Policy.active == True)
                .first()
            )

            if policy is None:
                policy = Policy(
                    category=category,
                    max_amount=max_amount,
                    max_daily_amount=max_daily_amount,
                    require_receipt=require_receipt,
                    require_approval=require_approval,
                    approval_threshold=approval_threshold,
                    description=description,
                )
                session.add(policy)
            else:
                policy.max_amount = max_amount
                policy.max_daily_amount = max_daily_amount
                policy.require_receipt = require_receipt
                policy.require_approval = require_approval
                policy.approval_threshold = approval_threshold
                policy.description = description
                policy.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(policy)
            return policy
        finally:
            session.close()

    def add_approval(
        self,
        report_id: int,
        approver_id: int,
        approval_level: int = 1,
        status: str = "pending",
        comments: Optional[str] = None,
    ) -> Approval:
        """Add approval.

        Args:
            report_id: Report ID.
            approver_id: Approver employee ID.
            approval_level: Approval level.
            status: Approval status.
            comments: Optional comments.

        Returns:
            Approval object.
        """
        session = self.get_session()
        try:
            approval = Approval(
                report_id=report_id,
                approver_id=approver_id,
                approval_level=approval_level,
                status=status,
                comments=comments,
            )
            session.add(approval)
            session.commit()
            session.refresh(approval)
            return approval
        finally:
            session.close()

    def get_expense_reports(
        self,
        employee_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ExpenseReport]:
        """Get expense reports with optional filtering.

        Args:
            employee_id: Optional employee ID filter.
            status: Optional status filter.
            limit: Optional limit on number of results.

        Returns:
            List of ExpenseReport objects.
        """
        session = self.get_session()
        try:
            query = session.query(ExpenseReport)

            if employee_id:
                query = query.filter(ExpenseReport.employee_id == employee_id)

            if status:
                query = query.filter(ExpenseReport.status == status)

            query = query.order_by(ExpenseReport.submission_date.desc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_policy(self, category: str) -> Optional[Policy]:
        """Get active policy for category.

        Args:
            category: Expense category.

        Returns:
            Policy object or None.
        """
        session = self.get_session()
        try:
            return (
                session.query(Policy)
                .filter(Policy.category == category, Policy.active == True)
                .first()
            )
        finally:
            session.close()
