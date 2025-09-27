from __future__ import annotations
from typing import List, Dict, Any

from sqlalchemy import (
    select
)

from Models import *
from db_scripts.db_session import get_session

def contragent_list_filter(type) -> List[Dict[str, Any]]:
    with get_session() as s:
        return [r.__dict__ for r in s.execute(select(Contragent).where(Contragent.type == type)).scalars().all()]

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

def contragent_update(contr_id: int, name: str, type_: str) -> None:
    with get_session() as s:
        c = s.get(Contragent, contr_id)
        if c:
            c.name = name
            c.type = type_  # хотя тип мы не меняем в UI
            s.commit()

def contragent_delete(contr_id: int) -> None:
    with get_session() as s:
        c = s.get(Contragent, contr_id)
        if c:
            s.delete(c)
            s.commit()