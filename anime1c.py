#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anime1c.py – упрощённый «1С» для учёта аниме-фигурок
tkinter + SQLite, одним файлом
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
import os

import datetime as dt
from typing import List, Dict, Any

DB_FILE = 'anime1c.db'

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

-- РЕГИСТР ОСТАТКОВ (проводки)
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

# ---------- Утилиты БД ----------
def dict_factory(c, r):
    return {col[0]: r[idx] for idx, col in enumerate(c.description)}

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = dict_factory
    return conn

def init_db():
    if not os.path.exists(DB_FILE):
        with get_conn() as c:
            c.executescript(SCHEMA_SQL)
            # Склад по умолчанию
            c.execute("INSERT OR IGNORE INTO warehouses(name) VALUES('Основной склад')")

# ---------- CRUD-обёртки ----------
def fetch_all(sql, params=()) -> List[Dict[str, Any]]:
    with get_conn() as c:
        return c.execute(sql, params).fetchall()

def fetch_one(sql, params=()):
    with get_conn() as c:
        return c.execute(sql, params).fetchone()

def execute(sql, params=()):
    with get_conn() as c:
        c.execute(sql, params)
        return c.lastrowid

# ---------- Проводки ----------
def post_doc(doc_id: int):
    with get_conn() as c:
        doc = c.execute("SELECT * FROM docs WHERE id=?", (doc_id,)).fetchone()
        if not doc:
            raise ValueError("Документ не найден")
        if doc['posted']:
            raise ValueError("Документ уже проведён")
        rows = c.execute("SELECT * FROM docs_table WHERE doc_id=?", (doc_id,)).fetchall()
        sign = 1 if doc['doc_type'] == 'приход' else -1
        for r in rows:
            c.execute(
                "INSERT INTO stock(item_id, warehouse_id, qty, doc_id, date) VALUES (?,?,?,?,?)",
                (r['item_id'], doc['warehouse_id'], sign * r['qty'], doc_id, doc['date'])
            )
        c.execute("UPDATE docs SET posted=1 WHERE id=?", (doc_id,))

def unpost_doc(doc_id: int):
    with get_conn() as c:
        c.execute("DELETE FROM stock WHERE doc_id=?", (doc_id,))
        c.execute("UPDATE docs SET posted=0 WHERE id=?", (doc_id,))

def get_stock(item_id: int, warehouse_id: int) -> float:
    row = fetch_one(
        "SELECT SUM(qty) as s FROM stock WHERE item_id=? AND warehouse_id=?",
        (item_id, warehouse_id)
    )
    return row['s'] or 0.0

# ---------- GUI ----------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Anime1C – учёт фигурок")
        self.geometry("1100x650")
        self.make_menu()
        self.make_main_paned()

    def make_menu(self):
        m = tk.Menu(self)
        self.config(menu=m)

        refs = tk.Menu(m, tearoff=0)
        refs.add_command(label="Товары", command=lambda: self.open_reference("items"))
        refs.add_command(label="Контрагенты", command=lambda: self.open_reference("contragents"))
        refs.add_command(label="Склады", command=lambda: self.open_reference("warehouses"))
        m.add_cascade(label="Справочники", menu=refs)

        docs = tk.Menu(m, tearoff=0)
        docs.add_command(label="Приход", command=lambda: self.open_doc("приход"))
        docs.add_command(label="Расход", command=lambda: self.open_doc("расход"))
        m.add_cascade(label="Документы", menu=docs)

        rep = tk.Menu(m, tearoff=0)
        rep.add_command(label="Остатки", command=self.report_stock)
        m.add_cascade(label="Отчёты", menu=rep)

    def make_main_paned(self):
        pan = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pan.pack(fill=tk.BOTH, expand=1)

        self.nav = ttk.Treeview(pan, height=20)
        pan.add(self.nav)
        self.nav.bind('<<TreeviewSelect>>', self.on_nav_select)

        self.content_frame = ttk.Frame(pan)
        pan.add(self.content_frame)

        # Заполняем навигатор
        for g, items in (("Справочники", ["items","contragents","warehouses"]),
                         ("Документы", ["приход","расход"])):
            gid = self.nav.insert('', 'end', text=g)
            for it in items:
                self.nav.insert(gid, 'end', text=it, tags=(it,))

    def on_nav_select(self, _):
        sel = self.nav.item(self.nav.selection()[0])['text']
        if sel == "items":
            self.show_items()
        elif sel == "contragents":
            self.show_contragents()
        elif sel == "warehouses":
            self.show_warehouses()
        elif sel in ("приход","расход"):
            self.show_docs_list(sel)

    # ---------- СПРАВОЧНИКИ ----------
    def show_items(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Справочник товаров").pack(pady=4)
        cols = ("id","code","name","category","sell_price")
        self.tv = ttk.Treeview(self.content_frame, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
            self.tv.column(c, width=120)
        self.tv.pack(fill=tk.BOTH, expand=1)

        btn = ttk.Frame(self.content_frame)
        btn.pack(fill=tk.X)
        ttk.Button(btn, text="Добавить", command=self.add_item).pack(side=tk.LEFT)
        ttk.Button(btn, text="Удалить", command=self.del_item).pack(side=tk.LEFT)

        for r in fetch_all("SELECT * FROM items ORDER BY code"):
            self.tv.insert('', 'end', values=tuple(r[c] for c in cols))

    def add_item(self):
        d = ItemDialog(self)
        if d.res:
            execute("INSERT INTO items(code,name,category,buy_price,sell_price) VALUES (?,?,?,?,?)",
                    (d.res['code'], d.res['name'], d.res['category'],
                     d.res['buy_price'], d.res['sell_price']))
            self.show_items()

    def del_item(self):
        sel = self.tv.selection()
        if not sel:
            return
        iid = self.tv.item(sel[0])['values'][0]
        try:
            execute("DELETE FROM items WHERE id=?", (iid,))
        except sqlite3.IntegrityError:
            messagebox.showerror("Ошибка", "Есть ссылки в документах")
        self.show_items()

    def show_contragents(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Контрагенты").pack(pady=4)
        cols = ("id","name","type")
        self.tv = ttk.Treeview(self.content_frame, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.pack(fill=tk.BOTH, expand=1)
        ttk.Button(self.content_frame, text="Добавить",
                   command=self.add_contr).pack()
        for r in fetch_all("SELECT * FROM contragents ORDER BY name"):
            self.tv.insert('', 'end', values=tuple(r[c] for c in cols))

    def add_contr(self):
        name = simpledialog.askstring("Контрагент", "Название")
        if not name:
            return
        tp = 'supplier' if messagebox.askyesno("Тип", "Поставщик?") else 'customer'
        execute("INSERT INTO contragents(name,type) VALUES (?,?)", (name, tp))
        self.show_contragents()

    def show_warehouses(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Склады").pack(pady=4)
        cols = ("id","name")
        self.tv = ttk.Treeview(self.content_frame, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.pack(fill=tk.BOTH, expand=1)
        ttk.Button(self.content_frame, text="Добавить",
                   command=self.add_wh).pack()
        for r in fetch_all("SELECT * FROM warehouses ORDER BY name"):
            self.tv.insert('', 'end', values=tuple(r[c] for c in cols))

    def add_wh(self):
        name = simpledialog.askstring("Склад", "Название")
        if name:
            execute("INSERT INTO warehouses(name) VALUES (?)", (name,))
            self.show_warehouses()

    # ---------- ДОКУМЕНТЫ ----------
    def show_docs_list(self, doc_type):
        self.clear_content()
        ttk.Label(self.content_frame, text=f"Документы «{doc_type}»").pack(pady=4)
        cols = ("id","date","contragent","warehouse","posted")
        self.tv = ttk.Treeview(self.content_frame, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.pack(fill=tk.BOTH, expand=1)
        ttk.Button(self.content_frame, text="Создать",
                   command=lambda: self.open_doc(doc_type)).pack()
        self.tv.bind('<Double-1>', lambda e: self.edit_doc())

        sql = """SELECT d.id, d.date,
                        COALESCE(c.name,'-') as contragent,
                        w.name as warehouse,
                        d.posted
                 FROM docs d
                 JOIN warehouses w ON w.id=d.warehouse_id
                 LEFT JOIN contragents c ON c.id=d.contragent_id
                 WHERE d.doc_type=?
                 ORDER BY d.date DESC"""
        for r in fetch_all(sql, (doc_type,)):
            self.tv.insert('', 'end', values=tuple(r[c] for c in cols))

    def open_doc(self, doc_type):
        DocDialog(self, doc_type)

    def edit_doc(self):
        sel = self.tv.selection()
        if not sel:
            return
        doc_id = self.tv.item(sel[0])['values'][0]
        DocDialog(self, None, doc_id)

    # ---------- ОТЧЁТ ----------
    def report_stock(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Остатки по складу").pack(pady=4)
        cols = ("item","warehouse","qty")
        self.tv = ttk.Treeview(self.content_frame, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.pack(fill=tk.BOTH, expand=1)

        sql = """SELECT i.name as item, w.name as warehouse,
                        SUM(s.qty) as qty
                 FROM stock s
                 JOIN items i ON i.id=s.item_id
                 JOIN warehouses w ON w.id=s.warehouse_id
                 GROUP BY i.id, w.id
                 HAVING qty<>0
                 ORDER BY w.name, i.name"""
        for r in fetch_all(sql):
            self.tv.insert('', 'end', values=(r['item'], r['warehouse'], f"{r['qty']:.0f}"))

    # ---------- УТИЛИТЫ ----------
    def clear_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

    def open_reference(self, table):
        if table == "items":
            self.show_items()
        elif table == "contragents":
            self.show_contragents()
        elif table == "warehouses":
            self.show_warehouses()

# ---------- ДИАЛОГ ТОВАРА ----------
class ItemDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.res = None
        self.title("Товар")
        self.geometry("400x300")
        ttk.Label(self, text="Код").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
        self.e_code = ttk.Entry(self)
        self.e_code.grid(row=0, column=1, sticky=tk.EW, padx=6)
        ttk.Label(self, text="Название").grid(row=1, column=0, sticky=tk.W, padx=6, pady=4)
        self.e_name = ttk.Entry(self)
        self.e_name.grid(row=1, column=1, sticky=tk.EW, padx=6)
        ttk.Label(self, text="Категория").grid(row=2, column=0, sticky=tk.W, padx=6, pady=4)
        self.e_cat = ttk.Entry(self)
        self.e_cat.grid(row=2, column=1, sticky=tk.EW, padx=6)
        ttk.Label(self, text="Закупка").grid(row=3, column=0, sticky=tk.W, padx=6, pady=4)
        self.e_buy = ttk.Entry(self)
        self.e_buy.grid(row=3, column=1, sticky=tk.EW, padx=6)
        ttk.Label(self, text="Продажа").grid(row=4, column=0, sticky=tk.W, padx=6, pady=4)
        self.e_sell = ttk.Entry(self)
        self.e_sell.grid(row=4, column=1, sticky=tk.EW, padx=6)

        ttk.Button(self, text="Сохранить", command=self.on_save).grid(row=5, column=1, pady=10)
        self.columnconfigure(1, weight=1)

    def on_save(self):
        self.res = {
            'code': self.e_code.get(),
            'name': self.e_name.get(),
            'category': self.e_cat.get(),
            'buy_price': float(self.e_buy.get() or 0),
            'sell_price': float(self.e_sell.get() or 0)
        }
        if not self.res['code'] or not self.res['name']:
            messagebox.showerror("Ошибка", "Код и название обязательны")
            return
        self.destroy()

# ---------- ДИАЛОГ ДОКУМЕНТА ----------
class DocDialog(tk.Toplevel):
    def __init__(self, master, doc_type, doc_id=None):
        super().__init__(master)
        self.master = master
        self.doc_type = doc_type
        self.doc_id = doc_id
        self.title("Документ")
        self.geometry("700x500")
        self.build_head()
        self.build_table()
        if doc_id:
            self.load_doc()
        else:
            self.date.set_date(dt.date.today())
            self.posted.set(0)

        ttk.Button(self, text="Сохранить", command=self.save).pack(side=tk.LEFT, padx=4)
        ttk.Button(self, text="Провести", command=self.post).pack(side=tk.LEFT, padx=4)
        ttk.Button(self, text="Отменить проводку", command=self.unpost).pack(side=tk.LEFT, padx=4)

    def build_head(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=6, pady=6)
        ttk.Label(top, text="Дата").grid(row=0, column=0, sticky=tk.W)
        self.date = DateEntry(top, width=12, bg='white')
        self.date.grid(row=0, column=1, sticky=tk.W)
        ttk.Label(top, text="Склад").grid(row=0, column=2, sticky=tk.W, padx=(10,0))
        self.wh_cb = ttk.Combobox(top, state='readonly', width=20)
        self.wh_cb.grid(row=0, column=3, sticky=tk.W)
        whs = fetch_all("SELECT id,name FROM warehouses ORDER BY name")
        self.wh_map = {r['name']: r['id'] for r in whs}
        self.wh_cb['values'] = list(self.wh_map.keys())
        if whs:
            self.wh_cb.current(0)

        ttk.Label(top, text="Контрагент").grid(row=1, column=0, sticky=tk.W)
        self.contr_cb = ttk.Combobox(top, state='readonly', width=30)
        self.contr_cb.grid(row=1, column=1, columnspan=3, sticky=tk.EW)
        contrs = fetch_all("SELECT id,name FROM contragents ORDER BY name")
        self.contr_map = {r['name']: r['id'] for r in contrs}
        self.contr_cb['values'] = list(self.contr_map.keys())

        ttk.Label(top, text="Комментарий").grid(row=2, column=0, sticky=tk.W)
        self.comment = ttk.Entry(top)
        self.comment.grid(row=2, column=1, columnspan=3, sticky=tk.EW)
        top.columnconfigure(3, weight=1)

        self.posted = tk.IntVar()
        ttk.Checkbutton(top, text="Проведён", variable=self.posted, state='disabled').grid(row=3, column=0, columnspan=2, sticky=tk.W)

    def build_table(self):
        mid = ttk.Frame(self)
        mid.pack(fill=tk.BOTH, expand=1, padx=6, pady=6)
        cols = ("item","qty","price","sum")
        self.tv = ttk.Treeview(mid, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.pack(fill=tk.BOTH, expand=1)
        ttk.Button(mid, text="Добавить строку", command=self.add_row).pack()
        self.tv.bind('<Double-1>', lambda e: self.edit_row())

    def load_doc(self):
        d = fetch_one("SELECT * FROM docs WHERE id=?", (self.doc_id,))
        self.date.set_date(dt.datetime.strptime(d['date'], '%Y-%m-%d').date())
        self.comment.insert(0, d['comment'] or '')
        self.posted.set(d['posted'])
        # склад
        wh_name = fetch_one("SELECT name FROM warehouses WHERE id=?", (d['warehouse_id'],))['name']
        self.wh_cb.set(wh_name)
        # контрагент
        if d['contragent_id']:
            contr_name = fetch_one("SELECT name FROM contragents WHERE id=?", (d['contragent_id'],))['name']
            self.contr_cb.set(contr_name)
        # таблица
        rows = fetch_all("SELECT dt.*, i.name as item FROM docs_table dt JOIN items i ON i.id=dt.item_id WHERE dt.doc_id=?", (self.doc_id,))
        for r in rows:
            sm = r['qty'] * r['price']
            self.tv.insert('', 'end', values=(r['item'], r['qty'], r['price'], sm), tags=(r['id'],))

    def add_row(self):
        d = DocRowDialog(self)
        if d.res:
            sm = d.res['qty'] * d.res['price']
            self.tv.insert('', 'end', values=(d.res['item_name'], d.res['qty'], d.res['price'], sm),
                           tags=(d.res['item_id'],))

    def edit_row(self):
        sel = self.tv.selection()
        if not sel:
            return
        # упрощённо – удалим и добавим
        self.tv.delete(sel[0])
        self.add_row()

    def save(self):
        # собираем head
        wh_id = self.wh_map[self.wh_cb.get()]
        contr_id = self.contr_map.get(self.contr_cb.get())
        date_str = self.date.get_date().strftime('%Y-%m-%d')
        if not self.doc_id:
            self.doc_id = execute(
                "INSERT INTO docs(doc_type,date,warehouse_id,contragent_id,comment,posted) VALUES (?,?,?,?,?,0)",
                (self.doc_type, date_str, wh_id, contr_id, self.comment.get())
            )
        else:
            execute(
                "UPDATE docs SET date=?, warehouse_id=?, contragent_id=?, comment=? WHERE id=?",
                (date_str, wh_id, contr_id, self.comment.get(), self.doc_id)
            )
        # таблица – удалим старые
        execute("DELETE FROM docs_table WHERE doc_id=?", (self.doc_id,))
        # новые
        for it in self.tv.get_children():
            vals = self.tv.item(it)['values']
            item_name, qty, price, _ = vals
            item_id = self.tv.item(it)['tags'][0]
            execute("INSERT INTO docs_table(doc_id,item_id,qty,price) VALUES (?,?,?,?)",
                    (self.doc_id, item_id, qty, price))
        messagebox.showinfo("Сохранено", "Документ сохранён")

    def post(self):
        self.save()
        try:
            post_doc(self.doc_id)
            messagebox.showinfo("Проведён", "Документ проведён")
            self.destroy()
            self.master.show_docs_list(self.doc_type)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def unpost(self):
        try:
            unpost_doc(self.doc_id)
            messagebox.showinfo("Отмена", "Проводка отменена")
            self.destroy()
            self.master.show_docs_list(self.doc_type)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

# ---------- ДИАЛОГ СТРОКИ ДОКУМЕНТА ----------
class DocRowDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.res = None
        self.title("Строка документа")
        self.geometry("400x250")
        ttk.Label(self, text="Товар").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
        self.cb = ttk.Combobox(self, state='readonly', width=30)
        self.cb.grid(row=0, column=1, padx=6)
        items = fetch_all("SELECT id,name FROM items ORDER BY name")
        self.item_map = {r['name']: r['id'] for r in items}
        self.cb['values'] = list(self.item_map.keys())
        if items:
            self.cb.current(0)

        ttk.Label(self, text="Кол-во").grid(row=1, column=0, sticky=tk.W, padx=6, pady=4)
        self.e_qty = ttk.Entry(self)
        self.e_qty.grid(row=1, column=1, padx=6)
        self.e_qty.insert(0, "1")

        ttk.Label(self, text="Цена").grid(row=2, column=0, sticky=tk.W, padx=6, pady=4)
        self.e_price = ttk.Entry(self)
        self.e_price.grid(row=2, column=1, padx=6)
        self.e_price.insert(0, "0")

        ttk.Button(self, text="OK", command=self.on_ok).grid(row=3, column=1, pady=10)

    def on_ok(self):
        name = self.cb.get()
        self.res = {
            'item_id': self.item_map[name],
            'item_name': name,
            'qty': float(self.e_qty.get()),
            'price': float(self.e_price.get())
        }
        self.destroy()

# ---------- ЗАПУСК ----------
if __name__ == '__main__':
    init_db()
    App().mainloop()