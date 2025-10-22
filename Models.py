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

from enumerates import DOC_TYPES, ITEM_TYPES

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
    
    base_unit_id: Mapped[int] = mapped_column(ForeignKey("units_of_measure.id"))  # Базовая ЕИ
    storage_unit_id: Mapped[Optional[int]] = mapped_column(ForeignKey("units_of_measure.id"), nullable=True)  # Для остатков
    report_unit_id: Mapped[Optional[int]] = mapped_column(ForeignKey("units_of_measure.id"), nullable=True)  # Для отчётов

    base_unit: Mapped[UnitOfMeasure] = relationship(foreign_keys=[base_unit_id])

    item_type: Mapped[str] = mapped_column(String, default=ITEM_TYPES[0])  

    base_unit_id: Mapped[int] = mapped_column(ForeignKey("units_of_measure.id"))        # Базовая ЕИ
    storage_unit_id: Mapped[int] = mapped_column(ForeignKey("units_of_measure.id"))     # Для остатков
    report_unit_id: Mapped[int] = mapped_column(ForeignKey("units_of_measure.id"))      # Для отчётов

    # Связи
    base_unit: Mapped[UnitOfMeasure] = relationship(foreign_keys=[base_unit_id])
    storage_unit: Mapped[UnitOfMeasure] = relationship(foreign_keys=[storage_unit_id])
    report_unit: Mapped[UnitOfMeasure] = relationship(foreign_keys=[report_unit_id])
    storage_unit: Mapped[Optional[UnitOfMeasure]] = relationship(foreign_keys=[storage_unit_id])
    report_unit: Mapped[Optional[UnitOfMeasure]] = relationship(foreign_keys=[report_unit_id])
    lines: Mapped[List["DocsTable"]] = relationship(back_populates="item")



class Contragent(Base):
    __tablename__ = "contragents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)  # supplier / seller

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
    
    bonus_mode: Mapped[str] = mapped_column(String, nullable=True)  # 'save' или 'spend'
    bonus_amount: Mapped[float] = mapped_column(Float, default=0.0)  # сумма бонусов
    
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
    unit_id: Mapped[int] = mapped_column(ForeignKey("units_of_measure.id"))  
    
    unit: Mapped["UnitOfMeasure"] = relationship()
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
    
    


class BonusBalance(Base):
    __tablename__ = "bonus_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contragent_id: Mapped[int] = mapped_column(ForeignKey("contragents.id"), unique=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)  

    contragent: Mapped["Contragent"] = relationship()
    
   
   
    
class UnitOfMeasure(Base):
    __tablename__ = "units_of_measure"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)  # "Коробка", "Грамм", "Штука"
    base_unit_id: Mapped[Optional[int]] = mapped_column(ForeignKey("units_of_measure.id"), nullable=True)
    ratio_to_base: Mapped[float] = mapped_column(Float, default=1.0)  # Сколько базовых в этой единице
    weight: Mapped[Optional[float]] = mapped_column(Float)  # Вес единицы (кг)
    volume: Mapped[Optional[float]] = mapped_column(Float)  # Объём (л)
    
    # Для каких типов товаров подходит
    applicable_to: Mapped[str] = mapped_column(String, default=ITEM_TYPES[0])  
    
    # Связь с базовой единицей (сама на себя)
    base_unit: Mapped["UnitOfMeasure"] = relationship(remote_side="UnitOfMeasure.id", back_populates="derived_units")
    derived_units: Mapped[List["UnitOfMeasure"]] = relationship(back_populates="base_unit")
    
    
    
class ProductionDoc(Base):
    __tablename__ = "production_docs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    comment: Mapped[Optional[str]] = mapped_column(String)
    posted: Mapped[bool] = mapped_column(Boolean, default=False)
    in_doc_id: Mapped[int] = mapped_column(ForeignKey("docs.id"), unique=True, nullable=True)
    out_doc_id: Mapped[int] = mapped_column(ForeignKey("docs.id"), unique=True,  nullable=True)

    in_doc: Mapped[Doc] = relationship("Doc", foreign_keys=[in_doc_id]  )
    out_doc: Mapped[Doc] = relationship("Doc",  foreign_keys=[out_doc_id])
    warehouse: Mapped[Warehouse] = relationship()
    input_lines: Mapped[List["ProductionInput"]] = relationship(cascade="all, delete-orphan")
    output_lines: Mapped[List["ProductionOutput"]] = relationship(cascade="all, delete-orphan")


class ProductionInput(Base):
    __tablename__ = "production_input"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey("production_docs.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    unit_id: Mapped[int] = mapped_column(ForeignKey("units_of_measure.id"))
    qty: Mapped[float] = mapped_column(Float)

    doc: Mapped[ProductionDoc] = relationship(back_populates="input_lines")
    item: Mapped[Item] = relationship()
    unit: Mapped[UnitOfMeasure] = relationship()


class ProductionOutput(Base):
    __tablename__ = "production_output"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey("production_docs.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    unit_id: Mapped[int] = mapped_column(ForeignKey("units_of_measure.id"))
    qty: Mapped[float] = mapped_column(Float)

    doc: Mapped[ProductionDoc] = relationship(back_populates="output_lines")
    item: Mapped[Item] = relationship()
    unit: Mapped[UnitOfMeasure] = relationship()
    