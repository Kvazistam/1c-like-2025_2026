from sqlalchemy import select, delete
from Models import ProductionDoc, ProductionInput, ProductionOutput, Stock
from .db_session import get_session

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