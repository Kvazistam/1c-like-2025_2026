"""
init_db.py – миграция и демо-данные
(ORM SQLAlchemy 2.0, регистр цен item_prices, единицы измерения, производство)
"""

from datetime import date

from sqlalchemy import select
from Models import (
    Base, Item, SalePrice, UnitOfMeasure,
)
from db_scripts import (
    get_session, sale_price_set,
    warehouse_add, contragent_add, item_add, user_add, engine,
    unit_add 
)
from enumerates import CONTRAGENT_TYPES, ITEM_TYPES


DEMO = {
    "warehouses": ["Основной склад", "Резервный склад"],
    "contragents": [
        ("ЯпонОпт", CONTRAGENT_TYPES[0]),
        ("АнимеДистриб", CONTRAGENT_TYPES[0]),
        ("Розничный покупатель", CONTRAGENT_TYPES[1]),
    ],
    "units": [
    ("Штука", 1.0, None, None, ITEM_TYPES[0]),
    ("Грамм", 1.0, 0.001, None, ITEM_TYPES[1]),
    ("Килограмм", 1000.0, 1.0, None, ITEM_TYPES[1]),
    ("Литр", 1.0, None, 1.0, ITEM_TYPES[2]),
    ("Коробка", 24.0, None, None, ITEM_TYPES[0]),
    ],
    "items": [
        # (name, category, buy_price, sell_price, base_unit_name)
        ("Rem Figma Re:Zero", "Figma", 2200, 3500, "Штука", ITEM_TYPES[0]),
        ("Hatsune Miku Nendoroid", "Nendoroid", 1500, 2800, "Штука", ITEM_TYPES[0]),
        ("Levi Pop Up Parade", "Pop Up Parade", 1800, 3000, "Штука", ITEM_TYPES[0]),
        ("Сахар", "Сыпучие", 50, 100, "Грамм", ITEM_TYPES[1]),  # базовая ЕИ — граммы
    ],
    "users": [
        ("admin", "", "admin"),
        ("buyer", "", "buy"),
        ("seller", "", "sell"),
        ("", "", "admin")
    ],
}


def migrate_with_price_register():
    """Создаёт все таблицы + переносит sell_price в регистр."""
    Base.metadata.create_all(engine)

    with get_session() as s:
        
        if hasattr(Item, 'sell_price'):
            for it in s.scalars(select(Item)).all():
                s.add(SalePrice(item_id=it.id, price=it.sell_price, date_from=date(2000, 1, 1)))
            s.commit()
            print("Старые sell_price перенесены в регистр SalePrice")


def main():
    migrate_with_price_register()

    # ------- 1. Добавляем единицы измерения -------
    unit_map = {}
    for name, ratio, _, _, item_type in DEMO["units"]:
        unit_id = unit_add(name, ratio, applicable_to=item_type)
        unit_map[name] = unit_id

    # ------- 2. Склады и контрагенты -------
    for w in DEMO["warehouses"]:
        warehouse_add(w)

    for name, tp in DEMO["contragents"]:
        contragent_add(name, tp)

    # ------- 3. Товары + цены + привязка к ЕИ -------
    for name, cat, buy, sell, base_unit_name, item_type in DEMO["items"]:
        base_unit_id = unit_map[base_unit_name]
        # item_add теперь принимает base_unit_id
        it_id = item_add(
            name=name,
            category=cat,
            buy_price=buy,
            item_type=item_type,
            base_unit_id=base_unit_id,
            storage_unit_id=base_unit_id  # можно указать отдельно
        )
        sale_price_set(it_id, sell, date.today())

    # ------- 4. Пользователи -------
    for u, p, r in DEMO["users"]:
        user_add(u, p, r)  

    print("✅ База готова: демо-данные, ЕИ, товары, цены")


if __name__ == "__main__":
    main()