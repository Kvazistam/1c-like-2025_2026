"""
init_db.py – миграция и демо-данные
(ORM SQLAlchemy 2.0, регистр цен item_prices)
"""

from datetime import date

from sqlalchemy import select
from Models import Base, Item, SalePrice
from db_scripts import (
    get_session, sale_price_set,
    warehouse_add, contragent_add, item_add, user_add, engine
)
from enumerates import CONTRAGENT_TYPES

DEMO = {
    "warehouses": ["Основной склад", "Резервный склад"],
    "contragents": [
        ("ЯпонОпт", CONTRAGENT_TYPES[0]),
        ("АнимеДистриб", CONTRAGENT_TYPES[0]),
        ("Розничный покупатель", CONTRAGENT_TYPES[1]),
    ],
    "items": [
        ( "Rem Figma Re:Zero", "Figma", 2200, 3500),
        ( "Hatsune Miku Nendoroid", "Nendoroid", 1500, 2800),
        ("Levi Pop Up Parade", "Pop Up Parade", 1800, 3000),
    ],
    "users": [
        ("admin",  "", "admin"),
        ("buyer",  "",    "buy"),
        ("seller", "",    "sell"),
        ("","","admin")
    ],
}

def migrate_with_price_register():
    """Создаёт все таблицы + переносит sell_price в регистр."""
    Base.metadata.create_all(engine)          # создаст и item_prices

    with get_session() as s:
        # если в items ещё осталась колонка sell_price – переносим
        if hasattr(Item, 'sell_price'):
            for it in s.scalars(select(Item)).all():
                # первая цена «с начала времен»
                s.add(SalePrice(item_id=it.id, price=it.sell_price,
                                date_from=date(2000, 1, 1)))
            s.commit()
            # ====== SQLite не умеет ALTER DROP, поэтому просто игнорируем поле ======
            # в модели мы его уже удалили, новые БД его не создадут
            print("Старые sell_price перенесены в регистр item_prices")

def main():
    migrate_with_price_register()

    # ------- демо-данные -------
    for w in DEMO["warehouses"]:
        warehouse_add(w)

    for name, tp in DEMO["contragents"]:
        contragent_add(name, tp)

    # товары + цены
    for name, cat, buy, sell in DEMO["items"]:
        # item_add теперь сам создаёт запись в ItemPrice
        it_id = item_add(name, cat, buy)
        sale_price_set(it_id, sell, date.today()) 

    for u, p, r in DEMO["users"]:
        user_add(u, p, r)

    print("База готова, демо-данные добавлены.")

if __name__ == "__main__":
    main()