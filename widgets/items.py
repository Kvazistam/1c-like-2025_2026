import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from db_scripts import item_list, item_add, item_delete, item_update, item_get
from widgets.dialogs import ItemDialog


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
        ttk.Button(btn, text='Редактировать', command=self._edit).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(btn, text='Удалить',
                   command=self._delete).pack(side=tk.LEFT)
        
        self.tv.bind("<Double-1>", lambda e: self._edit())

        self._refresh()

    def _refresh(self):
        for i in self.tv.get_children():
            self.tv.delete(i)
        for row in item_list():
            self.tv.insert('', 'end', values=(row['name'], row['id'],
                                              row['category']))

    def _get_selected_item(self):
        sel = self.tv.selection()
        if not sel:
            return None
        item = self.tv.item(sel[0])
        return {
            'id': item['values'][1],
            'name': item['values'][0],
            'category': item['values'][2] or None
        }

    def _add(self):
        d = ItemDialog(self.frame)
        self.frame.wait_window(d)
        if d.res:
            try:
                item_add(**d.res)
                self._refresh()
            except Exception as e:
                messagebox.showerror('Ошибка', str(
                    f"Не удалось вставить товар {d.res.name}"))

    def _edit(self):
        selected = self._get_selected_item()
        if not selected:
            messagebox.showwarning(
                "Внимание", "Выберите товар для редактирования")
            return

        # Получаем полные данные (включая buy_price) — item_list() их возвращает
        full_data = item_get(int(selected["id"]))
        if not full_data:
            messagebox.showerror("Ошибка", "Товар не найден")
            return
        item_data = {
            "name": full_data.name,
            "id": full_data.id,
            "category": full_data.category,
            "buy_price": full_data.buy_price,
            "image": full_data.image
        }
        d = ItemDialog(self.frame, item_id=item_data["id"], item_data=item_data)
        self.frame.wait_window(d)
        if d.res:
            try:
                item_update(selected['id'], **d.res)
                self._refresh()
            except Exception as e:
                messagebox.showerror(
                    'Ошибка', f"Не удалось обновить товар:\n{e}")

    def _delete(self):
        sel = self.tv.selection()
        if not sel:
            return
        iid = int(self.tv.item(sel[0])['values'][1])
        try:
            item_delete(iid)
            self._refresh()
        except Exception as e:
            messagebox.showerror('Ошибка', str(e))
