import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from opentelemetry import trace
from starlette.responses import Response

from app.config import get_settings
from app.logging_config import configure_logging
from app.metrics import ERROR_COUNT, REQUEST_COUNT, REQUEST_LATENCY, metrics_response
from app.predictor import predict_sentiment
from app.schemas import HealthResponse, PredictRequest, PredictResponse
from app.tracing import configure_tracing, instrument_fastapi

settings = get_settings()
configure_logging(settings.log_level)
configure_tracing(settings)

logger = logging.getLogger("observelite")
tracer = trace.get_tracer(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="ObserveLite",
        description="A lightweight observability demo with FastAPI, Prometheus, OpenTelemetry, Jaeger, and Grafana.",
        version="1.0.0",
    )

    @app.middleware("http")
    async def observability_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        endpoint = request.url.path
        start_time = time.perf_counter()

        with tracer.start_as_current_span("incoming request") as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.route", endpoint)
            logger.info(
                "request received",
                extra={"method": method, "endpoint": endpoint},
            )

            try:
                response = await call_next(request)
            except Exception:
                latency = time.perf_counter() - start_time
                ERROR_COUNT.labels(method=method, endpoint=endpoint, http_status="500").inc()
                REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status="500").inc()
                REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
                logger.exception(
                    "exception while handling request",
                    extra={"method": method, "endpoint": endpoint, "latency_seconds": round(latency, 6)},
                )
                raise

            latency = time.perf_counter() - start_time
            status = str(response.status_code)
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=status).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)

            if response.status_code >= 500:
                ERROR_COUNT.labels(method=method, endpoint=endpoint, http_status=status).inc()

            logger.info(
                "request completed",
                extra={
                    "method": method,
                    "endpoint": endpoint,
                    "http_status": response.status_code,
                    "latency_seconds": round(latency, 6),
                },
            )
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.server_duration_seconds", latency)

            return response

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse()

    @app.get("/metrics")
    async def metrics() -> Response:
        return metrics_response()

    @app.post("/predict", response_model=PredictResponse)
    async def predict(payload: PredictRequest) -> PredictResponse:
        sentiment, confidence = predict_sentiment(payload.text)

        with tracer.start_as_current_span("response generation") as span:
            response = PredictResponse(
                sentiment=sentiment,
                confidence=confidence,
                input_length=len(payload.text),
            )
            span.set_attribute("response.sentiment", response.sentiment)
            return response

    instrument_fastapi(app)
    return app


app = create_app()
