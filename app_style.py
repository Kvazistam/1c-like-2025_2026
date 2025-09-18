from tkinter import ttk
import tkinter as tk

def apply_1c_style(root):
    style = ttk.Style(root)
    style.theme_use('clam')

    # цвета 1С
    bg_main   = '#F4F4F4'
    bg_panel  = '#E0E0E0'
    bg_sel    = '#FFE7A2'
    fg_main   = '#000000'
    fg_gray   = '#606060'

    style.configure('TFrame', background=bg_main)
    style.configure('TLabelframe', background=bg_main, foreground=fg_gray)
    style.configure('TButton', background=bg_panel, relief='flat', padding=4)
    style.map('TButton', background=[('active', bg_sel)])
    style.configure('Treeview', fieldbackground=bg_main, background=bg_main,
                    foreground=fg_main, rowheight=24)
    style.map('Treeview', background=[('selected', bg_sel)])
    root.option_add('*Font', ('Arial', 9))
    
    