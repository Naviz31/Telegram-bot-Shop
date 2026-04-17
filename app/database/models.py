from copy import deepcopy
from datetime import datetime
import json

from sqlalchemy import BigInteger, JSON, String
from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text, select, Boolean, ARRAY
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


engine = create_async_engine(url="sqlite+aiosqlite:///db.sqlite3")
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class JSONEncoded(TypeDecorator):
    # Указываем тип базы данных (например, String), который будет хранить сериализованные данные
    impl = String

    def process_bind_param(self, value, dialect):
        # Сериализация списка в строку JSON перед вставкой в базу данных
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        # Десериализация строки JSON обратно в список при извлечении из базы данных
        if value is not None:
            return json.loads(value)
        return value

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=True)
    registered: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    cart: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    payment_history: Mapped[str] = mapped_column(String(2048), nullable=True)
    referral_code: Mapped[str] = mapped_column(String(128), nullable=True)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=True)
    image: Mapped[str] = mapped_column(String(128), nullable=True)
    description: Mapped[str] = mapped_column(String(4096), nullable=True)
    price: Mapped[int] = mapped_column(BigInteger, nullable=True)
    status: Mapped[bool] = mapped_column(Boolean, nullable=True)
    sizes: Mapped[str] = mapped_column(String(128), nullable=True)
    mass: Mapped[int] = mapped_column(BigInteger, nullable=True)
    remains: Mapped[int] = mapped_column(BigInteger, nullable=True)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    registered: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    order_data: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    delivery: Mapped[str] = mapped_column(String(1024), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(128), nullable=True)
    manager: Mapped[str] = mapped_column(String(1024), nullable=True)
    post_code: Mapped[str] = mapped_column(String(128), nullable=True)
    delivery_cost: Mapped[int] = mapped_column(BigInteger, nullable=True)
    delivery_days: Mapped[str] = mapped_column(String(128), nullable=True)
    cost: Mapped[int] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(1024), nullable=True)
    order_type: Mapped[str] = mapped_column(String(1024), nullable=True)
    track_number: Mapped[str] = mapped_column(String(1024), nullable=True)
    fullname: Mapped[str] = mapped_column(String(1024), nullable=True)
    admin_status: Mapped[str] = mapped_column(String(1024), nullable=True)


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
