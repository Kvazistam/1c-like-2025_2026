#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
init_db.py – первичное заполнение БД демо-данными
"""

import sqlite3
import os
import hashlib

DB_FILE = "anime1c.db"

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

-- СПРАВОЧНИКИ
CREATE TABLE IF NOT EXISTS items(
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    category    TEXT,
    buy_price   REAL DEFAULT 0,
    sell_price  REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS contragents(
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT CHECK( type IN ('supplier','customer') ) NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouses(
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- ДОКУМЕНТЫ
CREATE TABLE IF NOT EXISTS docs(
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_type  TEXT CHECK( doc_type IN ('приход','расход','инвентаризация') ) NOT NULL,
    date      TEXT NOT NULL,
    contragent_id  INTEGER,
    warehouse_id   INTEGER NOT NULL,
    comment   TEXT,
    posted    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS docs_table(
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id   INTEGER NOT NULL REFERENCES docs(id) ON DELETE CASCADE,
    item_id  INTEGER NOT NULL REFERENCES items(id),
    qty      REAL CHECK( qty > 0 ),
    price    REAL
);

-- РЕГИСТР ОСТАТКОВ
CREATE TABLE IF NOT EXISTS stock(
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id   INTEGER NOT NULL,
    warehouse_id INTEGER NOT NULL,
    qty       REAL NOT NULL,
    doc_id    INTEGER NOT NULL,
    date      TEXT NOT NULL
);

-- ПОЛЬЗОВАТЕЛИ
CREATE TABLE IF NOT EXISTS users(
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    passhash TEXT NOT NULL
);
"""

DEMO_DATA = {
    "warehouses": [
        ("Основной склад",),
        ("Резервный склад",),
    ],
    "contragents": [
        ("ЯпонОпт", "supplier"),
        ("АнимеДистриб", "supplier"),
        ("Розничный покупатель", "customer"),
    ],
    "items": [
        ("001", "Rem Figma Re:Zero", "Figma", 2200, 3500),
        ("002", "Hatsune Miku Nendoroid", "Nendoroid", 1500, 2800),
        ("003", "Levi Ackerman Pop Up Parade", "Pop Up Parade", 1800, 3000),
    ],
    "users": [
        ("admin", "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"),  # 123456
    ],
}

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_schema():
    with get_conn() as c:
        c.executescript(SCHEMA_SQL)

def fill_demo():
    with get_conn() as c:
        # склады
        for name, in DEMO_DATA["warehouses"]:
            c.execute("INSERT OR IGNORE INTO warehouses(name) VALUES (?)", (name,))
        # контрагенты
        for name, tp in DEMO_DATA["contragents"]:
            c.execute("INSERT OR IGNORE INTO contragents(name,type) VALUES (?,?)", (name, tp))
        # товары
        for code, name, cat, buy, sell in DEMO_DATA["items"]:
            c.execute(
                "INSERT OR IGNORE INTO items(code,name,category,buy_price,sell_price) VALUES (?,?,?,?,?)",
                (code, name, cat, buy, sell)
            )
        # пользователи
        for u, ph in DEMO_DATA["users"]:
            c.execute("INSERT OR IGNORE INTO users(username,passhash) VALUES (?,?)", (u, ph))

def main():
    if not os.path.exists(DB_FILE):
        print("База не найдена – создаём новую.")
    init_schema()
    fill_demo()
    print("База инициализирована / обновлена.")

if __name__ == "__main__":
    main()