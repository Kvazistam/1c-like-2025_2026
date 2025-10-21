# widgets/production_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import date

from db_scripts import (
    warehouse_list, item_list, unit_list,
    production_save_head, production_save_lines, production_post, production_unpost, production_get
)
from widgets.production_row_dialog import ProductionRowDialog


class ProductionDialog(tk.Toplevel):
    def __init__(self, master, doc_id=None, on_close=None):
        super().__init__(master)
        self.doc_id = doc_id
        self.on_close = on_close
        self.title("Производство (Комплектация)")
        self.geometry("900x600")

        self._build_head()
        self._build_tables()
        if doc_id:
            self._load_doc()
        else:
            self.widgets['date'].set_date(date.today())
            self.posted.set(0)

        self._build_buttons()

    def _build_head(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=6, pady=6)
        top.columnconfigure(1, weight=1)

        # Дата
        ttk.Label(top, text="Дата").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.widgets = {}
        self.widgets['date'] = DateEntry(top, width=12)
        self.widgets['date'].grid(row=0, column=1, sticky='we')

        # Склад
        ttk.Label(top, text="Склад").grid(row=1, column=0, sticky=tk.W, pady=4)
        whs = warehouse_list()
        self.wh_map = {r['name']: r['id'] for r in whs}
        self.widgets['warehouse'] = ttk.Combobox(top, values=list(self.wh_map.keys()), state='readonly')
        self.widgets['warehouse'].grid(row=1, column=1, sticky='we')
        if whs:
            self.widgets['warehouse'].current(0)

        # Комментарий
        ttk.Label(top, text="Комментарий").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.widgets['comment'] = ttk.Entry(top)
        self.widgets['comment'].grid(row=2, column=1, sticky='we')

        # Статус
        self.posted = tk.IntVar()
        ttk.Checkbutton(top, text="Проведён", variable=self.posted, state='disabled').grid(
            row=3, column=0, columnspan=2, sticky=tk.W
        )

    def _build_tables(self):
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        # === Списание материалов ===
        ttk.Label(main, text="Списание материалов (сырьё)").pack(anchor=tk.W)
        input_frame = ttk.Frame(main)
        input_frame.pack(fill=tk.BOTH, expand=True)
        self._create_table(input_frame, 'input')

        ttk.Button(main, text="Добавить материал", command=lambda: self._add_row('input')).pack(pady=2)

        # === Приход продукции ===
        ttk.Label(main, text="Приход продукции (готовое)").pack(anchor=tk.W, pady=(10, 0))
        output_frame = ttk.Frame(main)
        output_frame.pack(fill=tk.BOTH, expand=True)
        self._create_table(output_frame, 'output')

        ttk.Button(main, text="Добавить продукцию", command=lambda: self._add_row('output')).pack(pady=2)

    def _create_table(self, parent, table_type):
        cols = ('Товар', 'Ед. изм.', 'Количество')
        tree = ttk.Treeview(parent, columns=cols, show='headings', height=5)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=150)
        tree.pack(fill=tk.BOTH, expand=True)
        setattr(self, f'{table_type}_tree', tree)

    def _add_row(self, table_type):
        dialog = ProductionRowDialog(self, table_type)
        self.wait_window(dialog)
        if dialog.res:
            tree = getattr(self, f'{table_type}_tree')
            tree.insert('', 'end', values=(
                dialog.res['item_name'],
                dialog.res['unit_name'],
                dialog.res['qty']
            ), tags=(
                dialog.res['item_id'],
                dialog.res['unit_id']
            ))

    def _load_doc(self):
        d = production_get(self.doc_id)
        if not d:
            return

        self.widgets['date'].set_date(d.date)
        wh_name = next(n for n, i in self.wh_map.items() if i == d.warehouse_id)
        self.widgets['warehouse'].set(wh_name)
        if d.comment:
            self.widgets['comment'].insert(0, d.comment)
        self.posted.set(d.posted)

        for line in d.input_lines:
            self.input_tree.insert('', 'end', values=(
                line.item.name,
                line.unit.name,
                line.qty
            ), tags=(line.item_id, line.unit_id))

        for line in d.output_lines:
            self.output_tree.insert('', 'end', values=(
                line.item.name,
                line.unit.name,
                line.qty
            ), tags=(line.item_id, line.unit_id))

    def _build_buttons(self):
        btn_bar = ttk.Frame(self)
        btn_bar.pack(fill=tk.X, pady=4)
        ttk.Button(btn_bar, text='Сохранить', command=self._save).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text='Провести', command=self._post).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text='Отменить проводку', command=self._unpost).pack(side=tk.LEFT, padx=4)

    def _save(self):
        wh_id = self.wh_map[self.widgets['warehouse'].get()]
        date_ = self.widgets['date'].get_date()
        comment = self.widgets['comment'].get()

        if not self.doc_id:
            self.doc_id = production_save_head(date_, wh_id, comment)
        else:
            # Для простоты — пересохраняем всё (можно добавить update_head)
            pass

        # Собираем строки
        input_rows = []
        for item in self.input_tree.get_children():
            vals = self.input_tree.item(item)['values']
            tags = self.input_tree.item(item)['tags']
            input_rows.append({
                'item_id': int(tags[0]),
                'unit_id': int(tags[1]),
                'qty': float(vals[2])
            })

        output_rows = []
        for item in self.output_tree.get_children():
            vals = self.output_tree.item(item)['values']
            tags = self.output_tree.item(item)['tags']
            output_rows.append({
                'item_id': int(tags[0]),
                'unit_id': int(tags[1]),
                'qty': float(vals[2])
            })

        production_save_lines(self.doc_id, input_rows, output_rows)
        if self.on_close:
            self.on_close()

    def _post(self):
        self._save()
        try:
            production_post(self.doc_id)
            messagebox.showinfo('Успех', 'Производство проведено')
            self.destroy()
            if self.on_close:
                self.on_close()
        except Exception as e:
            messagebox.showerror('Ошибка', str(e))

    def _unpost(self):
        try:
            production_unpost(self.doc_id)
            messagebox.showinfo('Успех', 'Проводка отменена')
            self.destroy()
            if self.on_close:
                self.on_close()
        except Exception as e:
            messagebox.showerror('Ошибка', str(e))