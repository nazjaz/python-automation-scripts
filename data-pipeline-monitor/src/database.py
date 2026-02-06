"""Database models and operations for data pipeline monitoring."""

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


class Pipeline(Base):
    """Data pipeline definition."""

    __tablename__ = "pipelines"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    pipeline_type = Column(String(100))
    status = Column(String(20), default="active")
    health_status = Column(String(20), default="healthy")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    runs = relationship("PipelineRun", back_populates="pipeline")
    quality_checks = relationship("QualityCheck", back_populates="pipeline")
    alerts = relationship("Alert", back_populates="pipeline")


class PipelineRun(Base):
    """Pipeline execution run."""

    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False)
    run_id = Column(String(100), unique=True, nullable=False)
    status = Column(String(20), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    records_processed = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_message = Column(Text)
    metadata = Column(Text)

    pipeline = relationship("Pipeline", back_populates="runs")


class QualityCheck(Base):
    """Data quality check result."""

    __tablename__ = "quality_checks"

    id = Column(Integer, primary_key=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False)
    check_name = Column(String(200), nullable=False)
    check_type = Column(String(100))
    status = Column(String(20), nullable=False)
    severity = Column(String(20))
    result_value = Column(Float)
    threshold_value = Column(Float)
    message = Column(Text)
    checked_at = Column(DateTime, default=datetime.utcnow)

    pipeline = relationship("Pipeline", back_populates="quality_checks")


class Failure(Base):
    """Pipeline failure record."""

    __tablename__ = "failures"

    id = Column(Integer, primary_key=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False)
    run_id = Column(String(100))
    failure_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    error_message = Column(Text, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolution_status = Column(String(20), default="open")

    pipeline = relationship("Pipeline")


class RemediationWorkflow(Base):
    """Remediation workflow execution."""

    __tablename__ = "remediation_workflows"

    id = Column(Integer, primary_key=True)
    failure_id = Column(Integer, ForeignKey("failures.id"), nullable=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False)
    workflow_name = Column(String(200), nullable=False)
    workflow_type = Column(String(100))
    status = Column(String(20), default="pending")
    triggered_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result = Column(Text)
    error_message = Column(Text)

    pipeline = relationship("Pipeline")
    failure = relationship("Failure")


class Alert(Base):
    """Alert notification."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="sent")
    acknowledged_at = Column(DateTime, nullable=True)

    pipeline = relationship("Pipeline", back_populates="alerts")


class HealthMetric(Base):
    """Pipeline health metric."""

    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False)
    metric_name = Column(String(200), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))
    recorded_at = Column(DateTime, default=datetime.utcnow)

    pipeline = relationship("Pipeline")


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

    def add_pipeline(
        self,
        name: str,
        description: Optional[str] = None,
        pipeline_type: Optional[str] = None,
    ) -> Pipeline:
        """Add a new pipeline.

        Args:
            name: Pipeline name.
            description: Pipeline description.
            pipeline_type: Pipeline type.

        Returns:
            Created Pipeline object.
        """
        session = self.get_session()
        try:
            pipeline = Pipeline(
                name=name,
                description=description,
                pipeline_type=pipeline_type,
            )
            session.add(pipeline)
            session.commit()
            session.refresh(pipeline)
            return pipeline
        finally:
            session.close()

    def get_pipeline(self, pipeline_id: int) -> Optional[Pipeline]:
        """Get pipeline by ID.

        Args:
            pipeline_id: Pipeline ID.

        Returns:
            Pipeline object or None.
        """
        session = self.get_session()
        try:
            return session.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
        finally:
            session.close()

    def get_pipeline_by_name(self, name: str) -> Optional[Pipeline]:
        """Get pipeline by name.

        Args:
            name: Pipeline name.

        Returns:
            Pipeline object or None.
        """
        session = self.get_session()
        try:
            return session.query(Pipeline).filter(Pipeline.name == name).first()
        finally:
            session.close()

    def get_all_pipelines(self, status: Optional[str] = None) -> List[Pipeline]:
        """Get all pipelines.

        Args:
            status: Optional status filter.

        Returns:
            List of Pipeline objects.
        """
        session = self.get_session()
        try:
            query = session.query(Pipeline)
            if status:
                query = query.filter(Pipeline.status == status)
            return query.all()
        finally:
            session.close()

    def add_pipeline_run(
        self,
        pipeline_id: int,
        run_id: str,
        status: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        records_processed: int = 0,
        records_failed: int = 0,
        error_message: Optional[str] = None,
        metadata: Optional[str] = None,
    ) -> PipelineRun:
        """Add pipeline run.

        Args:
            pipeline_id: Pipeline ID.
            run_id: Run identifier.
            status: Run status (success, failed, running).
            start_time: Run start time.
            end_time: Run end time.
            records_processed: Number of records processed.
            records_failed: Number of records failed.
            error_message: Error message if failed.
            metadata: Additional metadata.

        Returns:
            Created PipelineRun object.
        """
        session = self.get_session()
        try:
            duration_seconds = None
            if end_time and start_time:
                duration_seconds = (end_time - start_time).total_seconds()

            pipeline_run = PipelineRun(
                pipeline_id=pipeline_id,
                run_id=run_id,
                status=status,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration_seconds,
                records_processed=records_processed,
                records_failed=records_failed,
                error_message=error_message,
                metadata=metadata,
            )
            session.add(pipeline_run)
            session.commit()
            session.refresh(pipeline_run)
            return pipeline_run
        finally:
            session.close()

    def get_recent_runs(
        self, pipeline_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[PipelineRun]:
        """Get recent pipeline runs.

        Args:
            pipeline_id: Optional pipeline ID to filter by.
            limit: Maximum number of runs to return.

        Returns:
            List of PipelineRun objects.
        """
        session = self.get_session()
        try:
            query = session.query(PipelineRun).order_by(PipelineRun.start_time.desc())
            if pipeline_id:
                query = query.filter(PipelineRun.pipeline_id == pipeline_id)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def add_quality_check(
        self,
        pipeline_id: int,
        check_name: str,
        check_type: str,
        status: str,
        severity: Optional[str] = None,
        result_value: Optional[float] = None,
        threshold_value: Optional[float] = None,
        message: Optional[str] = None,
    ) -> QualityCheck:
        """Add quality check result.

        Args:
            pipeline_id: Pipeline ID.
            check_name: Check name.
            check_type: Check type.
            status: Check status (passed, failed, warning).
            severity: Check severity.
            result_value: Check result value.
            threshold_value: Threshold value.
            message: Check message.

        Returns:
            Created QualityCheck object.
        """
        session = self.get_session()
        try:
            quality_check = QualityCheck(
                pipeline_id=pipeline_id,
                check_name=check_name,
                check_type=check_type,
                status=status,
                severity=severity,
                result_value=result_value,
                threshold_value=threshold_value,
                message=message,
            )
            session.add(quality_check)
            session.commit()
            session.refresh(quality_check)
            return quality_check
        finally:
            session.close()

    def add_failure(
        self,
        pipeline_id: int,
        failure_type: str,
        severity: str,
        error_message: str,
        run_id: Optional[str] = None,
    ) -> Failure:
        """Add failure record.

        Args:
            pipeline_id: Pipeline ID.
            failure_type: Failure type.
            severity: Failure severity (low, medium, high, critical).
            error_message: Error message.
            run_id: Optional run ID.

        Returns:
            Created Failure object.
        """
        session = self.get_session()
        try:
            failure = Failure(
                pipeline_id=pipeline_id,
                run_id=run_id,
                failure_type=failure_type,
                severity=severity,
                error_message=error_message,
            )
            session.add(failure)
            session.commit()
            session.refresh(failure)
            return failure
        finally:
            session.close()

    def get_open_failures(
        self, pipeline_id: Optional[int] = None
    ) -> List[Failure]:
        """Get open failures.

        Args:
            pipeline_id: Optional pipeline ID to filter by.

        Returns:
            List of Failure objects.
        """
        session = self.get_session()
        try:
            query = session.query(Failure).filter(
                Failure.resolution_status == "open"
            )
            if pipeline_id:
                query = query.filter(Failure.pipeline_id == pipeline_id)
            return query.order_by(Failure.detected_at.desc()).all()
        finally:
            session.close()

    def add_remediation_workflow(
        self,
        pipeline_id: int,
        workflow_name: str,
        workflow_type: str,
        failure_id: Optional[int] = None,
    ) -> RemediationWorkflow:
        """Add remediation workflow.

        Args:
            pipeline_id: Pipeline ID.
            workflow_name: Workflow name.
            workflow_type: Workflow type.
            failure_id: Optional failure ID.

        Returns:
            Created RemediationWorkflow object.
        """
        session = self.get_session()
        try:
            workflow = RemediationWorkflow(
                pipeline_id=pipeline_id,
                workflow_name=workflow_name,
                workflow_type=workflow_type,
                failure_id=failure_id,
            )
            session.add(workflow)
            session.commit()
            session.refresh(workflow)
            return workflow
        finally:
            session.close()

    def update_workflow_status(
        self,
        workflow_id: int,
        status: str,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update workflow status.

        Args:
            workflow_id: Workflow ID.
            status: Workflow status.
            result: Workflow result.
            error_message: Error message if failed.
        """
        session = self.get_session()
        try:
            workflow = (
                session.query(RemediationWorkflow)
                .filter(RemediationWorkflow.id == workflow_id)
                .first()
            )
            if workflow:
                workflow.status = status
                if status == "completed":
                    workflow.completed_at = datetime.utcnow()
                workflow.result = result
                workflow.error_message = error_message
                session.commit()
        finally:
            session.close()

    def add_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        pipeline_id: Optional[int] = None,
    ) -> Alert:
        """Add alert.

        Args:
            alert_type: Alert type.
            severity: Alert severity.
            title: Alert title.
            message: Alert message.
            pipeline_id: Optional pipeline ID.

        Returns:
            Created Alert object.
        """
        session = self.get_session()
        try:
            alert = Alert(
                pipeline_id=pipeline_id,
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
            )
            session.add(alert)
            session.commit()
            session.refresh(alert)
            return alert
        finally:
            session.close()

    def get_recent_alerts(
        self, pipeline_id: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Alert]:
        """Get recent alerts.

        Args:
            pipeline_id: Optional pipeline ID to filter by.
            limit: Maximum number of alerts to return.

        Returns:
            List of Alert objects.
        """
        session = self.get_session()
        try:
            query = session.query(Alert).order_by(Alert.sent_at.desc())
            if pipeline_id:
                query = query.filter(Alert.pipeline_id == pipeline_id)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def update_pipeline_health(
        self, pipeline_id: int, health_status: str
    ) -> None:
        """Update pipeline health status.

        Args:
            pipeline_id: Pipeline ID.
            health_status: Health status (healthy, degraded, unhealthy).
        """
        session = self.get_session()
        try:
            pipeline = session.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
            if pipeline:
                pipeline.health_status = health_status
                pipeline.updated_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()

    def add_health_metric(
        self,
        pipeline_id: int,
        metric_name: str,
        metric_value: float,
        metric_unit: Optional[str] = None,
    ) -> HealthMetric:
        """Add health metric.

        Args:
            pipeline_id: Pipeline ID.
            metric_name: Metric name.
            metric_value: Metric value.
            metric_unit: Metric unit.

        Returns:
            Created HealthMetric object.
        """
        session = self.get_session()
        try:
            metric = HealthMetric(
                pipeline_id=pipeline_id,
                metric_name=metric_name,
                metric_value=metric_value,
                metric_unit=metric_unit,
            )
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()
