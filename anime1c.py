#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
from app_style import apply_1c_style
from widgets import ItemsWidget, ContragentsWidget, WarehousesWidget, DocsWidget, StockWidget

class App:
    def __init__(self, master: tk.Tk, role: str):
        self.role = role          # 'buy' | 'sell' | 'admin'
        self.master = master
        master.title('Anime1C – учёт фигурок')
        master.geometry('1100x650')
        apply_1c_style(master)

        self.current_sub = 'buy' if role != 'sell' else 'sell'

        
        self._build_sub_tabs()   # радио-переключатели
        self._build_toolbar()    # наша новая панель
        self._build_content()    # фрейм для виджетов
        
        self._show_start_page()   # что показать сразу после входа

    def _build_toolbar(self):
        """Панель-кнопки под переключателем подсистем."""
        # контейнер под всё
        self.toolbar = ttk.Frame(self.master)
        self.toolbar.pack(side=tk.TOP, fill=tk.X, padx=4, pady=2)

        # кнопки будем хранить, чтобы потом легко пересоздавать
        self.btn_map = {}
        self._rebuild_toolbar_buttons()

    def _rebuild_toolbar_buttons(self):
        """Удаляем старые кнопки и создаём новые под текущий режим."""
        # очистить старые
        for w in self.toolbar.winfo_children():
            w.destroy()
        self.btn_map.clear()

        style = ttk.Style()
        style.configure('Tool.TButton', padding=6)

        # ---------- общие кнопки ----------
        self._add_tool_btn('Номенклатура', 'items')
        self._add_tool_btn('Склады',      'warehouses')
        self._add_tool_btn('Остатки',     'остатки')

        # ---------- режим-специфичные ----------
        if self.current_sub == 'buy':
            self._add_tool_btn('Поставщики', 'contragents')
            self._add_tool_btn('Приход',     'приход')
        else:  # sell
            self._add_tool_btn('Покупатели', 'contragents')
            self._add_tool_btn('Расход',     'расход')

        # можно добавить ещё «Цены» или что нужно
        # self._add_tool_btn('Цены', 'prices')
    
    def _add_tool_btn(self, label: str, widget_tag: str):
        """Создаёт кнопку и сразу вешает команду."""
        btn = ttk.Button(self.toolbar, text=label, style='Tool.TButton',
                        command=lambda: self._open_widget(widget_tag))
        btn.pack(side=tk.LEFT, padx=2)
        self.btn_map[widget_tag] = btn
    # ---------------- вкладки «Закупки / Продажи» ----------------
    def _build_sub_tabs(self):
        self.tab_frame = ttk.Frame(self.master)
        self.tab_frame.pack(side=tk.TOP, fill=tk.X, padx=4, pady=2)

        self.div_var = tk.StringVar(value=self.current_sub)
        style = ttk.Style()
        style.configure('Sub.TRadiobutton', relief='raised', padding=6)
        style.map('Sub.TRadiobutton',
                  background=[('selected', '#FFE7A2'),
                              ('!selected', '#F0F0F0'),
                              ('active', '#E0E0E0')])

        for txt, val in (('Закупки', 'buy'), ('Продажи', 'sell')):
            rb = ttk.Radiobutton(self.tab_frame, text=txt, variable=self.div_var,
                                 value=val, command=self._on_div_change,
                                 style='Sub.TRadiobutton')
            rb.pack(side=tk.LEFT, padx=2)
            if self.role == 'buy' and val == 'sell':
                rb.state(['disabled'])
            if self.role == 'sell' and val == 'buy':
                rb.state(['disabled'])


    # ---------------- обработчики ----------------
    def _on_div_change(self):
        self.current_sub = self.div_var.get()
        self._rebuild_nav_tree()
        self._clear_content()

    
    # ---------------- контейнер для виджетов ----------------
    def _build_content(self):
        self.content = ttk.Frame(self.master)
        self.content.pack(fill=tk.BOTH, expand=1)

    # ---------------- переключение подсистем ----------------
    def _on_div_change(self):
        self.current_sub = self.div_var.get()
        self._rebuild_toolbar_buttons()  # <-- пересобрать кнопки
        self._clear_content()
        self._show_start_page()

    # ---------------- очистить правую часть ----------------
    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    # ---------------- стартовый экран ----------------
    def _show_start_page(self):
        """Что показывать сразу после входа или после смены режима."""
        if self.current_sub == 'buy':
            self._open_widget('items')     # можно заменить на любой нужный
        else:
            self._open_widget('items')

    # ---------------- открыть нужный виджет ----------------
    def _open_widget(self, tag: str):
        self._clear_content()
        if tag in ('items', "предметы"):
            ItemsWidget(self.content)
        elif tag == 'contragents':
            ContragentsWidget(self.content, self.current_sub)
        elif tag == 'warehouses':
            WarehousesWidget(self.content)
        elif tag in ('приход', 'расход'):
            DocsWidget(self.content, tag)
        elif tag == 'остатки':
            StockWidget(self.content)

    # ---------------- утилиты ----------------
    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()