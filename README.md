# FMECA Analysis Tool

Настольное приложение для анализа видов отказов, последствий и критичности (**АВПКО**) в области вычислительной техники и ЦОД.

---

## Русский

### Описание

Реализовано на **Python 3.10+**, графический интерфейс **Tkinter**, хранение в **SQLite**. Поддерживаются справочники, расширенные поля FMECA, расчёт RPN и количественной критичности, импорт/экспорт, отчёты и визуализация.

### Основные возможности

**Записи FMEA/FMECA**
- Иерархия: система → подсистема → компонент → вид отказа.
- Оценки **S, O, D** (1–10) и автоматический расчёт **RPN = S × O × D**.
- Расширенные поля: функция, локальный / верхний / конечный эффекты, текущие меры, рекомендации, ответственный, срок, статус.
- Параметры надёжности **λ, α, β, t** и расчёт **критичности Cm = λ × α × β × t**.
- Остаточный риск: **S/O/D после мер** и **RPN после мер** (см. раздел «RPN до и после мер» ниже).
- Признаки: ОПФ, скрытый отказ, ОППО; фаза миссии, режим работы.

**Справочники**
- Категории компонентов, типы отказов, причины, последствия.
- Справочники расширенных полей (функции, эффекты, меры, ответственные и т.д.).
- Добавление и **удаление** записей в справочниках (удаление блокируется, если значение используется в записях FMEA).
- В форме записи — свободный ввод и кнопка «+» для пользовательских значений.

**Анализ и качество**
- Категории риска по RPN: низкий (&lt;40), средний (40–99), высокий (100–199), критический (≥200).
- Панель **качества анализа** (полнота заполнения полей).
- **Объяснить риск** — текстовая сводка по выбранной записи.
- Фильтр по таблице, режим «только актуальные» записи, очистка неактуальных.

**Визуализация**
- Распределение RPN, RPN по компонентам и категориям.
- Категории риска (круговая диаграмма).
- Матрица S×O, матрица критичности (класс тяжести × уровень вероятности).
- Рейтинг по количественной критичности Cm.
- Граф зависимостей (компонент → отказ → причина → последствие).

**Экспорт и отчёты**
- **Excel** — несколько листов, включая полную таблицу АВПКО.
- **PDF** — краткий отчёт с таблицами.
- **Полный отчёт (PDF)** — все записи по разделам + 7 графиков.

**Демо-данные**
- При первом запуске (пустая база) автоматически загружается **50 записей** (сценарии ЦОД/серверов).
- Повторная загрузка: **Справочники → Загрузить демо (50 записей)**.

### RPN до и после мер

| Показатель | Откуда берутся оценки | Формула |
|------------|------------------------|---------|
| **RPN до мер** | Основные S, O, D (верх блока формы) | S × O × D |
| **RPN после мер** | Остаточные S, O, D (низ формы) | S_ост × O_ост × D_ост |
| **Снижение риска** | Разница | RPN до − RPN после |

Если в БД сохранён явный «остаточный RPN», он используется в приоритете; иначе значение пересчитывается из остаточных S/O/D.

### Требования

- Python **3.10+**
- Зависимости: `pandas`, `matplotlib`, `openpyxl`, `reportlab`, `seaborn`, `networkx` (см. `requirements.txt`)

### Установка и запуск

```bash
cd fmeca_app
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

База данных: `data/fmea.db` (каталог создаётся автоматически).

### Интерфейс (кратко)

| Элемент | Действие |
|---------|----------|
| Добавить / Изменить / Удалить | CRUD записей АВПКО |
| Экспорт Excel / PDF / Полный отчёт | Выгрузка данных |
| Графики | Меню визуализаций |
| Справочники | Просмотр, добавление, удаление справочников; демо-данные |
| Качество анализа | Полнота и проблемные записи |
| Объяснить риск | Текст по выбранной строке |
| Пересчитать RPN | Массовый пересчёт в БД |

### Листы Excel при экспорте

| Лист | Содержание |
|------|------------|
| FMEA Analysis | Основная таблица (S, O, D, RPN) |
| АВПКО полный | Все поля записи |
| Количественная критичность | λ, α, β, t, Cm |
| Сводка анализа | Статистика полноты и рисков |
| До-После мер | RPN до / после / снижение |
| FMECA Standardized | Сводный формат (англ. заголовки) |
| Топ-20 по RPN / Cm | Приоритетные записи |
| Статистика RPN, Справка | Сводки и пороги RPN |

### Структура проекта

| Файл / каталог | Назначение |
|----------------|------------|
| `main.py` | Точка входа |
| `gui.py` | Интерфейс Tkinter |
| `database.py` | SQLite: схема, миграции, CRUD, справочники |
| `model.py` | RPN, Cm, полнота, DataFrame для отчётов |
| `io_utils.py` | Импорт XML, экспорт Excel/PDF |
| `reports.py` | Полный PDF-отчёт с графиками |
| `visualization.py` | Графики matplotlib |
| `graph_analysis.py` | Граф зависимостей (NetworkX) |
| `demo_data.py` | Генерация 50 демо-записей |
| `standards.py` | Пороги RPN, вспомогательные константы |
| `tests/` | Модульные тесты (`unittest`) |
| `fonts/` | Шрифты DejaVu для PDF с кириллицей |
| `sample_fmeca.xml`, `new_sample.xml` | Примеры XML |

### Тесты

```bash
python -m unittest discover -s tests -v
```

### Миграции БД

Схема обновляется **без пересоздания** таблиц (add-only миграции в `database.py`). Старые файлы `fmea.db` остаются совместимыми.

---

## English

### Description

A **desktop FMEA / FMECA** tool for IT infrastructure and data-center scenarios. **Python**, **Tkinter**, **SQLite**, with dictionaries, extended FMECA fields, RPN and quantitative criticality (Cm), import/export, and reporting.

### Features

- Failure records with system / subsystem / component hierarchy and reference data.
- **RPN** = S × O × D; **Cm** = λ × α × β × t when reliability inputs are provided.
- Extended fields, residual S/O/D, before/after RPN in reports.
- Editable dictionaries with add/delete (delete blocked if a value is in use).
- Quality dashboard, risk explanation, dependency graph, seven chart types.
- **50 demo records** on first run (empty database); reload via **Dictionaries → Load demo (50 records)**.
- Excel/PDF/full PDF export with comprehensive FMECA sheets.

### Requirements & run

```bash
cd fmeca_app
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Default database: `data/fmea.db`.

### Tests

```bash
python -m unittest discover -s tests -v
```

### Before / after RPN

- **Before actions:** main S, O, D → RPN = S × O × D  
- **After actions:** residual S, O, D → residual RPN = S × O × D  
- **Risk reduction:** before − after  

---

## License / Лицензия

Font files in `fonts/` are subject to their own **LICENSE** and **COPYRIGHT** (DejaVu). Application code license is as specified by the project author.
