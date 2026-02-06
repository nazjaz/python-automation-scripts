"""Monitors API endpoint performance."""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests

from src.database import DatabaseManager, APIEndpoint, APIRequest

logger = logging.getLogger(__name__)


class APIMonitor:
    """Monitors API endpoint performance."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Dict,
    ) -> None:
        """Initialize API monitor.

        Args:
            db_manager: Database manager instance.
            config: Configuration dictionary.
        """
        self.db_manager = db_manager
        self.config = config
        self.monitoring_config = config.get("monitoring", {})
        self.timeout = self.monitoring_config.get("timeout_seconds", 30)
        self.max_retries = self.monitoring_config.get("max_retries", 3)
        self.retry_delay = self.monitoring_config.get("retry_delay_seconds", 1)
        self.user_agent = self.monitoring_config.get("user_agent", "API-Performance-Monitor/1.0")
        self.follow_redirects = self.monitoring_config.get("follow_redirects", True)
        self.verify_ssl = self.monitoring_config.get("verify_ssl", True)

    def monitor_endpoint(
        self,
        endpoint_id: int,
        headers: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> APIRequest:
        """Monitor a single API endpoint.

        Args:
            endpoint_id: Endpoint ID.
            headers: Optional request headers.
            data: Optional request data.

        Returns:
            APIRequest object.
        """
        endpoint = (
            self.db_manager.get_session()
            .query(APIEndpoint)
            .filter(APIEndpoint.id == endpoint_id)
            .first()
        )

        if not endpoint:
            raise ValueError(f"Endpoint {endpoint_id} not found")

        logger.info(f"Monitoring endpoint: {endpoint.full_url}", extra={"endpoint_id": endpoint_id})

        start_time = time.time()
        response_time_ms = None
        status_code = None
        response_size_bytes = None
        error_message = None

        request_headers = headers or {}
        request_headers["User-Agent"] = self.user_agent

        for attempt in range(self.max_retries):
            try:
                response = requests.request(
                    method=endpoint.method,
                    url=endpoint.full_url,
                    headers=request_headers,
                    json=data,
                    timeout=self.timeout,
                    allow_redirects=self.follow_redirects,
                    verify=self.verify_ssl,
                )

                response_time_ms = (time.time() - start_time) * 1000
                status_code = response.status_code
                response_size_bytes = len(response.content)

                break

            except requests.exceptions.Timeout:
                error_message = f"Request timeout after {self.timeout} seconds"
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                response_time_ms = self.timeout * 1000

            except requests.exceptions.RequestException as e:
                error_message = str(e)
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                response_time_ms = (time.time() - start_time) * 1000

        if response_time_ms is None:
            response_time_ms = self.timeout * 1000

        request = self.db_manager.add_request(
            endpoint_id=endpoint_id,
            response_time_ms=response_time_ms,
            status_code=status_code,
            response_size_bytes=response_size_bytes,
            error_message=error_message,
        )

        logger.info(
            f"Endpoint monitored: {endpoint.full_url} - {response_time_ms:.2f}ms",
            extra={
                "endpoint_id": endpoint_id,
                "response_time_ms": response_time_ms,
                "status_code": status_code,
            },
        )

        return request

    def monitor_all_endpoints(
        self,
        headers: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> List[APIRequest]:
        """Monitor all active endpoints.

        Args:
            headers: Optional request headers.
            data: Optional request data.

        Returns:
            List of APIRequest objects.
        """
        endpoints = self.db_manager.get_endpoints(active_only=True)
        requests = []

        for endpoint in endpoints:
            try:
                request = self.monitor_endpoint(
                    endpoint_id=endpoint.id,
                    headers=headers,
                    data=data,
                )
                requests.append(request)
            except Exception as e:
                logger.error(
                    f"Error monitoring endpoint {endpoint.id}: {e}",
                    extra={"endpoint_id": endpoint.id, "error": str(e)},
                )

        logger.info(
            f"Monitored {len(requests)} endpoints",
            extra={"endpoints_monitored": len(requests)},
        )

        return requests
