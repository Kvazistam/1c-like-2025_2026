# db_scripts/sales_report.py
from sqlalchemy import select, func
from Models import Doc, DocsTable, Contragent, Item, Stock
from enumerates import CONTRAGENT_TYPES
from .db_session import get_session


def get_sales_by_seller() -> list:
    """
    Возвращает список покупателей с их заказами.
    Формат:
    [
        {
            "seller": "Иван",
            "total_qty": 6,
            "total_amount": 8046.0,
            "items": [
                {"item_name": "Пластиковая фигурка DxD", "price": 2299.0, "qty": 3, "amount": 6897.0},
                ...
            ]
        },
        ...
    ]
    """
    with get_session() as s:
        stmt = (
            select(
                Contragent.name.label(CONTRAGENT_TYPES[1]),
                Item.name.label("item_name"),
                DocsTable.price,
                DocsTable.qty,
                (DocsTable.qty * DocsTable.price).label("amount")
            )
            .select_from(Doc)
            .join(Contragent, Doc.contragent_id == Contragent.id)
            .join(DocsTable, Doc.id == DocsTable.doc_id)
            .join(Item, DocsTable.item_id == Item.id)
            .where(Doc.doc_type == 'расход')
            .order_by(Contragent.name, Item.name)
        )

        rows = s.execute(stmt).mappings().all()

        # Группируем по покупателю
        report = {}
        for row in rows:
            seller = row[CONTRAGENT_TYPES[1]]
            if seller not in report:
                report[seller] = {
                    CONTRAGENT_TYPES[1]: seller,
                    "total_qty": 0.0,
                    "total_amount": 0.0,
                    "items": []
                }
            item_data = {
                "item_name": row['item_name'],
                "price": row['price'],
                "qty": row['qty'],
                "amount": row['amount']
            }
            report[seller]["items"].append(item_data)
            report[seller]["total_qty"] += row['qty']
            report[seller]["total_amount"] += row['amount']

        return list(report.values())