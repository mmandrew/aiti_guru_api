from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import async_session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, delete
from .schemas import PaymentData, RefundResponse
from .crud import get_or_404
from .models import User, Order, Payment
from .database import get_db

app = FastAPI(title="aiti_guru_api")


@app.post("/acquiring-start/")
async def make_acquiring(payment_data: PaymentData, db: async_session = Depends(get_db)):
    async with db.begin():
        order = await get_or_404(db, Order, payment_data.order_id, "Соответствующий заказ не найден")
        user = await get_or_404(db, User, order.user_id, "Соответствующий пользователь не найден")

        if user.current_money < payment_data.amount:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="У пользователя не хватает средств на счете"
            )

        if order.remained_cost < payment_data.amount:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Попытка оплатить больше требуемой суммы"
            )

        try:
            payment = Payment(
                order_id=payment_data.order_id,
                amount=payment_data.amount,
                type=payment_data.type
            )
            db.add(payment)
            # обновить счет клиента (триггер)
            # уменьшить remained_cost на величину платежа (триггер)
            # Обновляем статус заказа (триггер)
            return {"id": payment.id}
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            ) from e


@app.delete("/refund-acquiring/")
async def return_payment(id: int, db: async_session = Depends(get_db)):
    async with db.begin():
        payment = await get_or_404(db, Payment, id, "Платеж с таким номером не найден")
        order = await get_or_404(db, Order, payment.order_id, "Заказ для платежа не найден")
        user = await get_or_404(db, User, order.user_id, "Пользователь не найден")

        try:
            stmt_payment_delete = delete(Payment).where(Payment.id == payment.id)
            await db.execute(stmt_payment_delete)
            # вернуть деньги клиенту (триггер)
            # увеличить остаток стоимости (триггер)
            # при необходимости изменить статус заказа (триггер)
            return RefundResponse(
                success=True,
                payment_id=payment.id,
                refunded_amount=payment.amount,
                user_balance=user.current_money,
                order_remaining=order.remained_cost,
                order_status=order.status
            )
        except Exception as e:
            return RefundResponse(
                success=False,
                error="Internal server error: could not process refund"
            )


@app.get("/acquiring-check/")
async def get_payments(payment_id: int, db: async_session = Depends(get_db)):
    stmt = select(Payment.id, Payment.amount, Payment.order_id, Payment.created_at).where(Payment.id == payment_id)
    try:
        payment = (await db.execute(stmt)).fetchone()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        return {
            "id": payment.id,
            "amount": payment.amount,
            "order_id": payment.order_id,
            "created_at": payment.created_at
        }
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment record"
        ) from e
