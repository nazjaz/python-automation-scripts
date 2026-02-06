"""Application Uptime Monitor.

Monitors application uptime across multiple regions, tracks performance
degradation, and automatically routes traffic to healthy instances with failover.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import requests
import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class InstanceStatus(str, Enum):
    """Instance health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class RegionConfig(BaseModel):
    """Configuration for a deployment region."""

    name: str = Field(..., description="Region identifier")
    instances: List[str] = Field(
        ..., description="List of instance URLs/endpoints"
    )
    health_check_endpoint: str = Field(
        default="/health",
        description="Health check endpoint path",
    )
    health_check_timeout: float = Field(
        default=5.0, description="Health check timeout in seconds"
    )
    priority: int = Field(
        default=1, description="Routing priority (lower number = higher priority)"
    )


class PerformanceThresholds(BaseModel):
    """Performance degradation thresholds."""

    max_response_time_ms: float = Field(
        default=500.0, description="Maximum acceptable response time in milliseconds"
    )
    min_success_rate: float = Field(
        default=0.95, description="Minimum acceptable success rate (0.0-1.0)"
    )
    degradation_window_minutes: int = Field(
        default=5,
        description="Time window for detecting degradation in minutes",
    )
    consecutive_failures_threshold: int = Field(
        default=3, description="Consecutive failures before marking unhealthy"
    )


class RoutingConfig(BaseModel):
    """Traffic routing configuration."""

    routing_strategy: str = Field(
        default="priority",
        description="Routing strategy: priority, round_robin, or least_latency",
    )
    failover_enabled: bool = Field(
        default=True, description="Enable automatic failover to backup regions"
    )
    health_check_interval_seconds: int = Field(
        default=30, description="Interval between health checks"
    )
    metrics_retention_hours: int = Field(
        default=24, description="Hours to retain performance metrics"
    )


class Config(BaseModel):
    """Main configuration model."""

    regions: List[RegionConfig] = Field(
        ..., description="List of deployment regions"
    )
    performance: PerformanceThresholds = Field(
        default_factory=PerformanceThresholds,
        description="Performance degradation thresholds",
    )
    routing: RoutingConfig = Field(
        default_factory=RoutingConfig, description="Traffic routing settings"
    )
    metrics_file: str = Field(
        default="logs/metrics.json",
        description="Path to store performance metrics",
    )
    routing_state_file: str = Field(
        default="logs/routing_state.json",
        description="Path to store current routing state",
    )


class AppSettings(BaseSettings):
    """Application settings from environment variables."""

    config_path: str = "config.yaml"
    api_key: Optional[str] = Field(default=None, description="API key for health checks")


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""

    instance_url: str
    region: str
    status: InstanceStatus
    response_time_ms: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None


@dataclass
class InstanceMetrics:
    """Performance metrics for an instance."""

    instance_url: str
    region: str
    health_checks: List[HealthCheckResult] = field(default_factory=list)
    current_status: InstanceStatus = InstanceStatus.UNKNOWN
    consecutive_failures: int = 0
    last_healthy_time: Optional[datetime] = None

    def get_recent_checks(
        self, window_minutes: int
    ) -> List[HealthCheckResult]:
        """Get health checks within time window."""
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        return [
            check
            for check in self.health_checks
            if check.timestamp >= cutoff
        ]

    def calculate_success_rate(self, window_minutes: int) -> float:
        """Calculate success rate within time window."""
        recent = self.get_recent_checks(window_minutes)
        if not recent:
            return 1.0
        successful = sum(1 for check in recent if check.success)
        return successful / len(recent)

    def calculate_avg_response_time(self, window_minutes: int) -> float:
        """Calculate average response time within time window."""
        recent = self.get_recent_checks(window_minutes)
        if not recent:
            return 0.0
        successful_checks = [c for c in recent if c.success]
        if not successful_checks:
            return float("inf")
        return sum(c.response_time_ms for c in successful_checks) / len(
            successful_checks
        )


@dataclass
class RoutingState:
    """Current traffic routing state."""

    active_instances: List[str] = field(default_factory=list)
    backup_instances: List[str] = field(default_factory=list)
    last_update: Optional[datetime] = None
    routing_strategy: str = "priority"


def load_config(config_path: Path) -> Config:
    """Load and validate configuration from YAML file.

    Args:
        config_path: Path to configuration YAML file

    Returns:
        Validated configuration object

    Raises:
        FileNotFoundError: If config file does not exist
        ValueError: If configuration is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        config = Config(**config_data)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in configuration file: {e}")
        raise ValueError(f"Invalid YAML configuration: {e}") from e
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


def perform_health_check(
    instance_url: str,
    region_config: RegionConfig,
    timeout: float,
    api_key: Optional[str] = None,
) -> HealthCheckResult:
    """Perform health check on an instance.

    Args:
        instance_url: Base URL of the instance
        region_config: Region configuration
        timeout: Request timeout in seconds
        api_key: Optional API key for authentication

    Returns:
        HealthCheckResult with check outcome
    """
    health_url = f"{instance_url.rstrip('/')}{region_config.health_check_endpoint}"
    start_time = time.time()

    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        response = requests.get(
            health_url, timeout=timeout, headers=headers
        )
        response_time_ms = (time.time() - start_time) * 1000

        if response.status_code == 200:
            status = InstanceStatus.HEALTHY
            success = True
            error_message = None
        else:
            status = InstanceStatus.UNHEALTHY
            success = False
            error_message = f"HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        response_time_ms = timeout * 1000
        status = InstanceStatus.UNHEALTHY
        success = False
        error_message = "Request timeout"
    except requests.exceptions.RequestException as e:
        response_time_ms = (time.time() - start_time) * 1000
        status = InstanceStatus.UNHEALTHY
        success = False
        error_message = str(e)
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000
        status = InstanceStatus.UNKNOWN
        success = False
        error_message = f"Unexpected error: {e}"

    return HealthCheckResult(
        instance_url=instance_url,
        region=region_config.name,
        status=status,
        response_time_ms=response_time_ms,
        timestamp=datetime.now(),
        success=success,
        error_message=error_message,
    )


def check_all_instances(
    config: Config, api_key: Optional[str] = None
) -> Dict[str, InstanceMetrics]:
    """Check health of all instances across all regions.

    Args:
        config: Configuration object
        api_key: Optional API key for health checks

    Returns:
        Dictionary mapping instance URLs to their metrics
    """
    all_metrics: Dict[str, InstanceMetrics] = {}

    for region_config in config.regions:
        for instance_url in region_config.instances:
            if instance_url not in all_metrics:
                all_metrics[instance_url] = InstanceMetrics(
                    instance_url=instance_url, region=region_config.name
                )

            logger.info(f"Checking instance: {instance_url} in region {region_config.name}")
            result = perform_health_check(
                instance_url,
                region_config,
                region_config.health_check_timeout,
                api_key,
            )

            metrics = all_metrics[instance_url]
            metrics.health_checks.append(result)

            if result.success:
                metrics.consecutive_failures = 0
                metrics.last_healthy_time = result.timestamp
            else:
                metrics.consecutive_failures += 1

            logger.info(
                f"Instance {instance_url}: {result.status.value}, "
                f"response_time={result.response_time_ms:.2f}ms"
            )

    return all_metrics


def evaluate_instance_status(
    metrics: InstanceMetrics, config: Config
) -> InstanceStatus:
    """Evaluate instance status based on performance metrics.

    Args:
        metrics: Instance metrics to evaluate
        config: Configuration with thresholds

    Returns:
        Current status of the instance
    """
    if metrics.consecutive_failures >= config.performance.consecutive_failures_threshold:
        return InstanceStatus.UNHEALTHY

    window_minutes = config.performance.degradation_window_minutes
    success_rate = metrics.calculate_success_rate(window_minutes)
    avg_response_time = metrics.calculate_avg_response_time(window_minutes)

    if success_rate < config.performance.min_success_rate:
        return InstanceStatus.UNHEALTHY

    if avg_response_time > config.performance.max_response_time_ms:
        return InstanceStatus.DEGRADED

    if success_rate >= config.performance.min_success_rate:
        return InstanceStatus.HEALTHY

    return InstanceStatus.UNKNOWN


def select_healthy_instances(
    all_metrics: Dict[str, InstanceMetrics],
    config: Config,
) -> List[str]:
    """Select healthy instances for traffic routing.

    Args:
        all_metrics: Metrics for all instances
        config: Configuration object

    Returns:
        List of healthy instance URLs ordered by routing strategy
    """
    healthy_instances = []

    for instance_url, metrics in all_metrics.items():
        status = evaluate_instance_status(metrics, config)
        metrics.current_status = status

        if status == InstanceStatus.HEALTHY:
            healthy_instances.append(instance_url)
        elif status == InstanceStatus.DEGRADED:
            logger.warning(
                f"Instance {instance_url} is degraded but may still be usable"
            )

    if config.routing.routing_strategy == "priority":
        region_priorities = {
            region.name: region.priority
            for region in config.regions
        }
        healthy_instances.sort(
            key=lambda url: (
                region_priorities.get(
                    next(
                        (
                            m.region
                            for m in all_metrics.values()
                            if m.instance_url == url
                        ),
                        "",
                    ),
                    999,
                ),
                all_metrics[url].calculate_avg_response_time(
                    config.performance.degradation_window_minutes
                ),
            )
        )
    elif config.routing.routing_strategy == "least_latency":
        healthy_instances.sort(
            key=lambda url: all_metrics[url].calculate_avg_response_time(
                config.performance.degradation_window_minutes
            )
        )

    return healthy_instances


def update_routing_state(
    healthy_instances: List[str],
    config: Config,
    current_state: Optional[RoutingState] = None,
) -> RoutingState:
    """Update traffic routing state based on healthy instances.

    Args:
        healthy_instances: List of healthy instance URLs
        config: Configuration object
        current_state: Current routing state (optional)

    Returns:
        Updated routing state
    """
    if not healthy_instances:
        logger.error("No healthy instances available for routing")
        if current_state:
            return current_state
        return RoutingState()

    active_count = min(3, len(healthy_instances))
    active_instances = healthy_instances[:active_count]
    backup_instances = healthy_instances[active_count:]

    new_state = RoutingState(
        active_instances=active_instances,
        backup_instances=backup_instances,
        last_update=datetime.now(),
        routing_strategy=config.routing.routing_strategy,
    )

    if current_state and current_state.active_instances != active_instances:
        logger.info(
            f"Routing changed. New active instances: {active_instances}"
        )
        if config.routing.failover_enabled:
            logger.info("Failover routing activated")

    return new_state


def save_metrics(
    all_metrics: Dict[str, InstanceMetrics], metrics_file: Path
) -> None:
    """Save performance metrics to file.

    Args:
        all_metrics: Dictionary of instance metrics
        metrics_file: Path to save metrics JSON file
    """
    metrics_file.parent.mkdir(parents=True, exist_ok=True)

    metrics_data = {}
    for instance_url, metrics in all_metrics.items():
        recent_checks = metrics.health_checks[-100:]
        metrics_data[instance_url] = {
            "region": metrics.region,
            "current_status": metrics.current_status.value,
            "consecutive_failures": metrics.consecutive_failures,
            "last_healthy_time": (
                metrics.last_healthy_time.isoformat()
                if metrics.last_healthy_time
                else None
            ),
            "recent_checks": [
                {
                    "timestamp": check.timestamp.isoformat(),
                    "status": check.status.value,
                    "response_time_ms": check.response_time_ms,
                    "success": check.success,
                    "error_message": check.error_message,
                }
                for check in recent_checks
            ],
        }

    try:
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(metrics_data, f, indent=2)
        logger.debug(f"Metrics saved to {metrics_file}")
    except Exception as e:
        logger.error(f"Failed to save metrics: {e}")


def save_routing_state(routing_state: RoutingState, state_file: Path) -> None:
    """Save routing state to file.

    Args:
        routing_state: Current routing state
        state_file: Path to save state JSON file
    """
    state_file.parent.mkdir(parents=True, exist_ok=True)

    state_data = {
        "active_instances": routing_state.active_instances,
        "backup_instances": routing_state.backup_instances,
        "last_update": (
            routing_state.last_update.isoformat()
            if routing_state.last_update
            else None
        ),
        "routing_strategy": routing_state.routing_strategy,
    }

    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2)
        logger.debug(f"Routing state saved to {state_file}")
    except Exception as e:
        logger.error(f"Failed to save routing state: {e}")


def load_routing_state(state_file: Path) -> Optional[RoutingState]:
    """Load routing state from file.

    Args:
        state_file: Path to state JSON file

    Returns:
        RoutingState if file exists, None otherwise
    """
    if not state_file.exists():
        return None

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state_data = json.load(f)

        return RoutingState(
            active_instances=state_data.get("active_instances", []),
            backup_instances=state_data.get("backup_instances", []),
            last_update=(
                datetime.fromisoformat(state_data["last_update"])
                if state_data.get("last_update")
                else None
            ),
            routing_strategy=state_data.get("routing_strategy", "priority"),
        )
    except Exception as e:
        logger.warning(f"Failed to load routing state: {e}")
        return None


def monitor_and_route(config_path: Path, api_key: Optional[str] = None) -> None:
    """Monitor instances and update routing configuration.

    Args:
        config_path: Path to configuration file
        api_key: Optional API key for health checks

    Raises:
        FileNotFoundError: If config file is missing
        ValueError: If configuration is invalid
    """
    config = load_config(config_path)
    state_file = Path(config.routing_state_file)
    metrics_file = Path(config.metrics_file)

    current_state = load_routing_state(state_file)

    logger.info("Starting health check cycle")
    all_metrics = check_all_instances(config, api_key)

    healthy_instances = select_healthy_instances(all_metrics, config)
    logger.info(f"Found {len(healthy_instances)} healthy instances")

    new_state = update_routing_state(
        healthy_instances, config, current_state
    )

    save_metrics(all_metrics, metrics_file)
    save_routing_state(new_state, state_file)

    logger.info(
        f"Active instances: {new_state.active_instances}, "
        f"Backup instances: {new_state.backup_instances}"
    )


def run_monitoring_loop(config_path: Path, api_key: Optional[str] = None) -> None:
    """Run continuous monitoring loop.

    Args:
        config_path: Path to configuration file
        api_key: Optional API key for health checks
    """
    config = load_config(config_path)
    interval = config.routing.health_check_interval_seconds

    logger.info(
        f"Starting monitoring loop with {interval}s interval. "
        "Press Ctrl+C to stop."
    )

    try:
        while True:
            monitor_and_route(config_path, api_key)
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Monitoring loop stopped by user")
    except Exception as e:
        logger.error(f"Error in monitoring loop: {e}")
        raise


def main() -> None:
    """Main entry point for the uptime monitor."""
    settings = AppSettings()
    config_path = Path(settings.config_path)

    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent
        config_path = project_root / config_path

    try:
        logger.info("Starting application uptime monitoring")
        monitor_and_route(config_path, settings.api_key)
        logger.info("Monitoring cycle completed")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
