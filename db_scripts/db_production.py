from typing import Any, Dict, List, Optional
from sqlalchemy import select, delete
from Models import ProductionDoc, ProductionInput, ProductionOutput, Stock, Warehouse
from .db_session import get_session
from sqlalchemy.orm import selectinload
def production_get(doc_id: int) -> Optional[ProductionDoc]:
    """
    Загружает документ производства со всеми связанными строками.
    """
    with get_session() as s:
        return s.execute(
            select(ProductionDoc)
            .options(
                selectinload(ProductionDoc.input_lines)
                .selectinload(ProductionInput.item),
                selectinload(ProductionDoc.input_lines)
                .selectinload(ProductionInput.unit),
                selectinload(ProductionDoc.output_lines)
                .selectinload(ProductionOutput.item),
                selectinload(ProductionDoc.output_lines)
                .selectinload(ProductionOutput.unit),
                selectinload(ProductionDoc.warehouse)
            )
            .where(ProductionDoc.id == doc_id)
        ).scalar_one_or_none()


def production_unpost(doc_id: int) -> None:
    """
    Отменяет проведение документа производства.
    Удаляет движения по складу и возвращает документ в непроведённое состояние.
    """
    with get_session() as s:
        d = s.get(ProductionDoc, doc_id)
        if not d or not d.posted:
            return

        # Удаляем движения по складу
        s.execute(delete(Stock).where(Stock.doc_id == doc_id))

        d.posted = False
        s.commit()

def production_save_head(date_, warehouse_id, comment=""):
    with get_session() as s:
        d = ProductionDoc(date=date_, warehouse_id=warehouse_id, comment=comment)
        s.add(d)
        s.commit()
        return d.id

def production_save_lines(doc_id, input_rows, output_rows):
    with get_session() as s:
        s.execute(delete(ProductionInput).where(ProductionInput.doc_id == doc_id))
        s.execute(delete(ProductionOutput).where(ProductionOutput.doc_id == doc_id))
        
        for r in input_rows:
            s.add(ProductionInput(
                doc_id=doc_id,
                item_id=r['item_id'],
                unit_id=r['unit_id'],
                qty=r['qty']
            ))
        for r in output_rows:
            s.add(ProductionOutput(
                doc_id=doc_id,
                item_id=r['item_id'],
                unit_id=r['unit_id'],
                qty=r['qty']
            ))
        s.commit()

def production_post(doc_id):
    with get_session() as s:
        d = s.get(ProductionDoc, doc_id)
        if not d or d.posted:
            raise ValueError("Документ не найден или уже проведён")
        
        # Списание материалов (input)
        for line in d.input_lines:
            base_qty = line.qty * line.unit.ratio_to_base
            st = Stock(
                item_id=line.item_id,
                warehouse_id=d.warehouse_id,
                qty=-base_qty,  # списание
                doc_id=doc_id,
                date=d.date
            )
            s.add(st)
        
        # Приход готовой продукции (output)
        for line in d.output_lines:
            base_qty = line.qty * line.unit.ratio_to_base
            st = Stock(
                item_id=line.item_id,
                warehouse_id=d.warehouse_id,
                qty=base_qty,  # приход
                doc_id=doc_id,
                date=d.date
            )
            s.add(st)
        
        d.posted = True
        s.commit()
        

def production_list() -> List[Dict[str, Any]]:
    """Список документов производства."""
    with get_session() as s:
        stmt = (
            select(
                ProductionDoc.id,
                ProductionDoc.date,
                ProductionDoc.posted,
                ProductionDoc.comment,
                Warehouse.name.label("warehouse")
            )
            .join(Warehouse, ProductionDoc.warehouse_id == Warehouse.id)
            .order_by(ProductionDoc.date.desc())
        )
        rows = s.execute(stmt).mappings().all()
        return [dict(r) for r in rows]


def production_delete(doc_id: int) -> None:
    """Удалить документ производства (только непроведённый)."""
    with get_session() as s:
        d = s.get(ProductionDoc, doc_id)
        if d:
            if d.posted:
                raise ValueError("Нельзя удалить проведённый документ")
            s.delete(d)
            s.commit()