"""Database models and operations for performance monitor data."""

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
    department = Column(String(100), index=True)
    position = Column(String(100))
    manager_id = Column(Integer, ForeignKey("employees.id"))
    hire_date = Column(Date, index=True)
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    manager = relationship("Employee", remote_side=[id], backref="direct_reports")
    metrics = relationship("PerformanceMetric", back_populates="employee", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="employee", cascade="all, delete-orphan")
    reviews = relationship("PerformanceReview", back_populates="employee", cascade="all, delete-orphan")
    training_needs = relationship("TrainingNeed", back_populates="employee", cascade="all, delete-orphan")
    development_plans = relationship("DevelopmentPlan", back_populates="employee", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, employee_id={self.employee_id}, name={self.name})>"


class PerformanceMetric(Base):
    """Database model for performance metrics."""

    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    metric_type = Column(String(100), nullable=False, index=True)
    metric_date = Column(Date, nullable=False, index=True)
    value = Column(Float, nullable=False)
    target_value = Column(Float)
    unit = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="metrics")

    def __repr__(self) -> str:
        return (
            f"<PerformanceMetric(id={self.id}, employee_id={self.employee_id}, "
            f"metric_type={self.metric_type}, value={self.value})>"
        )


class Goal(Base):
    """Database model for employee goals."""

    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    goal_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    goal_type = Column(String(100), nullable=False, index=True)
    target_value = Column(Float)
    current_value = Column(Float, default=0.0)
    unit = Column(String(50))
    start_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=False, index=True)
    status = Column(String(50), default="not_started", index=True)
    completion_percentage = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = relationship("Employee", back_populates="goals")

    def __repr__(self) -> str:
        return (
            f"<Goal(id={self.id}, employee_id={self.employee_id}, "
            f"goal_id={self.goal_id}, status={self.status})>"
        )


class PerformanceReview(Base):
    """Database model for performance reviews."""

    __tablename__ = "performance_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    review_id = Column(String(100), unique=True, nullable=False, index=True)
    review_type = Column(String(100), nullable=False, index=True)
    review_period_start = Column(Date, nullable=False, index=True)
    review_period_end = Column(Date, nullable=False, index=True)
    overall_rating = Column(Float)
    overall_rating_category = Column(String(50), index=True)
    strengths = Column(Text)
    areas_for_improvement = Column(Text)
    recommendations = Column(Text)
    file_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(String(255))

    employee = relationship("Employee", back_populates="reviews")

    def __repr__(self) -> str:
        return (
            f"<PerformanceReview(id={self.id}, employee_id={self.employee_id}, "
            f"review_type={self.review_type}, overall_rating={self.overall_rating})>"
        )


class TrainingNeed(Base):
    """Database model for training needs."""

    __tablename__ = "training_needs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    skill_category = Column(String(100), nullable=False, index=True)
    skill_name = Column(String(255), nullable=False)
    priority = Column(String(50), default="medium", index=True)
    identified_reason = Column(Text)
    current_level = Column(String(50))
    target_level = Column(String(50))
    identified_at = Column(DateTime, default=datetime.utcnow, index=True)
    addressed = Column(Boolean, default=False, index=True)
    addressed_at = Column(DateTime)

    employee = relationship("Employee", back_populates="training_needs")

    def __repr__(self) -> str:
        return (
            f"<TrainingNeed(id={self.id}, employee_id={self.employee_id}, "
            f"skill_name={self.skill_name}, priority={self.priority})>"
        )


class DevelopmentPlan(Base):
    """Database model for development plans."""

    __tablename__ = "development_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    plan_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    objectives = Column(Text)
    milestones = Column(Text)
    resources = Column(Text)
    status = Column(String(50), default="active", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = relationship("Employee", back_populates="development_plans")

    def __repr__(self) -> str:
        return (
            f"<DevelopmentPlan(id={self.id}, employee_id={self.employee_id}, "
            f"plan_id={self.plan_id}, status={self.status})>"
        )


class DatabaseManager:
    """Manages database operations for performance monitor data."""

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
        position: Optional[str] = None,
        manager_id: Optional[int] = None,
        hire_date: Optional[date] = None,
    ) -> Employee:
        """Add or update employee.

        Args:
            employee_id: Employee ID.
            name: Employee name.
            email: Employee email.
            department: Optional department.
            position: Optional position.
            manager_id: Optional manager ID.
            hire_date: Optional hire date.

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
                    position=position,
                    manager_id=manager_id,
                    hire_date=hire_date,
                )
                session.add(employee)
            else:
                employee.name = name
                employee.email = email
                employee.department = department
                employee.position = position
                employee.manager_id = manager_id
                employee.hire_date = hire_date
                employee.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(employee)
            return employee
        finally:
            session.close()

    def add_metric(
        self,
        employee_id: int,
        metric_type: str,
        metric_date: date,
        value: float,
        target_value: Optional[float] = None,
        unit: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> PerformanceMetric:
        """Add performance metric.

        Args:
            employee_id: Employee ID.
            metric_type: Metric type.
            metric_date: Metric date.
            value: Metric value.
            target_value: Optional target value.
            unit: Optional unit.
            notes: Optional notes.

        Returns:
            PerformanceMetric object.
        """
        session = self.get_session()
        try:
            metric = PerformanceMetric(
                employee_id=employee_id,
                metric_type=metric_type,
                metric_date=metric_date,
                value=value,
                target_value=target_value,
                unit=unit,
                notes=notes,
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()

    def add_goal(
        self,
        employee_id: int,
        goal_id: str,
        title: str,
        goal_type: str,
        start_date: date,
        due_date: date,
        description: Optional[str] = None,
        target_value: Optional[float] = None,
        unit: Optional[str] = None,
    ) -> Goal:
        """Add goal.

        Args:
            employee_id: Employee ID.
            goal_id: Goal ID.
            title: Goal title.
            goal_type: Goal type.
            start_date: Start date.
            due_date: Due date.
            description: Optional description.
            target_value: Optional target value.
            unit: Optional unit.

        Returns:
            Goal object.
        """
        session = self.get_session()
        try:
            goal = Goal(
                employee_id=employee_id,
                goal_id=goal_id,
                title=title,
                goal_type=goal_type,
                start_date=start_date,
                due_date=due_date,
                description=description,
                target_value=target_value,
                unit=unit,
            )
            session.add(goal)
            session.commit()
            session.refresh(goal)
            return goal
        finally:
            session.close()

    def add_review(
        self,
        employee_id: int,
        review_id: str,
        review_type: str,
        review_period_start: date,
        review_period_end: date,
        overall_rating: Optional[float] = None,
        overall_rating_category: Optional[str] = None,
        strengths: Optional[str] = None,
        areas_for_improvement: Optional[str] = None,
        recommendations: Optional[str] = None,
        file_path: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> PerformanceReview:
        """Add performance review.

        Args:
            employee_id: Employee ID.
            review_id: Review ID.
            review_type: Review type.
            review_period_start: Review period start date.
            review_period_end: Review period end date.
            overall_rating: Optional overall rating.
            overall_rating_category: Optional rating category.
            strengths: Optional strengths.
            areas_for_improvement: Optional areas for improvement.
            recommendations: Optional recommendations.
            file_path: Optional file path.
            created_by: Optional creator name.

        Returns:
            PerformanceReview object.
        """
        session = self.get_session()
        try:
            review = PerformanceReview(
                employee_id=employee_id,
                review_id=review_id,
                review_type=review_type,
                review_period_start=review_period_start,
                review_period_end=review_period_end,
                overall_rating=overall_rating,
                overall_rating_category=overall_rating_category,
                strengths=strengths,
                areas_for_improvement=areas_for_improvement,
                recommendations=recommendations,
                file_path=file_path,
                created_by=created_by,
            )
            session.add(review)
            session.commit()
            session.refresh(review)
            return review
        finally:
            session.close()

    def add_training_need(
        self,
        employee_id: int,
        skill_category: str,
        skill_name: str,
        priority: str = "medium",
        identified_reason: Optional[str] = None,
        current_level: Optional[str] = None,
        target_level: Optional[str] = None,
    ) -> TrainingNeed:
        """Add training need.

        Args:
            employee_id: Employee ID.
            skill_category: Skill category.
            skill_name: Skill name.
            priority: Priority level.
            identified_reason: Optional reason for identification.
            current_level: Optional current skill level.
            target_level: Optional target skill level.

        Returns:
            TrainingNeed object.
        """
        session = self.get_session()
        try:
            training_need = TrainingNeed(
                employee_id=employee_id,
                skill_category=skill_category,
                skill_name=skill_name,
                priority=priority,
                identified_reason=identified_reason,
                current_level=current_level,
                target_level=target_level,
            )
            session.add(training_need)
            session.commit()
            session.refresh(training_need)
            return training_need
        finally:
            session.close()

    def add_development_plan(
        self,
        employee_id: int,
        plan_id: str,
        title: str,
        start_date: date,
        end_date: date,
        description: Optional[str] = None,
        objectives: Optional[str] = None,
        milestones: Optional[str] = None,
        resources: Optional[str] = None,
    ) -> DevelopmentPlan:
        """Add development plan.

        Args:
            employee_id: Employee ID.
            plan_id: Plan ID.
            title: Plan title.
            start_date: Start date.
            end_date: End date.
            description: Optional description.
            objectives: Optional objectives.
            milestones: Optional milestones.
            resources: Optional resources.

        Returns:
            DevelopmentPlan object.
        """
        session = self.get_session()
        try:
            plan = DevelopmentPlan(
                employee_id=employee_id,
                plan_id=plan_id,
                title=title,
                start_date=start_date,
                end_date=end_date,
                description=description,
                objectives=objectives,
                milestones=milestones,
                resources=resources,
            )
            session.add(plan)
            session.commit()
            session.refresh(plan)
            return plan
        finally:
            session.close()

    def get_employees(
        self,
        active_only: bool = True,
        department: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Employee]:
        """Get employees with optional filtering.

        Args:
            active_only: Whether to return only active employees.
            department: Optional department filter.
            limit: Optional limit on number of results.

        Returns:
            List of Employee objects.
        """
        session = self.get_session()
        try:
            query = session.query(Employee)

            if active_only:
                query = query.filter(Employee.active == True)

            if department:
                query = query.filter(Employee.department == department)

            query = query.order_by(Employee.name)

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_goals(
        self,
        employee_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Goal]:
        """Get goals with optional filtering.

        Args:
            employee_id: Optional employee ID filter.
            status: Optional status filter.
            limit: Optional limit on number of results.

        Returns:
            List of Goal objects.
        """
        session = self.get_session()
        try:
            query = session.query(Goal)

            if employee_id:
                query = query.filter(Goal.employee_id == employee_id)

            if status:
                query = query.filter(Goal.status == status)

            query = query.order_by(Goal.due_date)

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_unaddressed_training_needs(
        self,
        employee_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[TrainingNeed]:
        """Get unaddressed training needs.

        Args:
            employee_id: Optional employee ID filter.
            limit: Optional limit on number of results.

        Returns:
            List of TrainingNeed objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(TrainingNeed)
                .filter(TrainingNeed.addressed == False)
            )

            if employee_id:
                query = query.filter(TrainingNeed.employee_id == employee_id)

            query = query.order_by(TrainingNeed.priority.desc(), TrainingNeed.identified_at.desc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()
