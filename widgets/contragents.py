import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from db_scripts import contragent_list, contragent_add, contragent_list_filter, contragent_update, contragent_delete
from enumerates import CONTRAGENT_TYPES


class ContragentsWidget:
    def __init__(self, parent, mode: str):
        self.mode = mode        
        self.parent = parent
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        title = 'Поставщики' if self.mode == 'buy' else 'Покупатели'
        ttk.Label(self.parent, text=title).pack(pady=4)
        cols = ('Код', 'Имя')
        self.tv = ttk.Treeview(self.parent, columns=cols, show='headings')
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.pack(fill=tk.BOTH, expand=1)
        
        
        ttk.Button(self.parent, text='Добавить', command=self._add).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.parent, text="Редактировать", command=self._edit).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.parent, text="Удалить", command=self._delete).pack(side=tk.LEFT, padx=5)
        
        self.tv.bind("<Double-1>", lambda e: self._edit())

    def _get_expected_type(self):
        return CONTRAGENT_TYPES[0] if self.mode == 'buy' else CONTRAGENT_TYPES[1]
    
    def _get_selected_id(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите контрагента")
            return None
        return int(self.tv.item(sel[0])['values'][0])

    def _refresh(self):
        con_type = self._get_expected_type()
        for i in self.tv.get_children():
            self.tv.delete(i)
        for row in contragent_list_filter(con_type):
            self.tv.insert('', 'end', values=(row['id'], row['name'], row['type']))

    def _add(self):
        name = simpledialog.askstring(title='Контрагент',
                                      prompt='Название:')
        if not name:
            return
        tp = CONTRAGENT_TYPES[0] if self.mode == 'buy' else CONTRAGENT_TYPES[1]
        try:
            contragent_add(name, tp)
            self._refresh()
        except Exception as e:
            messagebox.showerror('Ошибка', str(e))
            
    def _edit(self):
        contr_id = self._get_selected_id()
        if not contr_id:
            return
        # Получаем текущие данные
        all_contr = contragent_list()
        current = next((c for c in all_contr if c['id'] == contr_id), None)
        if not current:
            return

        name = simpledialog.askstring("Редактировать", "Наименование:", initialvalue=current['name'])
        if name is None:
            return
        try:
            # ВАЖНО: тип НЕ МЕНЯЕМ! Сохраняем тот же
            contragent_update(contr_id, name=name, type_=current['type'])
            self._refresh()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _delete(self):
        contr_id = self._get_selected_id()
        if not contr_id:
            return
        if messagebox.askyesno("Подтверждение", "Удалить контрагента?"):
            try:
                contragent_delete(contr_id)
                self._refresh()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))