import logging
from prometheus_client import start_http_server
from prometheus_client.registry import REGISTRY

from src.metrics.exporter import MetricsManager


logger = logging.getLogger("PyInfraGuard.MetricsServer")


class MetricsServerManager:
    """Manages the lifecycle of the Prometheus HTTP metrics server."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Initialize server configuration parameters.

        Args:
            host: Network interface to bind the metrics server to.
            port: Port to expose the Prometheus /metrics endpoint.
        """
        self._host = host
        self._port = port
        self._server_started = False

    def start(self) -> None:
        """Start the Prometheus HTTP server to expose internal runtime metrics."""
        if self._server_started:
            logger.warning("Metrics server is already running.")
            return

        try:
            logger.info(f"Starting Prometheus metrics server on {self._host}:{self._port}")
            start_http_server(port=self._port, addr=self._host, registry=REGISTRY)
            self._server_started = True
            logger.info("Prometheus metrics server successfully started.")
        except Exception as err:
            logger.error(f"Failed to start Prometheus metrics server: {err!s}", exc_info=True)
            MetricsManager.track_error(component="metrics_server")
            raise
