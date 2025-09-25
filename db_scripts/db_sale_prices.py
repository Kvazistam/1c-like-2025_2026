from __future__ import annotations
from datetime import date
from typing import List, Dict, Any

from sqlalchemy import (
    select
)
from sqlalchemy.orm import selectinload

from Models import *
from db_scripts.db_session import get_session

def sale_price_get_date(item_id: int, on_date: date) -> float:
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

def sale_price_set(item_id: int, new_price: float, start: date):
    with get_session() as s:
        s.add(SalePrice(item_id=item_id,
                        start_date=start,
                        price=new_price))
        s.commit()
        
def sale_price_get_id(doc_id: int):
    with get_session() as s:
        res = s.execute(
            select(SalePrice)
            .options(selectinload(SalePrice.item))
            .where(SalePrice.id == doc_id)
            
        ).scalar_one_or_none()
        return res
        
        
# --- Sale Prices (розничные цены) ---
def sale_price_list() -> List[Dict[str, Any]]:
    """Список всех розничных цен."""
    with get_session() as s:
        stmt = (
            select(SalePrice.item_id,Item.name.label('item_name'), SalePrice.start_date, SalePrice.price, SalePrice.id)
            .join(Item, SalePrice.item_id == Item.id)
            .order_by(SalePrice.start_date.desc(), Item.name)
        )
        rows = s.execute(stmt).mappings().all()
        return [dict(r) for r in rows]


def sale_price_update(price_id: int, item_id: int, start_date: date, price: float) -> None:
    """Обновить запись цены."""
    with get_session() as s:
        sp = s.get(SalePrice, price_id)
        if sp:
            sp.item_id = item_id
            sp.start_date = start_date
            sp.price = price
            s.commit()


def sale_price_delete(price_id: int) -> None:
    """Удалить запись цены."""
    with get_session() as s:
        sp = s.get(SalePrice, price_id)
        if sp:
            s.delete(sp)
            s.commit()
#-------------------------------------------
