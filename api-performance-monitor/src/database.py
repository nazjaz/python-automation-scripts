"""Database models and operations for API performance monitoring data."""

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


class APIEndpoint(Base):
    """Database model for API endpoints."""

    __tablename__ = "api_endpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    base_url = Column(String(500), nullable=False, index=True)
    path = Column(String(500), nullable=False, index=True)
    method = Column(String(10), default="GET", index=True)
    full_url = Column(String(1000), unique=True, nullable=False, index=True)
    description = Column(Text)
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requests = relationship("APIRequest", back_populates="endpoint", cascade="all, delete-orphan")
    metrics = relationship("EndpointMetric", back_populates="endpoint", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<APIEndpoint(id={self.id}, full_url={self.full_url}, method={self.method})>"


class APIRequest(Base):
    """Database model for API requests."""

    __tablename__ = "api_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint_id = Column(Integer, ForeignKey("api_endpoints.id"), nullable=False, index=True)
    request_time = Column(DateTime, nullable=False, index=True)
    response_time_ms = Column(Float, nullable=False, index=True)
    status_code = Column(Integer, index=True)
    response_size_bytes = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    endpoint = relationship("APIEndpoint", back_populates="requests")

    def __repr__(self) -> str:
        return (
            f"<APIRequest(id={self.id}, endpoint_id={self.endpoint_id}, "
            f"response_time_ms={self.response_time_ms}, status_code={self.status_code})>"
        )


class EndpointMetric(Base):
    """Database model for endpoint performance metrics."""

    __tablename__ = "endpoint_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint_id = Column(Integer, ForeignKey("api_endpoints.id"), nullable=False, index=True)
    metric_time = Column(DateTime, nullable=False, index=True)
    avg_response_time_ms = Column(Float)
    min_response_time_ms = Column(Float)
    max_response_time_ms = Column(Float)
    p50_response_time_ms = Column(Float)
    p75_response_time_ms = Column(Float)
    p90_response_time_ms = Column(Float)
    p95_response_time_ms = Column(Float)
    p99_response_time_ms = Column(Float)
    request_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    error_rate = Column(Float)
    throughput_per_second = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    endpoint = relationship("APIEndpoint", back_populates="metrics")

    def __repr__(self) -> str:
        return (
            f"<EndpointMetric(id={self.id}, endpoint_id={self.endpoint_id}, "
            f"avg_response_time_ms={self.avg_response_time_ms}, request_count={self.request_count})>"
        )


class Bottleneck(Base):
    """Database model for identified bottlenecks."""

    __tablename__ = "bottlenecks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint_id = Column(Integer, ForeignKey("api_endpoints.id"), nullable=False, index=True)
    bottleneck_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    impact_percentage = Column(Float)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime)

    def __repr__(self) -> str:
        return (
            f"<Bottleneck(id={self.id}, endpoint_id={self.endpoint_id}, "
            f"bottleneck_type={self.bottleneck_type}, severity={self.severity})>"
        )


class OptimizationRecommendation(Base):
    """Database model for optimization recommendations."""

    __tablename__ = "optimization_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint_id = Column(Integer, ForeignKey("api_endpoints.id"), nullable=False, index=True)
    recommendation_type = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(50), default="medium", index=True)
    estimated_improvement = Column(Float)
    implemented = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    implemented_at = Column(DateTime)

    def __repr__(self) -> str:
        return (
            f"<OptimizationRecommendation(id={self.id}, endpoint_id={self.endpoint_id}, "
            f"recommendation_type={self.recommendation_type}, priority={self.priority})>"
        )


class DatabaseManager:
    """Manages database operations for API performance monitoring data."""

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

    def add_endpoint(
        self,
        base_url: str,
        path: str,
        method: str = "GET",
        description: Optional[str] = None,
    ) -> APIEndpoint:
        """Add or update API endpoint.

        Args:
            base_url: Base URL of the API.
            path: Endpoint path.
            method: HTTP method.
            description: Optional description.

        Returns:
            APIEndpoint object.
        """
        full_url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"

        session = self.get_session()
        try:
            endpoint = (
                session.query(APIEndpoint)
                .filter(APIEndpoint.full_url == full_url, APIEndpoint.method == method)
                .first()
            )

            if endpoint is None:
                endpoint = APIEndpoint(
                    base_url=base_url,
                    path=path,
                    method=method,
                    full_url=full_url,
                    description=description,
                )
                session.add(endpoint)
            else:
                endpoint.description = description
                endpoint.active = True
                endpoint.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(endpoint)
            return endpoint
        finally:
            session.close()

    def add_request(
        self,
        endpoint_id: int,
        response_time_ms: float,
        status_code: Optional[int] = None,
        response_size_bytes: Optional[int] = None,
        error_message: Optional[str] = None,
        request_time: Optional[datetime] = None,
    ) -> APIRequest:
        """Add API request record.

        Args:
            endpoint_id: Endpoint ID.
            response_time_ms: Response time in milliseconds.
            status_code: Optional HTTP status code.
            response_size_bytes: Optional response size in bytes.
            error_message: Optional error message.
            request_time: Optional request timestamp.

        Returns:
            APIRequest object.
        """
        session = self.get_session()
        try:
            request = APIRequest(
                endpoint_id=endpoint_id,
                request_time=request_time or datetime.utcnow(),
                response_time_ms=response_time_ms,
                status_code=status_code,
                response_size_bytes=response_size_bytes,
                error_message=error_message,
            )
            session.add(request)
            session.commit()
            session.refresh(request)
            return request
        finally:
            session.close()

    def add_metric(
        self,
        endpoint_id: int,
        avg_response_time_ms: Optional[float] = None,
        min_response_time_ms: Optional[float] = None,
        max_response_time_ms: Optional[float] = None,
        p50_response_time_ms: Optional[float] = None,
        p75_response_time_ms: Optional[float] = None,
        p90_response_time_ms: Optional[float] = None,
        p95_response_time_ms: Optional[float] = None,
        p99_response_time_ms: Optional[float] = None,
        request_count: int = 0,
        success_count: int = 0,
        error_count: int = 0,
        error_rate: Optional[float] = None,
        throughput_per_second: Optional[float] = None,
        metric_time: Optional[datetime] = None,
    ) -> EndpointMetric:
        """Add endpoint metric.

        Args:
            endpoint_id: Endpoint ID.
            avg_response_time_ms: Average response time.
            min_response_time_ms: Minimum response time.
            max_response_time_ms: Maximum response time.
            p50_response_time_ms: 50th percentile response time.
            p75_response_time_ms: 75th percentile response time.
            p90_response_time_ms: 90th percentile response time.
            p95_response_time_ms: 95th percentile response time.
            p99_response_time_ms: 99th percentile response time.
            request_count: Total request count.
            success_count: Success count.
            error_count: Error count.
            error_rate: Error rate.
            throughput_per_second: Throughput per second.
            metric_time: Optional metric timestamp.

        Returns:
            EndpointMetric object.
        """
        session = self.get_session()
        try:
            metric = EndpointMetric(
                endpoint_id=endpoint_id,
                metric_time=metric_time or datetime.utcnow(),
                avg_response_time_ms=avg_response_time_ms,
                min_response_time_ms=min_response_time_ms,
                max_response_time_ms=max_response_time_ms,
                p50_response_time_ms=p50_response_time_ms,
                p75_response_time_ms=p75_response_time_ms,
                p90_response_time_ms=p90_response_time_ms,
                p95_response_time_ms=p95_response_time_ms,
                p99_response_time_ms=p99_response_time_ms,
                request_count=request_count,
                success_count=success_count,
                error_count=error_count,
                error_rate=error_rate,
                throughput_per_second=throughput_per_second,
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()

    def add_bottleneck(
        self,
        endpoint_id: int,
        bottleneck_type: str,
        severity: str,
        description: str,
        impact_percentage: Optional[float] = None,
    ) -> Bottleneck:
        """Add bottleneck record.

        Args:
            endpoint_id: Endpoint ID.
            bottleneck_type: Type of bottleneck.
            severity: Severity level.
            description: Bottleneck description.
            impact_percentage: Optional impact percentage.

        Returns:
            Bottleneck object.
        """
        session = self.get_session()
        try:
            bottleneck = Bottleneck(
                endpoint_id=endpoint_id,
                bottleneck_type=bottleneck_type,
                severity=severity,
                description=description,
                impact_percentage=impact_percentage,
            )
            session.add(bottleneck)
            session.commit()
            session.refresh(bottleneck)
            return bottleneck
        finally:
            session.close()

    def add_recommendation(
        self,
        endpoint_id: int,
        recommendation_type: str,
        title: str,
        description: str,
        priority: str = "medium",
        estimated_improvement: Optional[float] = None,
    ) -> OptimizationRecommendation:
        """Add optimization recommendation.

        Args:
            endpoint_id: Endpoint ID.
            recommendation_type: Type of recommendation.
            title: Recommendation title.
            description: Recommendation description.
            priority: Priority level.
            estimated_improvement: Optional estimated improvement percentage.

        Returns:
            OptimizationRecommendation object.
        """
        session = self.get_session()
        try:
            recommendation = OptimizationRecommendation(
                endpoint_id=endpoint_id,
                recommendation_type=recommendation_type,
                title=title,
                description=description,
                priority=priority,
                estimated_improvement=estimated_improvement,
            )
            session.add(recommendation)
            session.commit()
            session.refresh(recommendation)
            return recommendation
        finally:
            session.close()

    def get_endpoints(
        self,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[APIEndpoint]:
        """Get endpoints with optional filtering.

        Args:
            active_only: Whether to return only active endpoints.
            limit: Optional limit on number of results.

        Returns:
            List of APIEndpoint objects.
        """
        session = self.get_session()
        try:
            query = session.query(APIEndpoint)

            if active_only:
                query = query.filter(APIEndpoint.active == True)

            query = query.order_by(APIEndpoint.created_at.desc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_requests(
        self,
        endpoint_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[APIRequest]:
        """Get requests with optional filtering.

        Args:
            endpoint_id: Optional endpoint ID filter.
            start_time: Optional start time filter.
            end_time: Optional end time filter.
            limit: Optional limit on number of results.

        Returns:
            List of APIRequest objects.
        """
        session = self.get_session()
        try:
            query = session.query(APIRequest)

            if endpoint_id:
                query = query.filter(APIRequest.endpoint_id == endpoint_id)

            if start_time:
                query = query.filter(APIRequest.request_time >= start_time)

            if end_time:
                query = query.filter(APIRequest.request_time <= end_time)

            query = query.order_by(APIRequest.request_time.desc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_unresolved_bottlenecks(
        self, limit: Optional[int] = None
    ) -> List[Bottleneck]:
        """Get unresolved bottlenecks.

        Args:
            limit: Optional limit on number of results.

        Returns:
            List of unresolved Bottleneck objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(Bottleneck)
                .filter(Bottleneck.resolved == False)
                .order_by(Bottleneck.detected_at.desc())
            )

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_unimplemented_recommendations(
        self, limit: Optional[int] = None
    ) -> List[OptimizationRecommendation]:
        """Get unimplemented recommendations.

        Args:
            limit: Optional limit on number of results.

        Returns:
            List of unimplemented OptimizationRecommendation objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(OptimizationRecommendation)
                .filter(OptimizationRecommendation.implemented == False)
                .order_by(OptimizationRecommendation.created_at.desc())
            )

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()
