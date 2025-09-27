# widgets/bonus_report.py
import tkinter as tk
from tkinter import ttk
from db_scripts import contragent_list_filter, get_bonus_balance
from enumerates import CONTRAGENT_TYPES


class BonusReportWidget:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(self.frame, text="Бонусы покупателей").pack(pady=4)

        # Таблица
        cols = ("Покупатель", "Бонусы (руб.)")
        self.tree = ttk.Treeview(self.frame, columns=cols, show="headings", height=20)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="w" if col == "Покупатель" else "e")
        self.tree.column("Покупатель", width=250)
        self.tree.column("Бонусы (руб.)", width=120)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self._refresh()

    def _refresh(self):
        """Загрузить всех покупателей и их бонусы."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Получаем только покупателей (type='customer')
        all_contr = contragent_list_filter(CONTRAGENT_TYPES[1])

        total = 0.0
        for c in all_contr:
            balance = get_bonus_balance(c['id'])
            total += balance
            self.tree.insert("", tk.END, values=(c['name'], f"{balance:.0f}"))

        # Итоговая строка
        self.tree.insert("", tk.END, values=("Итого:", f"{total:.0f}"), tags=("total",))
        self.tree.tag_configure("total", background="#F0F0F0", font=("Arial", 10, "bold"))