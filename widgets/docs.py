import tkinter as tk
from tkinter import ttk
from db_scripts import doc_list

from widgets.dialogs import DocDialog
class DocsWidget:
    def __init__(self, parent, doc_type: str):
        self.parent = parent
        self.doc_type = doc_type
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        ttk.Label(self.parent, text=f'Документы «{self.doc_type}»').pack(pady=4)
        cols = ('id', 'date', 'contragent', 'warehouse', 'posted')
        self.tv = ttk.Treeview(self.parent, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.pack(fill=tk.BOTH, expand=1)
        ttk.Button(self.parent, text='Создать',
                   command=self._create).pack()
        self.tv.bind('<Double-1>', lambda e: self._edit())

    def _refresh(self):
        for i in self.tv.get_children():
            self.tv.delete(i)
        for row in doc_list(self.doc_type):
            self.tv.insert('', 'end', values=(
                row['id'], row['date'], row['contragent'] or '-',
                row['warehouse'], 'Да' if row['posted'] else 'Нет'))

    def _create(self):
        DocDialog(self.parent, self.doc_type, on_close=self._refresh)

    def _edit(self):
        sel = self.tv.selection()
        if not sel:
            return
        doc_id = int(self.tv.item(sel[0])['values'][0])
        DocDialog(self.parent, None, doc_id, on_close=self._refresh)


