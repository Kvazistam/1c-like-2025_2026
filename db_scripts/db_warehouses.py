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
