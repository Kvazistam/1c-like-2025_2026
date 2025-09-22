

"""
ORM-слой и CRUD-функции для Anime1C
SQLAlchemy 2.0 (синхронный режим)
"""

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

class ItemPrice(Base):
    """Регистр цен по времени."""
    __tablename__ = 'item_prices'

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('items.id'))
    price: Mapped[float] = mapped_column(Float)
    date_from: Mapped[date] = mapped_column(Date)   # начало действия
    date_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # NULL = «до сих пор»

    item: Mapped['Item'] = relationship()

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
# ---- создание таблиц ----
def create_tables():
    Base.metadata.create_all(engine)


# ---- CRUD-обёртки ----
def get_session() -> Session:
    return Session(engine, future=True)


# --- Items ---
def item_list() -> List[Dict[str, Any]]:
    with get_session() as s:
        rows = s.execute(select(Item)).scalars().all()
        return [r.__dict__ for r in rows]


# 3.1  получить актуальную цену на дату
def price_get(item_id: int, on_date: date = None) -> float:
    on_date = on_date or date.today()
    with get_session() as s:
        row = s.scalar(
            select(ItemPrice.price)
            .where(ItemPrice.item_id == item_id,
                   ItemPrice.date_from <= on_date,
                   or_(ItemPrice.date_to.is_(None),
                       ItemPrice.date_to >= on_date))
            .order_by(ItemPrice.date_from.desc())
            .limit(1)
        )
        return row or 0.0

# 3.2  установить новую цену (закрываем предыдущую)
def price_set(item_id: int, new_price: float, from_date: date = None):
    from_date = from_date or date.today()
    with get_session() as s:
        # закрываем старую
        s.execute(
            update(ItemPrice)
            .where(ItemPrice.item_id == item_id,
                   ItemPrice.date_to.is_(None))
            .values(date_to=from_date - timedelta(days=1))
        )
        # добавляем новую
        s.add(ItemPrice(item_id=item_id, price=new_price, date_from=from_date))
        s.commit()

def item_add(name: str, category: Optional[str],
             buy_price: float = None, image: Optional[bytes] = None) -> int:
    with get_session() as s:
        it = Item(name=name, category=category,
                  buy_price=buy_price, image=image)  
        s.add(it)
        s.commit()
        return it.id


def item_delete(item_id: int) -> None:
    with get_session() as s:
        it = s.get(Item, item_id)
        if it:
            s.delete(it)
            s.commit()


# --- Contragents ---
def contragent_list() -> List[Dict[str, Any]]:
    with get_session() as s:
        return [r.__dict__ for r in s.execute(select(Contragent)).scalars().all()]


def contragent_add(name: str, type_: str) -> int:
    with get_session() as s:
        c = Contragent(name=name, type=type_)
        s.add(c)
        s.commit()
        return c.id


# --- Warehouses ---
def warehouse_list() -> List[Dict[str, Any]]:
    with get_session() as s:
        return [r.__dict__ for r in s.execute(select(Warehouse)).scalars().all()]


def warehouse_add(name: str) -> int:
    with get_session() as s:
        w = Warehouse(name=name)
        s.add(w)
        s.commit()
        return w.id


# --- Docs ---
def doc_save_head(doc_type: str, date_: date, warehouse_id: int,
                  contragent_id: Optional[int], comment: Optional[str]) -> int:
    """Создаёт новый документ и возвращает id."""
    with get_session() as s:
        d = Doc(doc_type=doc_type, date=date_, warehouse_id=warehouse_id,
                contragent_id=contragent_id, comment=comment, posted=False)
        s.add(d)
        s.commit()
        return d.id


def doc_update_head(doc_id: int, date_: date, warehouse_id: int,
                    contragent_id: Optional[int], comment: Optional[str]) -> None:
    with get_session() as s:
        d = s.get(Doc, doc_id)
        if d:
            d.date = date_
            d.warehouse_id = warehouse_id
            d.contragent_id = contragent_id
            d.comment = comment
            s.commit()


def doc_list(doc_type: str) -> List[Dict[str, Any]]:
    with get_session() as s:
        stmt = (
            select(Doc.id, Doc.date, Doc.doc_type, Doc.posted,
                   Warehouse.name.label("warehouse"),
                   Contragent.name.label("contragent"))
            .join(Warehouse)
            .outerjoin(Contragent)
            .where(Doc.doc_type == doc_type)
            .order_by(Doc.date.desc())
        )
        rows = s.execute(stmt).mappings().all()
        return [dict(r) for r in rows]


def doc_get(doc_id: int) -> Optional[Doc]:
    with get_session() as s:
        return s.execute(
            select(Doc)
            .options(
                selectinload(Doc.lines).selectinload(DocsTable.item),
                selectinload(Doc.warehouse),
                selectinload(Doc.contragent)
            )
            .where(Doc.id == doc_id)
        ).scalar_one_or_none()


def doc_delete(doc_id: int) -> None:
    with get_session() as s:
        d = s.get(Doc, doc_id)
        if d:
            s.delete(d)
            s.commit()


# --- DocsTable ---
def doc_save_table(doc_id: int, rows: List[Dict[str, Any]]) -> None:
    """rows = [{'item_id': int, 'qty': float, 'price': float}, ...]"""
    with get_session() as s:
        # удалим старые строки
        s.execute(delete(DocsTable).where(DocsTable.doc_id == doc_id))
        # добавим новые
        for r in rows:
            line = DocsTable(doc_id=doc_id, item_id=r['item_id'],
                             qty=r['qty'], price=r['price'])
            s.add(line)
        print('doc_id:', doc_id, 'rows:', rows)
        s.commit()
        
# --- Подсчет колитчества товара на складе --- 
def stock_on_date(item_id: int, warehouse_id: int, on_date: date) -> float:
    """Остаток товара на складе на конкретную дату (включая все проведённые движения)."""
    with get_session() as s:
        total = s.scalar(
            select(func.sum(Stock.qty))
            .where(Stock.item_id == item_id,
                   Stock.warehouse_id == warehouse_id,
                   Stock.date <= on_date)
        )
        return total or 0.0

# --- Проводки / остатки ---
def doc_post(doc_id: int) -> None:
    with get_session() as s:
        d = s.get(Doc, doc_id)
        if not d:
            raise ValueError("Документ не найден")
        if d.posted:
            raise ValueError("Документ уже проведён")

        if d.doc_type == DOC_TYPES[1]:
            for line in d.lines:
                avail = stock_on_date(line.item_id, d.warehouse_id, d.date)
                if avail < line.qty:
                    raise ValueError(
                        f"Недостаточно товара '{line.item.name}' "
                        f"на складе '{d.warehouse.name}' "
                        f"(доступно {avail:.2f}, требуется {line.qty:.2f})"
                    )
        
        sign = 1 if d.doc_type == DOC_TYPES[0] else -1

        for line in d.lines:
            # --------------- ключевое изменение ---------------
            if d.doc_type == DOC_TYPES[1]:          # ПРОДАЖА
                line.price = price_get(line.item_id, d.date)
            # --------------------------------------------------

            st = Stock(item_id=line.item_id,
                       warehouse_id=d.warehouse_id,
                       qty=sign * line.qty,
                       doc_id=doc_id,
                       date=d.date)
            s.add(st)

        d.posted = True
        s.commit()


def doc_unpost(doc_id: int) -> None:
    with get_session() as s:
        d = s.get(Doc, doc_id)
        if d:
            d.posted = False
            s.execute(delete(Stock).where(Stock.doc_id == doc_id))
            s.commit()


def stock_balance(item_id: int, warehouse_id: int) -> float:
    with get_session() as s:
        total = s.scalar(
            select(func.sum(Stock.qty))
            .where(Stock.item_id == item_id, Stock.warehouse_id == warehouse_id)
        )
        return total or 0.0
    

def stock_movements(warehouse_id: Optional[int] = None,
                    item_id: Optional[int] = None,
                    limit: int = 500) -> List[Dict[str, Any]]:
    with get_session() as s:
        stmt = (
            select(Stock.id, Stock.date, Stock.qty,
                   Warehouse.name.label('warehouse'),
                   Item.name.label('item'),
                   Doc.doc_type,
                   Contragent.name.label('contragent'))
            .select_from(Stock)
            .join(Warehouse, Stock.warehouse_id == Warehouse.id)          
            .join(Item, Stock.item_id == Item.id)                        
            .join(Doc, Stock.doc_id == Doc.id)                           
            .outerjoin(Contragent, Doc.contragent_id == Contragent.id)   
            .where(Doc.posted == True)
            .order_by(Stock.date.desc(), Stock.id.desc())
        )

        if warehouse_id:
            stmt = stmt.where(Stock.warehouse_id == warehouse_id)
        if item_id:
            stmt = stmt.where(Stock.item_id == item_id)

        rows = s.execute(stmt.limit(limit)).mappings().all()
        return [dict(r) for r in rows]


# def stock_report() -> List[Dict[str, Any]]:
#     """Остатки по складам."""
#     with get_session() as s:
#         stmt = (
#             select(Item.name.label("item"),
#                    Warehouse.name.label("warehouse"),
#                    func.sum(Stock.qty).label("qty"))
#             .join(Item).join(Warehouse)
#             .group_by(Item.id, Warehouse.id)
#             .having(func.sum(Stock.qty) != 0)
#             .order_by(Warehouse.name, Item.name)
#         )
#         rows = s.execute(stmt).mappings().all()
#         return [dict(r) for r in rows]


# --- Пользователи (для будущего входа) ---
def user_add(username: str, plain_password: str, role: str) -> None:
    ph = hashlib.sha256(plain_password.encode()).hexdigest()
    with get_session() as s:
        s.add(User(username=username, passhash=ph, role=role))
        s.commit()


def user_check(username: str, plain_password: str) -> tuple[bool, str]:
    ph = hashlib.sha256(plain_password.encode()).hexdigest()
    with get_session() as s:
        u = s.scalar(select(User).where(User.username == username))
        if u and u.passhash == ph:
            return True, u.role
        return False, ''


# --- Миграция / создание всего ---
def migrate():
    create_tables()
    

def sale_price_get(item_id: int, on_date: date) -> float:
    """Цена на дату (последняя по дате)."""
    with get_session() as s:
        row = s.scalar(
            select(SalePrice.price)
            .where(SalePrice.item_id == item_id,
                   SalePrice.start_date <= on_date)
            .order_by(SalePrice.start_date.desc())
            .limit(1)
        )
        return row or 0.0

def sale_price_set(item_id: int, new_price: float, start: date = None):
    with get_session() as s:
        s.add(SalePrice(item_id=item_id,
                        start_date=start or date.today(),
                        price=new_price))
        s.commit()
        
