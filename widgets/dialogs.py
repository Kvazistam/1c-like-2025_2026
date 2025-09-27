import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
from db_scripts import sale_price_get_id, doc_update_head, sale_price_set, sale_price_update, sale_price_get_date
from tkcalendar import DateEntry
from datetime import date
from PIL import Image, ImageTk
import io
from db_scripts import (
    # модели
    item_list, contragent_list, warehouse_list, doc_save_head, doc_save_table, doc_get, doc_post, doc_unpost
)
from db_scripts.db_items import item_buy_price_get
from enumerates import DOC_TYPES
class ItemDialog(tk.Toplevel):
    def __init__(self, master, item_id = None, item_data: dict = None):
        super().__init__(master)
        self.res = None
        self.title("Товар")
        self.geometry("500x700")
        self.image = None
        self.image_label = None  

        labels = ("Название", "Категория", "Цена закупки")
        self.entries = {}
        for i, lbl in enumerate(labels):
            ttk.Label(self, text=lbl).grid(row=i, column=0, sticky=tk.W, padx=6, pady=4)
            e = ttk.Entry(self)
            e.grid(row=i, column=1, sticky=tk.EW, padx=6)
            key = lbl.lower().replace(' ', '_')
            self.entries[key] = e

        # картинка
        img_row = len(labels)
        ttk.Label(self, text="Картинка").grid(row=len(labels), column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Button(self, text="Выбрать...", command=self.pick_image).grid(row=len(labels), column=1, sticky=tk.W, padx=6)
        
        # Место для отображения картинки
        self.image_label = tk.Label(self, bg="white", relief="sunken")
        self.image_label.grid(row=len(labels)+1, column=0, columnspan=2, sticky="nswe")
        self._show_placeholder()

        # Кнопка сохранения
        ttk.Button(self, text="Сохранить", command=self.on_save).grid(
            row=img_row+2, column=0, pady=10, padx = 6, sticky='w'
        )

        self.columnconfigure(1, weight=1)
        self.rowconfigure(img_row+1, weight=1)
        self.image_bytes = None
        
        
        if item_data:
            self.entries['название'].insert(0, item_data.get('name', ''))
            cat = item_data.get('category')
            if cat:
                self.entries['категория'].insert(0, cat)
            self.entries['цена_закупки'].insert(0, str(item_data.get('buy_price', 0)))
            
            if item_data.get('image'):
                self.image_bytes = item_data['image']
                self._show_image(self.image_bytes)
        self.transient(master)        # остаётся поверх master
        self.grab_set()               # перехватывает весь ввод
        self.focus_set()              # фокус на этом окне

    def _show_placeholder(self):
        """Показать заглушку 'Нет изображения'."""
        self.image_label.config(image='', text="Нет изображения", compound="center")

    def _show_image(self, image_bytes: bytes):
        """Отобразить изображение, масштабированное под размер Label."""
        try:
            original = Image.open(io.BytesIO(image_bytes))

            target_width = 500
            target_height = 500


            original.thumbnail((target_width, target_height), Image.LANCZOS)
            resized = original

            self.photo = ImageTk.PhotoImage(resized)
            self.image_label.config(image=self.photo, text="", width=target_width, height=target_height)
        except Exception as e:
            print(f"Ошибка отображения изображения: {e}")
            self._show_placeholder()


    def pick_image(self):
        from tkinter import filedialog, messagebox
        path = filedialog.askopenfilename(
            parent=self,
            title="Выберите изображение",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if path:
            try:
                with open(path, 'rb') as f:
                    self.image_bytes = f.read()
                self._show_image(self.image_bytes)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить изображение:\n{e}", parent=self)
                self.image_bytes = None
                self._show_placeholder()

    def on_save(self):
        name = self.entries['название'].get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Название обязательно", parent=self)
            return
        category = self.entries['категория'].get().strip() or None
        try:
            buy_price = float(self.entries["цена_закупки"].get() or 0)
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректная цена закупки", parent=self)
            return

        self.res = {
            'name': name,
            'category': category,
            'buy_price': buy_price,
            'image': self.image_bytes
        }
        self.destroy()

class SalePriceDialog(tk.Toplevel):
    def __init__(self, master, price_id=None, on_save=None):
        super().__init__(master)
        self.price_id = price_id
        self.on_save = on_save
        self.title("Розничная цена")
        self.geometry("450x250")
        self.resizable(False, False)

        # Поля
        ttk.Label(self, text="Товар:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=8)
        self.item_cb = ttk.Combobox(self, state="readonly", width=30)
        self.item_cb.grid(row=0, column=1, padx=10, pady=8)

        ttk.Label(self, text="Дата начала:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=8)
        self.date_entry = DateEntry(self, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.date_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=8)

        ttk.Label(self, text="Цена:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=8)
        self.price_entry = ttk.Entry(self, width=15)
        self.price_entry.grid(row=2, column=1, sticky=tk.W, padx=10, pady=8)

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="Сохранить", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=5)

        if price_id:
            self._load(price_id)
        else:
            # Заполним список товаров
            items = item_list()
            self.item_map = {r['name']: r['id'] for r in items}
            self.item_cb['values'] = list(self.item_map.keys())
            if items:
                self.item_cb.current(0)

        

    def _load(self, price_id):
        reg = sale_price_get_id(price_id)
        if reg:
            # Найдём имя товара по item_id
            item_id = reg.item_id
            item_name = reg.item.name
            item_date = reg.start_date
            item_price = reg.price
            self.item_cb.set(item_name)
            self.date_entry.set_date(item_date)
            self.price_entry.insert(0, str(item_price))

    def _save(self):
        try:
            item_name = self.item_cb.get()
            if not item_name:
                messagebox.showerror("Ошибка", "Выберите товар")
                return
            item_id = self.item_map[item_name]
            start_date = self.date_entry.get_date()
            price = float(self.price_entry.get())

            if self.price_id:
                sale_price_update(self.price_id, item_id, start_date, price)
            else:
                sale_price_set(item_id, price, start_date)

            if self.on_save:
                self.on_save()
            self.destroy()
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректная цена")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


#------Диалог Цены--------
class PriceDialog(tk.Toplevel):
    def __init__(self, master, doc_id=None, item_id = None, date = None, on_close=None):
        super().__init__(master)
        self.doc_id = doc_id
        self.item_id = item_id
        self.on_close = on_close
        self.title('Регистр')
        self.geometry('700x500')
        self._build_head()
        if item_id:
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
        labels = (('Дата', 0), ('Товар', 1), ('Цена', 2))
        self.widgets = {}
        for text, row in labels:

            ttk.Label(top, text=text).grid(row=row, column=0,
                                        sticky=tk.W, padx=(0, 3), pady=4)
            if text == 'Дата':
                w = DateEntry(top, width=12, justify = "right")
                w.grid(row=row, column=1, sticky='we')  
                self.widgets['date'] = w

            elif text == 'Товар':
                w = ttk.Combobox(top, state='readonly', width=20)
                w.grid(row=row, column=1, sticky='we')   
                self.widgets['items'] = w
                items = item_list()
                self.items_map = {r['name']: r['id'] for r in items}
                w['values'] = list(self.items_map.keys())
                if items:
                    w.current(0)

            elif text == 'Цена':
                w = ttk.Entry(top)
                w.grid(row=row, column=1, sticky='we', columnspan=3)
                self.widgets['price'] = w

        self.posted = tk.IntVar()
        ttk.Checkbutton(top, text='Проведён', variable=self.posted, state='disabled').grid(
            row=row+1, column=0, columnspan=2, sticky='w')


    # ---------- загрузка документа ----------
    def _load_reg(self):
        d = sale_price_get_id(self.doc_id)
        if not d:
            return
        self.widgets['date'].set_date(d.date_from)
        self.widgets['item'].insert(0, d.items or '')
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

# ---------- диалог документа ----------
# class DocDialog(tk.Toplevel):
#     def __init__(self, master, doc_type, doc_id=None, on_close=None):
#         super().__init__(master)
#         self.doc_type = doc_type
#         self.doc_id = doc_id
#         self.on_close = on_close
#         self.title('Документ')
#         self.geometry('700x500')
#         self._build_head()
#         self._build_table()
#         if doc_id:
#             self._load_doc()
#         else:
#             self.widgets['date'].set_date(date.today())
#             self.posted.set(0)

#         btn_bar = ttk.Frame(self)
#         btn_bar.pack(fill=tk.X, pady=4)
#         ttk.Button(btn_bar, text='Сохранить', command=self._save).pack(side=tk.LEFT, padx=4)
#         ttk.Button(btn_bar, text='Провести', command=self._post).pack(side=tk.LEFT, padx=4)
#         ttk.Button(btn_bar, text='Отменить проводку', command=self._unpost).pack(side=tk.LEFT, padx=4)

#     # ---------- head ----------
#     def _build_head(self):
#         top = ttk.Frame(self)
#         top.pack(fill=tk.X, padx=6, pady=6)
#         top.columnconfigure(1, weight=1)
#         top.columnconfigure(3, weight=1)
#         labels = (('Дата', 0), ('Склад', 1), ('Контрагент', 2), ('Комментарий', 3))
#         self.widgets = {}
#         for text, row in labels:

#             ttk.Label(top, text=text).grid(row=row, column=0,
#                                         sticky=tk.W, padx=(0, 3), pady=4)
#             if text == 'Дата':
#                 w = DateEntry(top, width=12, justify = "right")
#                 w.grid(row=row, column=1, sticky='we')  
#                 self.widgets['date'] = w

#             elif text == 'Склад':
#                 w = ttk.Combobox(top, state='readonly', width=20)
#                 w.grid(row=row, column=1, sticky='we')   # <-- we
#                 self.widgets['warehouse'] = w
#                 whs = warehouse_list()
#                 self.wh_map = {r['name']: r['id'] for r in whs}
#                 w['values'] = list(self.wh_map.keys())
#                 if whs:
#                     w.current(0)

#             elif text == 'Контрагент':
#                 w = ttk.Combobox(top, state='readonly', width=30)
#                 w.grid(row=row, column=1, sticky='we', columnspan=3)
#                 self.widgets['contragent'] = w
#                 cons = contragent_list()
#                 self.contr_map = {r['name']: r['id'] for r in cons}
#                 w['values'] = list(self.contr_map.keys())

#             elif text == 'Комментарий':  # комментарий
#                 w = ttk.Entry(top)
#                 w.grid(row=row, column=1, sticky='we', columnspan=3)
#                 self.widgets['comment'] = w

#         self.posted = tk.IntVar()
#         ttk.Checkbutton(top, text='Проведён', variable=self.posted, state='disabled').grid(
#             row=row+1, column=0, columnspan=2, sticky=tk.W)

#     # ---------- table ----------
#     def _build_table(self):
#         mid = ttk.Frame(self)
#         mid.pack(fill=tk.BOTH, expand=1, padx=6, pady=6)
#         cols = ('Товар', 'Количество', 'Цена закупки', 'Сумма')
#         self.tv = ttk.Treeview(mid, columns=cols, show='headings')
#         for c in cols:
#             self.tv.heading(c, text=c)
#         self.tv.pack(fill=tk.BOTH, expand=1)
#         ttk.Button(mid, text='Добавить строку', command=self._add_row).pack()
#         self.tv.bind('<Double-1>', lambda e: self._edit_row())

#     # ---------- загрузка документа ----------
#     def _load_doc(self):
#         d = doc_get(self.doc_id)
#         if not d:
#             return
#         self.widgets['date'].set_date(d.date)
#         self.widgets['comment'].insert(0, d.comment or '')
#         self.posted.set(d.posted)
#         wh_name = next(n for n, i in self.wh_map.items() if i == d.warehouse_id)
#         self.widgets['warehouse'].set(wh_name)
#         if d.contragent_id:
#             contr_name = next(n for n, i in self.contr_map.items() if i == d.contragent_id)
#             self.widgets['contragent'].set(contr_name)
#         for line in d.lines:
#             sm = line.qty * line.price
#             self.tv.insert('', 'end', values=(line.item.name, line.qty, line.price, sm),
#                            tags=(line.item_id,))

#     # ---------- работа со строками ----------
#     def _add_row(self):
#         d = DocRowDialog(self)
#         self.wait_window(d)
#         if d.res:
#             rows = [
#                 {'item_id': d.res['item_id'], 
#                  'qty': d.res['qty'], 
#                  'price': sale_price_get_date(d.res['item_id'], self.widgets['date'].get_date())
#                 }]
#             # print(sale_price_get_date(d.res['item_id'], self.widgets['date'].get_date()))
#             if self.doc_id:
#                 doc_save_table(self.doc_id, rows)
#             sm = rows[0]['qty'] * rows[0]['price']
#             self.tv.insert('', 'end', values=(rows[0]['item_name'], rows[0]['qty'], rows[0]['price'], sm),
#                            tags=(rows[0]['item_id'],))

#     def _edit_row(self):
#         sel = self.tv.selection()
#         if not sel:
#             return
#         self.tv.delete(sel[0])
#         self._add_row()

    
#     def _save(self):
#         # head
#         wh_id = self.wh_map[self.widgets['warehouse'].get()]
#         contr_name = self.widgets['contragent'].get()
#         contr_id = self.contr_map.get(contr_name)
#         date_ = self.widgets['date'].get_date()
#         comment = self.widgets['comment'].get()

#         if not self.doc_id:
#             self.doc_id = doc_save_head(self.doc_type, date_, wh_id, contr_id, comment)
#         else:
#             doc_update_head(self.doc_id, date_, wh_id, contr_id, comment)

#         # table
#         rows = []
#         for it in self.tv.get_children():
#             vals = self.tv.item(it)['values']
#             item_id = int(self.tv.item(it)['tags'][0])
#             qty, price = float(vals[1]), float(vals[2])
#             rows.append({'item_id': item_id, 'qty': qty, 'price': price})
#         doc_save_table(self.doc_id, rows)
#         # messagebox.showinfo("Сохранено", "Документ сохранён")
#         if self.on_close:
#                 self.on_close()

#     # ---------- проводки ----------
#     def _post(self):
#         self._save()
#         try:
#             doc_post(self.doc_id)
#             messagebox.showinfo('Проведён', 'Документ проведён')
#             self.destroy()
#             if self.on_close:
#                 self.on_close()
#         except Exception as e:
#             messagebox.showerror('Ошибка', str(e))

#     def _unpost(self):
#         try:
#             doc_unpost(self.doc_id)
#             messagebox.showinfo('Отмена', 'Проводка отменена')
#             self.destroy()
#             if self.on_close:
#                 self.on_close()
#         except Exception as e:
#             messagebox.showerror('Ошибка', str(e))

# widgets/dialogs.py (продолжение)

class DocDialog(tk.Toplevel):
    def __init__(self, master, doc_type, doc_id=None, on_close=None):
        super().__init__(master)
        self.doc_type = doc_type
        self.doc_id = doc_id
        self.on_close = on_close
        self.title('Продажа' if doc_type == DOC_TYPES[1] else 'Закупка')
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

    def _build_head(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=6, pady=6)
        top.columnconfigure(1, weight=1)

        labels = (('Дата', 0), ('Склад', 1), ('Контрагент', 2), ('Комментарий', 3))
        self.widgets = {}
        for text, row in labels:
            ttk.Label(top, text=text).grid(row=row, column=0, sticky=tk.W, padx=(0, 3), pady=4)
            if text == 'Дата':
                w = DateEntry(top, width=12, justify="right")
                w.grid(row=row, column=1, sticky='we')
                self.widgets['date'] = w
            elif text == 'Склад':
                w = ttk.Combobox(top, state='readonly', width=20)
                w.grid(row=row, column=1, sticky='we')
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
            elif text == 'Комментарий':
                w = ttk.Entry(top)
                w.grid(row=row, column=1, sticky='we', columnspan=3)
                self.widgets['comment'] = w

        self.posted = tk.IntVar()
        ttk.Checkbutton(top, text='Проведён', variable=self.posted, state='disabled').grid(
            row=4, column=0, columnspan=2, sticky=tk.W)

    def _build_table(self):
        mid = ttk.Frame(self)
        mid.pack(fill=tk.BOTH, expand=1, padx=6, pady=6)
        cols = ('Товар', 'Количество', 'Цена', 'Сумма')
        self.tv = ttk.Treeview(mid, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
            self.tv.column(c, width=120)
        self.tv.pack(fill=tk.BOTH, expand=1)
        ttk.Button(mid, text='Добавить строку', command=self._add_row).pack(pady=(5, 0))

    def _add_row(self):
        # Передаём тип документа и текущую дату
        current_date = self.widgets['date'].get_date()
        d = DocRowDialog(self, doc_type=self.doc_type, doc_date=current_date)
        self.wait_window(d)
        if d.res:
            sm = d.res['qty'] * d.res['price']
            self.tv.insert('', 'end', values=(
                d.res['item_name'],
                d.res['qty'],
                d.res['price'],
                sm
            ), tags=(d.res['item_id'],))

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

    def _save(self):
        wh_id = self.wh_map[self.widgets['warehouse'].get()]
        contr_name = self.widgets['contragent'].get()
        contr_id = self.contr_map.get(contr_name)
        date_ = self.widgets['date'].get_date()
        comment = self.widgets['comment'].get()

        if not self.doc_id:
            self.doc_id = doc_save_head(self.doc_type, date_, wh_id, contr_id, comment)
        else:
            doc_update_head(self.doc_id, date_, wh_id, contr_id, comment)

        rows = []
        for it in self.tv.get_children():
            vals = self.tv.item(it)['values']
            item_id = int(self.tv.item(it)['tags'][0])
            qty, price = float(vals[1]), float(vals[2])
            rows.append({'item_id': item_id, 'qty': qty, 'price': price})
        doc_save_table(self.doc_id, rows)

        if self.on_close:
            self.on_close()

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

# class DocRowDialog(tk.Toplevel):
# # ---------- диалог строки документа ----------
#     def __init__(self, master):
#         super().__init__(master)
#         self.res = None
#         self.title('Строка документа')
#         self.geometry('400x250')

#         ttk.Label(self, text='Товар').grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
#         self.cb = ttk.Combobox(self, state='readonly', width=30)
#         self.cb.grid(row=0, column=1, padx=6)
#         items = item_list()
#         self.item_map = {r['name']: r['id'] for r in items}
#         self.cb['values'] = list(self.item_map.keys())
#         if items:
#             self.cb.current(0)

#         ttk.Label(self, text='Кол-во').grid(row=1, column=0, sticky=tk.W, padx=6, pady=4)
#         self.e_qty = ttk.Entry(self)
#         self.e_qty.grid(row=1, column=1, padx=6)
#         self.e_qty.insert(0, '1')

#         # ttk.Label(self, text='Цена').grid(row=2, column=0, sticky=tk.W, padx=6, pady=4)
#         # self.e_price = ttk.Entry(self)
#         # self.e_price.grid(row=2, column=1, padx=6)
#         # self.e_price.insert(0, '0')

#         ttk.Button(self, text='OK', command=self._ok).grid(row=3, column=1, pady=10)

#     def _ok(self):
#         name = self.cb.get()
#         self.res = {
#             'item_id': self.item_map[name],
#             'item_name': name,
#             'qty': float(self.e_qty.get()),
#         }
#         self.destroy()
        
# widgets/dialogs.py


class DocRowDialog(tk.Toplevel):
    def __init__(self, master,doc_date=None, doc_type=None):
        super().__init__(master)
        self.doc_type = doc_type
        self.doc_date = doc_date 
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

        # Подставляем цену и блокируем поле, если это расход
        self.cb.bind('<<ComboboxSelected>>', self._on_item_select)
        self._on_item_select()  # инициализация при открытии

        ttk.Button(self, text='OK', command=self._ok).grid(row=3, column=1, pady=10)

    def _on_item_select(self, event=None):
        item_name = self.cb.get()
        item_id = self.item_map[item_name]
        if not item_name:
            return
        if self.doc_type == DOC_TYPES[0]:
            price = item_buy_price_get(item_id)
        else:
            price = sale_price_get_date(item_id, self.doc_date)
        self.e_price.config(state='normal')
        self.e_price.delete(0, 'end')
        self.e_price.insert(0, f"{price:.2f}")
        self.e_price.config(state='readonly')

    def _ok(self):
        name = self.cb.get()
        if not name:
            messagebox.showerror("Ошибка", "Выберите товар", parent=self)
            return
        try:
            qty = float(self.e_qty.get())
            price = float(self.e_price.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректное количество или цена", parent=self)
            return

        self.res = {
            'item_id': self.item_map[name],
            'item_name': name,
            'qty': qty,
            'price': price
        }
        self.destroy()       
        
        
        
        
        
        
        
