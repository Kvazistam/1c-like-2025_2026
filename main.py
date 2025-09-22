#!/usr/bin/env python3
import tkinter as tk
from auth import AuthWindow

if __name__ == '__main__':
    root = tk.Tk()
    AuthWindow(root)
    root.mainloop()