#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anime1c.py – GUI-оболочка Anime1C (ORM-вариант)
только вызовы CRUD-функций из db_crud.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter import filedialog
from db_scripts import doc_update_head
from tkcalendar import DateEntry
from datetime import date, datetime
import os
from app_style import apply_1c_style

from db_scripts import (
    # модели
    Item, Contragent, Warehouse, Doc, DocsTable, Stock,
    # CRUD
    item_list, item_add, item_delete,
    contragent_list, contragent_add,
    warehouse_list, warehouse_add,
    doc_list, doc_save_head, doc_save_table, doc_get, doc_post, doc_unpost,
    stock_report,
)


# ---------- GUI ----------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Anime1C – учёт фигурок (ORM)")
        self.geometry("1100x650")
        self.make_menu()
        self.make_main_paned()
        apply_1c_style(self)

    # ---------- меню ----------
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

    # ---------- панели ----------
    def make_main_paned(self):
        pan = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pan.pack(fill=tk.BOTH, expand=1)

        self.nav = ttk.Treeview(pan, height=20)
        pan.add(self.nav)
        self.nav.bind('<<TreeviewSelect>>', self.on_nav_select)

        self.content_frame = ttk.Frame(pan)
        pan.add(self.content_frame)

        # заполняем навигатор
        for g, items in (("Справочники", ["items", "contragents", "warehouses"]),
                         ("Документы", ["приход", "расход"])):
            gid = self.nav.insert('', 'end', text=g)
            for it in items:
                self.nav.insert(gid, 'end', text=it, tags=(it,))

    # ---------- навигация ----------
    def on_nav_select(self, _):
        sel = self.nav.item(self.nav.selection()[0])['text']
        if sel == "items":
            self.show_items()
        elif sel == "contragents":
            self.show_contragents()
        elif sel == "warehouses":
            self.show_warehouses()
        elif sel in ("приход", "расход"):
            self.show_docs_list(sel)

    # ---------- справочник товары ----------
    def show_items(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Справочник товаров").pack(pady=4)
        cols = ("id", "code", "name", "category", "sell_price", )
        self.tv = ttk.Treeview(self.content_frame, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
            self.tv.column(c, width=120)
        self.tv.pack(fill=tk.BOTH, expand=1)
        
        # self.tv.bind('<Double-1>', lambda e: self.show_item_card())
        
        btn = ttk.Frame(self.content_frame)
        btn.pack(fill=tk.X)
        ttk.Button(btn, text="Добавить", command=self.add_item).pack(side=tk.LEFT)
        ttk.Button(btn, text="Удалить", command=self.del_item).pack(side=tk.LEFT)

        for row in item_list():
            self.tv.insert('', 'end', values=(row['id'], row['code'], row['name'],
                                              row['category'], row['sell_price']))

    def add_item(self):
        d = ItemDialog(self)
        self.wait_window(d)
        if d.res:
            try:
                item_add(**d.res)
                self.show_items()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def del_item(self):
        sel = self.tv.selection()
        if not sel:
            return
        iid = int(self.tv.item(sel[0])['values'][0])
        try:
            item_delete(iid)
            self.show_items()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    # ---------- контрагенты ----------
    def show_contragents(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Контрагенты").pack(pady=4)
        cols = ("id", "name", "type")
        self.tv = ttk.Treeview(self.content_frame, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.pack(fill=tk.BOTH, expand=1)
        ttk.Button(self.content_frame, text="Добавить", command=self.add_contr).pack()
        for row in contragent_list():
            self.tv.insert('', 'end', values=(row['id'], row['name'], row['type']))

    def add_contr(self):
        name = simpledialog.askstring("Контрагент", "Название")
        if not name:
            return
        tp = 'supplier' if messagebox.askyesno("Тип", "Поставщик?") else 'customer'
        contragent_add(name, tp)
        self.show_contragents()

    # ---------- склады ----------
    def show_warehouses(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Склады").pack(pady=4)
        cols = ("id", "name")
        self.tv = ttk.Treeview(self.content_frame, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.pack(fill=tk.BOTH, expand=1)
        ttk.Button(self.content_frame, text="Добавить", command=self.add_wh).pack()
        for row in warehouse_list():
            self.tv.insert('', 'end', values=(row['id'], row['name']))

    def add_wh(self):
        name = simpledialog.askstring("Склад", "Название")
        if name:
            warehouse_add(name)
            self.show_warehouses()

    # ---------- документы ----------
    def show_docs_list(self, doc_type):
        self.clear_content()
        ttk.Label(self.content_frame, text=f"Документы «{doc_type}»").pack(pady=4)
        cols = ("id", "date", "contragent", "warehouse", "posted")
        self.tv = ttk.Treeview(self.content_frame, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.pack(fill=tk.BOTH, expand=1)
        ttk.Button(self.content_frame, text="Создать",
                   command=lambda: self.open_doc(doc_type)).pack()
        self.tv.bind('<Double-1>', lambda e: self.edit_doc())

        for row in doc_list(doc_type):
            self.tv.insert('', 'end', values=(
                row['id'], row['date'], row['contragent'] or '-',
                row['warehouse'], "Да" if row['posted'] else "Нет"))

    def open_doc(self, doc_type):
        DocDialog(self, doc_type)

    def edit_doc(self):
        sel = self.tv.selection()
        if not sel:
            return
        doc_id = int(self.tv.item(sel[0])['values'][0])
        DocDialog(self, None, doc_id)

    # ---------- отчёт остатки ----------
    def report_stock(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Остатки по складам").pack(pady=4)
        cols = ("item", "warehouse", "qty")
        self.tv = ttk.Treeview(self.content_frame, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.pack(fill=tk.BOTH, expand=1)

        for row in stock_report():
            self.tv.insert('', 'end', values=(
                row['item'], row['warehouse'], f"{row['qty']:.0f}"))

    # ---------- утилиты ----------
    def clear_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

    def open_reference(self, table):
        {"items": self.show_items,
         "contragents": self.show_contragents,
         "warehouses": self.show_warehouses}[table]()


# ---------- диалог товара ----------
class ItemDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.res = None
        self.title("Товар")
        self.geometry("400x350")

        labels = ("Код", "Название", "Категория", "Закупка", "Продажа")
        self.entries = {}
        for i, lbl in enumerate(labels):
            ttk.Label(self, text=lbl).grid(row=i, column=0, sticky=tk.W, padx=6, pady=4)
            e = ttk.Entry(self)
            e.grid(row=i, column=1, sticky=tk.EW, padx=6)
            key = lbl.lower().replace(' ', '_')
            self.entries[key] = e

        # картинка
        ttk.Label(self, text="Картинка").grid(row=len(labels), column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Button(self, text="Выбрать...", command=self.pick_image).grid(row=len(labels), column=1, sticky=tk.W, padx=6)

        ttk.Button(self, text="Сохранить", command=self.on_save).grid(row=len(labels)+1, column=1, pady=10)
        self.columnconfigure(1, weight=1)

        self.image_bytes = None

    def pick_image(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png")])
        if path:
            with open(path, 'rb') as f:
                self.image_bytes = f.read()

    def on_save(self):
        self.res = {
            'code': self.entries['код'].get(),
            'name': self.entries['название'].get(),
            'category': self.entries['категория'].get() or None,
            'buy_price': float(self.entries['закупка'].get() or 0),
            'sell_price': float(self.entries['продажа'].get() or 0),
            'image': self.image_bytes
        }
        if not self.res['code'] or not self.res['name']:
            messagebox.showerror("Ошибка", "Код и название обязательны")
            return
        self.destroy()


# ---------- диалог документа ----------
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
            self.widgets['date'].set_date(date.today())
            self.posted.set(0)

        btn_bar = ttk.Frame(self)
        btn_bar.pack(fill=tk.X, pady=4)
        ttk.Button(btn_bar, text="Сохранить", command=self.save).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text="Провести", command=self.post).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text="Отменить проводку", command=self.unpost).pack(side=tk.LEFT, padx=4)

    # ---------- head ----------
    def build_head(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=6, pady=6)

        labels = (("Дата", 0), ("Склад", 2), ("Контрагент", 0), ("Комментарий", 2))
        self.widgets = {}
        for text, col in labels:
            ttk.Label(top, text=text).grid(row=col//2, column=col % 2 * 2, sticky=tk.W, padx=(10 if col else 0), pady=4)
            if text == "Дата":
                w = DateEntry(top, width=12)
                w.grid(row=col//2, column=col % 2 * 2 + 1, sticky=tk.W)
                self.widgets['date'] = w
            elif text == "Склад":
                w = ttk.Combobox(top, state='readonly', width=20)
                w.grid(row=col//2, column=col % 2 * 2 + 1, sticky=tk.W)
                self.widgets['warehouse'] = w
                whs = warehouse_list()
                self.wh_map = {r['name']: r['id'] for r in whs}
                w['values'] = list(self.wh_map.keys())
                if whs:
                    w.current(0)
            elif text == "Контрагент":
                w = ttk.Combobox(top, state='readonly', width=30)
                w.grid(row=col//2, column=col % 2 * 2 + 1, sticky=tk.EW, columnspan=3)
                self.widgets['contragent'] = w
                cons = contragent_list()
                self.contr_map = {r['name']: r['id'] for r in cons}
                w['values'] = list(self.contr_map.keys())
            else:  # комментарий
                w = ttk.Entry(top)
                w.grid(row=col//2, column=col % 2 * 2 + 1, sticky=tk.EW, columnspan=3)
                self.widgets['comment'] = w
        top.columnconfigure(3, weight=1)

        self.posted = tk.IntVar()
        ttk.Checkbutton(top, text="Проведён", variable=self.posted, state='disabled').grid(
            row=3, column=0, columnspan=2, sticky=tk.W)

    # ---------- table ----------
    def build_table(self):
        mid = ttk.Frame(self)
        mid.pack(fill=tk.BOTH, expand=1, padx=6, pady=6)
        cols = ("item", "qty", "price", "sum")
        self.tv = ttk.Treeview(mid, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.pack(fill=tk.BOTH, expand=1)
        ttk.Button(mid, text="Добавить строку", command=self.add_row).pack()
        self.tv.bind('<Double-1>', lambda e: self.edit_row())

    # ---------- загрузка документа ----------
    def load_doc(self):
        d = doc_get(self.doc_id)
        if not d:
            return
        self.widgets["date"].set_date(d.date)
        self.widgets['comment'].insert(0, d.comment or '')
        self.posted.set(d.posted)
        # склад
        wh_name = next(n for n, i in self.wh_map.items() if i == d.warehouse_id)
        self.widgets['warehouse'].set(wh_name)
        # контрагент
        if d.contragent_id:
            contr_name = next(n for n, i in self.contr_map.items() if i == d.contragent_id)
            self.widgets['contragent'].set(contr_name)
        # таблица
        print(d.lines)
        for line in d.lines:
            sm = line.qty * line.price
            self.tv.insert('', 'end', values=(line.item.name, line.qty, line.price, sm),
                           tags=(line.item_id,))

    # ---------- работа со строками ----------
    def add_row(self):
        d = DocRowDialog(self)
        self.wait_window(d)
        print("зашел в add_row", d.res)
        if d.res:
            print(d.res["item_id"])
            # сразу сохраняем строку в БД
            rows = [{'item_id': d.res['item_id'],
                     'qty': d.res['qty'],
                     'price': d.res['price']}]
            if self.doc_id:   # документ уже создан
                doc_save_table(self.doc_id, rows)
            # показываем в Treeview
            sm = d.res['qty'] * d.res['price']
            self.tv.insert('', 'end', values=(d.res['item_name'],
                                              d.res['qty'],
                                              d.res['price'],
                                              sm),
                           tags=(d.res['item_id'],))

    def edit_row(self):
        sel = self.tv.selection()
        if not sel:
            return
        # удаляем старую строку из Treeview и из БД
        item_id = int(self.tv.item(sel[0])['tags'][0])
        self.tv.delete(sel[0])
        # добавляем новую
        self.add_row()

    # ---------- сохранение ----------
    def save(self):
        # head
        wh_id = self.wh_map[self.widgets['warehouse'].get()]
        contr_name = self.widgets['contragent'].get()
        contr_id = self.contr_map.get(contr_name)
        date_ = self.widgets['date'].get_date()
        comment = self.widgets['comment'].get()

        if not self.doc_id:
            self.doc_id = doc_save_head(self.doc_type, date_, wh_id, contr_id, comment)
        else:
            doc_update_head(self.doc_id, date_, wh_id, contr_id, comment)

        # table
        rows = []
        for it in self.tv.get_children():
            vals = self.tv.item(it)['values']
            item_id = int(self.tv.item(it)['tags'][0])
            qty, price = float(vals[1]), float(vals[2])
            rows.append({'item_id': item_id, 'qty': qty, 'price': price})
        doc_save_table(self.doc_id, rows)
        messagebox.showinfo("Сохранено", "Документ сохранён")

    # ---------- проводки ----------
    def post(self):
        self.save()
        try:
            doc_post(self.doc_id)
            messagebox.showinfo("Проведён", "Документ проведён")
            self.destroy()
            self.master.show_docs_list(self.doc_type)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def unpost(self):
        try:
            doc_unpost(self.doc_id)
            messagebox.showinfo("Отмена", "Проводка отменена")
            self.destroy()
            self.master.show_docs_list(self.doc_type)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


# ---------- диалог строки документа ----------
class DocRowDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.res = None
        self.title("Строка документа")
        self.geometry("400x250")

        ttk.Label(self, text="Товар").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
        self.cb = ttk.Combobox(self, state='readonly', width=30)
        self.cb.grid(row=0, column=1, padx=6)
        items = item_list()
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

from PIL import Image, ImageTk
import io

def pick_image(self):
    path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png")])
    if path:
        with open(path, 'rb') as f:
            self.image_bytes = f.read()

def show_image(self, image_bytes):
    window = tk.Toplevel(self)
    window.title("Изображение")
    im = Image.open(io.BytesIO(image_bytes))
    im.thumbnail((400, 400))
    ph = ImageTk.PhotoImage(im)
    lbl = ttk.Label(window, image=ph)
    lbl.image = ph
    lbl.pack()

# ---------- запуск ----------
if __name__ == '__main__':
    App().mainloop()