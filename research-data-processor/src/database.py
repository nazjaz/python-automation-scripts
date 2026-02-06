"""Database models and operations for research data processor data."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
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


class Dataset(Base):
    """Database model for datasets."""

    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))
    row_count = Column(Integer)
    column_count = Column(Integer)
    cleaned = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    analyses = relationship("Analysis", back_populates="dataset", cascade="all, delete-orphan")
    figures = relationship("Figure", back_populates="dataset", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, dataset_id={self.dataset_id}, name={self.name})>"


class Analysis(Base):
    """Database model for statistical analyses."""

    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False, index=True)
    analysis_type = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    results = Column(Text)
    p_value = Column(Float)
    significance = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    dataset = relationship("Dataset", back_populates="analyses")

    def __repr__(self) -> str:
        return (
            f"<Analysis(id={self.id}, dataset_id={self.dataset_id}, "
            f"analysis_type={self.analysis_type}, p_value={self.p_value})>"
        )


class Figure(Base):
    """Database model for generated figures."""

    __tablename__ = "figures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False, index=True)
    figure_id = Column(String(100), unique=True, nullable=False, index=True)
    figure_type = Column(String(100), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    file_format = Column(String(50))
    publication_ready = Column(Boolean, default=False, index=True)
    width = Column(Float)
    height = Column(Float)
    dpi = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    dataset = relationship("Dataset", back_populates="figures")

    def __repr__(self) -> str:
        return (
            f"<Figure(id={self.id}, figure_id={self.figure_id}, "
            f"figure_type={self.figure_type}, publication_ready={self.publication_ready})>"
        )


class DatabaseManager:
    """Manages database operations for research data processor data."""

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

    def add_dataset(
        self,
        dataset_id: str,
        name: str,
        file_path: str,
        file_type: Optional[str] = None,
        row_count: Optional[int] = None,
        column_count: Optional[int] = None,
    ) -> Dataset:
        """Add or update dataset.

        Args:
            dataset_id: Dataset ID.
            name: Dataset name.
            file_path: File path.
            file_type: Optional file type.
            row_count: Optional row count.
            column_count: Optional column count.

        Returns:
            Dataset object.
        """
        session = self.get_session()
        try:
            dataset = (
                session.query(Dataset)
                .filter(Dataset.dataset_id == dataset_id)
                .first()
            )

            if dataset is None:
                dataset = Dataset(
                    dataset_id=dataset_id,
                    name=name,
                    file_path=file_path,
                    file_type=file_type,
                    row_count=row_count,
                    column_count=column_count,
                )
                session.add(dataset)
            else:
                dataset.name = name
                dataset.file_path = file_path
                dataset.file_type = file_type
                dataset.row_count = row_count
                dataset.column_count = column_count
                dataset.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(dataset)
            return dataset
        finally:
            session.close()

    def add_analysis(
        self,
        dataset_id: int,
        analysis_type: str,
        description: Optional[str] = None,
        results: Optional[str] = None,
        p_value: Optional[float] = None,
        significance: Optional[bool] = None,
    ) -> Analysis:
        """Add analysis record.

        Args:
            dataset_id: Dataset ID.
            analysis_type: Analysis type.
            description: Optional description.
            results: Optional results JSON string.
            p_value: Optional p-value.
            significance: Optional significance flag.

        Returns:
            Analysis object.
        """
        session = self.get_session()
        try:
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type=analysis_type,
                description=description,
                results=results,
                p_value=p_value,
                significance=significance,
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            return analysis
        finally:
            session.close()

    def add_figure(
        self,
        dataset_id: int,
        figure_id: str,
        figure_type: str,
        file_path: str,
        file_format: Optional[str] = None,
        publication_ready: bool = False,
        width: Optional[float] = None,
        height: Optional[float] = None,
        dpi: Optional[int] = None,
    ) -> Figure:
        """Add figure record.

        Args:
            dataset_id: Dataset ID.
            figure_id: Figure ID.
            figure_type: Figure type.
            file_path: File path.
            file_format: Optional file format.
            publication_ready: Whether figure is publication-ready.
            width: Optional width.
            height: Optional height.
            dpi: Optional DPI.

        Returns:
            Figure object.
        """
        session = self.get_session()
        try:
            figure = Figure(
                dataset_id=dataset_id,
                figure_id=figure_id,
                figure_type=figure_type,
                file_path=file_path,
                file_format=file_format,
                publication_ready=publication_ready,
                width=width,
                height=height,
                dpi=dpi,
            )
            session.add(figure)
            session.commit()
            session.refresh(figure)
            return figure
        finally:
            session.close()

    def get_datasets(
        self,
        cleaned: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> List[Dataset]:
        """Get datasets with optional filtering.

        Args:
            cleaned: Optional cleaned filter.
            limit: Optional limit on number of results.

        Returns:
            List of Dataset objects.
        """
        session = self.get_session()
        try:
            query = session.query(Dataset)

            if cleaned is not None:
                query = query.filter(Dataset.cleaned == cleaned)

            query = query.order_by(Dataset.created_at.desc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_figures(
        self,
        dataset_id: Optional[int] = None,
        publication_ready: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> List[Figure]:
        """Get figures with optional filtering.

        Args:
            dataset_id: Optional dataset ID filter.
            publication_ready: Optional publication-ready filter.
            limit: Optional limit on number of results.

        Returns:
            List of Figure objects.
        """
        session = self.get_session()
        try:
            query = session.query(Figure)

            if dataset_id:
                query = query.filter(Figure.dataset_id == dataset_id)

            if publication_ready is not None:
                query = query.filter(Figure.publication_ready == publication_ready)

            query = query.order_by(Figure.created_at.desc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()
