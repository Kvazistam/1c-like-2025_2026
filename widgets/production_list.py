# widgets/production_list.py
import tkinter as tk
from tkinter import ttk, messagebox
from db_scripts import production_list, production_delete
from widgets.production_dialog import ProductionDialog


class ProductionListWidget:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(self.frame, text="Документы производства").pack(pady=4)

        # Кнопки
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(btn_frame, text="Создать", command=self._create).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Открыть", command=self._open).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self._delete).pack(side=tk.LEFT, padx=5)

        # Таблица
        cols = ("ID", "Дата", "Склад", "Комментарий", "Проведён")
        self.tree = ttk.Treeview(self.frame, columns=cols, show="headings", height=15)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.column("ID", width=50)
        self.tree.column("Комментарий", width=200)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.tree, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", lambda e: self._open())

        self._refresh()

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        docs = production_list()
        for d in docs:
            posted_text = "Да" if d['posted'] else "Нет"
            self.tree.insert("", tk.END, values=(
                d['id'],
                d['date'],
                d['warehouse'],
                d['comment'] or "",
                posted_text
            ))

    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите документ")
            return None
        return int(self.tree.item(sel[0])['values'][0])

    def _create(self):
        def on_close():
            self._refresh()
        dialog = ProductionDialog(self.frame, on_close=on_close)
        self.frame.wait_window(dialog)

    def _open(self):
        doc_id = self._get_selected_id()
        if not doc_id:
            return
        def on_close():
            self._refresh()
        dialog = ProductionDialog(self.frame, doc_id=doc_id, on_close=on_close)
        self.frame.wait_window(dialog)

    def _delete(self):
        doc_id = self._get_selected_id()
        if not doc_id:
            return

        # Проверяем, проведён ли документ
        docs = production_list()
        selected_doc = next((d for d in docs if d['id'] == doc_id), None)
        if selected_doc and selected_doc['posted']:
            messagebox.showerror("Ошибка", "Нельзя удалить проведённый документ!")
            return

        if messagebox.askyesno("Подтверждение", "Удалить документ производства?"):
            try:
                production_delete(doc_id)
                self._refresh()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))