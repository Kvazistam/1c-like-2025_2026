# widgets/sales_report.py
import tkinter as tk
from tkinter import ttk
from db_scripts import get_sales_by_seller
from enumerates import CONTRAGENT_TYPES


class SalesReportWidget:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(self.frame, text="Отчёт по покупателям").pack(pady=4)

        cols = ("Покупатель", "Товар", "Цена", "Количество", "Сумма")
        self.tree = ttk.Treeview(self.frame, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120)
        self.tree.column("Покупатель", width=150)
        self.tree.column("Товар", width=200)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self._refresh()

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        data = get_sales_by_seller()
        total_qty = 0
        total_amount = 0.0

        for seller_data in data:
            # Добавляем строку покупателя (родитель)
            parent = self.tree.insert("", "end", values=(
                seller_data[CONTRAGENT_TYPES[1]],
                "",
                "",
                f"{seller_data['total_qty']:.0f}",
                f"{seller_data['total_amount']:.0f}"
            ), open=False)  # не раскрывать по умолчанию

            # Добавляем строки товаров (дети)
            for item in seller_data["items"]:
                child = self.tree.insert(parent, "end", values=(
                    "",
                    item["item_name"],
                    f"{item['price']:.2f}",
                    f"{item['qty']:.0f}",
                    f"{item['amount']:.0f}"
                ))
                total_qty += item['qty']
                total_amount += item['amount']

        # Добавляем итоговую строку
        self.tree.insert("", "end", values=(
            "Итого",
            "",
            "",
            f"{total_qty:.0f}",
            f"{total_amount:.0f}"
        ), tags=("total",))

        # Стиль для итоговой строки
        self.tree.tag_configure("total", background="#F0F0F0", font=("Arial", 10, "bold"))