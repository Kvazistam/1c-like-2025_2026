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

def item_add(name: str, category: Optional[str],
             buy_price: float = None, image: Optional[bytes] = None) -> int:
    with get_session() as s:
        it = Item(name=name, category=category,
                  buy_price=buy_price, image=image)  
        s.add(it)
        s.commit()
        return it.id

def item_update(item_id: int, name: str, category: Optional[str], buy_price: float = None, image: Optional[bytes] = None) -> None:
    with get_session() as s:
        it = s.get(Item, item_id)
        if it:
            it.name = name
            it.category = category
            if image:
                it.image = image
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

