"""Database models and operations for fitness challenge system."""

from datetime import datetime, timedelta
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


class Participant(Base):
    """Fitness challenge participant."""

    __tablename__ = "participants"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    phone = Column(String(50))
    fitness_level = Column(String(50))
    preferences = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    challenges = relationship("Challenge", back_populates="participant")
    goals = relationship("Goal", back_populates="participant")
    progress_entries = relationship("ProgressEntry", back_populates="participant")


class Challenge(Base):
    """Fitness challenge."""

    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    challenge_name = Column(String(200), nullable=False)
    challenge_type = Column(String(100))
    description = Column(Text)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    target_value = Column(Float)
    target_unit = Column(String(50))
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    participant = relationship("Participant", back_populates="challenges")
    progress_entries = relationship("ProgressEntry", back_populates="challenge")


class Goal(Base):
    """Fitness goal for participant."""

    __tablename__ = "goals"

    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    goal_name = Column(String(200), nullable=False)
    goal_type = Column(String(100))
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, default=0.0)
    unit = Column(String(50))
    deadline = Column(DateTime)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    participant = relationship("Participant", back_populates="goals")


class ProgressEntry(Base):
    """Progress entry for challenge or goal."""

    __tablename__ = "progress_entries"

    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    entry_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    participant = relationship("Participant", back_populates="progress_entries")
    challenge = relationship("Challenge", back_populates="progress_entries")


class Leaderboard(Base):
    """Leaderboard for challenge."""

    __tablename__ = "leaderboards"

    id = Column(Integer, primary_key=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    rank = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)

    challenge = relationship("Challenge")
    participant = relationship("Participant")


class Message(Base):
    """Message sent to participant."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    message_type = Column(String(50), nullable=False)
    subject = Column(String(200))
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="sent")

    participant = relationship("Participant")


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

    def add_participant(
        self,
        name: str,
        email: str,
        phone: Optional[str] = None,
        fitness_level: Optional[str] = None,
        preferences: Optional[str] = None,
    ) -> Participant:
        """Add a new participant.

        Args:
            name: Participant name.
            email: Participant email.
            phone: Participant phone number.
            fitness_level: Fitness level (beginner, intermediate, advanced).
            preferences: Participant preferences as JSON string.

        Returns:
            Created Participant object.
        """
        session = self.get_session()
        try:
            participant = Participant(
                name=name,
                email=email,
                phone=phone,
                fitness_level=fitness_level,
                preferences=preferences,
            )
            session.add(participant)
            session.commit()
            session.refresh(participant)
            return participant
        finally:
            session.close()

    def get_participant(self, participant_id: int) -> Optional[Participant]:
        """Get participant by ID.

        Args:
            participant_id: Participant ID.

        Returns:
            Participant object or None.
        """
        session = self.get_session()
        try:
            return session.query(Participant).filter(Participant.id == participant_id).first()
        finally:
            session.close()

    def get_participant_by_email(self, email: str) -> Optional[Participant]:
        """Get participant by email.

        Args:
            email: Participant email.

        Returns:
            Participant object or None.
        """
        session = self.get_session()
        try:
            return session.query(Participant).filter(Participant.email == email).first()
        finally:
            session.close()

    def get_all_participants(self, limit: Optional[int] = None) -> List[Participant]:
        """Get all participants.

        Args:
            limit: Maximum number of participants to return.

        Returns:
            List of Participant objects.
        """
        session = self.get_session()
        try:
            query = session.query(Participant)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def create_challenge(
        self,
        participant_id: int,
        challenge_name: str,
        challenge_type: str,
        start_date: datetime,
        end_date: datetime,
        target_value: Optional[float] = None,
        target_unit: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Challenge:
        """Create a new challenge.

        Args:
            participant_id: Participant ID.
            challenge_name: Challenge name.
            challenge_type: Challenge type (steps, distance, calories, etc.).
            start_date: Challenge start date.
            end_date: Challenge end date.
            target_value: Target value.
            target_unit: Target unit.
            description: Challenge description.

        Returns:
            Created Challenge object.
        """
        session = self.get_session()
        try:
            challenge = Challenge(
                participant_id=participant_id,
                challenge_name=challenge_name,
                challenge_type=challenge_type,
                start_date=start_date,
                end_date=end_date,
                target_value=target_value,
                target_unit=target_unit,
                description=description,
            )
            session.add(challenge)
            session.commit()
            session.refresh(challenge)
            return challenge
        finally:
            session.close()

    def get_active_challenges(
        self, participant_id: Optional[int] = None
    ) -> List[Challenge]:
        """Get active challenges.

        Args:
            participant_id: Optional participant ID to filter by.

        Returns:
            List of active Challenge objects.
        """
        session = self.get_session()
        try:
            query = session.query(Challenge).filter(
                Challenge.status == "active",
                Challenge.end_date >= datetime.utcnow(),
            )
            if participant_id:
                query = query.filter(Challenge.participant_id == participant_id)
            return query.all()
        finally:
            session.close()

    def create_goal(
        self,
        participant_id: int,
        goal_name: str,
        goal_type: str,
        target_value: float,
        unit: str,
        deadline: Optional[datetime] = None,
    ) -> Goal:
        """Create a new goal.

        Args:
            participant_id: Participant ID.
            goal_name: Goal name.
            goal_type: Goal type (weight_loss, muscle_gain, endurance, etc.).
            target_value: Target value.
            unit: Unit of measurement.
            deadline: Goal deadline.

        Returns:
            Created Goal object.
        """
        session = self.get_session()
        try:
            goal = Goal(
                participant_id=participant_id,
                goal_name=goal_name,
                goal_type=goal_type,
                target_value=target_value,
                unit=unit,
                deadline=deadline,
            )
            session.add(goal)
            session.commit()
            session.refresh(goal)
            return goal
        finally:
            session.close()

    def update_goal_progress(
        self, goal_id: int, current_value: float
    ) -> None:
        """Update goal progress.

        Args:
            goal_id: Goal ID.
            current_value: Current progress value.
        """
        session = self.get_session()
        try:
            goal = session.query(Goal).filter(Goal.id == goal_id).first()
            if goal:
                goal.current_value = current_value
                goal.updated_at = datetime.utcnow()
                if current_value >= goal.target_value:
                    goal.status = "completed"
                session.commit()
        finally:
            session.close()

    def get_active_goals(
        self, participant_id: Optional[int] = None
    ) -> List[Goal]:
        """Get active goals.

        Args:
            participant_id: Optional participant ID to filter by.

        Returns:
            List of active Goal objects.
        """
        session = self.get_session()
        try:
            query = session.query(Goal).filter(Goal.status == "active")
            if participant_id:
                query = query.filter(Goal.participant_id == participant_id)
            return query.all()
        finally:
            session.close()

    def add_progress_entry(
        self,
        participant_id: int,
        value: float,
        unit: str,
        challenge_id: Optional[int] = None,
        goal_id: Optional[int] = None,
        entry_date: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> ProgressEntry:
        """Add progress entry.

        Args:
            participant_id: Participant ID.
            value: Progress value.
            unit: Unit of measurement.
            challenge_id: Optional challenge ID.
            goal_id: Optional goal ID.
            entry_date: Entry date.
            notes: Optional notes.

        Returns:
            Created ProgressEntry object.
        """
        session = self.get_session()
        try:
            if entry_date is None:
                entry_date = datetime.utcnow()

            progress_entry = ProgressEntry(
                participant_id=participant_id,
                challenge_id=challenge_id,
                goal_id=goal_id,
                value=value,
                unit=unit,
                entry_date=entry_date,
                notes=notes,
            )
            session.add(progress_entry)

            if goal_id:
                goal = session.query(Goal).filter(Goal.id == goal_id).first()
                if goal:
                    total_progress = sum(
                        pe.value
                        for pe in session.query(ProgressEntry)
                        .filter(ProgressEntry.goal_id == goal_id)
                        .all()
                    )
                    self.update_goal_progress(goal_id, total_progress)

            session.commit()
            session.refresh(progress_entry)
            return progress_entry
        finally:
            session.close()

    def get_progress_entries(
        self,
        participant_id: Optional[int] = None,
        challenge_id: Optional[int] = None,
        goal_id: Optional[int] = None,
        days: Optional[int] = None,
    ) -> List[ProgressEntry]:
        """Get progress entries.

        Args:
            participant_id: Optional participant ID to filter by.
            challenge_id: Optional challenge ID to filter by.
            goal_id: Optional goal ID to filter by.
            days: Optional number of days to look back.

        Returns:
            List of ProgressEntry objects.
        """
        session = self.get_session()
        try:
            query = session.query(ProgressEntry)

            if participant_id:
                query = query.filter(ProgressEntry.participant_id == participant_id)
            if challenge_id:
                query = query.filter(ProgressEntry.challenge_id == challenge_id)
            if goal_id:
                query = query.filter(ProgressEntry.goal_id == goal_id)
            if days:
                cutoff = datetime.utcnow() - timedelta(days=days)
                query = query.filter(ProgressEntry.entry_date >= cutoff)

            return query.order_by(ProgressEntry.entry_date.desc()).all()
        finally:
            session.close()

    def update_leaderboard(
        self,
        challenge_id: Optional[int],
        participant_id: int,
        rank: int,
        score: float,
    ) -> Leaderboard:
        """Update leaderboard entry.

        Args:
            challenge_id: Optional challenge ID.
            participant_id: Participant ID.
            rank: Participant rank.
            score: Participant score.

        Returns:
            Leaderboard object.
        """
        session = self.get_session()
        try:
            existing = (
                session.query(Leaderboard)
                .filter(
                    Leaderboard.challenge_id == challenge_id,
                    Leaderboard.participant_id == participant_id,
                )
                .first()
            )

            if existing:
                existing.rank = rank
                existing.score = score
                existing.calculated_at = datetime.utcnow()
                session.commit()
                session.refresh(existing)
                return existing
            else:
                leaderboard = Leaderboard(
                    challenge_id=challenge_id,
                    participant_id=participant_id,
                    rank=rank,
                    score=score,
                )
                session.add(leaderboard)
                session.commit()
                session.refresh(leaderboard)
                return leaderboard
        finally:
            session.close()

    def get_leaderboard(
        self, challenge_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Leaderboard]:
        """Get leaderboard.

        Args:
            challenge_id: Optional challenge ID to filter by.
            limit: Maximum number of entries to return.

        Returns:
            List of Leaderboard objects ordered by rank.
        """
        session = self.get_session()
        try:
            query = session.query(Leaderboard).order_by(Leaderboard.rank.asc())
            if challenge_id:
                query = query.filter(Leaderboard.challenge_id == challenge_id)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def add_message(
        self,
        participant_id: int,
        message_type: str,
        content: str,
        subject: Optional[str] = None,
    ) -> Message:
        """Add message.

        Args:
            participant_id: Participant ID.
            message_type: Message type (motivational, reminder, achievement, etc.).
            content: Message content.
            subject: Optional message subject.

        Returns:
            Created Message object.
        """
        session = self.get_session()
        try:
            message = Message(
                participant_id=participant_id,
                message_type=message_type,
                content=content,
                subject=subject,
            )
            session.add(message)
            session.commit()
            session.refresh(message)
            return message
        finally:
            session.close()

    def get_recent_messages(
        self, participant_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Message]:
        """Get recent messages.

        Args:
            participant_id: Optional participant ID to filter by.
            limit: Maximum number of messages to return.

        Returns:
            List of Message objects.
        """
        session = self.get_session()
        try:
            query = session.query(Message).order_by(Message.sent_at.desc())
            if participant_id:
                query = query.filter(Message.participant_id == participant_id)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()
