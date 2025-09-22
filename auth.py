import tkinter as tk
from tkinter import ttk, messagebox
from db_scripts import user_check   # ваша функция
from anime1c import App             # главное окно

class AuthWindow:
    def __init__(self, master: tk.Tk):
        self.master = master
        master.title('Авторизация – Anime Store')
        master.geometry('300x150')
        master.resizable(False, False)

        ttk.Label(master, text='Логин').pack(pady=5)
        self.login = ttk.Entry(master)
        self.login.pack()

        ttk.Label(master, text='Пароль').pack(pady=5)
        self.password = ttk.Entry(master, show='*')
        self.password.pack()

        ttk.Button(master, text='Войти', command=self.try_login).pack(pady=15)

    def try_login(self):
        ok, role = user_check(self.login.get(), self.password.get())
        if not ok:
            messagebox.showerror('Ошибка', 'Неверный логин/пароль')
            return

        # ----- успешно -----
        self.master.destroy()          # закрываем форму входа
        main_root = tk.Tk()            # создаём новый корень
        App(main_root, role)           # передаём роль в App
        main_root.mainloop()