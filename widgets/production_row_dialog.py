# widgets/production_row_dialog.py
import tkinter as tk
from tkinter import ttk

from db_scripts import item_list, unit_list_all
from db_scripts.db_units import unit_list_for_item


class ProductionRowDialog(tk.Toplevel):
    def __init__(self, master, table_type):
        super().__init__(master)
        self.table_type = table_type
        self.res = None
        self.title(f"{'Материал' if table_type == 'input' else 'Продукция'}")
        self.geometry("400x200")

        # Товар
        ttk.Label(self, text="Товар").grid(row=0, column=0, sticky=tk.W, padx=6, pady=6)
        items = item_list()
        self.item_map = {r['name']: r['id'] for r in items}
        self.cb_item = ttk.Combobox(self, values=list(self.item_map.keys()), state='readonly')
        self.cb_item.grid(row=0, column=1, sticky='we', padx=6)
        if items:
            self.cb_item.current(0)
        self.cb_item.bind("<<ComboboxSelected>>", self._on_item_select)

        # Единица измерения
        ttk.Label(self, text="Ед. изм.").grid(row=1, column=0, sticky=tk.W, padx=6, pady=6)
        self.cb_unit = ttk.Combobox(self, state='readonly')
        self.cb_unit.grid(row=1, column=1, sticky='we', padx=6)

        # Количество
        ttk.Label(self, text="Количество").grid(row=2, column=0, sticky=tk.W, padx=6, pady=6)
        self.e_qty = ttk.Entry(self)
        self.e_qty.grid(row=2, column=1, sticky='we', padx=6)
        self.e_qty.insert(0, '1')

        ttk.Button(self, text="OK", command=self._ok).grid(row=3, column=1, pady=10)

        # Инициализация единиц измерения
        self._on_item_select()

    def _on_item_select(self, event=None):
        item_name = self.cb_item.get()
        if not item_name:
            return
        item_id = self.item_map[item_name]
        units = unit_list_for_item(item_id)  # ← функция должна возвращать ЕИ для товара
        self.unit_map = {u['name']: u['id'] for u in units}
        self.cb_unit['values'] = list(self.unit_map.keys())
        if units:
            self.cb_unit.current(0)

    def _ok(self):
        item_name = self.cb_item.get()
        unit_name = self.cb_unit.get()
        if not item_name or not unit_name:
            return
        try:
            qty = float(self.e_qty.get())
        except ValueError:
            return

        self.res = {
            'item_id': self.item_map[item_name],
            'item_name': item_name,
            'unit_id': self.unit_map[unit_name],
            'unit_name': unit_name,
            'qty': qty
        }
        self.destroy()