"""Database models and operations for logistics monitoring."""

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


class Supplier(Base):
    """Supplier in the supply chain."""

    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True)
    supplier_id = Column(String(100), unique=True, nullable=False)
    supplier_name = Column(String(200), nullable=False)
    location = Column(String(200))
    contact_info = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    shipments = relationship("Shipment", back_populates="supplier")


class Shipment(Base):
    """Shipment in the supply chain."""

    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True)
    shipment_id = Column(String(100), unique=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    origin = Column(String(200), nullable=False)
    destination = Column(String(200), nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    shipped_at = Column(DateTime, nullable=True)
    estimated_delivery = Column(DateTime, nullable=True)
    actual_delivery = Column(DateTime, nullable=True)
    weight_kg = Column(Float)
    volume_m3 = Column(Float)
    priority = Column(String(20), default="normal")

    supplier = relationship("Supplier", back_populates="shipments")
    tracking_events = relationship("TrackingEvent", back_populates="shipment", cascade="all, delete-orphan")
    routes = relationship("Route", back_populates="shipment", cascade="all, delete-orphan")
    delays = relationship("Delay", back_populates="shipment", cascade="all, delete-orphan")


class TrackingEvent(Base):
    """Tracking event for shipment."""

    __tablename__ = "tracking_events"

    id = Column(Integer, primary_key=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    event_type = Column(String(100), nullable=False)
    location = Column(String(200))
    timestamp = Column(DateTime, nullable=False)
    description = Column(Text)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    shipment = relationship("Shipment", back_populates="tracking_events")


class Route(Base):
    """Route for shipment."""

    __tablename__ = "routes"

    id = Column(Integer, primary_key=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    route_name = Column(String(200))
    origin = Column(String(200), nullable=False)
    destination = Column(String(200), nullable=False)
    waypoints = Column(Text)
    distance_km = Column(Float)
    estimated_duration_hours = Column(Float)
    actual_duration_hours = Column(Float, nullable=True)
    cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_optimized = Column(String(10), default="false")

    shipment = relationship("Shipment", back_populates="routes")


class Delay(Base):
    """Delay prediction or occurrence."""

    __tablename__ = "delays"

    id = Column(Integer, primary_key=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    delay_type = Column(String(100), nullable=False)
    predicted_delay_hours = Column(Float)
    actual_delay_hours = Column(Float, nullable=True)
    reason = Column(Text)
    predicted_at = Column(DateTime, default=datetime.utcnow)
    occurred_at = Column(DateTime, nullable=True)
    severity = Column(String(20), default="medium")

    shipment = relationship("Shipment", back_populates="delays")


class OptimizationRecommendation(Base):
    """Route optimization recommendation."""

    __tablename__ = "optimization_recommendations"

    id = Column(Integer, primary_key=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True)
    recommendation_type = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    current_route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    recommended_route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    expected_savings_hours = Column(Float)
    expected_savings_cost = Column(Float)
    priority = Column(String(20), default="medium")
    generated_at = Column(DateTime, default=datetime.utcnow)

    shipment = relationship("Shipment")
    current_route = relationship("Route", foreign_keys=[current_route_id])
    recommended_route = relationship("Route", foreign_keys=[recommended_route_id])


class LogisticsMetric(Base):
    """Logistics performance metric."""

    __tablename__ = "logistics_metrics"

    id = Column(Integer, primary_key=True)
    time_window_start = Column(DateTime, nullable=False)
    time_window_end = Column(DateTime, nullable=False)
    total_shipments = Column(Integer, default=0)
    on_time_deliveries = Column(Integer, default=0)
    delayed_deliveries = Column(Integer, default=0)
    average_delay_hours = Column(Float)
    on_time_percentage = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


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

    def add_supplier(
        self,
        supplier_id: str,
        supplier_name: str,
        location: Optional[str] = None,
        contact_info: Optional[str] = None,
    ) -> Supplier:
        """Add a new supplier.

        Args:
            supplier_id: Supplier identifier.
            supplier_name: Supplier name.
            location: Supplier location.
            contact_info: Contact information.

        Returns:
            Created Supplier object.
        """
        session = self.get_session()
        try:
            supplier = Supplier(
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                location=location,
                contact_info=contact_info,
            )
            session.add(supplier)
            session.commit()
            session.refresh(supplier)
            return supplier
        finally:
            session.close()

    def get_supplier(self, supplier_id: str) -> Optional[Supplier]:
        """Get supplier by supplier ID.

        Args:
            supplier_id: Supplier identifier.

        Returns:
            Supplier object or None.
        """
        session = self.get_session()
        try:
            return session.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
        finally:
            session.close()

    def add_shipment(
        self,
        shipment_id: str,
        supplier_id: int,
        origin: str,
        destination: str,
        estimated_delivery: Optional[datetime] = None,
        weight_kg: Optional[float] = None,
        volume_m3: Optional[float] = None,
        priority: str = "normal",
    ) -> Shipment:
        """Add a new shipment.

        Args:
            shipment_id: Shipment identifier.
            supplier_id: Supplier ID.
            origin: Origin location.
            destination: Destination location.
            estimated_delivery: Estimated delivery datetime.
            weight_kg: Weight in kilograms.
            volume_m3: Volume in cubic meters.
            priority: Priority level (low, normal, high, urgent).

        Returns:
            Created Shipment object.
        """
        session = self.get_session()
        try:
            shipment = Shipment(
                shipment_id=shipment_id,
                supplier_id=supplier_id,
                origin=origin,
                destination=destination,
                estimated_delivery=estimated_delivery,
                weight_kg=weight_kg,
                volume_m3=volume_m3,
                priority=priority,
            )
            session.add(shipment)
            session.commit()
            session.refresh(shipment)
            return shipment
        finally:
            session.close()

    def get_shipment(self, shipment_id: str) -> Optional[Shipment]:
        """Get shipment by shipment ID.

        Args:
            shipment_id: Shipment identifier.

        Returns:
            Shipment object or None.
        """
        session = self.get_session()
        try:
            return session.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
        finally:
            session.close()

    def get_active_shipments(
        self, status: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Shipment]:
        """Get active shipments.

        Args:
            status: Optional status filter.
            limit: Maximum number of shipments to return.

        Returns:
            List of Shipment objects.
        """
        session = self.get_session()
        try:
            query = session.query(Shipment).order_by(Shipment.created_at.desc())
            if status:
                query = query.filter(Shipment.status == status)
            else:
                query = query.filter(Shipment.status.in_(["pending", "in_transit", "shipped"]))
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def update_shipment_status(
        self,
        shipment_id: str,
        status: str,
        shipped_at: Optional[datetime] = None,
        actual_delivery: Optional[datetime] = None,
    ) -> None:
        """Update shipment status.

        Args:
            shipment_id: Shipment identifier.
            status: New status.
            shipped_at: Shipment datetime.
            actual_delivery: Actual delivery datetime.
        """
        session = self.get_session()
        try:
            shipment = session.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
            if shipment:
                shipment.status = status
                if shipped_at:
                    shipment.shipped_at = shipped_at
                if actual_delivery:
                    shipment.actual_delivery = actual_delivery
                session.commit()
        finally:
            session.close()

    def add_tracking_event(
        self,
        shipment_id: int,
        event_type: str,
        timestamp: datetime,
        location: Optional[str] = None,
        description: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> TrackingEvent:
        """Add tracking event.

        Args:
            shipment_id: Shipment ID.
            event_type: Event type (departed, in_transit, arrived, delayed, etc.).
            timestamp: Event timestamp.
            location: Location description.
            description: Event description.
            latitude: Latitude coordinate.
            longitude: Longitude coordinate.

        Returns:
            Created TrackingEvent object.
        """
        session = self.get_session()
        try:
            event = TrackingEvent(
                shipment_id=shipment_id,
                event_type=event_type,
                timestamp=timestamp,
                location=location,
                description=description,
                latitude=latitude,
                longitude=longitude,
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return event
        finally:
            session.close()

    def get_shipment_tracking_events(
        self, shipment_id: int, limit: Optional[int] = None
    ) -> List[TrackingEvent]:
        """Get tracking events for shipment.

        Args:
            shipment_id: Shipment ID.
            limit: Maximum number of events to return.

        Returns:
            List of TrackingEvent objects ordered by timestamp.
        """
        session = self.get_session()
        try:
            query = (
                session.query(TrackingEvent)
                .filter(TrackingEvent.shipment_id == shipment_id)
                .order_by(TrackingEvent.timestamp.asc())
            )
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def add_route(
        self,
        shipment_id: int,
        origin: str,
        destination: str,
        distance_km: float,
        estimated_duration_hours: float,
        cost: Optional[float] = None,
        waypoints: Optional[str] = None,
        is_optimized: str = "false",
    ) -> Route:
        """Add route for shipment.

        Args:
            shipment_id: Shipment ID.
            origin: Origin location.
            destination: Destination location.
            distance_km: Distance in kilometers.
            estimated_duration_hours: Estimated duration in hours.
            cost: Route cost.
            waypoints: Waypoints as JSON string.
            is_optimized: Whether route is optimized (true/false).

        Returns:
            Created Route object.
        """
        session = self.get_session()
        try:
            route = Route(
                shipment_id=shipment_id,
                origin=origin,
                destination=destination,
                distance_km=distance_km,
                estimated_duration_hours=estimated_duration_hours,
                cost=cost,
                waypoints=waypoints,
                is_optimized=is_optimized,
            )
            session.add(route)
            session.commit()
            session.refresh(route)
            return route
        finally:
            session.close()

    def get_shipment_routes(self, shipment_id: int) -> List[Route]:
        """Get routes for shipment.

        Args:
            shipment_id: Shipment ID.

        Returns:
            List of Route objects.
        """
        session = self.get_session()
        try:
            return (
                session.query(Route)
                .filter(Route.shipment_id == shipment_id)
                .order_by(Route.created_at.desc())
                .all()
            )
        finally:
            session.close()

    def add_delay(
        self,
        shipment_id: int,
        delay_type: str,
        predicted_delay_hours: float,
        reason: Optional[str] = None,
        severity: str = "medium",
    ) -> Delay:
        """Add delay prediction or occurrence.

        Args:
            shipment_id: Shipment ID.
            delay_type: Delay type (weather, traffic, customs, etc.).
            predicted_delay_hours: Predicted delay in hours.
            reason: Delay reason.
            severity: Severity level (low, medium, high, critical).

        Returns:
            Created Delay object.
        """
        session = self.get_session()
        try:
            delay = Delay(
                shipment_id=shipment_id,
                delay_type=delay_type,
                predicted_delay_hours=predicted_delay_hours,
                reason=reason,
                severity=severity,
            )
            session.add(delay)
            session.commit()
            session.refresh(delay)
            return delay
        finally:
            session.close()

    def get_shipment_delays(
        self, shipment_id: int, limit: Optional[int] = None
    ) -> List[Delay]:
        """Get delays for shipment.

        Args:
            shipment_id: Shipment ID.
            limit: Maximum number of delays to return.

        Returns:
            List of Delay objects.
        """
        session = self.get_session()
        try:
            query = (
                session.query(Delay)
                .filter(Delay.shipment_id == shipment_id)
                .order_by(Delay.predicted_at.desc())
            )
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def add_optimization_recommendation(
        self,
        shipment_id: Optional[int],
        recommendation_type: str,
        title: str,
        description: str,
        expected_savings_hours: Optional[float] = None,
        expected_savings_cost: Optional[float] = None,
        current_route_id: Optional[int] = None,
        recommended_route_id: Optional[int] = None,
        priority: str = "medium",
    ) -> OptimizationRecommendation:
        """Add optimization recommendation.

        Args:
            shipment_id: Optional shipment ID.
            recommendation_type: Recommendation type.
            title: Recommendation title.
            description: Recommendation description.
            expected_savings_hours: Expected time savings in hours.
            expected_savings_cost: Expected cost savings.
            current_route_id: Current route ID.
            recommended_route_id: Recommended route ID.
            priority: Priority level (low, medium, high, urgent).

        Returns:
            Created OptimizationRecommendation object.
        """
        session = self.get_session()
        try:
            recommendation = OptimizationRecommendation(
                shipment_id=shipment_id,
                recommendation_type=recommendation_type,
                title=title,
                description=description,
                expected_savings_hours=expected_savings_hours,
                expected_savings_cost=expected_savings_cost,
                current_route_id=current_route_id,
                recommended_route_id=recommended_route_id,
                priority=priority,
            )
            session.add(recommendation)
            session.commit()
            session.refresh(recommendation)
            return recommendation
        finally:
            session.close()

    def get_optimization_recommendations(
        self, shipment_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[OptimizationRecommendation]:
        """Get optimization recommendations.

        Args:
            shipment_id: Optional shipment ID to filter by.
            limit: Maximum number of recommendations to return.

        Returns:
            List of OptimizationRecommendation objects.
        """
        session = self.get_session()
        try:
            query = session.query(OptimizationRecommendation).order_by(
                OptimizationRecommendation.priority.desc(),
                OptimizationRecommendation.expected_savings_hours.desc(),
            )
            if shipment_id:
                query = query.filter(OptimizationRecommendation.shipment_id == shipment_id)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def add_logistics_metric(
        self,
        time_window_start: datetime,
        time_window_end: datetime,
        total_shipments: int,
        on_time_deliveries: int,
        delayed_deliveries: int,
        average_delay_hours: Optional[float] = None,
    ) -> LogisticsMetric:
        """Add logistics performance metric.

        Args:
            time_window_start: Start of time window.
            time_window_end: End of time window.
            total_shipments: Total number of shipments.
            on_time_deliveries: Number of on-time deliveries.
            delayed_deliveries: Number of delayed deliveries.
            average_delay_hours: Average delay in hours.

        Returns:
            Created LogisticsMetric object.
        """
        session = self.get_session()
        try:
            on_time_percentage = (
                on_time_deliveries / total_shipments * 100 if total_shipments > 0 else 0.0
            )

            metric = LogisticsMetric(
                time_window_start=time_window_start,
                time_window_end=time_window_end,
                total_shipments=total_shipments,
                on_time_deliveries=on_time_deliveries,
                delayed_deliveries=delayed_deliveries,
                average_delay_hours=average_delay_hours,
                on_time_percentage=on_time_percentage,
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()

    def get_recent_metrics(self, days: int = 7) -> List[LogisticsMetric]:
        """Get recent logistics metrics.

        Args:
            days: Number of days to look back.

        Returns:
            List of LogisticsMetric objects.
        """
        session = self.get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            return (
                session.query(LogisticsMetric)
                .filter(LogisticsMetric.time_window_start >= cutoff)
                .order_by(LogisticsMetric.time_window_start.desc())
                .all()
            )
        finally:
            session.close()
