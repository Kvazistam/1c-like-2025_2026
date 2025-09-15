
"""
init_db.py – миграция и демо-данные
(использует ORM из db_crud.py)
"""

from datetime import date
from db_scripts import migrate, warehouse_add, contragent_add, item_add, user_add

DEMO = {
    "warehouses": ["Основной склад", "Резервный склад"],
    "contragents": [
        ("ЯпонОпт", "supplier"),
        ("АнимеДистриб", "supplier"),
        ("Розничный покупатель", "customer"),
    ],
    "items": [
        ("001", "Rem Figma Re:Zero", "Figma", 2200, 3500),
        ("002", "Hatsune Miku Nendoroid", "Nendoroid", 1500, 2800),
        ("003", "Levi Pop Up Parade", "Pop Up Parade", 1800, 3000),
    ],
    "users": [
        ("admin", "123456"),
    ],
}

def main():
    migrate()
    # склады
    for w in DEMO["warehouses"]:
        warehouse_add(w)
    # контрагенты
    for name, tp in DEMO["contragents"]:
        contragent_add(name, tp)
    # товары
    for code, name, cat, buy, sell in DEMO["items"]:
        item_add(code, name, cat, buy, sell)
    # пользователи
    for u, p in DEMO["users"]:
        user_add(u, p)
    print("База готова, демо-данные добавлены.")

if __name__ == "__main__":
    main()