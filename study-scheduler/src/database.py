"""Database models and operations for study scheduler data."""

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


class Course(Base):
    """Database model for courses."""

    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(100), unique=True, index=True)
    difficulty = Column(String(50), default="medium", index=True)
    priority = Column(String(50), default="medium", index=True)
    total_hours_required = Column(Float, default=0.0)
    hours_completed = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    exams = relationship("Exam", back_populates="course", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Course(id={self.id}, name={self.name}, code={self.code})>"


class Exam(Base):
    """Database model for exams."""

    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    exam_date = Column(Date, nullable=False, index=True)
    exam_type = Column(String(100))
    weight_percentage = Column(Float)
    preparation_hours_required = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="exams")

    def __repr__(self) -> str:
        return f"<Exam(id={self.id}, name={self.name}, exam_date={self.exam_date})>"


class StudySession(Base):
    """Database model for study sessions."""

    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    session_date = Column(Date, nullable=False, index=True)
    start_time = Column(String(10))
    end_time = Column(String(10))
    duration_minutes = Column(Integer)
    topics_covered = Column(Text)
    completion_status = Column(String(50), default="scheduled", index=True)
    effectiveness_rating = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="study_sessions")
    progress_records = relationship("ProgressRecord", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<StudySession(id={self.id}, course_id={self.course_id}, "
            f"session_date={self.session_date}, completion_status={self.completion_status})>"
        )


class ProgressRecord(Base):
    """Database model for progress tracking records."""

    __tablename__ = "progress_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("study_sessions.id"), nullable=False, index=True)
    record_date = Column(Date, nullable=False, index=True)
    hours_studied = Column(Float, default=0.0)
    completion_percentage = Column(Float)
    topics_mastered = Column(Integer, default=0)
    topics_reviewed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("StudySession", back_populates="progress_records")

    def __repr__(self) -> str:
        return (
            f"<ProgressRecord(id={self.id}, session_id={self.session_id}, "
            f"completion_percentage={self.completion_percentage})>"
        )


class LearningPreference(Base):
    """Database model for learning preferences."""

    __tablename__ = "learning_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, default=1, index=True)
    study_style = Column(String(100))
    preferred_study_times = Column(String(500))
    daily_study_hours = Column(Float, default=4.0)
    break_frequency_minutes = Column(Integer, default=90)
    review_frequency_days = Column(Integer, default=7)
    active_recall_enabled = Column(Boolean, default=True)
    spaced_repetition_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<LearningPreference(id={self.id}, study_style={self.study_style})>"


class Recommendation(Base):
    """Database model for recommendations."""

    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_type = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(50), default="medium", index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True, index=True)
    implemented = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    implemented_at = Column(DateTime)

    def __repr__(self) -> str:
        return (
            f"<Recommendation(id={self.id}, recommendation_type={self.recommendation_type}, "
            f"title={self.title}, priority={self.priority})>"
        )


class DatabaseManager:
    """Manages database operations for study scheduler data."""

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

    def add_course(
        self,
        name: str,
        code: str,
        difficulty: str = "medium",
        priority: str = "medium",
        total_hours_required: float = 0.0,
    ) -> Course:
        """Add or update course.

        Args:
            name: Course name.
            code: Course code.
            difficulty: Course difficulty level.
            priority: Course priority level.
            total_hours_required: Total hours required for course.

        Returns:
            Course object.
        """
        session = self.get_session()
        try:
            course = (
                session.query(Course)
                .filter(Course.code == code)
                .first()
            )

            if course is None:
                course = Course(
                    name=name,
                    code=code,
                    difficulty=difficulty,
                    priority=priority,
                    total_hours_required=total_hours_required,
                )
                session.add(course)
            else:
                course.name = name
                course.difficulty = difficulty
                course.priority = priority
                course.total_hours_required = total_hours_required
                course.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(course)
            return course
        finally:
            session.close()

    def add_exam(
        self,
        course_id: int,
        name: str,
        exam_date: date,
        exam_type: Optional[str] = None,
        weight_percentage: Optional[float] = None,
        preparation_hours_required: Optional[float] = None,
    ) -> Exam:
        """Add exam.

        Args:
            course_id: Course ID.
            name: Exam name.
            exam_date: Exam date.
            exam_type: Optional exam type.
            weight_percentage: Optional weight percentage.
            preparation_hours_required: Optional preparation hours required.

        Returns:
            Exam object.
        """
        session = self.get_session()
        try:
            exam = Exam(
                course_id=course_id,
                name=name,
                exam_date=exam_date,
                exam_type=exam_type,
                weight_percentage=weight_percentage,
                preparation_hours_required=preparation_hours_required,
            )
            session.add(exam)
            session.commit()
            session.refresh(exam)
            return exam
        finally:
            session.close()

    def get_courses(self, limit: Optional[int] = None) -> List[Course]:
        """Get all courses.

        Args:
            limit: Optional limit on number of results.

        Returns:
            List of Course objects.
        """
        session = self.get_session()
        try:
            query = session.query(Course).order_by(Course.name.asc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_exams(
        self,
        course_id: Optional[int] = None,
        upcoming_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Exam]:
        """Get exams with optional filtering.

        Args:
            course_id: Optional course ID filter.
            upcoming_only: Whether to return only upcoming exams.
            limit: Optional limit on number of results.

        Returns:
            List of Exam objects.
        """
        session = self.get_session()
        try:
            query = session.query(Exam)

            if course_id:
                query = query.filter(Exam.course_id == course_id)

            if upcoming_only:
                today = date.today()
                query = query.filter(Exam.exam_date >= today)

            query = query.order_by(Exam.exam_date.asc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def add_study_session(
        self,
        course_id: int,
        session_date: date,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        topics_covered: Optional[str] = None,
        completion_status: str = "scheduled",
        effectiveness_rating: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> StudySession:
        """Add study session.

        Args:
            course_id: Course ID.
            session_date: Session date.
            start_time: Optional start time.
            end_time: Optional end time.
            duration_minutes: Optional duration in minutes.
            topics_covered: Optional topics covered.
            completion_status: Completion status.
            effectiveness_rating: Optional effectiveness rating (1-5).
            notes: Optional notes.

        Returns:
            StudySession object.
        """
        session = self.get_session()
        try:
            study_session = StudySession(
                course_id=course_id,
                session_date=session_date,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration_minutes,
                topics_covered=topics_covered,
                completion_status=completion_status,
                effectiveness_rating=effectiveness_rating,
                notes=notes,
            )
            session.add(study_session)
            session.commit()
            session.refresh(study_session)
            return study_session
        finally:
            session.close()

    def get_study_sessions(
        self,
        course_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        completion_status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[StudySession]:
        """Get study sessions with optional filtering.

        Args:
            course_id: Optional course ID filter.
            start_date: Optional start date filter.
            end_date: Optional end date filter.
            completion_status: Optional completion status filter.
            limit: Optional limit on number of results.

        Returns:
            List of StudySession objects.
        """
        session = self.get_session()
        try:
            query = session.query(StudySession)

            if course_id:
                query = query.filter(StudySession.course_id == course_id)

            if start_date:
                query = query.filter(StudySession.session_date >= start_date)

            if end_date:
                query = query.filter(StudySession.session_date <= end_date)

            if completion_status:
                query = query.filter(StudySession.completion_status == completion_status)

            query = query.order_by(StudySession.session_date.asc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def add_progress_record(
        self,
        session_id: int,
        record_date: date,
        hours_studied: float = 0.0,
        completion_percentage: Optional[float] = None,
        topics_mastered: int = 0,
        topics_reviewed: int = 0,
    ) -> ProgressRecord:
        """Add progress record.

        Args:
            session_id: Study session ID.
            record_date: Record date.
            hours_studied: Hours studied.
            completion_percentage: Optional completion percentage.
            topics_mastered: Number of topics mastered.
            topics_reviewed: Number of topics reviewed.

        Returns:
            ProgressRecord object.
        """
        session = self.get_session()
        try:
            progress = ProgressRecord(
                session_id=session_id,
                record_date=record_date,
                hours_studied=hours_studied,
                completion_percentage=completion_percentage,
                topics_mastered=topics_mastered,
                topics_reviewed=topics_reviewed,
            )
            session.add(progress)
            session.commit()
            session.refresh(progress)
            return progress
        finally:
            session.close()

    def get_learning_preference(self, user_id: int = 1) -> Optional[LearningPreference]:
        """Get learning preferences for user.

        Args:
            user_id: User ID.

        Returns:
            LearningPreference object or None.
        """
        session = self.get_session()
        try:
            return (
                session.query(LearningPreference)
                .filter(LearningPreference.user_id == user_id)
                .first()
            )
        finally:
            session.close()

    def update_learning_preference(
        self,
        user_id: int = 1,
        study_style: Optional[str] = None,
        preferred_study_times: Optional[str] = None,
        daily_study_hours: Optional[float] = None,
        break_frequency_minutes: Optional[int] = None,
        review_frequency_days: Optional[int] = None,
        active_recall_enabled: Optional[bool] = None,
        spaced_repetition_enabled: Optional[bool] = None,
    ) -> LearningPreference:
        """Update learning preferences.

        Args:
            user_id: User ID.
            study_style: Optional study style.
            preferred_study_times: Optional preferred study times (comma-separated).
            daily_study_hours: Optional daily study hours.
            break_frequency_minutes: Optional break frequency.
            review_frequency_days: Optional review frequency.
            active_recall_enabled: Optional active recall enabled.
            spaced_repetition_enabled: Optional spaced repetition enabled.

        Returns:
            LearningPreference object.
        """
        session = self.get_session()
        try:
            preference = self.get_learning_preference(user_id)

            if preference is None:
                preference = LearningPreference(user_id=user_id)
                session.add(preference)

            if study_style is not None:
                preference.study_style = study_style
            if preferred_study_times is not None:
                preference.preferred_study_times = preferred_study_times
            if daily_study_hours is not None:
                preference.daily_study_hours = daily_study_hours
            if break_frequency_minutes is not None:
                preference.break_frequency_minutes = break_frequency_minutes
            if review_frequency_days is not None:
                preference.review_frequency_days = review_frequency_days
            if active_recall_enabled is not None:
                preference.active_recall_enabled = active_recall_enabled
            if spaced_repetition_enabled is not None:
                preference.spaced_repetition_enabled = spaced_repetition_enabled

            preference.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(preference)
            return preference
        finally:
            session.close()

    def add_recommendation(
        self,
        recommendation_type: str,
        title: str,
        description: str,
        priority: str = "medium",
        course_id: Optional[int] = None,
    ) -> Recommendation:
        """Add recommendation.

        Args:
            recommendation_type: Type of recommendation.
            title: Recommendation title.
            description: Recommendation description.
            priority: Priority level.
            course_id: Optional course ID.

        Returns:
            Recommendation object.
        """
        session = self.get_session()
        try:
            recommendation = Recommendation(
                recommendation_type=recommendation_type,
                title=title,
                description=description,
                priority=priority,
                course_id=course_id,
            )
            session.add(recommendation)
            session.commit()
            session.refresh(recommendation)
            return recommendation
        finally:
            session.close()

    def get_unimplemented_recommendations(
        self, limit: Optional[int] = None
    ) -> List[Recommendation]:
        """Get unimplemented recommendations.

        Args:
            limit: Optional limit on number of results.

        Returns:
            List of unimplemented Recommendation objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(Recommendation)
                .filter(Recommendation.implemented == False)
                .order_by(Recommendation.created_at.desc())
            )

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()
