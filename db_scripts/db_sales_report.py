from sqlalchemy import select, func
from Models import Doc, DocsTable, Contragent, Item
from enumerates import DOC_TYPES, CONTRAGENT_TYPES
from .db_session import get_session


def get_sales_by_seller() -> list:
    """
    Возвращает список покупателей с агрегированными продажами по товарам.
    Формат:
    [
        {
            "seller": "Иван",
            "total_qty": 6,
            "total_amount": 8046.0,
            "items": [
                {"item_name": "Пластиковая фигурка DxD", "total_qty": 3, "total_amount": 6897.0},
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
                func.sum(DocsTable.qty).label("total_qty"),
                func.sum(DocsTable.qty * DocsTable.price).label("total_amount")
            )
            .select_from(Doc)
            .join(Contragent, Doc.contragent_id == Contragent.id)
            .join(DocsTable, Doc.id == DocsTable.doc_id)
            .join(Item, DocsTable.item_id == Item.id)
            .where(Doc.doc_type == DOC_TYPES[1])  # расход
            .group_by(Contragent.name, Item.name)
            .order_by(Contragent.name, Item.name)
        )

        rows = s.execute(stmt).mappings().all()

        # Группируем по покупателю
        report = {}
        for row in rows:
            customer = row[CONTRAGENT_TYPES[1]]
            if customer not in report:
                report[customer] = {
                    CONTRAGENT_TYPES[1]: customer,
                    "total_qty": 0.0,
                    "total_amount": 0.0,
                    "items": []
                }

            item_data = {
                "item_name": row['item_name'],
                "total_qty": float(row['total_qty']),
                "total_amount": float(row['total_amount'])
            }
            report[customer]["items"].append(item_data)
            report[customer]["total_qty"] += row['total_qty']
            report[customer]["total_amount"] += row['total_amount']

        return list(report.values())