from pydantic import BaseModel, Field
from typing import Literal, Optional


class PaymentData(BaseModel):
    order_id: int = Field(gt=0)
    amount: float = Field(gt=0)
    type: Optional[Literal["Наличные", "Эквайринг"]] = None


class RefundResponse(BaseModel):
    success: bool
    payment_id: int | None = None
    refunded_amount: float | None = None
    user_balance: float | None = None
    order_remaining: float | None = None
    order_status: str | None = None
    error: str | None = None
