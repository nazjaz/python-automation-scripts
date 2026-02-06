"""Database models and operations for survey processing."""

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


class Survey(Base):
    """Survey definition."""

    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True)
    survey_name = Column(String(200), nullable=False)
    description = Column(Text)
    survey_type = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="active")

    questions = relationship("Question", back_populates="survey", cascade="all, delete-orphan")
    responses = relationship("Response", back_populates="survey", cascade="all, delete-orphan")


class Question(Base):
    """Survey question."""

    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(100))
    question_order = Column(Integer, default=0)
    required = Column(String(10), default="false")
    options = Column(Text)

    survey = relationship("Survey", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")


class Response(Base):
    """Survey response from a respondent."""

    __tablename__ = "responses"

    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    respondent_id = Column(String(100))
    respondent_email = Column(String(200))
    submitted_at = Column(DateTime, default=datetime.utcnow)
    satisfaction_score = Column(Float)
    processed_at = Column(DateTime, nullable=True)

    survey = relationship("Survey", back_populates="responses")
    answers = relationship("Answer", back_populates="response", cascade="all, delete-orphan")


class Answer(Base):
    """Answer to a survey question."""

    __tablename__ = "answers"

    id = Column(Integer, primary_key=True)
    response_id = Column(Integer, ForeignKey("responses.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_text = Column(Text)
    answer_value = Column(Float)
    answer_choice = Column(String(200))

    response = relationship("Response", back_populates="answers")
    question = relationship("Question", back_populates="answers")


class Trend(Base):
    """Identified trend in survey responses."""

    __tablename__ = "trends"

    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    trend_name = Column(String(200), nullable=False)
    trend_type = Column(String(100))
    description = Column(Text)
    confidence_score = Column(Float)
    identified_at = Column(DateTime, default=datetime.utcnow)

    survey = relationship("Survey")


class Insight(Base):
    """Insight generated from survey analysis."""

    __tablename__ = "insights"

    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    insight_type = Column(String(100))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20))
    generated_at = Column(DateTime, default=datetime.utcnow)

    survey = relationship("Survey")


class Summary(Base):
    """Executive summary for survey."""

    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False, unique=True)
    summary_text = Column(Text, nullable=False)
    satisfaction_score = Column(Float)
    response_count = Column(Integer)
    key_insights = Column(Text)
    recommendations = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

    survey = relationship("Survey")


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

    def add_survey(
        self,
        survey_name: str,
        description: Optional[str] = None,
        survey_type: Optional[str] = None,
    ) -> Survey:
        """Add a new survey.

        Args:
            survey_name: Survey name.
            description: Survey description.
            survey_type: Survey type.

        Returns:
            Created Survey object.
        """
        session = self.get_session()
        try:
            survey = Survey(
                survey_name=survey_name,
                description=description,
                survey_type=survey_type,
            )
            session.add(survey)
            session.commit()
            session.refresh(survey)
            return survey
        finally:
            session.close()

    def get_survey(self, survey_id: int) -> Optional[Survey]:
        """Get survey by ID.

        Args:
            survey_id: Survey ID.

        Returns:
            Survey object or None.
        """
        session = self.get_session()
        try:
            return session.query(Survey).filter(Survey.id == survey_id).first()
        finally:
            session.close()

    def get_all_surveys(self, status: Optional[str] = None) -> List[Survey]:
        """Get all surveys.

        Args:
            status: Optional status filter.

        Returns:
            List of Survey objects.
        """
        session = self.get_session()
        try:
            query = session.query(Survey)
            if status:
                query = query.filter(Survey.status == status)
            return query.all()
        finally:
            session.close()

    def add_question(
        self,
        survey_id: int,
        question_text: str,
        question_type: str,
        question_order: int = 0,
        required: str = "false",
        options: Optional[str] = None,
    ) -> Question:
        """Add a question to survey.

        Args:
            survey_id: Survey ID.
            question_text: Question text.
            question_type: Question type (rating, multiple_choice, text, etc.).
            question_order: Question order.
            required: Whether question is required.
            options: Optional JSON string of answer options.

        Returns:
            Created Question object.
        """
        session = self.get_session()
        try:
            question = Question(
                survey_id=survey_id,
                question_text=question_text,
                question_type=question_type,
                question_order=question_order,
                required=required,
                options=options,
            )
            session.add(question)
            session.commit()
            session.refresh(question)
            return question
        finally:
            session.close()

    def get_survey_questions(self, survey_id: int) -> List[Question]:
        """Get all questions for a survey.

        Args:
            survey_id: Survey ID.

        Returns:
            List of Question objects.
        """
        session = self.get_session()
        try:
            return (
                session.query(Question)
                .filter(Question.survey_id == survey_id)
                .order_by(Question.question_order)
                .all()
            )
        finally:
            session.close()

    def add_response(
        self,
        survey_id: int,
        respondent_id: Optional[str] = None,
        respondent_email: Optional[str] = None,
    ) -> Response:
        """Add a survey response.

        Args:
            survey_id: Survey ID.
            respondent_id: Respondent identifier.
            respondent_email: Respondent email.

        Returns:
            Created Response object.
        """
        session = self.get_session()
        try:
            response = Response(
                survey_id=survey_id,
                respondent_id=respondent_id,
                respondent_email=respondent_email,
            )
            session.add(response)
            session.commit()
            session.refresh(response)
            return response
        finally:
            session.close()

    def add_answer(
        self,
        response_id: int,
        question_id: int,
        answer_text: Optional[str] = None,
        answer_value: Optional[float] = None,
        answer_choice: Optional[str] = None,
    ) -> Answer:
        """Add an answer to a response.

        Args:
            response_id: Response ID.
            question_id: Question ID.
            answer_text: Answer text for text questions.
            answer_value: Answer value for numeric questions.
            answer_choice: Answer choice for multiple choice questions.

        Returns:
            Created Answer object.
        """
        session = self.get_session()
        try:
            answer = Answer(
                response_id=response_id,
                question_id=question_id,
                answer_text=answer_text,
                answer_value=answer_value,
                answer_choice=answer_choice,
            )
            session.add(answer)
            session.commit()
            session.refresh(answer)
            return answer
        finally:
            session.close()

    def get_survey_responses(
        self, survey_id: int, limit: Optional[int] = None
    ) -> List[Response]:
        """Get all responses for a survey.

        Args:
            survey_id: Survey ID.
            limit: Maximum number of responses to return.

        Returns:
            List of Response objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(Response)
                .filter(Response.survey_id == survey_id)
                .order_by(Response.submitted_at.desc())
            )
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def update_response_satisfaction(
        self, response_id: int, satisfaction_score: float
    ) -> None:
        """Update response satisfaction score.

        Args:
            response_id: Response ID.
            satisfaction_score: Satisfaction score.
        """
        session = self.get_session()
        try:
            response = session.query(Response).filter(Response.id == response_id).first()
            if response:
                response.satisfaction_score = satisfaction_score
                response.processed_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()

    def add_trend(
        self,
        survey_id: int,
        trend_name: str,
        trend_type: str,
        description: str,
        confidence_score: float,
    ) -> Trend:
        """Add identified trend.

        Args:
            survey_id: Survey ID.
            trend_name: Trend name.
            trend_type: Trend type.
            description: Trend description.
            confidence_score: Confidence score (0.0 to 1.0).

        Returns:
            Created Trend object.
        """
        session = self.get_session()
        try:
            trend = Trend(
                survey_id=survey_id,
                trend_name=trend_name,
                trend_type=trend_type,
                description=description,
                confidence_score=confidence_score,
            )
            session.add(trend)
            session.commit()
            session.refresh(trend)
            return trend
        finally:
            session.close()

    def get_survey_trends(self, survey_id: int) -> List[Trend]:
        """Get all trends for a survey.

        Args:
            survey_id: Survey ID.

        Returns:
            List of Trend objects.
        """
        session = self.get_session()
        try:
            return (
                session.query(Trend)
                .filter(Trend.survey_id == survey_id)
                .order_by(Trend.confidence_score.desc())
                .all()
            )
        finally:
            session.close()

    def add_insight(
        self,
        survey_id: int,
        insight_type: str,
        title: str,
        description: str,
        priority: str = "medium",
    ) -> Insight:
        """Add insight.

        Args:
            survey_id: Survey ID.
            insight_type: Insight type.
            title: Insight title.
            description: Insight description.
            priority: Insight priority (low, medium, high).

        Returns:
            Created Insight object.
        """
        session = self.get_session()
        try:
            insight = Insight(
                survey_id=survey_id,
                insight_type=insight_type,
                title=title,
                description=description,
                priority=priority,
            )
            session.add(insight)
            session.commit()
            session.refresh(insight)
            return insight
        finally:
            session.close()

    def get_survey_insights(
        self, survey_id: int, limit: Optional[int] = None
    ) -> List[Insight]:
        """Get all insights for a survey.

        Args:
            survey_id: Survey ID.
            limit: Maximum number of insights to return.

        Returns:
            List of Insight objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(Insight)
                .filter(Insight.survey_id == survey_id)
                .order_by(Insight.generated_at.desc())
            )
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def add_summary(
        self,
        survey_id: int,
        summary_text: str,
        satisfaction_score: float,
        response_count: int,
        key_insights: Optional[str] = None,
        recommendations: Optional[str] = None,
    ) -> Summary:
        """Add or update executive summary.

        Args:
            survey_id: Survey ID.
            summary_text: Summary text.
            satisfaction_score: Average satisfaction score.
            response_count: Number of responses.
            key_insights: Key insights as JSON string.
            recommendations: Recommendations as JSON string.

        Returns:
            Created or updated Summary object.
        """
        session = self.get_session()
        try:
            existing = (
                session.query(Summary).filter(Summary.survey_id == survey_id).first()
            )

            if existing:
                existing.summary_text = summary_text
                existing.satisfaction_score = satisfaction_score
                existing.response_count = response_count
                existing.key_insights = key_insights
                existing.recommendations = recommendations
                existing.generated_at = datetime.utcnow()
                session.commit()
                session.refresh(existing)
                return existing
            else:
                summary = Summary(
                    survey_id=survey_id,
                    summary_text=summary_text,
                    satisfaction_score=satisfaction_score,
                    response_count=response_count,
                    key_insights=key_insights,
                    recommendations=recommendations,
                )
                session.add(summary)
                session.commit()
                session.refresh(summary)
                return summary
        finally:
            session.close()

    def get_summary(self, survey_id: int) -> Optional[Summary]:
        """Get executive summary for survey.

        Args:
            survey_id: Survey ID.

        Returns:
            Summary object or None.
        """
        session = self.get_session()
        try:
            return session.query(Summary).filter(Summary.survey_id == survey_id).first()
        finally:
            session.close()
