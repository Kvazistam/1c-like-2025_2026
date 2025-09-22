import tkinter as tk
from tkinter import Radiobutton, ttk, messagebox, simpledialog
from tkinter import filedialog
from db_scripts import doc_update_head, user_check
from tkcalendar import DateEntry
from datetime import date, datetime
import os
from app_style import apply_1c_style

from db_scripts import (
    # модели
    Item, Contragent, Warehouse, Doc, DocsTable, Stock,
    # CRUD
    item_list, contragent_list, contragent_add,
    warehouse_list, warehouse_add,
    doc_list, doc_save_head, doc_save_table, doc_get, doc_post, doc_unpost,
)
class ItemDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.res = None
        self.title("Товар")
        self.geometry("400x350")

        labels = ("Название", "Категория", "Цена закупки")
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
            'name': self.entries['название'].get(),
            'category': self.entries['категория'].get() or None,
            'buy_price': float(self.entries["цена_закупки"].get() or 0),
            'image': self.image_bytes
        }
        if  not self.res['name']:
            messagebox.showerror("Ошибка", "Код и название обязательны")
            return
        self.destroy()


# ---------- диалог документа ----------
class DocDialog(tk.Toplevel):
    def __init__(self, master, doc_type, doc_id=None, on_close=None):
        super().__init__(master)
        self.doc_type = doc_type
        self.doc_id = doc_id
        self.on_close = on_close
        self.title('Документ')
        self.geometry('700x500')
        self._build_head()
        self._build_table()
        if doc_id:
            self._load_doc()
        else:
            self.widgets['date'].set_date(date.today())
            self.posted.set(0)

        btn_bar = ttk.Frame(self)
        btn_bar.pack(fill=tk.X, pady=4)
        ttk.Button(btn_bar, text='Сохранить', command=self._save).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text='Провести', command=self._post).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text='Отменить проводку', command=self._unpost).pack(side=tk.LEFT, padx=4)

    # ---------- head ----------
    def _build_head(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=6, pady=6)
        top.columnconfigure(1, weight=1)
        top.columnconfigure(3, weight=1)
        labels = (('Дата', 0), ('Склад', 1), ('Контрагент', 2), ('Комментарий', 3))
        self.widgets = {}
        for text, row in labels:

            ttk.Label(top, text=text).grid(row=row, column=0,
                                        sticky=tk.W, padx=(0, 3), pady=4)
            if text == 'Дата':
                w = DateEntry(top, width=12, justify = "right")
                w.grid(row=row, column=1, sticky='we')  
                self.widgets['date'] = w

            elif text == 'Склад':
                w = ttk.Combobox(top, state='readonly', width=20)
                w.grid(row=row, column=1, sticky='we')   # <-- we
                self.widgets['warehouse'] = w
                whs = warehouse_list()
                self.wh_map = {r['name']: r['id'] for r in whs}
                w['values'] = list(self.wh_map.keys())
                if whs:
                    w.current(0)

            elif text == 'Контрагент':
                w = ttk.Combobox(top, state='readonly', width=30)
                w.grid(row=row, column=1, sticky='we', columnspan=3)
                self.widgets['contragent'] = w
                cons = contragent_list()
                self.contr_map = {r['name']: r['id'] for r in cons}
                w['values'] = list(self.contr_map.keys())

            elif text == 'Комментарий':  # комментарий
                w = ttk.Entry(top)
                w.grid(row=row, column=1, sticky='we', columnspan=3)
                self.widgets['comment'] = w

        self.posted = tk.IntVar()
        ttk.Checkbutton(top, text='Проведён', variable=self.posted, state='disabled').grid(
            row=row+1, column=0, columnspan=2, sticky=tk.W)

    # ---------- table ----------
    def _build_table(self):
        mid = ttk.Frame(self)
        mid.pack(fill=tk.BOTH, expand=1, padx=6, pady=6)
        cols = ('Товар', 'Количество', 'Цена закупки', 'Сумма')
        self.tv = ttk.Treeview(mid, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.pack(fill=tk.BOTH, expand=1)
        ttk.Button(mid, text='Добавить строку', command=self._add_row).pack()
        self.tv.bind('<Double-1>', lambda e: self._edit_row())

    # ---------- загрузка документа ----------
    def _load_doc(self):
        d = doc_get(self.doc_id)
        if not d:
            return
        self.widgets['date'].set_date(d.date)
        self.widgets['comment'].insert(0, d.comment or '')
        self.posted.set(d.posted)
        wh_name = next(n for n, i in self.wh_map.items() if i == d.warehouse_id)
        self.widgets['warehouse'].set(wh_name)
        if d.contragent_id:
            contr_name = next(n for n, i in self.contr_map.items() if i == d.contragent_id)
            self.widgets['contragent'].set(contr_name)
        for line in d.lines:
            sm = line.qty * line.price
            self.tv.insert('', 'end', values=(line.item.name, line.qty, line.price, sm),
                           tags=(line.item_id,))

    # ---------- работа со строками ----------
    def _add_row(self):
        d = DocRowDialog(self)
        self.wait_window(d)
        if d.res:
            rows = [{'item_id': d.res['item_id'], 'qty': d.res['qty'], 'price': d.res['price']}]
            if self.doc_id:
                doc_save_table(self.doc_id, rows)
            sm = d.res['qty'] * d.res['price']
            self.tv.insert('', 'end', values=(d.res['item_name'], d.res['qty'], d.res['price'], sm),
                           tags=(d.res['item_id'],))

    def _edit_row(self):
        sel = self.tv.selection()
        if not sel:
            return
        self.tv.delete(sel[0])
        self._add_row()

    
    def _save(self):
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
        # messagebox.showinfo("Сохранено", "Документ сохранён")
        if self.on_close:
                self.on_close()

    # ---------- проводки ----------
    def _post(self):
        self._save()
        try:
            doc_post(self.doc_id)
            messagebox.showinfo('Проведён', 'Документ проведён')
            self.destroy()
            if self.on_close:
                self.on_close()
        except Exception as e:
            messagebox.showerror('Ошибка', str(e))

    def _unpost(self):
        try:
            doc_unpost(self.doc_id)
            messagebox.showinfo('Отмена', 'Проводка отменена')
            self.destroy()
            if self.on_close:
                self.on_close()
        except Exception as e:
            messagebox.showerror('Ошибка', str(e))


# ---------- диалог строки документа ----------
class DocRowDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.res = None
        self.title('Строка документа')
        self.geometry('400x250')

        ttk.Label(self, text='Товар').grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
        self.cb = ttk.Combobox(self, state='readonly', width=30)
        self.cb.grid(row=0, column=1, padx=6)
        items = item_list()
        self.item_map = {r['name']: r['id'] for r in items}
        self.cb['values'] = list(self.item_map.keys())
        if items:
            self.cb.current(0)

        ttk.Label(self, text='Кол-во').grid(row=1, column=0, sticky=tk.W, padx=6, pady=4)
        self.e_qty = ttk.Entry(self)
        self.e_qty.grid(row=1, column=1, padx=6)
        self.e_qty.insert(0, '1')

        ttk.Label(self, text='Цена').grid(row=2, column=0, sticky=tk.W, padx=6, pady=4)
        self.e_price = ttk.Entry(self)
        self.e_price.grid(row=2, column=1, padx=6)
        self.e_price.insert(0, '0')

        ttk.Button(self, text='OK', command=self._ok).grid(row=3, column=1, pady=10)

    def _ok(self):
        name = self.cb.get()
        self.res = {
            'item_id': self.item_map[name],
            'item_name': name,
            'qty': float(self.e_qty.get()),
            'price': float(self.e_price.get())
        }
        self.destroy()