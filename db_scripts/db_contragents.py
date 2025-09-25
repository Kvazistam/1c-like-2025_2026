from __future__ import annotations
from typing import List, Dict, Any

from sqlalchemy import (
    select
)

from Models import *
from db_scripts.db_session import get_session



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

