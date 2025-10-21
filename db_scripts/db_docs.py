from __future__ import annotations
from datetime import date
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    select, delete
)
from sqlalchemy.orm import selectinload

from Models import *
from db_scripts.db_sale_prices import sale_price_get_date
from db_scripts.db_session import get_session
from db_scripts.db_stock import stock_on_date
from enumerates import BONUS_PERCENT, DOC_TYPES
from .db_bonuses import add_bonus, get_bonus_balance, set_bonus_balance, spend_bonus

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
                    contragent_id: Optional[int], comment: Optional[str],
                    bonus_mode: Optional[str] = None, bonus_amount: float = 0.0):
    with get_session() as s:
        d = s.get(Doc, doc_id)
        if d:
            d.date = date_
            d.warehouse_id = warehouse_id
            d.contragent_id = contragent_id
            d.comment = comment
            if bonus_mode is not None:
                d.bonus_mode = bonus_mode
                d.bonus_amount = bonus_amount
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
        res =  s.execute(
            select(Doc)
            .options(
                selectinload(Doc.lines).selectinload(DocsTable.item),
                selectinload(Doc.lines)
                .selectinload(DocsTable.unit),
                selectinload(Doc.warehouse),
                selectinload(Doc.contragent)
            )
            .where(Doc.id == doc_id)
        ).scalar_one_or_none()
    return res


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
        s.execute(delete(DocsTable).where(DocsTable.doc_id == doc_id))
        for r in rows:
            line = DocsTable(
                doc_id=doc_id,
                item_id=r['item_id'],
                unit_id=r['unit_id'],  
                price=r['price'],
                qty=r['qty']
            )
            s.add(line)
        s.commit()
  
  
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
            if d.doc_type == DOC_TYPES[1]:          
                line.price = sale_price_get_date(line.item_id, d.date)
            # --------------------------------------------------

            st = Stock(item_id=line.item_id,
                       warehouse_id=d.warehouse_id,
                       qty=sign * line.qty,
                       doc_id=doc_id,
                       date=d.date)
            s.add(st)

        # --- Бонусы (только для расхода) ---
        if d.doc_type == DOC_TYPES[1] and d.contragent_id:
            
            total = sum(line.qty * line.price for line in d.lines)
            

            if d.bonus_mode == "save":
                bonus_earned = total * BONUS_PERCENT  # 5%

                add_bonus(d.contragent_id, bonus_earned)
                d.bonus_amount = bonus_earned
            elif d.bonus_mode == "spend":
                if d.bonus_amount > 0:
                    # Проверка: не больше 50% и не больше баланса
                    if d.bonus_amount > total / 2:
                        raise ValueError("Бонусами можно оплатить не более 50% суммы")
                    spend_bonus(d.contragent_id, d.bonus_amount)

        d.posted = True
        s.commit()





def doc_unpost(doc_id: int) -> None:
    with get_session() as s:
        d = s.get(Doc, doc_id)
        if not d or not d.posted:
            return

        
        if d.doc_type == DOC_TYPES[1] and d.contragent_id and d.bonus_amount > 0:

            if d.bonus_mode == "save":
 
                s.execute(
                    update(BonusBalance)
                    .where(BonusBalance.contragent_id == d.contragent_id)
                    .values(balance=BonusBalance.balance - d.bonus_amount)
                )
            elif d.bonus_mode == "spend":

                s.execute(
                    update(BonusBalance)
                    .where(BonusBalance.contragent_id == d.contragent_id)
                    .values(balance=BonusBalance.balance + d.bonus_amount)
                )



        s.execute(delete(Stock).where(Stock.doc_id == doc_id))
        d.posted = False
        s.commit()
