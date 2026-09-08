from uuid import UUID

from fastapi import APIRouter, status

from services.payment_api.api.schemas import ErrorResponse, PaymentCreateRequest, PaymentResponse
from services.payment_api.application.services import PaymentService


def create_payments_router(payment_service: PaymentService) -> APIRouter:
    router = APIRouter(prefix="/v1/payments", tags=["payments"])

    @router.post(
        "",
        response_model=PaymentResponse,
        status_code=status.HTTP_201_CREATED,
        responses={422: {"model": ErrorResponse, "description": "Invalid payment request"}},
    )
    async def create_payment(request: PaymentCreateRequest) -> PaymentResponse:
        payment = await payment_service.create_payment(
            amount_minor=request.amount_minor, currency=request.currency
        )
        return PaymentResponse.from_domain(payment)

    @router.get(
        "/{payment_id}",
        response_model=PaymentResponse,
        responses={
            404: {"model": ErrorResponse, "description": "Payment not found"},
            422: {"model": ErrorResponse, "description": "Invalid payment ID"},
        },
    )
    async def get_payment(payment_id: UUID) -> PaymentResponse:
        payment = await payment_service.get_payment(payment_id)
        return PaymentResponse.from_domain(payment)

    return router
