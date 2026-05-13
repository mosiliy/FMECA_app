# FMEA / FMECA Analysis Tool

---

## Русский

### Описание

Настольное приложение для анализа видов отказов, последствий и критичности (**FMEA / FMECA**) в области вычислительной техники. Реализовано на **Python** с графическим интерфейсом **Tkinter**, хранением данных в **SQLite** и поддержкой импорта/экспорта, отчётов и визуализации.

### Возможности

- Ведение записей отказов с привязкой к системе, подсистеме, компоненту и справочникам (категории, типы отказов, причины, последствия).
- Расчёт **RPN** (Severity × Occurrence × Detection) и **MIL-критичности режима** при наличии параметров λ, α, β и времени миссии.
- Расширенная структура FMECA: функция, локальный/верхний/конечный эффекты, меры и остаточный риск.
- Импорт из **XML**, экспорт в **Excel** и **PDF** (в т.ч. кириллица через шрифты в каталоге `fonts/`).
- Полный отчёт с графиками, матрица критичности, граф зависимостей.
- Панель **качества анализа**, текстовое **объяснение риска**, фильтрация и очистка записей, не соответствующих актуальной структуре.
- **Add-only миграции** схемы БД для совместимости со старыми файлами базы.

### Требования

- Python 3.10+ (рекомендуется актуальная стабильная ветка 3.x).
- Зависимости из `requirements.txt`: `pandas`, `matplotlib`, `openpyxl`, `reportlab`, `seaborn`, `networkx`.

### Установка

```bash
cd fmeca_app
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

На Linux/macOS активация: `source .venv/bin/activate`.

### Запуск приложения

```bash
python main.py
```

База данных по умолчанию создаётся в `data/fmea.db` (каталог создаётся автоматически).

### Структура проекта (кратко)

| Файл / каталог | Назначение |
|----------------|------------|
| `main.py` | Точка входа, запуск GUI |
| `gui.py` | Интерфейс пользователя |
| `database.py` | SQLite, схема, миграции, CRUD |
| `model.py` | Расчёты RPN, MIL, полнота, риски, отчётные DataFrame |
| `io_utils.py` | Импорт XML, экспорт Excel/PDF |
| `reports.py` | Сборка полных отчётов |
| `visualization.py` | Графики matplotlib/seaborn |
| `graph_analysis.py` | Граф зависимостей (NetworkX) |
| `tests/` | Модульные тесты (`unittest`) |
| `fonts/` | TTF для PDF с кириллицей |
| `sample_fmeca.xml`, `new_sample.xml` | Примеры XML |

### Тесты

```bash
python -m unittest discover -s tests -v
```

### Ориентиры по стандартам

В интерфейсе указаны ориентиры: **MIL-STD-1629A**, **IEC 60812**, **ГОСТ 27.310-95**, **ГОСТ Р ИСО/МЭК 31010**. Реализация носит учебно-практический характер; перед промышленным применением требуется сверка с актуальными редакциями нормативов вашей организации.

---

## English

### Description

A **desktop FMEA / FMECA** (Failure Mode, Effects, and Criticality Analysis) tool focused on IT hardware-style scenarios. Built with **Python**, **Tkinter** for the UI, **SQLite** for storage, plus import/export, reporting, and charts.

### Features

- Failure records linked to system, subsystem, component, and reference data (categories, failure types, causes, effects).
- **RPN** (S × O × D) and **MIL mode criticality** when λ, α, β, and mission time are provided.
- Extended FMECA fields: function, local / next-higher / end effects, actions, and residual risk.
- **XML** import; **Excel** and **PDF** export (Cyrillic via fonts in `fonts/`).
- Full PDF report with charts, criticality views, and a dependency graph.
- **Analysis quality** dashboard, **risk explanation** text, filtering and pruning of records that do not match the current FMECA structure.
- **Add-only database migrations** to keep older `fmea.db` files usable.

### Requirements

- Python 3.10+ recommended.
- Dependencies listed in `requirements.txt`: `pandas`, `matplotlib`, `openpyxl`, `reportlab`, `seaborn`, `networkx`.

### Installation

```bash
cd fmeca_app
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the application

```bash
python main.py
```

The default database path is `data/fmea.db` (the folder is created if missing).

### Project layout (short)

| Path | Role |
|------|------|
| `main.py` | Entry point |
| `gui.py` | Tkinter UI |
| `database.py` | SQLite schema, migrations, CRUD |
| `model.py` | RPN, MIL, completeness, risk helpers, reporting DataFrames |
| `io_utils.py` | XML import, Excel/PDF export |
| `reports.py` | Full report pipeline |
| `visualization.py` | Matplotlib / Seaborn charts |
| `graph_analysis.py` | Dependency graph (NetworkX) |
| `tests/` | Unit tests (`unittest`) |
| `fonts/` | TTF fonts for PDF Cyrillic |
| `sample_fmeca.xml`, `new_sample.xml` | Sample XML inputs |

### Tests

```bash
python -m unittest discover -s tests -v
```

### Standards note

The UI references **MIL-STD-1629A**, **IEC 60812**, and related Russian GOSTs as **guidance**. The implementation is educational/practical; validate against your organization’s current standards before production use.

---

## License / Лицензия

Font files in `fonts/` are subject to their own **LICENSE** and **COPYRIGHT** files (e.g. DejaVu). Application code license is as specified by the project author.
