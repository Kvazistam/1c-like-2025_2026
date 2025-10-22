from __future__ import annotations
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    select
)

from Models import *
from db_scripts.db_session import get_session

# --- Items ---


def item_list() -> List[Dict[str, Any]]:
    with get_session() as s:
        rows = s.execute(select(Item)).scalars().all()
        return [r.__dict__ for r in rows]


def item_add(name: str,
             category: Optional[str],
             buy_price: float = None,
             image: Optional[bytes] = None,
             item_type: str = ITEM_TYPES[0],
             base_unit_id: int = None,
             storage_unit_id: int = None,
             report_unit_id: int = None) -> int:
    
    if item_type not in ITEM_TYPES:
        raise ValueError(f"Недопустимый тип товара: {item_type}. Допустимые: {ITEM_TYPES}")
    with get_session() as s:
        it = Item(
            name=name,
            category=category,
            buy_price=buy_price or 0,
            image=image,
            item_type = item_type,
            base_unit_id=base_unit_id or 1,      
            storage_unit_id=storage_unit_id or base_unit_id or 1,
            report_unit_id = report_unit_id or base_unit_id or 1
        )
        s.add(it)
        s.commit()
        return it.id


def item_update(item_id: int,
                name: str,
                category: Optional[str],
                buy_price: float = None,
                image: Optional[bytes] = None,
                item_type: str = ITEM_TYPES[0],
                base_unit_id: int = None,
                storage_unit_id: int = None,
                report_unit_id: int = None) -> None:
    with get_session() as s:
        it = s.get(Item, item_id)
        if it:
            it.name = name
            it.category = category
            if image:
                it.image = image
            it.item_type= item_type
            it.base_unit_id= base_unit_id
            it.storage_unit_id= storage_unit_id
            it.report_unit_id= report_unit_id
            s.commit()


def item_delete(item_id: int) -> None:
    with get_session() as s:
        it = s.get(Item, item_id)
        if it:
            s.delete(it)
            s.commit()


def item_get(item_id):
    with get_session() as s:
        item = s.get(Item, item_id)
        return item


def item_buy_price_get(item_id):
    with get_session() as s:
        res = s.get(Item, item_id)
    return res.buy_price
