import tkinter as tk
from tkinter import ttk
from db_scripts import stock_movements
from datetime import date

class StockWidget:
    def __init__(self, parent):
        self.parent = parent
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        ttk.Label(self.parent, text=':Журнал прихода/расхода').pack(pady=4)

        cols = ('', 'Дата', 'Склад', 'Контрагент', 'Товар', 'Кол-во')
        self.tv = ttk.Treeview(self.parent, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
            self.tv.column(c, width=90 if c != 'Товар' else 200)
        self.tv.pack(fill=tk.BOTH, expand=1)

        # цветные иконки
        self.tv.tag_configure('plus', foreground="#19A02B")   # красный
        self.tv.tag_configure('minus', foreground="#db3434")  # синий

    def _refresh(self):
        for i in self.tv.get_children():
            self.tv.delete(i)

        for row in stock_movements():
            sign = '✚' if row['qty'] > 0 else '–'
            tag = 'plus' if row['qty'] > 0 else 'minus'
            self.tv.insert(
                '', 'end',
                values=(sign,
                        row['date'],
                        row['warehouse'],
                        row['contragent'] or '-',
                        row['item'],
                        f"{abs(row['qty']):.0f}"),
                tags=(tag,)
            )