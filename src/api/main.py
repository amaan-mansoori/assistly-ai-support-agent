"""FastAPI app factory for the customer-support platform."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from threading import Lock
from typing import Any, Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, sessionmaker

from src.api.middleware import RequestContextMiddleware
from src.api.errors import PlatformError
from src.api.routes.health import router as health_router
from src.db.database import make_engine, make_session_factory
from src.platform.config import PlatformSettings
from src.platform.metrics import MetricsRegistry
from src.platform.rate_limit import FixedWindowLimiter


def create_app(
    settings: PlatformSettings | None = None,
    *,
    session_factory: sessionmaker[Session] | None = None,
    agent_factory: Callable[[], Any] | None = None,
) -> FastAPI:
    settings = settings or PlatformSettings.from_env()
    logging.basicConfig(level=settings.log_level)
    engine = make_engine(settings.database_url)
    factory = session_factory or make_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        del _app
        yield
        engine.dispose()

    app = FastAPI(
        title="Assistly AI-Powered Customer Support Platform API",
        version="0.2.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = factory
    app.state.platform_config = None
    app.state.rate_limiter = FixedWindowLimiter(
        settings.rate_limit_per_minute, settings.redis_url
    )
    app.state.metrics = MetricsRegistry()
    app.state.agent_factory = agent_factory
    app.state.provider_name = "gemini"
    app.state.model_name = "gemini-3.8-flash"
    if agent_factory is None:
        agent_cache: list[Any] = []
        agent_lock = Lock()

        def make_agent() -> Any:
            if agent_cache:
                return agent_cache[0]
            with agent_lock:
                if agent_cache:
                    return agent_cache[0]
                from src.agent.config import AgentConfig
                from src.agent.orchestrator import SupportAgent
                from src.agent.reply_generator import configured_llm_call
                from src.retrieval.factory import build_retriever

                config = AgentConfig.load()
                retriever = build_retriever(settings, factory)
                llm_call: Callable[[str, str], str]
                try:
                    llm_call = configured_llm_call(
                        config.provider,
                        config.model,
                        timeout_seconds=config.provider_timeout_seconds,
                        max_retries=config.provider_max_retries,
                    )
                except RuntimeError:
                    def no_configured_provider(_system: str, _prompt: str) -> str:
                        del _system, _prompt
                        raise RuntimeError("No configured model provider.")

                    llm_call = no_configured_provider
                agent_cache.append(SupportAgent(retriever, llm_call, config))
                app.state.platform_config = config
                app.state.provider_name = config.provider
                app.state.model_name = config.model
                return agent_cache[0]

        app.state.agent_factory = make_agent
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    app.include_router(health_router)
    from src.api.routes.agent import router as agent_router
    from src.api.routes.analytics import router as analytics_router
    from src.api.routes.auth import router as auth_router
    from src.api.routes.conversations import router as conversations_router
    from src.api.routes.feedback import router as feedback_router
    from src.api.routes.metrics import router as metrics_router
    from src.api.routes.tickets import router as tickets_router

    for router in (
        auth_router,
        conversations_router,
        agent_router,
        tickets_router,
        feedback_router,
        analytics_router,
        metrics_router,
    ):
        app.include_router(router)

    @app.exception_handler(PlatformError)
    async def platform_error_handler(request: Request, exc: PlatformError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "request_id": getattr(request.state, "request_id", "unknown"),
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "The request was rejected."
        return JSONResponse(
            status_code=exc.status_code,
            headers=exc.headers,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": detail,
                    "request_id": getattr(request.state, "request_id", "unknown"),
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, _exc: RequestValidationError
    ) -> JSONResponse:
        del _exc
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request body or parameters are invalid.",
                    "request_id": getattr(request.state, "request_id", "unknown"),
                }
            },
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        logging.getLogger(__name__).error(
            "unhandled_api_error",
            extra={"request_id": request_id, "error_type": type(exc).__name__},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "The request could not be completed.",
                    "request_id": request_id,
                }
            },
        )

    return app


app = create_app()
