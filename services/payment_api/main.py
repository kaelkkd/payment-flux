from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.payment_api.api.routes import create_payments_router
from services.payment_api.api.schemas import ErrorCode, ErrorDetail, ErrorResponse
from services.payment_api.application.errors import PaymentNotFound
from services.payment_api.application.ports import PaymentUnitOfWork, PaymentUnitOfWorkFactory
from services.payment_api.application.services import PaymentService
from services.payment_api.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)
from services.payment_api.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from services.payment_api.settings import Settings


class HealthResponse(BaseModel):
    status: Literal["ok"]


def create_error_response(*, status_code: int, code: ErrorCode, message: str) -> JSONResponse:
    response = ErrorResponse(error=ErrorDetail(code=code, message=message))

    return JSONResponse(status_code=status_code, content=response.model_dump())


def create_app(
    settings: Settings | None = None, unit_of_work_factory: PaymentUnitOfWorkFactory | None = None
) -> FastAPI:
    resolved_settings = settings or Settings()
    engine = create_database_engine(resolved_settings.database_url)
    session_factory = create_session_factory(engine)

    if unit_of_work_factory is None:

        def create_unit_of_work() -> PaymentUnitOfWork:
            return SqlAlchemyUnitOfWork(session_factory=session_factory)

        resolved_unit_of_work_factory = create_unit_of_work
    else:
        resolved_unit_of_work_factory = unit_of_work_factory

    payment_service = PaymentService(resolved_unit_of_work_factory)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
        yield
        await engine.dispose()

    application = FastAPI(title="FluxPay Payment API", lifespan=lifespan)
    application.state.session_factory = session_factory
    application.include_router(create_payments_router(payment_service))

    @application.exception_handler(PaymentNotFound)
    async def payment_not_found(_: Request, _exc: PaymentNotFound) -> JSONResponse:
        return create_error_response(
            status_code=404, code="PAYMENT_NOT_FOUND", message="Payment was not found."
        )

    @application.get("/health/live", response_model=HealthResponse, tags=["health"])
    async def liveness() -> HealthResponse:
        return HealthResponse(status="ok")

    @application.exception_handler(RequestValidationError)
    async def invalid_request(_: Request, _exc: RequestValidationError) -> JSONResponse:
        return create_error_response(
            status_code=422, code="INVALID_REQUEST", message="The request is invalid."
        )

    return application


app = create_app()
