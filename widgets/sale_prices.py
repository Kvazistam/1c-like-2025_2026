# ---------- диалог розничной цены ----------
import tkinter as tk
from tkinter import messagebox, ttk


# widgets/sale_prices.py
import tkinter as tk
from tkinter import ttk, messagebox
from db_scripts import sale_price_list, sale_price_delete
from widgets.dialogs import SalePriceDialog

class SalePricesWidget:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)

        ttk.Label(self.frame, text="Регистр розничных цен").pack(pady=4)

        # Кнопки
        btn_frame = ttk.Frame(self.frame)
       
        
        

        # Таблица
        cols = ("№", "Товар", "Дата начала", "Цена")
        self.tree = ttk.Treeview(self.frame, columns=cols, show="headings", height=15)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.column("Товар", width=250)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.tree, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(btn_frame, text="Добавить", command=self._add).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Редактировать", command=self._edit).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self._delete).pack(side=tk.LEFT, padx=5)
        self.tree.bind("<Double-1>", lambda e: self._edit())

        self._refresh()

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        prices = sale_price_list()
        for p in prices:
            self.tree.insert("", tk.END, values=(
                p['id'],
                p['item_name'],
                p['start_date'],
                f"{p['price']:.2f}"
            ))

    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите запись")
            return None
        print(int(self.tree.item(sel[0])['values'][0]))
        return int(self.tree.item(sel[0])['values'][0])

    def _add(self):
        def on_save():
            self._refresh()
        dialog = SalePriceDialog(self.frame, on_save=on_save)
        self.frame.wait_window(dialog)

    def _edit(self):
        price_id = self._get_selected_id()
        if price_id is None:
            return
        def on_save():
            self._refresh()
        dialog = SalePriceDialog(self.frame, price_id=price_id, on_save=on_save)
        self.frame.wait_window(dialog)

    def _delete(self):
        price_id = self._get_selected_id()
        if price_id is None:
            return
        if messagebox.askyesno("Подтверждение", "Удалить цену?"):
            try:
                sale_price_delete(price_id)
                self._refresh()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))