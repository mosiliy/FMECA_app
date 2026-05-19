"""
Модуль для работы с базой данных SQLite.
Расширенная модель данных с поддержкой справочников FMEA.
"""

import sqlite3
from typing import List, Tuple, Optional, Dict
import os
from model import FMEAModel


class Database:
    """Класс для управления базой данных FMEA с расширенными справочниками."""
    
    FMECA_LOOKUP_DEFAULTS = {
        "function": [
            "Обработка вычислительных задач",
            "Хранение оперативных данных",
            "Долговременное хранение данных",
            "Стабилизация электропитания",
            "Передача сетевого трафика",
            "Охлаждение и теплоотвод",
        ],
        "effect": [
            "Снижение производительности",
            "Рост задержек",
            "Сбой вычислительных модулей",
            "Потеря доступности подсистемы",
            "Риск потери данных",
            "Срыв SLA/критичного сервиса",
        ],
        "mission_phase": [
            "Проектирование",
            "Интеграция",
            "Испытания",
            "Эксплуатация",
            "Техническое обслуживание",
        ],
        "operating_mode": [
            "Номинальный",
            "Пиковая нагрузка",
            "Резервный",
            "Деградированный",
            "Пуск/останов",
        ],
        "action": [
            "Замена компонента",
            "Плановое техническое обслуживание",
            "Обновление прошивки/ПО",
            "Усиление мониторинга",
            "Изменение режима эксплуатации",
        ],
        "owner": [
            "Инженер по надежности",
            "Системный инженер",
            "Инженер эксплуатации",
            "DBA",
            "Сетевой инженер",
        ],
    }
    
    FMECA_LOOKUP_LABELS = {
        "function": "Функции компонентов",
        "effect": "Эффекты",
        "mission_phase": "Фазы миссии",
        "operating_mode": "Режимы работы",
        "action": "Рекомендуемые меры",
        "owner": "Ответственные",
    }
    
    FAILURES_TABLE_MIGRATIONS = [
        ("function_text", "TEXT"),
        ("local_effect", "TEXT"),
        ("next_higher_effect", "TEXT"),
        ("end_effect", "TEXT"),
        ("current_controls", "TEXT"),
        ("recommended_actions", "TEXT"),
        ("action_owner", "TEXT"),
        ("due_date", "TEXT"),
        ("action_status", "TEXT"),
        ("failure_rate_lambda", "REAL DEFAULT 0"),
        ("mode_ratio_alpha", "REAL DEFAULT 0"),
        ("conditional_prob_beta", "REAL DEFAULT 0"),
        ("mission_time_t", "REAL DEFAULT 0"),
        ("mission_phase", "TEXT"),
        ("operating_mode", "TEXT"),
        ("is_single_point", "INTEGER DEFAULT 0"),
        ("is_latent", "INTEGER DEFAULT 0"),
        ("is_common_cause", "INTEGER DEFAULT 0"),
        ("mil_criticality", "REAL DEFAULT 0"),
        ("residual_severity", "INTEGER DEFAULT 0"),
        ("residual_occurrence", "INTEGER DEFAULT 0"),
        ("residual_detection", "INTEGER DEFAULT 0"),
        ("residual_rpn", "INTEGER DEFAULT 0"),
    ]
    
    def __init__(self, db_path: str = "data/fmea.db"):
        """Инициализация подключения к БД."""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self._create_tables()
        self._populate_default_data()
        self._populate_fmeca_lookups()
    
    def _create_tables(self):
        """Создание расширенной схемы БД."""
        
        # 1. Справочник категорий компонентов
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS component_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            )
        """)
        
        # 2. Компоненты с привязкой к категории
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system TEXT NOT NULL,
                subsystem TEXT,
                component TEXT NOT NULL,
                category_id INTEGER,
                description TEXT,
                FOREIGN KEY (category_id) REFERENCES component_categories(id)
            )
        """)
        
        # 3. Справочник типов отказов
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS failure_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                default_severity INTEGER CHECK(default_severity BETWEEN 1 AND 10),
                default_occurrence INTEGER CHECK(default_occurrence BETWEEN 1 AND 10),
                default_detection INTEGER CHECK(default_detection BETWEEN 1 AND 10)
            )
        """)
        
        # 4. Связь категория компонента ↔ тип отказа
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS category_failure_type (
                category_id INTEGER,
                failure_type_id INTEGER,
                PRIMARY KEY (category_id, failure_type_id),
                FOREIGN KEY (category_id) REFERENCES component_categories(id),
                FOREIGN KEY (failure_type_id) REFERENCES failure_types(id)
            )
        """)
        
        # 5. Справочник причин отказов
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS failure_causes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT
            )
        """)
        
        # 6. Связь тип отказа ↔ причина
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS failure_type_cause (
                failure_type_id INTEGER,
                cause_id INTEGER,
                PRIMARY KEY (failure_type_id, cause_id),
                FOREIGN KEY (failure_type_id) REFERENCES failure_types(id),
                FOREIGN KEY (cause_id) REFERENCES failure_causes(id)
            )
        """)
        
        # 7. Справочник последствий отказов
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS failure_effects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT
            )
        """)
        
        # 8. Связь тип отказа ↔ последствие
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS failure_type_effect (
                failure_type_id INTEGER,
                effect_id INTEGER,
                PRIMARY KEY (failure_type_id, effect_id),
                FOREIGN KEY (failure_type_id) REFERENCES failure_types(id),
                FOREIGN KEY (effect_id) REFERENCES failure_effects(id)
            )
        """)
        
        # 9. Основная таблица отказов (обновлённая)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_id INTEGER NOT NULL,
                failure_type_id INTEGER,
                cause_id INTEGER,
                effect_id INTEGER,
                failure_mode TEXT NOT NULL,
                failure_cause TEXT NOT NULL,
                failure_effect TEXT NOT NULL,
                severity INTEGER CHECK(severity BETWEEN 1 AND 10),
                occurrence INTEGER CHECK(occurrence BETWEEN 1 AND 10),
                detection INTEGER CHECK(detection BETWEEN 1 AND 10),
                rpn INTEGER,
                FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE,
                FOREIGN KEY (failure_type_id) REFERENCES failure_types(id),
                FOREIGN KEY (cause_id) REFERENCES failure_causes(id),
                FOREIGN KEY (effect_id) REFERENCES failure_effects(id)
            )
        """)
        
        # 10. Справочники расширенных полей FMECA
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fmeca_lookup_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                name TEXT NOT NULL,
                UNIQUE(domain, name)
            )
        """)
        
        self.connection.commit()
        self._migrate_failures_table()
    
    def _get_table_columns(self, table_name: str) -> set:
        """Получение списка существующих колонок таблицы."""
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        return {row[1] for row in self.cursor.fetchall()}
    
    def _migrate_failures_table(self):
        """
        Add-only миграция таблицы failures.
        Без удаления/пересоздания таблиц для совместимости со старыми БД.
        """
        existing_columns = self._get_table_columns("failures")
        
        for column_name, column_type in self.FAILURES_TABLE_MIGRATIONS:
            if column_name in existing_columns:
                continue
            
            self.cursor.execute(
                f"ALTER TABLE failures ADD COLUMN {column_name} {column_type}"
            )
        
        self.connection.commit()
    
    def _populate_default_data(self):
        """Заполнение справочников данными по умолчанию."""
        
        # Проверка: если уже есть данные, не добавляем
        self.cursor.execute("SELECT COUNT(*) FROM component_categories")
        if self.cursor.fetchone()[0] > 0:
            return
        
        # Категории компонентов
        categories = [
            ("Вычислительная система", "Комплексная система обработки данных"),
            ("Сервер", "Серверное оборудование"),
            ("Процессор", "Центральный процессор (CPU)"),
            ("Оперативная память", "RAM модули"),
            ("Накопитель", "HDD/SSD/NVMe накопители"),
            ("Блок питания", "Источник питания"),
            ("Материнская плата", "Системная плата"),
            ("Сетевое оборудование", "Коммутаторы, маршрутизаторы"),
            ("Система охлаждения", "Вентиляторы, радиаторы"),
        ]
        
        for cat_name, cat_desc in categories:
            self.cursor.execute(
                "INSERT INTO component_categories (name, description) VALUES (?, ?)",
                (cat_name, cat_desc)
            )
        
        # Типы отказов
        failure_types = [
            ("Перегрев", "Превышение допустимой температуры", 7, 4, 3),
            ("Ошибка чтения/записи", "Ошибки при операциях с данными", 8, 5, 4),
            ("Полный отказ", "Полная неработоспособность компонента", 10, 2, 7),
            ("Деградация производительности", "Снижение параметров работы", 6, 5, 3),
            ("Скачки напряжения", "Нестабильность питания", 9, 3, 4),
            ("Физическое повреждение", "Механическое разрушение", 9, 2, 8),
            ("Программный сбой", "Ошибка ПО или микрокода", 5, 6, 5),
        ]
        
        for ft_name, ft_desc, s, o, d in failure_types:
            self.cursor.execute(
                """INSERT INTO failure_types 
                   (name, description, default_severity, default_occurrence, default_detection)
                   VALUES (?, ?, ?, ?, ?)""",
                (ft_name, ft_desc, s, o, d)
            )
        
        # Причины отказов
        causes = [
            ("Отказ системы охлаждения", "Выход из строя вентиляторов"),
            ("Деградация ячеек памяти", "Износ физических носителей"),
            ("Исчерпание ресурса перезаписи", "Достижение лимита циклов записи"),
            ("Деградация конденсаторов", "Старение электролитических компонентов"),
            ("Статическое электричество", "ESD повреждение"),
            ("Перегрузка по току", "Превышение номинальной нагрузки"),
            ("Ошибка прошивки", "Дефект микрокода"),
            ("Вибрация и удары", "Механическое воздействие"),
        ]
        
        for cause_name, cause_desc in causes:
            self.cursor.execute(
                "INSERT INTO failure_causes (name, description) VALUES (?, ?)",
                (cause_name, cause_desc)
            )
        
        # Последствия отказов
        effects = [
            ("Снижение производительности", "Деградация скорости обработки"),
            ("Аварийное отключение", "Экстренное выключение системы"),
            ("Потеря данных", "Утрата информации"),
            ("Сбой приложений", "Зависание или крах ПО"),
            ("Повреждение других компонентов", "Каскадный отказ"),
            ("Неработоспособность системы", "Полная остановка"),
            ("Нестабильная работа", "Периодические сбои"),
        ]
        
        for effect_name, effect_desc in effects:
            self.cursor.execute(
                "INSERT INTO failure_effects (name, description) VALUES (?, ?)",
                (effect_name, effect_desc)
            )
        
        # Связи категория ↔ тип отказа (примеры)
        # Процессор → Перегрев, Деградация
        self.cursor.execute(
            "INSERT INTO category_failure_type VALUES (3, 1), (3, 4)"
        )
        # Память → Ошибка чтения/записи, Полный отказ
        self.cursor.execute(
            "INSERT INTO category_failure_type VALUES (4, 2), (4, 3)"
        )
        # Накопитель → Полный отказ, Ошибка чтения/записи
        self.cursor.execute(
            "INSERT INTO category_failure_type VALUES (5, 3), (5, 2)"
        )
        # Блок питания → Скачки напряжения
        self.cursor.execute(
            "INSERT INTO category_failure_type VALUES (6, 5)"
        )
        
        # Связи тип отказа ↔ причина (примеры)
        # Перегрев → Отказ охлаждения
        self.cursor.execute(
            "INSERT INTO failure_type_cause VALUES (1, 1)"
        )
        # Ошибка чтения/записи → Деградация ячеек
        self.cursor.execute(
            "INSERT INTO failure_type_cause VALUES (2, 2)"
        )
        # Полный отказ → Исчерпание ресурса
        self.cursor.execute(
            "INSERT INTO failure_type_cause VALUES (3, 3)"
        )
        # Скачки напряжения → Деградация конденсаторов
        self.cursor.execute(
            "INSERT INTO failure_type_cause VALUES (5, 4)"
        )
        
        # Связи тип отказа ↔ последствие (примеры)
        # Перегрев → Снижение производительности, Аварийное отключение
        self.cursor.execute(
            "INSERT INTO failure_type_effect VALUES (1, 1), (1, 2)"
        )
        # Ошибка чтения/записи → Потеря данных, Сбой приложений
        self.cursor.execute(
            "INSERT INTO failure_type_effect VALUES (2, 3), (2, 4)"
        )
        # Полный отказ → Неработоспособность системы
        self.cursor.execute(
            "INSERT INTO failure_type_effect VALUES (3, 6)"
        )
        # Скачки напряжения → Повреждение компонентов
        self.cursor.execute(
            "INSERT INTO failure_type_effect VALUES (5, 5)"
        )
        
        self.connection.commit()
    
    def _populate_fmeca_lookups(self):
        """Заполнение справочников расширенных полей FMECA значениями по умолчанию."""
        for domain, values in self.FMECA_LOOKUP_DEFAULTS.items():
            self.cursor.execute(
                "SELECT COUNT(*) FROM fmeca_lookup_values WHERE domain = ?",
                (domain,),
            )
            if self.cursor.fetchone()[0] > 0:
                continue
            for name in values:
                self.ensure_fmeca_lookup_value(domain, name)
    
    # ===== СПРАВОЧНИКИ РАСШИРЕННЫХ ПОЛЕЙ FMECA =====
    
    def get_fmeca_lookup_values(self, domain: str) -> List[str]:
        """Получение значений справочника расширенного поля."""
        return [name for _, name in self.get_all_fmeca_lookups(domain)]
    
    def get_all_fmeca_lookups(self, domain: str) -> List[Tuple[int, str]]:
        """Получение всех записей справочника расширенного поля (id, name)."""
        self.cursor.execute(
            "SELECT id, name FROM fmeca_lookup_values WHERE domain = ? ORDER BY name",
            (domain,),
        )
        return self.cursor.fetchall()
    
    def delete_fmeca_lookup(self, lookup_id: int) -> Tuple[bool, str]:
        """Удаление значения справочника расширенного поля."""
        self.cursor.execute("DELETE FROM fmeca_lookup_values WHERE id = ?", (lookup_id,))
        if self.cursor.rowcount == 0:
            return False, "Запись не найдена."
        self.connection.commit()
        return True, ""
    
    def ensure_fmeca_lookup_value(self, domain: str, name: str) -> None:
        """Добавление значения в справочник, если его ещё нет."""
        name = (name or "").strip()
        if not name:
            return
        try:
            self.cursor.execute(
                "INSERT INTO fmeca_lookup_values (domain, name) VALUES (?, ?)",
                (domain, name),
            )
            self.connection.commit()
        except sqlite3.IntegrityError:
            pass
    
    # ===== КОМПОНЕНТЫ И КАТЕГОРИИ =====
    
    def get_all_categories(self) -> List[Tuple[int, str]]:
        """Получение всех категорий компонентов."""
        self.cursor.execute("SELECT id, name FROM component_categories ORDER BY name")
        return self.cursor.fetchall()
    
    def add_category(self, name: str, description: str = "") -> int:
        """Добавление новой категории."""
        try:
            self.cursor.execute(
                "INSERT INTO component_categories (name, description) VALUES (?, ?)",
                (name, description)
            )
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Категория уже существует
            self.cursor.execute(
                "SELECT id FROM component_categories WHERE name = ?", (name,)
            )
            return self.cursor.fetchone()[0]
    
    def delete_category(self, category_id: int) -> Tuple[bool, str]:
        """Удаление категории компонента."""
        self.cursor.execute(
            "SELECT COUNT(*) FROM components WHERE category_id = ?", (category_id,)
        )
        if self.cursor.fetchone()[0] > 0:
            return False, "Категория используется компонентами. Сначала измените или удалите связанные записи."
        self.cursor.execute(
            "DELETE FROM category_failure_type WHERE category_id = ?", (category_id,)
        )
        self.cursor.execute(
            "DELETE FROM component_categories WHERE id = ?", (category_id,)
        )
        self.connection.commit()
        return True, ""
    
    def get_category_usage_count(self, category_id: int) -> int:
        self.cursor.execute(
            "SELECT COUNT(*) FROM components WHERE category_id = ?", (category_id,)
        )
        return self.cursor.fetchone()[0]
    
    def add_component(self, system: str, subsystem: str, component: str,
                     category_id: Optional[int] = None, description: str = "") -> int:
        """Добавление компонента с категорией."""
        self.cursor.execute("""
            INSERT INTO components (system, subsystem, component, category_id, description)
            VALUES (?, ?, ?, ?, ?)
        """, (system, subsystem, component, category_id, description))
        self.connection.commit()
        return self.cursor.lastrowid
    
    # ===== ТИПЫ ОТКАЗОВ =====
    
    def get_failure_types_for_category(self, category_id: int) -> List[Tuple]:
        """Получение типов отказов для категории компонента."""
        self.cursor.execute("""
            SELECT ft.id, ft.name, ft.default_severity, ft.default_occurrence, ft.default_detection
            FROM failure_types ft
            JOIN category_failure_type cft ON ft.id = cft.failure_type_id
            WHERE cft.category_id = ?
            ORDER BY ft.name
        """, (category_id,))
        return self.cursor.fetchall()
    
    def get_all_failure_types(self) -> List[Tuple]:
        """Получение всех типов отказов."""
        self.cursor.execute(
            "SELECT id, name, default_severity, default_occurrence, default_detection FROM failure_types ORDER BY name"
        )
        return self.cursor.fetchall()
    
    def add_failure_type(self, name: str, description: str = "",
                        default_s: int = 5, default_o: int = 5, default_d: int = 5) -> int:
        """Добавление нового типа отказа."""
        self.cursor.execute("""
            INSERT INTO failure_types (name, description, default_severity, default_occurrence, default_detection)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, default_s, default_o, default_d))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def delete_failure_type(self, failure_type_id: int) -> Tuple[bool, str]:
        """Удаление типа отказа."""
        self.cursor.execute(
            "SELECT COUNT(*) FROM failures WHERE failure_type_id = ?", (failure_type_id,)
        )
        if self.cursor.fetchone()[0] > 0:
            return False, "Тип отказа используется в записях FMEA."
        self.cursor.execute(
            "DELETE FROM category_failure_type WHERE failure_type_id = ?", (failure_type_id,)
        )
        self.cursor.execute(
            "DELETE FROM failure_type_cause WHERE failure_type_id = ?", (failure_type_id,)
        )
        self.cursor.execute(
            "DELETE FROM failure_type_effect WHERE failure_type_id = ?", (failure_type_id,)
        )
        self.cursor.execute("DELETE FROM failure_types WHERE id = ?", (failure_type_id,))
        self.connection.commit()
        return True, ""
    
    def get_or_add_failure_type(self, name: str) -> int:
        """Получение ID типа отказа или создание нового."""
        name = (name or "").strip()
        self.cursor.execute("SELECT id FROM failure_types WHERE name = ?", (name,))
        row = self.cursor.fetchone()
        if row:
            return row[0]
        return self.add_failure_type(name)
    
    def link_category_to_failure_type(self, category_id: int, failure_type_id: int):
        """Связывание категории и типа отказа."""
        try:
            self.cursor.execute(
                "INSERT INTO category_failure_type (category_id, failure_type_id) VALUES (?, ?)",
                (category_id, failure_type_id)
            )
            self.connection.commit()
        except sqlite3.IntegrityError:
            pass  # Связь уже существует
    
    # ===== ПРИЧИНЫ ОТКАЗОВ =====
    
    def get_causes_for_failure_type(self, failure_type_id: int) -> List[Tuple]:
        """Получение причин для типа отказа."""
        self.cursor.execute("""
            SELECT fc.id, fc.name
            FROM failure_causes fc
            JOIN failure_type_cause ftc ON fc.id = ftc.cause_id
            WHERE ftc.failure_type_id = ?
            ORDER BY fc.name
        """, (failure_type_id,))
        return self.cursor.fetchall()
    
    def get_all_causes(self) -> List[Tuple]:
        """Получение всех причин."""
        self.cursor.execute("SELECT id, name FROM failure_causes ORDER BY name")
        return self.cursor.fetchall()
    
    def add_cause(self, name: str, description: str = "") -> int:
        """Добавление новой причины."""
        self.cursor.execute(
            "INSERT INTO failure_causes (name, description) VALUES (?, ?)",
            (name, description)
        )
        self.connection.commit()
        return self.cursor.lastrowid
    
    def delete_cause(self, cause_id: int) -> Tuple[bool, str]:
        """Удаление причины отказа."""
        self.cursor.execute("SELECT COUNT(*) FROM failures WHERE cause_id = ?", (cause_id,))
        if self.cursor.fetchone()[0] > 0:
            return False, "Причина используется в записях FMEA."
        self.cursor.execute(
            "DELETE FROM failure_type_cause WHERE cause_id = ?", (cause_id,)
        )
        self.cursor.execute("DELETE FROM failure_causes WHERE id = ?", (cause_id,))
        self.connection.commit()
        return True, ""
    
    def get_or_add_cause(self, name: str) -> int:
        """Получение ID причины или создание новой."""
        name = (name or "").strip()
        self.cursor.execute("SELECT id FROM failure_causes WHERE name = ?", (name,))
        row = self.cursor.fetchone()
        if row:
            return row[0]
        return self.add_cause(name)
    
    def link_failure_type_to_cause(self, failure_type_id: int, cause_id: int):
        """Связывание типа отказа и причины."""
        try:
            self.cursor.execute(
                "INSERT INTO failure_type_cause (failure_type_id, cause_id) VALUES (?, ?)",
                (failure_type_id, cause_id)
            )
            self.connection.commit()
        except sqlite3.IntegrityError:
            pass
    
    # ===== ПОСЛЕДСТВИЯ ОТКАЗОВ =====
    
    def get_effects_for_failure_type(self, failure_type_id: int) -> List[Tuple]:
        """Получение последствий для типа отказа."""
        self.cursor.execute("""
            SELECT fe.id, fe.name
            FROM failure_effects fe
            JOIN failure_type_effect fte ON fe.id = fte.effect_id
            WHERE fte.failure_type_id = ?
            ORDER BY fe.name
        """, (failure_type_id,))
        return self.cursor.fetchall()
    
    def get_all_effects(self) -> List[Tuple]:
        """Получение всех последствий."""
        self.cursor.execute("SELECT id, name FROM failure_effects ORDER BY name")
        return self.cursor.fetchall()
    
    def add_effect(self, name: str, description: str = "") -> int:
        """Добавление нового последствия."""
        self.cursor.execute(
            "INSERT INTO failure_effects (name, description) VALUES (?, ?)",
            (name, description)
        )
        self.connection.commit()
        return self.cursor.lastrowid
    
    def delete_effect(self, effect_id: int) -> Tuple[bool, str]:
        """Удаление последствия отказа."""
        self.cursor.execute("SELECT COUNT(*) FROM failures WHERE effect_id = ?", (effect_id,))
        if self.cursor.fetchone()[0] > 0:
            return False, "Последствие используется в записях FMEA."
        self.cursor.execute(
            "DELETE FROM failure_type_effect WHERE effect_id = ?", (effect_id,)
        )
        self.cursor.execute("DELETE FROM failure_effects WHERE id = ?", (effect_id,))
        self.connection.commit()
        return True, ""
    
    def get_or_add_effect(self, name: str) -> int:
        """Получение ID последствия или создание нового."""
        name = (name or "").strip()
        self.cursor.execute("SELECT id FROM failure_effects WHERE name = ?", (name,))
        row = self.cursor.fetchone()
        if row:
            return row[0]
        return self.add_effect(name)
    
    def link_failure_type_to_effect(self, failure_type_id: int, effect_id: int):
        """Связывание типа отказа и последствия."""
        try:
            self.cursor.execute(
                "INSERT INTO failure_type_effect (failure_type_id, effect_id) VALUES (?, ?)",
                (failure_type_id, effect_id)
            )
            self.connection.commit()
        except sqlite3.IntegrityError:
            pass
    
    # ===== ОТКАЗЫ =====
    
    def add_failure(self, component_id: int, failure_mode: str,
                   failure_cause: str, failure_effect: str,
                   severity: int, occurrence: int, detection: int,
                   failure_type_id: Optional[int] = None,
                   cause_id: Optional[int] = None,
                   effect_id: Optional[int] = None,
                   function_text: Optional[str] = None,
                   local_effect: Optional[str] = None,
                   next_higher_effect: Optional[str] = None,
                   end_effect: Optional[str] = None,
                   current_controls: Optional[str] = None,
                   recommended_actions: Optional[str] = None,
                   action_owner: Optional[str] = None,
                   due_date: Optional[str] = None,
                   action_status: Optional[str] = None,
                   failure_rate_lambda: Optional[float] = None,
                   mode_ratio_alpha: Optional[float] = None,
                   conditional_prob_beta: Optional[float] = None,
                   mission_time_t: Optional[float] = None,
                   mission_phase: Optional[str] = None,
                   operating_mode: Optional[str] = None,
                   is_single_point: Optional[int] = None,
                   is_latent: Optional[int] = None,
                   is_common_cause: Optional[int] = None,
                   residual_severity: Optional[int] = None,
                   residual_occurrence: Optional[int] = None,
                   residual_detection: Optional[int] = None,
                   residual_rpn: Optional[int] = None) -> int:
        """Добавление записи об отказе."""
        dual_scores = FMEAModel.calculate_dual_scores(
            severity=severity,
            occurrence=occurrence,
            detection=detection,
            lambda_p=failure_rate_lambda,
            alpha=mode_ratio_alpha,
            beta=conditional_prob_beta,
            mission_time_t=mission_time_t
        )
        rpn = dual_scores["rpn"]
        mil_criticality = dual_scores["mil_criticality"]
        
        self.cursor.execute("""
            INSERT INTO failures (component_id, failure_type_id, cause_id, effect_id,
                                failure_mode, failure_cause, failure_effect,
                                severity, occurrence, detection, rpn,
                                function_text, local_effect, next_higher_effect, end_effect,
                                current_controls, recommended_actions, action_owner, due_date, action_status,
                                failure_rate_lambda, mode_ratio_alpha, conditional_prob_beta, mission_time_t,
                                mission_phase, operating_mode, is_single_point, is_latent, is_common_cause,
                                mil_criticality, residual_severity, residual_occurrence, residual_detection, residual_rpn)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (component_id, failure_type_id, cause_id, effect_id,
              failure_mode, failure_cause, failure_effect,
              severity, occurrence, detection, rpn,
              function_text, local_effect, next_higher_effect, end_effect,
              current_controls, recommended_actions, action_owner, due_date, action_status,
              failure_rate_lambda, mode_ratio_alpha, conditional_prob_beta, mission_time_t,
              mission_phase, operating_mode, is_single_point, is_latent, is_common_cause,
              mil_criticality, residual_severity, residual_occurrence, residual_detection, residual_rpn))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_component_mil_criticality_summary(self) -> List[Tuple]:
        """
        Суммарная MIL-критичность по компоненту.
        NULL значения mil_criticality игнорируются суммой через COALESCE.
        """
        self.cursor.execute("""
            SELECT c.component, SUM(COALESCE(f.mil_criticality, 0)) AS total_mil_criticality
            FROM failures f
            JOIN components c ON f.component_id = c.id
            GROUP BY c.component
            ORDER BY total_mil_criticality DESC
        """)
        return self.cursor.fetchall()
    
    def get_all_failures(self) -> List[Tuple]:
        """Получение всех записей FMEA с расширенной информацией."""
        self.cursor.execute("""
            SELECT f.id, c.system, c.subsystem, c.component,
                   cc.name as category,
                   f.failure_mode, f.failure_cause, f.failure_effect,
                   f.severity, f.occurrence, f.detection, f.rpn
            FROM failures f
            JOIN components c ON f.component_id = c.id
            LEFT JOIN component_categories cc ON c.category_id = cc.id
            ORDER BY f.rpn DESC
        """)
        return self.cursor.fetchall()
    
    def get_failures_for_standard_report(self, sort_by: str = "rpn") -> List[Tuple]:
        """
        Получение расширенных данных для стандартизированного FMECA отчёта.
        
        sort_by:
        - "rpn" (по умолчанию)
        - "mil_criticality"
        """
        order_clause = "f.rpn DESC"
        if sort_by == "mil_criticality":
            order_clause = "COALESCE(f.mil_criticality, -1) DESC, f.rpn DESC"
        
        self.cursor.execute(f"""
            SELECT
                f.id,
                c.system,
                c.subsystem,
                c.component,
                cc.name AS category,
                f.function_text,
                f.failure_mode,
                f.failure_cause,
                f.local_effect,
                f.next_higher_effect,
                f.end_effect,
                f.failure_effect,
                f.severity,
                f.occurrence,
                f.detection,
                f.rpn,
                f.mil_criticality,
                f.failure_rate_lambda,
                f.mode_ratio_alpha,
                f.conditional_prob_beta,
                f.mission_time_t,
                f.current_controls,
                f.recommended_actions,
                f.action_owner,
                f.due_date,
                f.action_status,
                f.mission_phase,
                f.operating_mode,
                f.is_single_point,
                f.is_latent,
                f.is_common_cause,
                f.residual_severity,
                f.residual_occurrence,
                f.residual_detection,
                f.residual_rpn
            FROM failures f
            JOIN components c ON f.component_id = c.id
            LEFT JOIN component_categories cc ON c.category_id = cc.id
            ORDER BY {order_clause}
        """)
        return self.cursor.fetchall()
    
    def get_failures_for_quality_dashboard(self) -> List[Dict]:
        """
        Получение записей в dict-формате для dashboard качества анализа.
        """
        self.cursor.execute("""
            SELECT
                f.id,
                c.component,
                f.function_text,
                f.failure_mode,
                f.failure_cause,
                f.local_effect,
                f.next_higher_effect,
                f.end_effect,
                f.recommended_actions,
                f.severity,
                f.occurrence,
                f.detection,
                f.mil_criticality
            FROM failures f
            JOIN components c ON f.component_id = c.id
            ORDER BY f.id
        """)
        
        rows = self.cursor.fetchall()
        records = []
        for row in rows:
            records.append({
                "id": row[0],
                "component": row[1],
                "function_text": row[2],
                "failure_mode": row[3],
                "failure_cause": row[4],
                "local_effect": row[5],
                "next_higher_effect": row[6],
                "end_effect": row[7],
                "recommended_actions": row[8],
                "severity": row[9],
                "occurrence": row[10],
                "detection": row[11],
                "mil_criticality": row[12],
            })
        return records
    
    def get_structured_failure_ids(self) -> List[int]:
        """
        ID записей, соответствующих актуальной структуре FMECA.
        Критерии: обязательные текстовые поля заполнены и S/O/D валидны.
        """
        self.cursor.execute("""
            SELECT id
            FROM failures
            WHERE
                function_text IS NOT NULL AND TRIM(function_text) <> ''
                AND failure_mode IS NOT NULL AND TRIM(failure_mode) <> ''
                AND failure_cause IS NOT NULL AND TRIM(failure_cause) <> ''
                AND local_effect IS NOT NULL AND TRIM(local_effect) <> ''
                AND next_higher_effect IS NOT NULL AND TRIM(next_higher_effect) <> ''
                AND end_effect IS NOT NULL AND TRIM(end_effect) <> ''
                AND recommended_actions IS NOT NULL AND TRIM(recommended_actions) <> ''
                AND severity BETWEEN 1 AND 10
                AND occurrence BETWEEN 1 AND 10
                AND detection BETWEEN 1 AND 10
        """)
        return [row[0] for row in self.cursor.fetchall()]
    
    def prune_to_structured_failures(self) -> Dict[str, int]:
        """
        Удаляет записи отказов, не соответствующие актуальной FMECA-структуре.
        Также удаляет компоненты без привязанных отказов.
        """
        self.cursor.execute("SELECT COUNT(*) FROM failures")
        total_before = self.cursor.fetchone()[0]
        
        structured_ids = self.get_structured_failure_ids()
        if structured_ids:
            placeholders = ",".join(["?"] * len(structured_ids))
            self.cursor.execute(
                f"DELETE FROM failures WHERE id NOT IN ({placeholders})",
                tuple(structured_ids)
            )
        else:
            self.cursor.execute("DELETE FROM failures")
        
        # Чистим orphan components после удаления failures
        self.cursor.execute("""
            DELETE FROM components
            WHERE id NOT IN (SELECT DISTINCT component_id FROM failures)
        """)
        
        self.connection.commit()
        
        self.cursor.execute("SELECT COUNT(*) FROM failures")
        total_after = self.cursor.fetchone()[0]
        return {
            "total_before": total_before,
            "total_after": total_after,
            "deleted": total_before - total_after,
        }
    
    def clear_all_data(self):
        """Очистка операционных данных (компоненты и отказы) перед импортом."""
        self.cursor.execute("DELETE FROM failures")
        self.cursor.execute("DELETE FROM components")
        self.connection.commit()
    
    def delete_failure(self, failure_id: int):
        """Удаление записи об отказе."""
        self.cursor.execute("DELETE FROM failures WHERE id = ?", (failure_id,))
        self.connection.commit()
    
    def update_failure(self, failure_id: int, severity: int,
                      occurrence: int, detection: int):
        """Обновление оценок S-O-D и пересчёт RPN."""
        rpn = severity * occurrence * detection
        self.cursor.execute("""
            UPDATE failures
            SET severity = ?, occurrence = ?, detection = ?, rpn = ?
            WHERE id = ?
        """, (severity, occurrence, detection, rpn, failure_id))
        self.connection.commit()
    
    def get_failure_by_id(self, failure_id: int) -> Optional[Dict]:
        """Получение полной записи отказа по ID для редактирования."""
        self.cursor.execute("""
            SELECT f.id, c.system, c.subsystem, c.component,
                   cc.name AS category,
                   c.category_id,
                   f.failure_type_id, ft.name AS failure_type,
                   f.cause_id, f.effect_id,
                   f.failure_mode, f.failure_cause, f.failure_effect,
                   f.severity, f.occurrence, f.detection, f.rpn,
                   f.function_text, f.local_effect, f.next_higher_effect, f.end_effect,
                   f.recommended_actions, f.action_owner, f.due_date,
                   f.failure_rate_lambda, f.mode_ratio_alpha, f.conditional_prob_beta, f.mission_time_t,
                   f.mission_phase, f.operating_mode,
                   f.residual_severity, f.residual_occurrence, f.residual_detection, f.residual_rpn
            FROM failures f
            JOIN components c ON f.component_id = c.id
            LEFT JOIN component_categories cc ON c.category_id = cc.id
            LEFT JOIN failure_types ft ON f.failure_type_id = ft.id
            WHERE f.id = ?
        """, (failure_id,))
        row = self.cursor.fetchone()
        if not row:
            return None
        
        return {
            "id": row[0],
            "system": row[1],
            "subsystem": row[2],
            "component": row[3],
            "category": row[4],
            "category_id": row[5],
            "failure_type_id": row[6],
            "failure_type": row[7],
            "cause_id": row[8],
            "effect_id": row[9],
            "failure_mode": row[10],
            "cause": row[11],
            "effect": row[12],
            "severity": row[13],
            "occurrence": row[14],
            "detection": row[15],
            "rpn": row[16],
            "function_text": row[17],
            "local_effect": row[18],
            "next_higher_effect": row[19],
            "end_effect": row[20],
            "recommended_actions": row[21],
            "action_owner": row[22],
            "due_date": row[23],
            "failure_rate_lambda": row[24],
            "mode_ratio_alpha": row[25],
            "conditional_prob_beta": row[26],
            "mission_time_t": row[27],
            "mission_phase": row[28],
            "operating_mode": row[29],
            "residual_severity": row[30],
            "residual_occurrence": row[31],
            "residual_detection": row[32],
            "residual_rpn": row[33],
        }
    
    def update_failure_extended(self, failure_id: int, data: Dict):
        """
        Расширенное обновление FMECA записи.
        Поддерживает dual scoring и residual risk без изменения архитектуры.
        """
        dual_scores = FMEAModel.calculate_dual_scores(
            severity=data["severity"],
            occurrence=data["occurrence"],
            detection=data["detection"],
            lambda_p=data.get("failure_rate_lambda"),
            alpha=data.get("mode_ratio_alpha"),
            beta=data.get("conditional_prob_beta"),
            mission_time_t=data.get("mission_time_t")
        )
        rpn = dual_scores["rpn"]
        mil_criticality = dual_scores["mil_criticality"]
        
        residual_rpn = data.get("residual_rpn")
        if residual_rpn is None:
            residual_rpn = FMEAModel.calc_residual_rpn(
                data.get("residual_severity"),
                data.get("residual_occurrence"),
                data.get("residual_detection"),
            )
        
        self.cursor.execute("""
            UPDATE failures
            SET failure_mode = ?, failure_cause = ?, failure_effect = ?,
                severity = ?, occurrence = ?, detection = ?, rpn = ?,
                function_text = ?, local_effect = ?, next_higher_effect = ?, end_effect = ?,
                recommended_actions = ?, action_owner = ?, due_date = ?,
                failure_rate_lambda = ?, mode_ratio_alpha = ?, conditional_prob_beta = ?, mission_time_t = ?,
                mission_phase = ?, operating_mode = ?,
                mil_criticality = ?, residual_severity = ?, residual_occurrence = ?, residual_detection = ?, residual_rpn = ?
            WHERE id = ?
        """, (
            data["failure_mode"], data["cause"], data["effect"],
            data["severity"], data["occurrence"], data["detection"], rpn,
            data.get("function_text"), data.get("local_effect"), data.get("next_higher_effect"), data.get("end_effect"),
            data.get("recommended_actions"), data.get("action_owner"), data.get("due_date"),
            data.get("failure_rate_lambda"), data.get("mode_ratio_alpha"), data.get("conditional_prob_beta"), data.get("mission_time_t"),
            data.get("mission_phase"), data.get("operating_mode"),
            mil_criticality, data.get("residual_severity"), data.get("residual_occurrence"), data.get("residual_detection"), residual_rpn,
            failure_id
        ))
        self.connection.commit()
    
    def recalculate_all_rpn(self):
        """Пересчёт RPN для всех записей."""
        self.cursor.execute("""
            UPDATE failures
            SET rpn = severity * occurrence * detection
        """)
        self.connection.commit()
    
    def close(self):
        """Закрытие соединения с БД."""
        self.connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()