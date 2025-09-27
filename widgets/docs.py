import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from db_scripts import doc_list, doc_delete
from db_scripts.db_docs import doc_unpost
from enumerates import DOC_TYPES
from widgets.dialogs import DocDialog
class DocsWidget:
    def __init__(self, parent, doc_type: str):
        self.parent = parent
        self.doc_type = doc_type
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        ttk.Label(self.parent, text=f'Документы «{self.doc_type}»').pack(pady=4)
        contr = 'Контрагент' if self.doc_type == DOC_TYPES[0] else "Покупатель"
        cols = ('Код', 'Дата', contr, 'Склад', 'Проведен')
        self.tv = ttk.Treeview(self.parent, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.pack(fill=tk.BOTH, expand=1)

        btn_frame = ttk.Frame(self.parent)
        btn_frame.pack(fill=tk.X, pady=4)
        ttk.Button(btn_frame, text='Создать', command=self._create).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text='Удалить', command=self._delete).pack(side=tk.LEFT, padx=2)  
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

        DocDialog(self.parent, self.doc_type, doc_id=doc_id, on_close=self._refresh)
        
    def _delete(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите документ для удаления")
            return
            
        
        values = self.tv.item(sel[0])['values']
        doc_id = int(values[0])
        posted = values[4]  # колонка 'posted'
        if posted == 'Да':
            try:
                doc_unpost(doc_id)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось отменить проводку:\n{e}")
                return
            
        
        if messagebox.askyesno("Подтверждение", "Удалить документ?"):
            try:
                doc_delete(doc_id)
                self._refresh()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))


