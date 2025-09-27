# widgets/warehouses.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from db_scripts import warehouse_list, warehouse_add, warehouse_update, warehouse_delete


class WarehousesWidget:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(self.frame, text="Склады").pack(pady=4)

        # Кнопки
        

        # Таблица
        cols = ("ID", "Наименование")
        self.tree = ttk.Treeview(self.frame, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.column("ID", width=50)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(btn_frame, text="Добавить", command=self._add).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Редактировать", command=self._edit).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self._delete).pack(side=tk.LEFT, padx=5)

        self.tree.bind("<Double-1>", lambda e: self._edit())

        self._refresh()

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        warehouses = warehouse_list()
        for w in warehouses:
            self.tree.insert("", tk.END, values=(w['id'], w['name']))

    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите склад")
            return None
        return int(self.tree.item(sel[0])['values'][0])

    def _add(self):
        name = simpledialog.askstring("Новый склад", "Наименование:")
        if not name:
            return
        try:
            warehouse_add(name=name)
            self._refresh()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _edit(self):
        wh_id = self._get_selected_id()
        if not wh_id:
            return
        # Получаем текущее имя
        warehouses = warehouse_list()
        current = next((w for w in warehouses if w['id'] == wh_id), None)
        if not current:
            return

        name = simpledialog.askstring("Редактировать", "Наименование:", initialvalue=current['name'])
        if name is None:
            return
        try:
            warehouse_update(wh_id, name=name)
            self._refresh()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _delete(self):
        wh_id = self._get_selected_id()
        if not wh_id:
            return
        if messagebox.askyesno("Подтверждение", "Удалить склад?"):
            try:
                warehouse_delete(wh_id)
                self._refresh()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))