import os

from gui import Application

from config import SETTINGS
#устанавливаем переменные окружения из словаря SETTINGS
for key, value in SETTINGS.items():
    os.environ[key] = value

if __name__ == '__main__':
    root = Application()
    root.mainloop()