"""Database models and operations for performance monitoring."""

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


class Database(Base):
    """Monitored database."""

    __tablename__ = "databases"

    id = Column(Integer, primary_key=True)
    database_id = Column(String(100), unique=True, nullable=False)
    database_name = Column(String(200), nullable=False)
    database_type = Column(String(100))
    connection_string = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    performance_metrics = relationship("PerformanceMetric", back_populates="database", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="database", cascade="all, delete-orphan")
    optimizations = relationship("Optimization", back_populates="database", cascade="all, delete-orphan")


class PerformanceMetric(Base):
    """Database performance metric."""

    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True)
    database_id = Column(Integer, ForeignKey("databases.id"), nullable=False)
    metric_type = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))
    collected_at = Column(DateTime, default=datetime.utcnow)

    database = relationship("Database", back_populates="performance_metrics")


class Query(Base):
    """Database query."""

    __tablename__ = "queries"

    id = Column(Integer, primary_key=True)
    query_id = Column(String(100), unique=True, nullable=False)
    database_id = Column(Integer, ForeignKey("databases.id"), nullable=False)
    query_text = Column(Text, nullable=False)
    execution_time_ms = Column(Float, nullable=False)
    execution_count = Column(Integer, default=1)
    average_execution_time_ms = Column(Float)
    slow_query_threshold_ms = Column(Float)
    is_slow = Column(String(10), default="false")
    table_name = Column(String(200))
    query_type = Column(String(50))
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)

    database = relationship("Database", back_populates="queries")
    optimizations = relationship("Optimization", back_populates="query", cascade="all, delete-orphan")


class Optimization(Base):
    """Query optimization recommendation."""

    __tablename__ = "optimizations"

    id = Column(Integer, primary_key=True)
    optimization_id = Column(String(100), unique=True, nullable=False)
    database_id = Column(Integer, ForeignKey("databases.id"), nullable=False)
    query_id = Column(Integer, ForeignKey("queries.id"), nullable=True)
    optimization_type = Column(String(100), nullable=False)
    optimization_description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False)
    estimated_improvement_percent = Column(Float)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)

    database = relationship("Database", back_populates="optimizations")
    query = relationship("Query", back_populates="optimizations")


class IndexSuggestion(Base):
    """Index suggestion for optimization."""

    __tablename__ = "index_suggestions"

    id = Column(Integer, primary_key=True)
    optimization_id = Column(Integer, ForeignKey("optimizations.id"), nullable=False)
    table_name = Column(String(200), nullable=False)
    column_names = Column(Text, nullable=False)
    index_type = Column(String(50))
    index_name = Column(String(200))
    estimated_improvement_percent = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    optimization = relationship("Optimization")


class PerformanceReport(Base):
    """Performance report."""

    __tablename__ = "performance_reports"

    id = Column(Integer, primary_key=True)
    report_id = Column(String(100), unique=True, nullable=False)
    database_id = Column(Integer, ForeignKey("databases.id"), nullable=False)
    report_type = Column(String(100), nullable=False)
    total_queries = Column(Integer, default=0)
    slow_queries = Column(Integer, default=0)
    average_execution_time_ms = Column(Float)
    total_optimizations = Column(Integer, default=0)
    pending_optimizations = Column(Integer, default=0)
    report_data = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

    database = relationship("Database")


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

    def add_database(
        self,
        database_id: str,
        database_name: str,
        database_type: Optional[str] = None,
        connection_string: Optional[str] = None,
    ) -> Database:
        """Add a new database to monitor.

        Args:
            database_id: Database identifier.
            database_name: Database name.
            database_type: Database type (postgresql, mysql, sqlite, etc.).
            connection_string: Database connection string.

        Returns:
            Created Database object.
        """
        session = self.get_session()
        try:
            database = Database(
                database_id=database_id,
                database_name=database_name,
                database_type=database_type,
                connection_string=connection_string,
            )
            session.add(database)
            session.commit()
            session.refresh(database)
            return database
        finally:
            session.close()

    def get_database(self, database_id: str) -> Optional[Database]:
        """Get database by database ID.

        Args:
            database_id: Database identifier.

        Returns:
            Database object or None.
        """
        session = self.get_session()
        try:
            return session.query(Database).filter(Database.database_id == database_id).first()
        finally:
            session.close()

    def add_performance_metric(
        self,
        database_id: int,
        metric_type: str,
        metric_value: float,
        metric_unit: Optional[str] = None,
    ) -> PerformanceMetric:
        """Add performance metric.

        Args:
            database_id: Database ID.
            metric_type: Metric type (cpu_usage, memory_usage, connection_count, etc.).
            metric_value: Metric value.
            metric_unit: Metric unit (percent, bytes, count, etc.).

        Returns:
            Created PerformanceMetric object.
        """
        session = self.get_session()
        try:
            metric = PerformanceMetric(
                database_id=database_id,
                metric_type=metric_type,
                metric_value=metric_value,
                metric_unit=metric_unit,
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()

    def get_recent_metrics(
        self, database_id: int, metric_type: Optional[str] = None, limit: Optional[int] = None
    ) -> List[PerformanceMetric]:
        """Get recent performance metrics.

        Args:
            database_id: Database ID.
            metric_type: Optional metric type to filter by.
            limit: Maximum number of metrics to return.

        Returns:
            List of PerformanceMetric objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(PerformanceMetric)
                .filter(PerformanceMetric.database_id == database_id)
                .order_by(PerformanceMetric.collected_at.desc())
            )
            if metric_type:
                query = query.filter(PerformanceMetric.metric_type == metric_type)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def add_query(
        self,
        query_id: str,
        database_id: int,
        query_text: str,
        execution_time_ms: float,
        slow_query_threshold_ms: float = 1000.0,
        table_name: Optional[str] = None,
        query_type: Optional[str] = None,
    ) -> Query:
        """Add or update query.

        Args:
            query_id: Query identifier (hash of query text).
            database_id: Database ID.
            query_text: Query text.
            execution_time_ms: Execution time in milliseconds.
            slow_query_threshold_ms: Slow query threshold in milliseconds.
            table_name: Table name.
            query_type: Query type (SELECT, INSERT, UPDATE, DELETE).

        Returns:
            Created or updated Query object.
        """
        session = self.get_session()
        try:
            existing = (
                session.query(Query)
                .filter(Query.query_id == query_id)
                .first()
            )

            is_slow = "true" if execution_time_ms >= slow_query_threshold_ms else "false"

            if existing:
                existing.execution_count += 1
                existing.execution_time_ms = execution_time_ms
                existing.average_execution_time_ms = (
                    (existing.average_execution_time_ms * (existing.execution_count - 1) + execution_time_ms)
                    / existing.execution_count
                )
                existing.is_slow = is_slow
                existing.last_seen_at = datetime.utcnow()
                session.commit()
                session.refresh(existing)
                return existing
            else:
                query = Query(
                    query_id=query_id,
                    database_id=database_id,
                    query_text=query_text,
                    execution_time_ms=execution_time_ms,
                    average_execution_time_ms=execution_time_ms,
                    slow_query_threshold_ms=slow_query_threshold_ms,
                    is_slow=is_slow,
                    table_name=table_name,
                    query_type=query_type,
                )
                session.add(query)
                session.commit()
                session.refresh(query)
                return query
        finally:
            session.close()

    def get_slow_queries(
        self, database_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Query]:
        """Get slow queries.

        Args:
            database_id: Optional database ID to filter by.
            limit: Maximum number of queries to return.

        Returns:
            List of Query objects ordered by execution time.
        """
        session = self.get_session()
        try:
            query = (
                session.query(Query)
                .filter(Query.is_slow == "true")
                .order_by(Query.execution_time_ms.desc())
            )
            if database_id:
                query = query.filter(Query.database_id == database_id)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def get_query(self, query_id: str) -> Optional[Query]:
        """Get query by query ID.

        Args:
            query_id: Query identifier.

        Returns:
            Query object or None.
        """
        session = self.get_session()
        try:
            return session.query(Query).filter(Query.query_id == query_id).first()
        finally:
            session.close()

    def add_optimization(
        self,
        optimization_id: str,
        database_id: int,
        optimization_type: str,
        optimization_description: str,
        priority: str,
        query_id: Optional[int] = None,
        estimated_improvement_percent: Optional[float] = None,
    ) -> Optimization:
        """Add optimization recommendation.

        Args:
            optimization_id: Optimization identifier.
            database_id: Database ID.
            optimization_type: Optimization type (index, query_rewrite, configuration, etc.).
            optimization_description: Optimization description.
            priority: Priority level (low, medium, high, urgent).
            query_id: Optional query ID.
            estimated_improvement_percent: Estimated improvement percentage.

        Returns:
            Created Optimization object.
        """
        session = self.get_session()
        try:
            optimization = Optimization(
                optimization_id=optimization_id,
                database_id=database_id,
                query_id=query_id,
                optimization_type=optimization_type,
                optimization_description=optimization_description,
                priority=priority,
                estimated_improvement_percent=estimated_improvement_percent,
            )
            session.add(optimization)
            session.commit()
            session.refresh(optimization)
            return optimization
        finally:
            session.close()

    def get_optimizations(
        self, database_id: Optional[int] = None, status: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Optimization]:
        """Get optimizations.

        Args:
            database_id: Optional database ID to filter by.
            status: Optional status to filter by (pending, applied, rejected).
            limit: Maximum number of optimizations to return.

        Returns:
            List of Optimization objects ordered by priority.
        """
        session = self.get_session()
        try:
            priority_order = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
            query = session.query(Optimization)

            if database_id:
                query = query.filter(Optimization.database_id == database_id)
            if status:
                query = query.filter(Optimization.status == status)

            optimizations = query.all()
            optimizations.sort(
                key=lambda x: priority_order.get(x.priority, 0), reverse=True
            )

            if limit:
                optimizations = optimizations[:limit]

            return optimizations
        finally:
            session.close()

    def add_index_suggestion(
        self,
        optimization_id: int,
        table_name: str,
        column_names: str,
        index_type: Optional[str] = None,
        index_name: Optional[str] = None,
        estimated_improvement_percent: Optional[float] = None,
    ) -> IndexSuggestion:
        """Add index suggestion.

        Args:
            optimization_id: Optimization ID.
            table_name: Table name.
            column_names: Column names as comma-separated string.
            index_type: Index type (btree, hash, etc.).
            index_name: Suggested index name.
            estimated_improvement_percent: Estimated improvement percentage.

        Returns:
            Created IndexSuggestion object.
        """
        session = self.get_session()
        try:
            suggestion = IndexSuggestion(
                optimization_id=optimization_id,
                table_name=table_name,
                column_names=column_names,
                index_type=index_type,
                index_name=index_name,
                estimated_improvement_percent=estimated_improvement_percent,
            )
            session.add(suggestion)
            session.commit()
            session.refresh(suggestion)
            return suggestion
        finally:
            session.close()

    def get_index_suggestions(
        self, optimization_id: Optional[int] = None
    ) -> List[IndexSuggestion]:
        """Get index suggestions.

        Args:
            optimization_id: Optional optimization ID to filter by.

        Returns:
            List of IndexSuggestion objects.
        """
        session = self.get_session()
        try:
            query = session.query(IndexSuggestion)
            if optimization_id:
                query = query.filter(IndexSuggestion.optimization_id == optimization_id)
            return query.all()
        finally:
            session.close()

    def add_performance_report(
        self,
        report_id: str,
        database_id: int,
        report_type: str,
        total_queries: int,
        slow_queries: int,
        average_execution_time_ms: float,
        total_optimizations: int = 0,
        pending_optimizations: int = 0,
        report_data: Optional[str] = None,
    ) -> PerformanceReport:
        """Add performance report.

        Args:
            report_id: Report identifier.
            database_id: Database ID.
            report_type: Report type (daily, weekly, monthly, on_demand).
            total_queries: Total number of queries.
            slow_queries: Number of slow queries.
            average_execution_time_ms: Average execution time in milliseconds.
            total_optimizations: Total number of optimizations.
            pending_optimizations: Number of pending optimizations.
            report_data: Report data as JSON string.

        Returns:
            Created PerformanceReport object.
        """
        session = self.get_session()
        try:
            report = PerformanceReport(
                report_id=report_id,
                database_id=database_id,
                report_type=report_type,
                total_queries=total_queries,
                slow_queries=slow_queries,
                average_execution_time_ms=average_execution_time_ms,
                total_optimizations=total_optimizations,
                pending_optimizations=pending_optimizations,
                report_data=report_data,
            )
            session.add(report)
            session.commit()
            session.refresh(report)
            return report
        finally:
            session.close()

    def get_recent_reports(
        self, database_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[PerformanceReport]:
        """Get recent performance reports.

        Args:
            database_id: Optional database ID to filter by.
            limit: Maximum number of reports to return.

        Returns:
            List of PerformanceReport objects.
        """
        session = self.get_session()
        try:
            query = session.query(PerformanceReport).order_by(
                PerformanceReport.generated_at.desc()
            )
            if database_id:
                query = query.filter(PerformanceReport.database_id == database_id)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()
