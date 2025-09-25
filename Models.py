from __future__ import annotations
import hashlib
import os
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    LargeBinary, create_engine, Column, Integer, String, Float, Date, Boolean, ForeignKey, or_,
    select, delete, func, event, update
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import (
    declarative_base, Mapped, mapped_column, relationship, Session
)

from enumerates import DOC_TYPES

DB_PATH = os.path.join(os.path.dirname(__file__), "anime1c.db")
DB_URL = f"sqlite:///{DB_PATH}"

# ---- engine ----
engine: Engine = create_engine(DB_URL, echo=False, future=True)


# ---- FK включить для SQLite ----
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ---- Base ----
Base = declarative_base()


# ---- Модели (таблицы) ----
class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # code: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    buy_price: Mapped[float] = mapped_column(Float, default=0)
    image: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)

    lines: Mapped[List["DocsTable"]] = relationship(back_populates="item")



class Contragent(Base):
    __tablename__ = "contragents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)  # supplier / customer

    docs: Mapped[List["Doc"]] = relationship(back_populates="contragent")


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)

    docs: Mapped[List["Doc"]] = relationship(back_populates="warehouse")
    stocks: Mapped[List["Stock"]] = relationship(back_populates="warehouse")


class Doc(Base):
    __tablename__ = "docs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doc_type: Mapped[str] = mapped_column(String)  # приход / расход / инвентаризация
    date: Mapped[date] = mapped_column(Date)
    contragent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contragents.id"), nullable=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    posted: Mapped[bool] = mapped_column(Boolean, default=False)

    contragent: Mapped[Optional["Contragent"]] = relationship(back_populates="docs")
    warehouse: Mapped["Warehouse"] = relationship(back_populates="docs")
    lines: Mapped[List["DocsTable"]] = relationship(back_populates="doc", cascade="all, delete-orphan")
    stocks: Mapped[List["Stock"]] = relationship(back_populates="doc", cascade="all, delete-orphan")


class DocsTable(Base):
    __tablename__ = "docs_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey("docs.id", ondelete="CASCADE"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    qty: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)

    doc: Mapped["Doc"] = relationship(back_populates="lines")
    item: Mapped["Item"] = relationship(back_populates="lines")


class Stock(Base):
    __tablename__ = "stock"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    qty: Mapped[float] = mapped_column(Float)
    doc_id: Mapped[int] = mapped_column(ForeignKey("docs.id"))
    date: Mapped[date] = mapped_column(Date)

    item: Mapped["Item"] = relationship()
    warehouse: Mapped["Warehouse"] = relationship(back_populates="stocks")
    doc: Mapped["Doc"] = relationship(back_populates="stocks")

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    passhash: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)   

class SalePrice(Base):
    __tablename__ = 'sale_prices'
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('items.id'))
    start_date: Mapped[date] = mapped_column(Date)
    price: Mapped[float] = mapped_column(Float)
    item: Mapped["Item"] = relationship()