"""Analyzes API performance bottlenecks."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np

from src.database import DatabaseManager, Bottleneck

logger = logging.getLogger(__name__)


class BottleneckAnalyzer:
    """Analyzes API performance bottlenecks."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize bottleneck analyzer.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.bottleneck_config = config.get("bottleneck_detection", {})
        self.error_rate_threshold = self.bottleneck_config.get("error_rate_threshold", 0.05)
        self.throughput_degradation = self.bottleneck_config.get("throughput_degradation_threshold", 0.20)
        self.min_samples = self.bottleneck_config.get("min_samples_for_bottleneck", 20)

    def analyze_endpoint(
        self,
        endpoint_id: int,
        hours: int = 24,
    ) -> List[Bottleneck]:
        """Analyze endpoint for bottlenecks.

        Args:
            endpoint_id: Endpoint ID.
            hours: Number of hours to analyze.

        Returns:
            List of Bottleneck objects.
        """
        if not self.bottleneck_config.get("enabled", True):
            return []

        start_time = datetime.utcnow() - timedelta(hours=hours)
        requests = self.db_manager.get_requests(
            endpoint_id=endpoint_id,
            start_time=start_time,
        )

        if len(requests) < self.min_samples:
            logger.debug(
                f"Insufficient samples for bottleneck analysis: {len(requests)} < {self.min_samples}",
                extra={"endpoint_id": endpoint_id, "request_count": len(requests)},
            )
            return []

        bottlenecks = []

        if self.bottleneck_config.get("check_response_times", True):
            bottlenecks.extend(self._check_response_time_bottlenecks(endpoint_id, requests))

        if self.bottleneck_config.get("check_error_rates", True):
            bottlenecks.extend(self._check_error_rate_bottlenecks(endpoint_id, requests))

        if self.bottleneck_config.get("check_throughput", True):
            bottlenecks.extend(self._check_throughput_bottlenecks(endpoint_id, requests))

        for bottleneck in bottlenecks:
            self.db_manager.add_bottleneck(
                endpoint_id=endpoint_id,
                bottleneck_type=bottleneck["type"],
                severity=bottleneck["severity"],
                description=bottleneck["description"],
                impact_percentage=bottleneck.get("impact_percentage"),
            )

        logger.info(
            f"Analyzed endpoint {endpoint_id} for bottlenecks: {len(bottlenecks)} found",
            extra={"endpoint_id": endpoint_id, "bottleneck_count": len(bottlenecks)},
        )

        return bottlenecks

    def _check_response_time_bottlenecks(
        self, endpoint_id: int, requests: List
    ) -> List[Dict]:
        """Check for response time bottlenecks.

        Args:
            endpoint_id: Endpoint ID.
            requests: List of APIRequest objects.

        Returns:
            List of bottleneck dictionaries.
        """
        bottlenecks = []

        response_times = [r.response_time_ms for r in requests if r.response_time_ms is not None]

        if not response_times:
            return bottlenecks

        avg_response_time = np.mean(response_times)
        p95_response_time = np.percentile(response_times, 95)
        p99_response_time = np.percentile(response_times, 99)

        slow_threshold = self.config.get("performance", {}).get("slow_endpoint_threshold_ms", 1000)
        very_slow_threshold = self.config.get("performance", {}).get("very_slow_endpoint_threshold_ms", 5000)

        if p99_response_time >= very_slow_threshold:
            bottlenecks.append(
                {
                    "type": "response_time",
                    "severity": "critical",
                    "description": f"P99 response time {p99_response_time:.2f}ms exceeds very slow threshold {very_slow_threshold}ms. "
                    f"Average: {avg_response_time:.2f}ms, P95: {p95_response_time:.2f}ms",
                    "impact_percentage": min((p99_response_time / very_slow_threshold - 1) * 100, 200),
                }
            )
        elif p95_response_time >= slow_threshold:
            bottlenecks.append(
                {
                    "type": "response_time",
                    "severity": "high",
                    "description": f"P95 response time {p95_response_time:.2f}ms exceeds slow threshold {slow_threshold}ms. "
                    f"Average: {avg_response_time:.2f}ms",
                    "impact_percentage": min((p95_response_time / slow_threshold - 1) * 100, 100),
                }
            )

        return bottlenecks

    def _check_error_rate_bottlenecks(
        self, endpoint_id: int, requests: List
    ) -> List[Dict]:
        """Check for error rate bottlenecks.

        Args:
            endpoint_id: Endpoint ID.
            requests: List of APIRequest objects.

        Returns:
            List of bottleneck dictionaries.
        """
        bottlenecks = []

        error_requests = [r for r in requests if r.status_code and r.status_code >= 400]
        error_rate = len(error_requests) / float(len(requests)) if requests else 0.0

        if error_rate >= self.error_rate_threshold:
            severity = "critical" if error_rate >= 0.10 else "high"
            bottlenecks.append(
                {
                    "type": "error_rate",
                    "severity": severity,
                    "description": f"Error rate {error_rate:.1%} exceeds threshold {self.error_rate_threshold:.1%}. "
                    f"{len(error_requests)} errors out of {len(requests)} requests",
                    "impact_percentage": error_rate * 100,
                }
            )

        return bottlenecks

    def _check_throughput_bottlenecks(
        self, endpoint_id: int, requests: List
    ) -> List[Dict]:
        """Check for throughput bottlenecks.

        Args:
            endpoint_id: Endpoint ID.
            requests: List of APIRequest objects.

        Returns:
            List of bottleneck dictionaries.
        """
        bottlenecks = []

        if len(requests) < 2:
            return bottlenecks

        requests_sorted = sorted(requests, key=lambda x: x.request_time)

        time_span = (requests_sorted[0].request_time - requests_sorted[-1].request_time).total_seconds()
        time_span = abs(time_span) if time_span else 1.0

        overall_throughput = len(requests) / time_span

        window_size = max(len(requests) // 4, 10)
        window_throughputs = []

        for i in range(0, len(requests) - window_size, window_size):
            window_requests = requests_sorted[i : i + window_size]
            window_time_span = (
                window_requests[0].request_time - window_requests[-1].request_time
            ).total_seconds()
            window_time_span = abs(window_time_span) if window_time_span else 1.0
            window_throughput = len(window_requests) / window_time_span
            window_throughputs.append(window_throughput)

        if window_throughputs:
            min_throughput = min(window_throughputs)
            throughput_degradation = (overall_throughput - min_throughput) / overall_throughput if overall_throughput > 0 else 0.0

            if throughput_degradation >= self.throughput_degradation:
                bottlenecks.append(
                    {
                        "type": "throughput",
                        "severity": "medium",
                        "description": f"Throughput degradation {throughput_degradation:.1%} detected. "
                        f"Overall: {overall_throughput:.2f} req/s, Minimum window: {min_throughput:.2f} req/s",
                        "impact_percentage": throughput_degradation * 100,
                    }
                )

        return bottlenecks

    def analyze_all_endpoints(
        self,
        hours: int = 24,
    ) -> List[Bottleneck]:
        """Analyze all endpoints for bottlenecks.

        Args:
            hours: Number of hours to analyze.

        Returns:
            List of all Bottleneck objects identified.
        """
        endpoints = self.db_manager.get_endpoints(active_only=True)
        all_bottlenecks = []

        for endpoint in endpoints:
            bottlenecks = self.analyze_endpoint(endpoint.id, hours=hours)
            all_bottlenecks.extend(bottlenecks)

        logger.info(
            f"Analyzed {len(endpoints)} endpoints: {len(all_bottlenecks)} bottlenecks found",
            extra={"endpoint_count": len(endpoints), "bottleneck_count": len(all_bottlenecks)},
        )

        return all_bottlenecks
