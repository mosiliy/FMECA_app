"""
Пути к ресурсам и данным приложения.
Поддержка запуска из исходников и из собранного .exe (PyInstaller).
"""

import sys
from pathlib import Path


def is_frozen() -> bool:
    """Запуск из собранного исполняемого файла."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_app_dir() -> Path:
    """
    Каталог приложения (рядом с .exe или корень проекта).
    Сюда пишутся data/, экспорты пользователя.
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_resource_dir() -> Path:
    """
    Каталог встроенных ресурсов (шрифты и т.д.).
    В .exe — временная распаковка PyInstaller (_MEIPASS).
    """
    if is_frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def get_data_dir() -> Path:
    """Каталог данных пользователя (создаётся при необходимости)."""
    data_dir = get_app_dir() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_database_path() -> Path:
    """Путь к файлу SQLite."""
    return get_data_dir() / "fmea.db"


def get_fonts_dir() -> Path:
    """Каталог шрифтов для PDF."""
    return get_resource_dir() / "fonts"
