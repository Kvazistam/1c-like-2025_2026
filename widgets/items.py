import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from db_scripts import item_list, item_add, item_delete, Item
from widgets.dialogs import ItemDialog   # ваш старый ItemDialog можно оставить тут же

class ItemsWidget:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=1)

        ttk.Label(self.frame, text='Номенклатура товаров').pack(pady=4)

        cols = ('Название товара', "Код", 'Категория')
        self.tv = ttk.Treeview(self.frame, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
            self.tv.column(c, width=120)
        self.tv.pack(fill=tk.BOTH, expand=1)

        btn = ttk.Frame(self.frame)
        btn.pack(fill=tk.X)
        ttk.Button(btn, text='Добавить', command=self._add).pack(side=tk.LEFT)
        ttk.Button(btn, text='Удалить', command=self._delete).pack(side=tk.LEFT)

        self._refresh()

    def _refresh(self):
        for i in self.tv.get_children():
            self.tv.delete(i)
        for row in item_list():
            self.tv.insert('', 'end', values=( row['name'],row['id'],
                                              row['category']))

    def _add(self):
        d = ItemDialog(self.frame)
        self.frame.wait_window(d)
        if d.res:
            try:
                item_add(**d.res)
                self._refresh()
            except Exception as e:
                messagebox.showerror('Ошибка', str(f"Не удалось вставить товар {d.res.name}"))

    def _delete(self):
        sel = self.tv.selection()
        if not sel:
            return
        print(sel)
        iid = int(self.tv.item(sel[0])['values'][1])
        try:
            item_delete(iid)
            self._refresh()
        except Exception as e:
            messagebox.showerror('Ошибка', str(e))