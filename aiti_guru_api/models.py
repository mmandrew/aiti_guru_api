from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Sequence, CheckConstraint
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    current_money = Column(Float, nullable=False)
    __table_args__ = (
        CheckConstraint('current_money >= 0', name='chk_current_money_ge_0'),
    )


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_name = Column(String, nullable=False)
    cost = Column(Float, nullable=False)
    remained_cost = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    __table_args__ = (
        CheckConstraint('remained_cost >= 0', name='chk_remained_cost_ge_0'),
        CheckConstraint('remained_cost <= cost', name='chk_remained_cost_le_cost'),
    )


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, Sequence("payments_id_seq"), primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    amount = Column(Float, nullable=False)
    type = Column(String)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
