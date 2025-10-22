import tkinter as tk
from tkinter import ttk, messagebox
from db_scripts import unit_list_all, unit_add, unit_update, unit_delete, unit_get
from enumerates import ITEM_TYPES


class UnitDialog(tk.Toplevel):
    def __init__(self, parent, title="Единица измерения", data=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()

        self.result = None

        ttk.Label(self, text="Название:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Label(self, text="Кратность:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Label(self, text="Вес (кг):").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Label(self, text="Объём (л):").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        ttk.Label(self, text="Тип товаров:").grid(row=4, column=0, sticky="e", padx=5, pady=5)

        self.name_var = tk.StringVar(value=data['name'] if data else "")
        self.ratio_var = tk.StringVar(value=str(data['ratio_to_base']) if data else "1")
        self.weight_var = tk.StringVar(value=str(data['weight']) if data and data['weight'] else "")
        self.volume_var = tk.StringVar(value=str(data['volume']) if data and data['volume'] else "")
        self.applicable_var = tk.StringVar(value=data['applicable_to'] if data and 'applicable_to' in data else ITEM_TYPES[0])

        ttk.Entry(self, textvariable=self.name_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        ttk.Entry(self, textvariable=self.ratio_var, width=30).grid(row=1, column=1, padx=5, pady=5)
        ttk.Entry(self, textvariable=self.weight_var, width=30).grid(row=2, column=1, padx=5, pady=5)
        ttk.Entry(self, textvariable=self.volume_var, width=30).grid(row=3, column=1, padx=5, pady=5)

        self.combo = ttk.Combobox(self, textvariable=self.applicable_var, values=ITEM_TYPES, state="readonly", width=27)
        self.combo.grid(row=4, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Сохранить", command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self.destroy())

        self.transient(parent)
        self.wait_window(self)

    def _on_ok(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Название обязательно")
            return
        try:
            ratio = float(self.ratio_var.get())
            weight = float(self.weight_var.get()) if self.weight_var.get() else None
            volume = float(self.volume_var.get()) if self.volume_var.get() else None
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректные числовые значения")
            return

        self.result = {
            "name": name,
            "ratio": ratio,
            "weight": weight,
            "volume": volume,
            "applicable_to": self.applicable_var.get()
        }
        self.destroy()


class UnitsWidget:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(self.frame, text="Единицы измерения").pack(pady=4)

        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(btn_frame, text="Добавить", command=self._add).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Редактировать", command=self._edit).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self._delete).pack(side=tk.LEFT, padx=5)

        cols = ("ID", "Название", "Кратность", "Вес (кг)", "Объём (л)", "Тип товаров")
        self.tree = ttk.Treeview(self.frame, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.column("Название", width=150)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<Double-1>", lambda e: self._edit())

        self._refresh()

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for u in unit_list_all():
            u_full = unit_get(u['id'])
            self.tree.insert("", tk.END, values=(
                u['id'],
                u['name'],
                f"{u['ratio_to_base']:.4g}",
                f"{u['weight'] or ''}",
                f"{u['volume'] or ''}",
                u_full.get('applicable_to', '')
            ))

    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите единицу измерения")
            return None
        return int(self.tree.item(sel[0])['values'][0])

    def _add(self):
        dlg = UnitDialog(self.frame, title="Добавить единицу измерения")
        if dlg.result:
            try:
                unit_add(
                    dlg.result['name'],
                    dlg.result['ratio'],
                    dlg.result['weight'],
                    dlg.result['volume'],
                    dlg.result['applicable_to']
                )
                self._refresh()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def _edit(self):
        unit_id = self._get_selected_id()
        if not unit_id:
            return
        current = unit_get(unit_id)
        if not current:
            return

        dlg = UnitDialog(self.frame, title="Редактировать единицу", data=current)
        if dlg.result:
            try:
                unit_update(
                    unit_id,
                    dlg.result['name'],
                    dlg.result['ratio'],
                    dlg.result['weight'],
                    dlg.result['volume']
                )
                # Обновим applicable_to вручную, если изменилось
                from db_scripts.db_session import get_session
                with get_session() as s:
                    u = s.get(type(current), unit_id)
                    if u:
                        u.applicable_to = dlg.result['applicable_to']
                        s.commit()

                self._refresh()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def _delete(self):
        unit_id = self._get_selected_id()
        if not unit_id:
            return
        if messagebox.askyesno("Подтверждение", "Удалить единицу измерения?"):
            try:
                unit_delete(unit_id)
                self._refresh()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Невозможно удалить: {e}")
