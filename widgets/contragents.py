import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from db_scripts import contragent_list, contragent_add

class ContragentsWidget:
    def __init__(self, parent, sub: str):
        self.sub = sub          # 'buy' -> поставщики, 'sell' -> покупатели
        self.parent = parent
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        title = 'Поставщики' if self.sub == 'buy' else 'Покупатели'
        ttk.Label(self.parent, text=title).pack(pady=4)
        cols = ('id', 'name', 'type')
        self.tv = ttk.Treeview(self.parent, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.pack(fill=tk.BOTH, expand=1)
        ttk.Button(self.parent, text='Добавить', command=self._add).pack()

    def _refresh(self):
        for i in self.tv.get_children():
            self.tv.delete(i)
        for row in contragent_list():
            self.tv.insert('', 'end', values=(row['id'], row['name'], row['type']))

    def _add(self):
        name = simpledialog.askstring(title='Контрагент',
                                      prompt='Название:')
        if not name:
            return
        tp = 'supplier' if self.sub == 'buy' else 'customer'
        try:
            contragent_add(name, tp)
            self._refresh()
        except Exception as e:
            messagebox.showerror('Ошибка', str(e))