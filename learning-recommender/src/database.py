"""Database models and operations for learning recommendation system."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class User(Base):
    """User in the learning system."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), unique=True, nullable=False)
    username = Column(String(200))
    email = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")
    behaviors = relationship("UserBehavior", back_populates="user", cascade="all, delete-orphan")
    objectives = relationship("LearningObjective", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")


class Course(Base):
    """Course in the learning system."""

    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    course_id = Column(String(100), unique=True, nullable=False)
    course_name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    difficulty_level = Column(String(50))
    estimated_duration = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan")


class Module(Base):
    """Module within a course."""

    __tablename__ = "modules"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    module_name = Column(String(200), nullable=False)
    module_order = Column(Integer, default=0)
    difficulty_level = Column(String(50))
    estimated_duration = Column(Integer)

    course = relationship("Course", back_populates="modules")
    progress = relationship("Progress", back_populates="module", cascade="all, delete-orphan")


class Enrollment(Base):
    """User enrollment in a course."""

    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="in_progress")
    completion_rate = Column(Float, default=0.0)

    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    progress = relationship("Progress", back_populates="enrollment", cascade="all, delete-orphan")


class Progress(Base):
    """User progress in a course module."""

    __tablename__ = "progress"

    id = Column(Integer, primary_key=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    progress_percentage = Column(Float, default=0.0)
    time_spent_minutes = Column(Integer, default=0)
    score = Column(Float, nullable=True)

    enrollment = relationship("Enrollment", back_populates="progress")
    module = relationship("Module", back_populates="progress")


class UserBehavior(Base):
    """User behavior tracking."""

    __tablename__ = "user_behaviors"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    behavior_type = Column(String(100), nullable=False)
    behavior_data = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="behaviors")


class LearningObjective(Base):
    """User learning objective."""

    __tablename__ = "learning_objectives"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    objective_name = Column(String(200), nullable=False)
    objective_type = Column(String(100))
    target_skill = Column(String(200))
    priority = Column(String(20), default="medium")
    target_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="active")

    user = relationship("User", back_populates="objectives")


class Recommendation(Base):
    """Personalized learning recommendation."""

    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    recommendation_type = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    confidence_score = Column(Float)
    difficulty_level = Column(String(50))
    priority = Column(String(20), default="medium")
    generated_at = Column(DateTime, default=datetime.utcnow)
    accepted = Column(String(10), default="false")

    user = relationship("User", back_populates="recommendations")
    course = relationship("Course")


class CompletionRate(Base):
    """Course completion rate metric."""

    __tablename__ = "completion_rates"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    time_window_start = Column(DateTime, nullable=False)
    time_window_end = Column(DateTime, nullable=False)
    total_enrollments = Column(Integer, default=0)
    completed_enrollments = Column(Integer, default=0)
    completion_rate = Column(Float)
    average_completion_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course")


class DatabaseManager:
    """Database operations manager."""

    def __init__(self, database_url: str):
        """Initialize database manager.

        Args:
            database_url: SQLAlchemy database URL.
        """
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(self.engine)

    def get_session(self):
        """Get database session.

        Returns:
            Database session object.
        """
        return self.SessionLocal()

    def add_user(
        self, user_id: str, username: Optional[str] = None, email: Optional[str] = None
    ) -> User:
        """Add a new user.

        Args:
            user_id: User identifier.
            username: Username.
            email: Email address.

        Returns:
            Created User object.
        """
        session = self.get_session()
        try:
            user = User(user_id=user_id, username=username, email=email)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by user ID.

        Args:
            user_id: User identifier.

        Returns:
            User object or None.
        """
        session = self.get_session()
        try:
            return session.query(User).filter(User.user_id == user_id).first()
        finally:
            session.close()

    def add_course(
        self,
        course_id: str,
        course_name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        estimated_duration: Optional[int] = None,
    ) -> Course:
        """Add a new course.

        Args:
            course_id: Course identifier.
            course_name: Course name.
            description: Course description.
            category: Course category.
            difficulty_level: Difficulty level (beginner, intermediate, advanced).
            estimated_duration: Estimated duration in minutes.

        Returns:
            Created Course object.
        """
        session = self.get_session()
        try:
            course = Course(
                course_id=course_id,
                course_name=course_name,
                description=description,
                category=category,
                difficulty_level=difficulty_level,
                estimated_duration=estimated_duration,
            )
            session.add(course)
            session.commit()
            session.refresh(course)
            return course
        finally:
            session.close()

    def get_course(self, course_id: str) -> Optional[Course]:
        """Get course by course ID.

        Args:
            course_id: Course identifier.

        Returns:
            Course object or None.
        """
        session = self.get_session()
        try:
            return session.query(Course).filter(Course.course_id == course_id).first()
        finally:
            session.close()

    def add_enrollment(
        self, user_id: int, course_id: int
    ) -> Enrollment:
        """Add user enrollment.

        Args:
            user_id: User ID.
            course_id: Course ID.

        Returns:
            Created Enrollment object.
        """
        session = self.get_session()
        try:
            enrollment = Enrollment(user_id=user_id, course_id=course_id)
            session.add(enrollment)
            session.commit()
            session.refresh(enrollment)
            return enrollment
        finally:
            session.close()

    def get_user_enrollments(self, user_id: int) -> List[Enrollment]:
        """Get all enrollments for a user.

        Args:
            user_id: User ID.

        Returns:
            List of Enrollment objects.
        """
        session = self.get_session()
        try:
            return (
                session.query(Enrollment)
                .filter(Enrollment.user_id == user_id)
                .all()
            )
        finally:
            session.close()

    def update_enrollment_completion(
        self, enrollment_id: int, completion_rate: float, completed: bool = False
    ) -> None:
        """Update enrollment completion.

        Args:
            enrollment_id: Enrollment ID.
            completion_rate: Completion rate (0.0 to 1.0).
            completed: Whether course is completed.
        """
        session = self.get_session()
        try:
            enrollment = session.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
            if enrollment:
                enrollment.completion_rate = completion_rate
                if completed:
                    enrollment.status = "completed"
                    enrollment.completed_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()

    def add_progress(
        self,
        enrollment_id: int,
        module_id: int,
        progress_percentage: float,
        time_spent_minutes: int = 0,
        score: Optional[float] = None,
    ) -> Progress:
        """Add or update progress.

        Args:
            enrollment_id: Enrollment ID.
            module_id: Module ID.
            progress_percentage: Progress percentage (0.0 to 1.0).
            time_spent_minutes: Time spent in minutes.
            score: Optional score.

        Returns:
            Created or updated Progress object.
        """
        session = self.get_session()
        try:
            existing = (
                session.query(Progress)
                .filter(
                    Progress.enrollment_id == enrollment_id,
                    Progress.module_id == module_id,
                )
                .first()
            )

            if existing:
                existing.progress_percentage = progress_percentage
                existing.time_spent_minutes = time_spent_minutes
                if score is not None:
                    existing.score = score
                if progress_percentage >= 1.0:
                    existing.completed_at = datetime.utcnow()
                session.commit()
                session.refresh(existing)
                return existing
            else:
                progress = Progress(
                    enrollment_id=enrollment_id,
                    module_id=module_id,
                    progress_percentage=progress_percentage,
                    time_spent_minutes=time_spent_minutes,
                    score=score,
                )
                if progress_percentage >= 1.0:
                    progress.completed_at = datetime.utcnow()
                session.add(progress)
                session.commit()
                session.refresh(progress)
                return progress
        finally:
            session.close()

    def add_user_behavior(
        self,
        user_id: int,
        behavior_type: str,
        behavior_data: Optional[str] = None,
    ) -> UserBehavior:
        """Add user behavior.

        Args:
            user_id: User ID.
            behavior_type: Behavior type (view, click, search, etc.).
            behavior_data: Behavior data as JSON string.

        Returns:
            Created UserBehavior object.
        """
        session = self.get_session()
        try:
            behavior = UserBehavior(
                user_id=user_id,
                behavior_type=behavior_type,
                behavior_data=behavior_data,
            )
            session.add(behavior)
            session.commit()
            session.refresh(behavior)
            return behavior
        finally:
            session.close()

    def get_user_behaviors(
        self, user_id: int, behavior_type: Optional[str] = None, limit: Optional[int] = None
    ) -> List[UserBehavior]:
        """Get user behaviors.

        Args:
            user_id: User ID.
            behavior_type: Optional behavior type filter.
            limit: Maximum number of behaviors to return.

        Returns:
            List of UserBehavior objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(UserBehavior)
                .filter(UserBehavior.user_id == user_id)
                .order_by(UserBehavior.timestamp.desc())
            )
            if behavior_type:
                query = query.filter(UserBehavior.behavior_type == behavior_type)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def add_learning_objective(
        self,
        user_id: int,
        objective_name: str,
        objective_type: str,
        target_skill: Optional[str] = None,
        priority: str = "medium",
        target_date: Optional[datetime] = None,
    ) -> LearningObjective:
        """Add learning objective.

        Args:
            user_id: User ID.
            objective_name: Objective name.
            objective_type: Objective type.
            target_skill: Target skill.
            priority: Priority level (low, medium, high).
            target_date: Target completion date.

        Returns:
            Created LearningObjective object.
        """
        session = self.get_session()
        try:
            objective = LearningObjective(
                user_id=user_id,
                objective_name=objective_name,
                objective_type=objective_type,
                target_skill=target_skill,
                priority=priority,
                target_date=target_date,
            )
            session.add(objective)
            session.commit()
            session.refresh(objective)
            return objective
        finally:
            session.close()

    def get_user_objectives(
        self, user_id: int, status: Optional[str] = None
    ) -> List[LearningObjective]:
        """Get user learning objectives.

        Args:
            user_id: User ID.
            status: Optional status filter (active, completed, etc.).

        Returns:
            List of LearningObjective objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(LearningObjective)
                .filter(LearningObjective.user_id == user_id)
                .order_by(LearningObjective.priority.desc(), LearningObjective.created_at.desc())
            )
            if status:
                query = query.filter(LearningObjective.status == status)
            return query.all()
        finally:
            session.close()

    def add_recommendation(
        self,
        user_id: int,
        course_id: int,
        recommendation_type: str,
        title: str,
        description: str,
        confidence_score: float,
        difficulty_level: Optional[str] = None,
        priority: str = "medium",
    ) -> Recommendation:
        """Add learning recommendation.

        Args:
            user_id: User ID.
            course_id: Course ID.
            recommendation_type: Recommendation type.
            title: Recommendation title.
            description: Recommendation description.
            confidence_score: Confidence score (0.0 to 1.0).
            difficulty_level: Recommended difficulty level.
            priority: Priority level (low, medium, high).

        Returns:
            Created Recommendation object.
        """
        session = self.get_session()
        try:
            recommendation = Recommendation(
                user_id=user_id,
                course_id=course_id,
                recommendation_type=recommendation_type,
                title=title,
                description=description,
                confidence_score=confidence_score,
                difficulty_level=difficulty_level,
                priority=priority,
            )
            session.add(recommendation)
            session.commit()
            session.refresh(recommendation)
            return recommendation
        finally:
            session.close()

    def get_user_recommendations(
        self, user_id: int, limit: Optional[int] = None
    ) -> List[Recommendation]:
        """Get user recommendations.

        Args:
            user_id: User ID.
            limit: Maximum number of recommendations to return.

        Returns:
            List of Recommendation objects ordered by confidence score.
        """
        session = self.get_session()
        try:
            query = (
                session.query(Recommendation)
                .filter(Recommendation.user_id == user_id)
                .order_by(Recommendation.confidence_score.desc(), Recommendation.generated_at.desc())
            )
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def add_completion_rate(
        self,
        course_id: int,
        time_window_start: datetime,
        time_window_end: datetime,
        total_enrollments: int,
        completed_enrollments: int,
        average_completion_time: Optional[float] = None,
    ) -> CompletionRate:
        """Add completion rate metric.

        Args:
            course_id: Course ID.
            time_window_start: Start of time window.
            time_window_end: End of time window.
            total_enrollments: Total number of enrollments.
            completed_enrollments: Number of completed enrollments.
            average_completion_time: Average completion time in minutes.

        Returns:
            Created CompletionRate object.
        """
        session = self.get_session()
        try:
            completion_rate_value = (
                completed_enrollments / total_enrollments * 100
                if total_enrollments > 0
                else 0.0
            )

            completion_rate = CompletionRate(
                course_id=course_id,
                time_window_start=time_window_start,
                time_window_end=time_window_end,
                total_enrollments=total_enrollments,
                completed_enrollments=completed_enrollments,
                completion_rate=completion_rate_value,
                average_completion_time=average_completion_time,
            )
            session.add(completion_rate)
            session.commit()
            session.refresh(completion_rate)
            return completion_rate
        finally:
            session.close()

    def get_completion_rates(
        self, course_id: Optional[int] = None
    ) -> List[CompletionRate]:
        """Get completion rates.

        Args:
            course_id: Optional course ID to filter by.

        Returns:
            List of CompletionRate objects.
        """
        session = self.get_session()
        try:
            query = session.query(CompletionRate).order_by(
                CompletionRate.time_window_start.desc()
            )
            if course_id:
                query = query.filter(CompletionRate.course_id == course_id)
            return query.all()
        finally:
            session.close()
