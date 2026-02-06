"""Database models and operations for cloud resource monitor data."""

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


class CloudResource(Base):
    """Database model for cloud resources."""

    __tablename__ = "cloud_resources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(String(100), unique=True, nullable=False, index=True)
    resource_name = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=False, index=True)
    cloud_provider = Column(String(50), nullable=False, index=True)
    region = Column(String(100))
    instance_type = Column(String(100))
    state = Column(String(50), default="running", index=True)
    cost_per_hour = Column(Float)
    tags = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    metrics = relationship("ResourceMetric", back_populates="resource", cascade="all, delete-orphan")
    recommendations = relationship("RightSizingRecommendation", back_populates="resource", cascade="all, delete-orphan")
    scaling_actions = relationship("ScalingAction", back_populates="resource", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<CloudResource(id={self.id}, resource_id={self.resource_id}, "
            f"resource_type={self.resource_type}, state={self.state})>"
        )


class ResourceMetric(Base):
    """Database model for resource utilization metrics."""

    __tablename__ = "resource_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(Integer, ForeignKey("cloud_resources.id"), nullable=False, index=True)
    metric_type = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_timestamp = Column(DateTime, nullable=False, index=True)
    unit = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    resource = relationship("CloudResource", back_populates="metrics")

    def __repr__(self) -> str:
        return (
            f"<ResourceMetric(id={self.id}, resource_id={self.resource_id}, "
            f"metric_type={self.metric_type}, metric_value={self.metric_value})>"
        )


class RightSizingRecommendation(Base):
    """Database model for right-sizing recommendations."""

    __tablename__ = "right_sizing_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(Integer, ForeignKey("cloud_resources.id"), nullable=False, index=True)
    recommendation_type = Column(String(50), nullable=False, index=True)
    current_instance_type = Column(String(100))
    recommended_instance_type = Column(String(100))
    estimated_cost_savings = Column(Float)
    estimated_cost_increase = Column(Float)
    utilization_analysis = Column(Text)
    priority = Column(String(50), default="medium", index=True)
    implemented = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    implemented_at = Column(DateTime)

    resource = relationship("CloudResource", back_populates="recommendations")

    def __repr__(self) -> str:
        return (
            f"<RightSizingRecommendation(id={self.id}, resource_id={self.resource_id}, "
            f"recommendation_type={self.recommendation_type}, priority={self.priority})>"
        )


class ScalingAction(Base):
    """Database model for scaling actions."""

    __tablename__ = "scaling_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(Integer, ForeignKey("cloud_resources.id"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)
    scaling_reason = Column(Text, nullable=False)
    current_capacity = Column(Integer)
    target_capacity = Column(Integer)
    triggered_by_metric = Column(String(100))
    metric_value = Column(Float)
    status = Column(String(50), default="pending", index=True)
    executed_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    resource = relationship("CloudResource", back_populates="scaling_actions")

    def __repr__(self) -> str:
        return (
            f"<ScalingAction(id={self.id}, resource_id={self.resource_id}, "
            f"action_type={self.action_type}, status={self.status})>"
        )


class IdleResource(Base):
    """Database model for identified idle resources."""

    __tablename__ = "idle_resources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(Integer, ForeignKey("cloud_resources.id"), nullable=False, index=True)
    idle_since = Column(DateTime, nullable=False, index=True)
    idle_duration_hours = Column(Float)
    idle_metrics = Column(Text)
    action_taken = Column(String(100))
    action_taken_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return (
            f"<IdleResource(id={self.id}, resource_id={self.resource_id}, "
            f"idle_duration_hours={self.idle_duration_hours})>"
        )


class DemandPattern(Base):
    """Database model for demand patterns."""

    __tablename__ = "demand_patterns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(Integer, ForeignKey("cloud_resources.id"), nullable=False, index=True)
    pattern_type = Column(String(100), nullable=False, index=True)
    pattern_description = Column(Text)
    peak_hours = Column(Text)
    low_hours = Column(Text)
    predicted_demand = Column(Float)
    confidence_score = Column(Float)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return (
            f"<DemandPattern(id={self.id}, resource_id={self.resource_id}, "
            f"pattern_type={self.pattern_type})>"
        )


class DatabaseManager:
    """Manages database operations for cloud resource monitor data."""

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

    def add_resource(
        self,
        resource_id: str,
        resource_name: str,
        resource_type: str,
        cloud_provider: str,
        region: Optional[str] = None,
        instance_type: Optional[str] = None,
        state: str = "running",
        cost_per_hour: Optional[float] = None,
        tags: Optional[str] = None,
    ) -> CloudResource:
        """Add or update cloud resource.

        Args:
            resource_id: Resource ID.
            resource_name: Resource name.
            resource_type: Resource type.
            cloud_provider: Cloud provider.
            region: Optional region.
            instance_type: Optional instance type.
            state: Resource state.
            cost_per_hour: Optional cost per hour.
            tags: Optional tags.

        Returns:
            CloudResource object.
        """
        session = self.get_session()
        try:
            resource = (
                session.query(CloudResource)
                .filter(CloudResource.resource_id == resource_id)
                .first()
            )

            if resource is None:
                resource = CloudResource(
                    resource_id=resource_id,
                    resource_name=resource_name,
                    resource_type=resource_type,
                    cloud_provider=cloud_provider,
                    region=region,
                    instance_type=instance_type,
                    state=state,
                    cost_per_hour=cost_per_hour,
                    tags=tags,
                )
                session.add(resource)
            else:
                resource.resource_name = resource_name
                resource.resource_type = resource_type
                resource.cloud_provider = cloud_provider
                resource.region = region
                resource.instance_type = instance_type
                resource.state = state
                resource.cost_per_hour = cost_per_hour
                resource.tags = tags
                resource.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(resource)
            return resource
        finally:
            session.close()

    def add_metric(
        self,
        resource_id: int,
        metric_type: str,
        metric_value: float,
        metric_timestamp: datetime,
        unit: Optional[str] = None,
    ) -> ResourceMetric:
        """Add resource metric.

        Args:
            resource_id: Resource ID.
            metric_type: Metric type.
            metric_value: Metric value.
            metric_timestamp: Metric timestamp.
            unit: Optional unit.

        Returns:
            ResourceMetric object.
        """
        session = self.get_session()
        try:
            metric = ResourceMetric(
                resource_id=resource_id,
                metric_type=metric_type,
                metric_value=metric_value,
                metric_timestamp=metric_timestamp,
                unit=unit,
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()

    def add_recommendation(
        self,
        resource_id: int,
        recommendation_type: str,
        current_instance_type: Optional[str] = None,
        recommended_instance_type: Optional[str] = None,
        estimated_cost_savings: Optional[float] = None,
        estimated_cost_increase: Optional[float] = None,
        utilization_analysis: Optional[str] = None,
        priority: str = "medium",
    ) -> RightSizingRecommendation:
        """Add right-sizing recommendation.

        Args:
            resource_id: Resource ID.
            recommendation_type: Recommendation type.
            current_instance_type: Optional current instance type.
            recommended_instance_type: Optional recommended instance type.
            estimated_cost_savings: Optional estimated cost savings.
            estimated_cost_increase: Optional estimated cost increase.
            utilization_analysis: Optional utilization analysis.
            priority: Priority level.

        Returns:
            RightSizingRecommendation object.
        """
        session = self.get_session()
        try:
            recommendation = RightSizingRecommendation(
                resource_id=resource_id,
                recommendation_type=recommendation_type,
                current_instance_type=current_instance_type,
                recommended_instance_type=recommended_instance_type,
                estimated_cost_savings=estimated_cost_savings,
                estimated_cost_increase=estimated_cost_increase,
                utilization_analysis=utilization_analysis,
                priority=priority,
            )
            session.add(recommendation)
            session.commit()
            session.refresh(recommendation)
            return recommendation
        finally:
            session.close()

    def add_scaling_action(
        self,
        resource_id: int,
        action_type: str,
        scaling_reason: str,
        current_capacity: Optional[int] = None,
        target_capacity: Optional[int] = None,
        triggered_by_metric: Optional[str] = None,
        metric_value: Optional[float] = None,
    ) -> ScalingAction:
        """Add scaling action.

        Args:
            resource_id: Resource ID.
            action_type: Action type (scale_up, scale_down).
            scaling_reason: Scaling reason.
            current_capacity: Optional current capacity.
            target_capacity: Optional target capacity.
            triggered_by_metric: Optional metric that triggered scaling.
            metric_value: Optional metric value.

        Returns:
            ScalingAction object.
        """
        session = self.get_session()
        try:
            action = ScalingAction(
                resource_id=resource_id,
                action_type=action_type,
                scaling_reason=scaling_reason,
                current_capacity=current_capacity,
                target_capacity=target_capacity,
                triggered_by_metric=triggered_by_metric,
                metric_value=metric_value,
            )
            session.add(action)
            session.commit()
            session.refresh(action)
            return action
        finally:
            session.close()

    def get_resources(
        self,
        resource_type: Optional[str] = None,
        cloud_provider: Optional[str] = None,
        state: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[CloudResource]:
        """Get resources with optional filtering.

        Args:
            resource_type: Optional resource type filter.
            cloud_provider: Optional cloud provider filter.
            state: Optional state filter.
            limit: Optional limit on number of results.

        Returns:
            List of CloudResource objects.
        """
        session = self.get_session()
        try:
            query = session.query(CloudResource)

            if resource_type:
                query = query.filter(CloudResource.resource_type == resource_type)

            if cloud_provider:
                query = query.filter(CloudResource.cloud_provider == cloud_provider)

            if state:
                query = query.filter(CloudResource.state == state)

            query = query.order_by(CloudResource.created_at.desc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_unimplemented_recommendations(
        self,
        resource_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[RightSizingRecommendation]:
        """Get unimplemented recommendations.

        Args:
            resource_id: Optional resource ID filter.
            limit: Optional limit on number of results.

        Returns:
            List of unimplemented RightSizingRecommendation objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(RightSizingRecommendation)
                .filter(RightSizingRecommendation.implemented == False)
            )

            if resource_id:
                query = query.filter(RightSizingRecommendation.resource_id == resource_id)

            query = query.order_by(RightSizingRecommendation.priority.desc(), RightSizingRecommendation.created_at.desc())

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_pending_scaling_actions(
        self,
        limit: Optional[int] = None,
    ) -> List[ScalingAction]:
        """Get pending scaling actions.

        Args:
            limit: Optional limit on number of results.

        Returns:
            List of pending ScalingAction objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(ScalingAction)
                .filter(ScalingAction.status == "pending")
                .order_by(ScalingAction.created_at.desc())
            )

            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()
