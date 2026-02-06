"""Tracks and analyzes API response times."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np

from src.database import DatabaseManager, APIRequest, EndpointMetric

logger = logging.getLogger(__name__)


class ResponseTimeTracker:
    """Tracks and analyzes API response times."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize response time tracker.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.performance_config = config.get("performance", {})
        self.percentiles = self.performance_config.get("response_time_percentiles", [50, 75, 90, 95, 99])
        self.min_requests = self.performance_config.get("min_requests_for_analysis", 10)

    def calculate_metrics(
        self,
        endpoint_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> EndpointMetric:
        """Calculate performance metrics for endpoint.

        Args:
            endpoint_id: Endpoint ID.
            start_time: Optional start time filter.
            end_time: Optional end time filter.

        Returns:
            EndpointMetric object.
        """
        requests = self.db_manager.get_requests(
            endpoint_id=endpoint_id,
            start_time=start_time,
            end_time=end_time,
        )

        if len(requests) < self.min_requests:
            logger.warning(
                f"Insufficient requests for metrics: {len(requests)} < {self.min_requests}",
                extra={"endpoint_id": endpoint_id, "request_count": len(requests)},
            )
            return None

        response_times = [r.response_time_ms for r in requests if r.response_time_ms is not None]

        if not response_times:
            return None

        success_requests = [r for r in requests if r.status_code and 200 <= r.status_code < 300]
        error_requests = [r for r in requests if r.status_code and r.status_code >= 400]

        avg_response_time = np.mean(response_times)
        min_response_time = np.min(response_times)
        max_response_time = np.max(response_times)

        percentile_values = {}
        for percentile in self.percentiles:
            percentile_values[f"p{percentile}"] = np.percentile(response_times, percentile)

        error_rate = len(error_requests) / float(len(requests)) if requests else 0.0

        time_span = None
        if start_time and end_time:
            time_span = (end_time - start_time).total_seconds()
        elif len(requests) > 1:
            time_span = (requests[0].request_time - requests[-1].request_time).total_seconds()
            time_span = abs(time_span) if time_span else 1.0

        throughput = len(requests) / time_span if time_span and time_span > 0 else None

        metric = self.db_manager.add_metric(
            endpoint_id=endpoint_id,
            avg_response_time_ms=avg_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            p50_response_time_ms=percentile_values.get("p50"),
            p75_response_time_ms=percentile_values.get("p75"),
            p90_response_time_ms=percentile_values.get("p90"),
            p95_response_time_ms=percentile_values.get("p95"),
            p99_response_time_ms=percentile_values.get("p99"),
            request_count=len(requests),
            success_count=len(success_requests),
            error_count=len(error_requests),
            error_rate=error_rate,
            throughput_per_second=throughput,
            metric_time=end_time or datetime.utcnow(),
        )

        logger.info(
            f"Calculated metrics for endpoint {endpoint_id}",
            extra={
                "endpoint_id": endpoint_id,
                "avg_response_time_ms": avg_response_time,
                "request_count": len(requests),
            },
        )

        return metric

    def identify_slow_endpoints(
        self,
        slow_threshold_ms: Optional[float] = None,
        very_slow_threshold_ms: Optional[float] = None,
    ) -> List[Dict]:
        """Identify slow endpoints.

        Args:
            slow_threshold_ms: Optional slow threshold in milliseconds.
            very_slow_threshold_ms: Optional very slow threshold in milliseconds.

        Returns:
            List of dictionaries with slow endpoint information.
        """
        if slow_threshold_ms is None:
            slow_threshold_ms = self.performance_config.get("slow_endpoint_threshold_ms", 1000)

        if very_slow_threshold_ms is None:
            very_slow_threshold_ms = self.performance_config.get("very_slow_endpoint_threshold_ms", 5000)

        endpoints = self.db_manager.get_endpoints(active_only=True)
        slow_endpoints = []

        for endpoint in endpoints:
            requests = self.db_manager.get_requests(endpoint_id=endpoint.id, limit=100)

            if len(requests) < self.min_requests:
                continue

            response_times = [r.response_time_ms for r in requests if r.response_time_ms is not None]

            if not response_times:
                continue

            avg_response_time = np.mean(response_times)
            p95_response_time = np.percentile(response_times, 95)

            severity = None
            if p95_response_time >= very_slow_threshold_ms:
                severity = "critical"
            elif p95_response_time >= slow_threshold_ms:
                severity = "high"

            if severity:
                slow_endpoints.append(
                    {
                        "endpoint_id": endpoint.id,
                        "full_url": endpoint.full_url,
                        "method": endpoint.method,
                        "avg_response_time_ms": avg_response_time,
                        "p95_response_time_ms": p95_response_time,
                        "severity": severity,
                    }
                )

        logger.info(
            f"Identified {len(slow_endpoints)} slow endpoints",
            extra={"slow_endpoint_count": len(slow_endpoints)},
        )

        return slow_endpoints
