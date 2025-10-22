from __future__ import annotations
from datetime import date
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    select, func
)

from Models import *
from db_scripts.db_session import get_session

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
            select(
                Stock.id, Stock.date, Stock.qty,
                Warehouse.name.label('warehouse'),
                Item.name.label('item'),
                Doc.doc_type,
                Contragent.name.label('contragent'),
                Item.base_unit_id,
                Item.report_unit_id
            )
            .select_from(Stock)
            .join(Warehouse, Stock.warehouse_id == Warehouse.id)
            .join(Item, Stock.item_id == Item.id)
            .join(Doc, Stock.doc_id == Doc.id)
            .outerjoin(Contragent, Doc.contragent_id == Contragent.id)
            .where(Doc.posted == True)
            .order_by(Stock.date.desc(), Stock.id.desc())
        )
        # ... фильтры ...
        rows = s.execute(stmt.limit(limit)).mappings().all()

        # Загружаем все ЕИ один раз
        units = {u.id: u for u in s.execute(select(UnitOfMeasure)).scalars().all()}

        result = []
        for r in rows:
            base_qty = r['qty']
            base_unit = units[r['base_unit_id']]
            report_unit_id = r['report_unit_id']
            
            if report_unit_id and report_unit_id in units:
                report_unit = units[report_unit_id]
                display_qty = (base_qty) / report_unit.ratio_to_base
                display_unit = report_unit.name
            else:
                display_qty = base_qty
                display_unit = base_unit.name

            result.append({
                'date': r['date'],
                'warehouse': r['warehouse'],
                'contragent': r['contragent'],
                'item': r['item'],
                'qty': display_qty,
                'unit': display_unit
            })
    return result
