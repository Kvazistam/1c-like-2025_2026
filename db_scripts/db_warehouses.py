from __future__ import annotations
from typing import List, Dict, Any

from sqlalchemy import (
    select
)

from Models import *
from db_scripts.db_session import get_session


def warehouse_list() -> List[Dict[str, Any]]:
    with get_session() as s:
        return [r.__dict__ for r in s.execute(select(Warehouse)).scalars().all()]


def warehouse_add(name: str) -> int:
    with get_session() as s:
        w = Warehouse(name=name)
        s.add(w)
        s.commit()
        return w.id

def warehouse_update(warehouse_id: int, name: str) -> None:
    with get_session() as s:
        w = s.get(Warehouse, warehouse_id)
        if w:
            w.name = name
            s.commit()

def warehouse_delete(warehouse_id: int) -> None:
    with get_session() as s:
        w = s.get(Warehouse, warehouse_id)
        if w:
            s.delete(w)
            s.commit()