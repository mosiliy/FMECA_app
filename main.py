"""
Точка входа в приложение FMEA/FMECA Analysis Tool.
"""

import tkinter as tk
from gui import FMEAApp
from database import Database
import sys


def test_database_structure():
    """Тестирование структуры данных из БД."""
    print("=" * 50)
    print("ДИАГНОСТИКА СТРУКТУРЫ БД")
    print("=" * 50)
    
    db = Database()
    data = db.get_all_failures()
    
    print(f"\nВсего записей: {len(data)}")
    
    if data:
        print(f"Количество полей в записи: {len(data[0])}")
        print(f"\nПервая запись:")
        print(data[0])
        
        print(f"\nОжидаемые поля (12):")
        fields = [
            'ID', 'Система', 'Подсистема', 'Компонент', 'Категория',
            'Вид отказа', 'Причина', 'Последствие',
            'S', 'O', 'D', 'RPN'
        ]
        for i, field in enumerate(fields):
            value = data[0][i] if i < len(data[0]) else "ОТСУТСТВУЕТ"
            print(f"  {i}: {field} = {value}")
    
    db.close()
    print("=" * 50)


def main():
    """Главная функция запуска приложения."""
    try:
        # Диагностика (закомментируйте после проверки)
        # test_database_structure()
        
        # Создание главного окна
        root = tk.Tk()
        
        # Инициализация приложения
        app = FMEAApp(root)
        
        # Запуск главного цикла
        app.run()
        
    except Exception as e:
        import traceback
        error_msg = f"Критическая ошибка при запуске приложения:\n\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        
        # Показать окно с ошибкой
        root = tk.Tk()
        root.withdraw()
        from tkinter import messagebox
        messagebox.showerror("Критическая ошибка", error_msg)
        
        sys.exit(1)


if __name__ == "__main__":
    main()