import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from db_scripts import warehouse_list, warehouse_add

class WarehousesWidget:
    def __init__(self, parent):
        self.parent = parent
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        ttk.Label(self.parent, text='Склады').pack(pady=4)
        cols = ('id', 'name')
        self.tv = ttk.Treeview(self.parent, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.pack(fill=tk.BOTH, expand=1)
        ttk.Button(self.parent, text='Добавить', command=self._add).pack()

    def _refresh(self):
        for i in self.tv.get_children():
            self.tv.delete(i)
        for row in warehouse_list():
            self.tv.insert('', 'end', values=(row['id'], row['name']))

    def _add(self):
        name = simpledialog.askstring('Склад', 'Название:')
        if name:
            try:
                warehouse_add(name)
                self._refresh()
            except Exception as e:
                messagebox.showerror('Ошибка', str(e))