from sqlalchemy.ext.asyncio import async_session
from sqlalchemy import select
from fastapi import HTTPException, status
from .models import User, Order, Payment


async def get_or_404(db: async_session, model, id: int, detail: str):
    stmt = select(model).where(model.id == id)
    obj = await db.execute(stmt)
    obj = obj.scalar_one_or_none()
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
    return obj
