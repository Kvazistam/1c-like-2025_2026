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
    item_list, warehouse_list, doc_save_head, doc_save_table, doc_get, doc_post, doc_unpost,
    contragent_list_filter, contragent_get_id, add_bonus, spend_bonus, get_bonus_balance
)
from db_scripts import unit_list_for_item, unit_get
from db_scripts.db_items import item_buy_price_get
from db_scripts.db_units import unit_list_for_item, unit_list_applicable
from enumerates import CONTRAGENT_TYPES, DOC_TYPES, ITEM_TYPES


class ItemDialog(tk.Toplevel):
    def __init__(self, master, item_id=None, item_data: dict = None):
        super().__init__(master)
        self.res = None
        self.title("Товар")
        self.geometry("500x700")

        labels = ("Название", "Категория", "Тип товара")
        self.entries = {}
        for i, lbl in enumerate(labels):
            ttk.Label(self, text=lbl).grid(row=i, column=0, sticky=tk.W, padx=6, pady=4)
            if lbl == "Тип товара":
                cb = ttk.Combobox(self, values=ITEM_TYPES, state="readonly")
                cb.grid(row=i, column=1, sticky=tk.EW, padx=6)
                cb.current(0)
                cb.bind("<<ComboboxSelected>>", self._on_type_change)
                self.entries['item_type'] = cb
            else:
                e = ttk.Entry(self)
                e.grid(row=i, column=1, sticky=tk.EW, padx=6)
                key = lbl.lower().replace(' ', '_')
                self.entries[key] = e

        # Единицы измерения
        self.unit_rows_start = len(labels)
        self._build_unit_selector()

        # Картинка
        img_row = self.unit_rows_start + 3
        ttk.Label(self, text="Картинка").grid(row=img_row, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Button(self, text="Выбрать...", command=self.pick_image).grid(row=img_row, column=1, sticky=tk.W, padx=6)

        self.image_label = tk.Label(self, bg="white", relief="sunken")
        self.image_label.grid(row=img_row+1, column=0, columnspan=2, sticky="nswe")
        self._show_placeholder()

        # Кнопка
        ttk.Button(self, text="Сохранить", command=self.on_save).grid(row=img_row+2, column=0, pady=10, padx=6, sticky='w')

        self.columnconfigure(1, weight=1)
        self.rowconfigure(img_row+1, weight=1)
        self.image_bytes = None

        # Загрузка данных
        if item_data:
            self._load_data(item_data)

        self.transient(master)
        self.grab_set()
        self.focus_set()

    def _build_unit_selector(self):
        self.cb_base = ttk.Combobox(self, state="readonly")
        self.cb_storage = ttk.Combobox(self, state="readonly")
        self.cb_report = ttk.Combobox(self, state="readonly")

        ttk.Label(self, text="Базовая ЕИ").grid(row=self.unit_rows_start, column=0, sticky=tk.W, padx=6, pady=4)
        self.cb_base.grid(row=self.unit_rows_start, column=1, sticky=tk.EW, padx=6)

        ttk.Label(self, text="ЕИ хранения").grid(row=self.unit_rows_start+1, column=0, sticky=tk.W, padx=6, pady=4)
        self.cb_storage.grid(row=self.unit_rows_start+1, column=1, sticky=tk.EW, padx=6)

        ttk.Label(self, text="ЕИ отчётов").grid(row=self.unit_rows_start+2, column=0, sticky=tk.W, padx=6, pady=4)
        self.cb_report.grid(row=self.unit_rows_start+2, column=1, sticky=tk.EW, padx=6)

    def _on_type_change(self, event=None):
        self.update_mesurament_list()

    def update_mesurament_list(self):
        item_type = self.entries['item_type'].get()
        units = unit_list_applicable(item_type)
        self.unit_map = {u['name']: u['id'] for u in units}
        unit_names = list(self.unit_map.keys()) or [""]

        self.cb_base['values'] = unit_names
        self.cb_storage['values'] = unit_names
        self.cb_report['values'] = unit_names

        if unit_names != [""]:
            self.cb_base.current(0)
            self.cb_storage.current(0)
            self.cb_report.current(0)

    def _load_data(self, item_data):
        self.entries['название'].insert(0, item_data.get('name', ''))
        cat = item_data.get('category')
        if cat:
            self.entries['категория'].insert(0, cat)

        # Тип товара
        item_type = item_data.get('item_type')
        if item_type in ITEM_TYPES:
            self.entries['item_type'].set(item_type)
            self.update_mesurament_list()

        # ЕИ
        def set_unit(cb, unit_id):
            unit = unit_get(unit_id)
            if unit and unit['name'] in self.unit_map:
                cb.set(unit['name'])

        set_unit(self.cb_base, item_data.get('base_unit_id'))
        set_unit(self.cb_storage, item_data.get('storage_unit_id'))
        set_unit(self.cb_report, item_data.get('report_unit_id'))

        # Картинка
        if item_data.get('image'):
            self.image_bytes = item_data['image']
            self._show_image(self.image_bytes)

    def on_save(self):
        name = self.entries['название'].get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Название обязательно", parent=self)
            return

        category = self.entries['категория'].get().strip() or None
        item_type = self.entries['item_type'].get()

        # Проверка ЕИ
        try:
            base_id = self.unit_map[self.cb_base.get()]
            storage_id = self.unit_map[self.cb_storage.get()]
            report_id = self.unit_map[self.cb_report.get()]
        except KeyError:
            messagebox.showerror("Ошибка", "Выберите корректные единицы измерения", parent=self)
            return

        self.res = {
            'name': name,
            'category': category,
            'item_type': item_type,
            'base_unit_id': base_id,
            'storage_unit_id': storage_id,
            'report_unit_id': report_id,
            'image': self.image_bytes
        }
        self.destroy()

    def _show_placeholder(self):
        """Показать заглушку 'Нет изображения'."""
        self.image_label.config(
            image='', text="Нет изображения", compound="center")

    def _show_image(self, image_bytes: bytes):
        """Отобразить изображение, масштабированное под размер Label."""
        try:
            original = Image.open(io.BytesIO(image_bytes))

            target_width = 500
            target_height = 500

            original.thumbnail((target_width, target_height), Image.LANCZOS)
            resized = original

            self.photo = ImageTk.PhotoImage(resized)
            self.image_label.config(
                image=self.photo, text="", width=target_width, height=target_height)
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
                messagebox.showerror(
                    "Ошибка", f"Не удалось загрузить изображение:\n{e}", parent=self)
                self.image_bytes = None
                self._show_placeholder()

    # def on_save(self):
    #     name = self.entries['название'].get().strip()
    #     if not name:
    #         messagebox.showerror("Ошибка", "Название обязательно", parent=self)
    #         return
    #     category = self.entries['категория'].get().strip() or None

    #     self.res = {
    #     'name': name,
    #     'category': category,
    #     'item_type': self.entries['item_type'].get(),
    #     'base_unit_id': self.unit_map[self.cb_base.get()],
    #     'storage_unit_id': self.unit_map[self.cb_storage.get()],
    #     'report_unit_id': self.unit_map[self.cb_report.get()],
    #     'image': self.image_bytes
    #     }
    #     self.destroy()

class SalePriceDialog(tk.Toplevel):
    def __init__(self, master, price_id=None, on_save=None):
        super().__init__(master)
        self.price_id = price_id
        self.on_save = on_save
        self.title("Розничная цена")
        self.geometry("450x250")
        self.resizable(False, False)

        # Поля
        ttk.Label(self, text="Товар:").grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=8)
        self.item_cb = ttk.Combobox(self, state="readonly", width=30)
        self.item_cb.grid(row=0, column=1, padx=10, pady=8)

        ttk.Label(self, text="Дата начала:").grid(
            row=1, column=0, sticky=tk.W, padx=10, pady=8)
        self.date_entry = DateEntry(
            self, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.date_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=8)

        ttk.Label(self, text="Цена:").grid(
            row=2, column=0, sticky=tk.W, padx=10, pady=8)
        self.price_entry = ttk.Entry(self, width=15)
        self.price_entry.grid(row=2, column=1, sticky=tk.W, padx=10, pady=8)

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="Сохранить",
                   command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(
            side=tk.LEFT, padx=5)

        items = item_list()
        self.item_map = {r['name']: r['id'] for r in items}
        self.item_cb['values'] = list(self.item_map.keys())

        if price_id:
            self._load(price_id)
        else:
            if items:
                self.item_cb.current(0)

    def _load(self, price_id):
        reg = sale_price_get_id(price_id)
        if reg:

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


class DocDialog(tk.Toplevel):
    def __init__(self, master, doc_type, doc_id=None, on_close=None):
        super().__init__(master)
        self.doc_type = doc_type
        self.doc_id = doc_id
        self.on_close = on_close
        self.title('Продажа' if doc_type == DOC_TYPES[1] else 'Закупка')
        self.geometry('700x700')
        self._build_head()
        self._build_table()
        if doc_id:
            self._load_doc()
        else:
            self.widgets['date'].set_date(date.today())
            self.posted.set(0)
        # Стиль для итоговой строки
        self.tv.tag_configure("total", background="#F0F0F0",
                              font=("Arial", 10, "bold"))
        btn_bar = ttk.Frame(self)
        btn_bar.pack(fill=tk.X, pady=4)
        ttk.Button(btn_bar, text='Сохранить', command=self._save).pack(
            side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text='Провести', command=self._post).pack(
            side=tk.LEFT, padx=4)
        # ttk.Button(btn_bar, text='Отменить проводку', command=self._unpost).pack(side=tk.LEFT, padx=4)

    def _build_head(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=6, pady=6)
        top.columnconfigure(1, weight=1)

        labels = (('Дата', 0), ('Склад', 1),
                  ('Контрагент', 2), ('Комментарий', 3))
        self.widgets = {}
        for text, row in labels:
            ttk.Label(top, text=text).grid(
                row=row, column=0, sticky=tk.W, padx=(0, 3), pady=4)
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
                cont_type = CONTRAGENT_TYPES[0] if self.doc_type == DOC_TYPES[0] else CONTRAGENT_TYPES[1]
                cons = contragent_list_filter(cont_type)
                self.contr_map = {r['name']: r['id'] for r in cons}
                w['values'] = list(self.contr_map.keys())
                self.widgets['contragent'].bind(
                    "<<ComboboxSelected>>", self._on_contragent_select)
            elif text == 'Комментарий':
                w = ttk.Entry(top)
                w.grid(row=row, column=1, sticky='we', columnspan=3)
                self.widgets['comment'] = w
        if self.doc_type == DOC_TYPES[1]:
            self._build_bonuses(top, row=row+1)
        self.posted = tk.IntVar()
        ttk.Checkbutton(top, text='Проведён', variable=self.posted, state='disabled').grid(
            row=row+1, column=0, columnspan=2, sticky=tk.W)

    def _build_bonuses(self, top, row):
        ttk.Label(top, text="Бонусы").grid(
            row=row, column=0, sticky=tk.W, padx=(0, 3), pady=4)

        bonus_frame = ttk.Frame(top)
        bonus_frame.grid(row=row, column=1, sticky='we', columnspan=3)

        self.bonus_mode = tk.StringVar(value="save")
        ttk.Radiobutton(bonus_frame, text="Копить",
                        variable=self.bonus_mode, value="save").pack(side=tk.LEFT)
        ttk.Radiobutton(bonus_frame, text="Тратить", variable=self.bonus_mode,
                        value="spend").pack(side=tk.LEFT, padx=(10, 0))

        self.bonus_entry = ttk.Entry(bonus_frame, width=10, state='disabled')
        self.bonus_entry.pack(side=tk.LEFT, padx=(10, 0))
        ttk.Label(bonus_frame, text="руб.").pack(side=tk.LEFT)
        self.bonus_entry.bind("<KeyRelease>", self._on_bonus_entry_change)

        self.bonus_mode.trace_add("write", self._on_bonus_mode_change)

        self.bonus_balance_label = ttk.Label(top, text="Баланс: 0 руб.")
        self.bonus_balance_label.grid(row=row+1, column=1, sticky='w')

    def _on_bonus_entry_change(self, event=None):
        self._update_total()

    def _build_table(self):
        mid = ttk.Frame(self)
        mid.pack(fill=tk.BOTH, expand=1, padx=6, pady=6)
        cols = ('Товар', 'Количество', 'Ед. изм.', 'Цена', 'Сумма')
        self.tv = ttk.Treeview(mid, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
            self.tv.column(c, width=120)
        self.tv.pack(fill=tk.BOTH, expand=1)

        self.context_menu = tk.Menu(self.tv, tearoff=0)
        self.context_menu.add_command(
            label="Редактировать", command=self._edit_row)
        self.context_menu.add_command(
            label="Удалить", command=self._delete_row)
        self.tv.bind("<Button-3>", self._show_context_menu)
        self.tv.bind("<Delete>", lambda e: self._delete_row())
        self.tv.bind("<Double-1>", lambda e: self._edit_row())

        total_frame = ttk.Frame(mid)
        total_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(total_frame, text="Итого:").pack(side=tk.LEFT)
        self.total_label = ttk.Label(
            total_frame, text="0 руб.", font=("Arial", 10, "bold"))
        self.total_label.pack(side=tk.LEFT, padx=(5, 0))
        self.tv.bind("<<TreeviewSelect>>", self._update_total)

        ttk.Button(mid, text='Добавить строку',
                   command=self._add_row).pack(padx=5, side='left')

    def _on_contragent_select(self, event=None):
        """Вызывается при выборе контрагента."""
        if self.doc_type == DOC_TYPES[1]:
            self._update_bonus_info()

    def _on_bonus_mode_change(self, *args):
        if self.bonus_mode.get() == "spend":
            self.bonus_entry.config(state='normal')
        else:
            self.bonus_entry.config(state='disabled')
            self.bonus_entry.delete(0, tk.END)
        self._update_total()

    def _update_bonus_info(self):
        """Обновить информацию о бонусах (баланс)."""

        contr_name = self.widgets['contragent'].get()
        if not contr_name:
            self.bonus_balance_label.config(text="Выберите покупателя")
            return
        contr_id = self.contr_map.get(contr_name)
        if not contr_id:
            return
        balance = get_bonus_balance(contr_id)
        self.bonus_balance_label.config(text=f"Баланс: {balance:.0f} руб.")

    def _update_total(self, event=None):
        """Обновить итоговую сумму с учётом бонусов."""
        # Считаем сумму всех строк
        total = 0.0
        for item in self.tv.get_children():
            try:
                amount = float(self.tv.item(item)['values'][3])
                total += amount
            except (IndexError, ValueError):
                continue

        # Вычитаем бонусы, если тратим
        bonus_amount = 0.0
        if self.doc_type == 'расход' and self.bonus_mode.get() == "spend":
            try:
                bonus_amount = float(self.bonus_entry.get() or 0)
                # Ограничиваем бонусы 50% от суммы
                max_bonus = total / 2
                if bonus_amount > max_bonus:
                    bonus_amount = max_bonus
            except ValueError:
                bonus_amount = 0.0

        final_total = total - bonus_amount
        self.total_label.config(text=f"{final_total:.2f} руб.")

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
                d.res['unit_name'],  
                d.res['price'],
                sm
            ), tags=(d.res['item_id'], d.res['unit_id']))
            self._update_total()

    def _show_context_menu(self, event):
        """Показать контекстное меню по ПКМ."""
        item = self.tv.identify_row(event.y)
        if item:
            self.tv.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _edit_row(self):
        """Редактировать выбранную строку."""
        sel = self.tv.selection()
        if not sel:
            return
        # Получаем текущие данные строки
        values = self.tv.item(sel[0])['values']
        tags = self.tv.item(sel[0])['tags']
        if not tags:
            return

        item_id = int(tags[0])
        item_name = values[0]
        qty = float(values[1])
        price = float(values[3])

        # Открываем диалог с предзаполненными данными
        current_date = self.widgets['date'].get_date()
        d = DocRowDialog(self, doc_type=self.doc_type, doc_date=current_date)
        # Предзаполняем поля
        d.cb.set(item_name)
        d.e_qty.delete(0, tk.END)
        d.e_qty.insert(0, str(qty))
        d.e_price.config(state='normal')
        d.e_price.delete(0, tk.END)
        d.e_price.insert(0, str(price))
        # расход — делаем readonly после установки
        if self.doc_type == DOC_TYPES[1]:
            d.e_price.config(state='readonly')
        self.wait_window(d)

        if d.res:
            sm = d.res['qty'] * d.res['price']
            self.tv.item(sel[0], values=(
                d.res['item_name'], d.res['qty'], d.res["unit_name"], d.res['price'], sm), tags=(d.res['item_id'], d.res['unit_id']))
            self._update_total()

    def _delete_row(self):
        """Удалить выбранную строку."""
        sel = self.tv.selection()
        if not sel:
            return
        self.tv.delete(sel[0])
        self._update_total()

    def _load_doc(self):
        d = doc_get(self.doc_id)
        if not d:
            return
        if d.posted:
            try:
                doc_unpost(self.doc_id)
                # Обновим данные после отмены
                d = doc_get(self.doc_id)
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror(
                    "Ошибка", f"Не удалось отменить проводку:\n{e}")
                self.destroy()
                return
        self.widgets['date'].set_date(d.date)
        self.widgets['comment'].insert(0, d.comment or '')
        self.posted.set(d.posted)
        self.widgets['warehouse'].set(d.warehouse.name)
        if d.contragent_id:
            self.widgets['contragent'].set(d.contragent.name)
            self._on_contragent_select()
        for line in d.lines:
            sm = line.qty * line.price
            self.tv.insert('', 'end', values=(line.item.name, line.qty, line.unit.name, line.price, sm),
                           tags=(line.item_id, line.unit_id))
        self._update_total()

    def _save(self):
        wh_id = self.wh_map[self.widgets['warehouse'].get()]
        contr_name = self.widgets['contragent'].get()
        
        date_ = self.widgets['date'].get_date()
        comment = self.widgets['comment'].get()

        if not contr_name:
            messagebox.showerror("Ошибка", "Выберите контрагента", parent=self)
            return
        contr_id = self.contr_map.get(contr_name)
        if contr_id is None:
            messagebox.showerror("Ошибка", "Некорректный контрагент")
            return
        if not self.doc_id:
            self.doc_id = doc_save_head(
                self.doc_type, date_, wh_id, contr_id, comment)
        else:
            doc_update_head(self.doc_id, date_, wh_id, contr_id, comment)

        rows = []
        for it in self.tv.get_children():
            vals = self.tv.item(it)['values']
            tags = self.tv.item(it)['tags']
            item_id = int(tags[0])
            unit_id = int(tags[1])
            qty, price = float(vals[1]), float(vals[3])
            unit = unit_get(unit_id)
            base_qty = qty * unit['ratio_to_base'] 
            rows.append({'item_id': item_id, 'qty': base_qty, 'unit_id': unit_id,  'price': price})            

        # Обновляем шапку с бонусами
        bonus_mode = self.bonus_mode.get() if self.doc_type == 'расход' else None
        try:
            bonus_amount = float(self.bonus_entry.get()
                                 or 0) if bonus_mode == "spend" else 0.0
        except ValueError:
            bonus_amount = 0.0
        doc_update_head(
            self.doc_id, date_, wh_id, contr_id, comment,
            bonus_mode=bonus_mode,
            bonus_amount=bonus_amount
        )
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


class DocRowDialog(tk.Toplevel):
    def __init__(self, master, doc_date=None, doc_type=None):
        super().__init__(master)
        self.doc_type = doc_type
        self.doc_date = doc_date
        self.res = None
        self.title('Строка документа')
        self.geometry('400x250')

        ttk.Label(self, text='Товар').grid(
            row=0, column=0, sticky=tk.W, padx=6, pady=4)
        self.cb = ttk.Combobox(self, state='readonly', width=30)
        self.cb.grid(row=0, column=1, padx=6)
        items = item_list()
        self.item_map = {r['name']: r['id'] for r in items}
        self.cb['values'] = list(self.item_map.keys())
        if items:
            self.cb.current(0)

        ttk.Label(self, text='Кол-во').grid(row=1,
                                            column=0, sticky=tk.W, padx=6, pady=4)
        self.e_qty = ttk.Entry(self)
        self.e_qty.grid(row=1, column=1, padx=6)
        self.e_qty.insert(0, '1')

        ttk.Label(self, text='Цена').grid(
            row=2, column=0, sticky=tk.W, padx=6, pady=4)
        self.e_price = ttk.Entry(self)
        self.e_price.grid(row=2, column=1, padx=6)
        self.e_price.insert(0, '0')

        # После выбора товара — выбор ЕИ
        ttk.Label(self, text='Ед. изм.').grid(row=3, column=0, sticky=tk.W, padx=6, pady=4)
        self.cb_unit = ttk.Combobox(self, state='readonly', width=20)
        self.cb_unit.grid(row=3, column=1, padx=6)
        
        # Подставляем цену и блокируем поле, если это расход
        self.cb.bind('<<ComboboxSelected>>', self._on_item_select)
        self._on_item_select()  # инициализация при открытии

        ttk.Button(self, text='OK', command=self._ok).grid(
            row=4, column=1, pady=10)
        
        

    # def _on_item_select(self, event=None):
    #     item_name = self.cb.get()
    #     item_id = self.item_map[item_name]
    #     if not item_name:
    #         return
    #     if self.doc_type == DOC_TYPES[1]:
    #         price = sale_price_get_date(item_id, self.doc_date)
    #         self.e_price.config(state='normal')
    #         self.e_price.delete(0, 'end')
    #         self.e_price.insert(0, f"{price:.2f}")
    #         self.e_price.config(state='readonly')
    #     else:
    #         self.e_price.config(state='normal')
    #         self.e_price.delete(0, 'end')
    #         self.e_price.insert(0, 0)

    def _on_item_select(self, event=None):
        item_name = self.cb.get()
        if not item_name:
            return

        item_id = self.item_map[item_name]


        units = unit_list_for_item(item_id)
        
        # Обновляем выпадающий список ЕИ
        self.unit_map = {u['name']: u['id'] for u in units}
        self.cb_unit['values'] = list(self.unit_map.keys())
        if units:
            self.cb_unit.current(0)
            selected_unit_id = self.unit_map[units[0]['name']]
        else:
            selected_unit_id = None

        if self.doc_type == DOC_TYPES[1]:  
            # Получаем базовую розничную цену (за базовую единицу товара)
            base_price = sale_price_get_date(item_id, self.doc_date)
            
            if selected_unit_id:
                # Получаем коэффициент ЕИ
                unit = unit_get(selected_unit_id)
                # Цена за выбранную ЕИ = базовая цена * ratio_to_base
                price = base_price * unit['ratio_to_base']
            else:
                price = base_price

            self.e_price.config(state='normal')
            self.e_price.delete(0, 'end')
            self.e_price.insert(0, f"{price:.2f}")
            self.e_price.config(state='readonly')
        else:  # приход
            # Для прихода можно брать buy_price или оставить 0
            self.e_price.config(state='normal')
            self.e_price.delete(0, 'end')
            self.e_price.insert(0, '0')

    def _ok(self):
        name = self.cb.get()
        unit_name = self.cb_unit.get()
        if not name:
            messagebox.showerror("Ошибка", "Выберите товар", parent=self)
            return
        try:
            qty = float(self.e_qty.get())
            price = float(self.e_price.get())
        except ValueError:
            messagebox.showerror(
                "Ошибка", "Некорректное количество или цена", parent=self)
            return
        
        self.res = {
            'item_id': self.item_map[name],
            'item_name': name,
            'unit_id': self.unit_map[unit_name],  
            'unit_name': unit_name,              
            'qty': qty,
            'price': price
        }
        self.destroy()
