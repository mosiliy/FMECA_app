"""
Графический интерфейс приложения на Tkinter.
Улучшенная версия с современным визуальным оформлением и контекстно-зависимыми справочниками.
"""

import tkinter as tk
import pandas as pd
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Optional, List, Tuple
import os

from database import Database
from model import FMEAModel
from io_utils import IOUtils
from visualization import Visualization
from reports import ReportGenerator


# ═══════════════════════════════════════════════════════════════════════
#  ЦВЕТОВАЯ СХЕМА
# ═══════════════════════════════════════════════════════════════════════

CLR_BG       = "#F5F5F5"
CLR_HEADER   = "#1F4E79"
CLR_BTN_BLUE = "#1565C0"
CLR_BTN_GRN  = "#2E7D32"
CLR_BTN_RED  = "#C62828"
CLR_BTN_ORN  = "#E65100"
CLR_BTN_PURP = "#6A1B9A"
CLR_BTN_TEAL = "#00695C"
CLR_BTN_GREY = "#757575"
CLR_BTN_DARK = "#455A64"

RPN_ROW_COLORS = {
    "Низкий":       "#E8F5E9",
    "Средний":      "#FFF9C4",
    "Высокий":      "#FFCCBC",
    "Критический":  "#FFCDD2",
}


class FMEAApp:
    """Главное окно приложения FMEA/FMECA с улучшенным дизайном."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("FMEA/FMECA Analysis Tool — Enhanced Edition")
        self.root.geometry("1600x800")
        self.root.minsize(1200, 600)
        self.root.configure(bg=CLR_BG)
        
        # Инициализация БД
        self.db = Database()
        self.model = FMEAModel()
        
        # Кэши для выпадающих списков
        self.current_category_id = None
        self.current_failure_type_id = None
        
        # Переменная для поиска/фильтрации
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_table())
        self.show_only_structured_var = tk.BooleanVar(value=False)
        
        # Переменные сортировки
        self._sort_col = "RPN"
        self._sort_asc = False
        
        # Создание интерфейса
        self._build_header()
        self._build_toolbar()
        self._build_quick_actions_bar()
        self._build_table()
        self._build_status_bar()
        
        # Загрузка данных
        self.refresh_table()
    
    # ═══════════════════════════════════════════════════════════════════
    #  UI CONSTRUCTION
    # ═══════════════════════════════════════════════════════════════════
    
    def _build_header(self):
        """Строит шапку приложения."""
        hdr = tk.Frame(self.root, bg=CLR_HEADER, height=56)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        
        tk.Label(
            hdr, 
            text="FMEA/FMECA — Анализ видов, последствий и критичности отказов ВТ",
            bg=CLR_HEADER, fg="white", font=("Arial", 13, "bold")
        ).pack(side=tk.LEFT, padx=16, pady=10)
        
        tk.Label(
            hdr, 
            text="MIL-STD-1629A  |  IEC 60812  |  ГОСТ 27.310-95  |  ГОСТ Р ИСО/МЭК 31010",
            bg=CLR_HEADER, fg="#90CAF9", font=("Arial", 9)
        ).pack(side=tk.RIGHT, padx=16)
    
    def _build_toolbar(self):
        """Строит панель инструментов с кнопками."""
        tb = tk.Frame(self.root, bg="#E0E0E0", pady=6)
        tb.pack(fill=tk.X)
        
        def btn(parent, text, cmd, bg, emoji=""):
            """Создаёт кнопку с единым стилем."""
            b = tk.Button(
                parent, 
                text=f"{emoji} {text}".strip(), 
                command=cmd,
                bg=bg, fg="white", font=("Arial", 9, "bold"),
                relief=tk.FLAT, padx=10, pady=5, cursor="hand2",
                activebackground=bg, activeforeground="white"
            )
            b.pack(side=tk.LEFT, padx=4)
            return b
        
        # Левая группа — CRUD
        btn(tb, "Добавить запись",  self.show_add_dialog, CLR_BTN_BLUE, "➕")
        btn(tb, "Редактировать",    self.edit_record,     CLR_BTN_DARK, "✏️")
        btn(tb, "Удалить запись",   self.delete_record,   CLR_BTN_RED,  "🗑")
        
        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y, pady=4)
        
        # Данные
        btn(tb, "Рассчитать RPN",   self.recalculate_rpn, CLR_BTN_PURP, "⚙️")
        btn(tb, "Импорт XML",       self.import_xml,      CLR_BTN_ORN,  "📥")
        
        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y, pady=4)
        
        # Экспорт / Графики
        btn(tb, "Экспорт Excel",    self.export_excel,    CLR_BTN_GRN,  "📊")
        btn(tb, "Экспорт PDF",      self.export_pdf,      CLR_BTN_RED,  "📄")
        btn(tb, "Полный отчёт",     self.export_full_report_pdf, CLR_BTN_TEAL, "📑")
        btn(tb, "Графики",          self.show_charts_menu, CLR_BTN_BLUE, "📈")
        
        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y, pady=4)
        
        # Справочники
        btn(tb, "Справочники",      self.show_dict_menu,  CLR_BTN_DARK, "📚")
        btn(tb, "Качество анализа", self.show_quality_dashboard, CLR_BTN_TEAL, "✅")
        btn(tb, "Объяснить риск",   self.explain_selected_risk, CLR_BTN_PURP, "🧠")
        btn(tb, "Очистить неактуальные", self.prune_to_structured_records, CLR_BTN_RED, "🧹")
        
        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y, pady=4)
        
        # Поиск
        tk.Label(tb, text="Фильтр:", bg="#E0E0E0", font=("Arial", 9)).pack(side=tk.RIGHT, padx=(0, 4))
        search_entry = tk.Entry(tb, textvariable=self.search_var, width=22, font=("Arial", 9))
        search_entry.pack(side=tk.RIGHT, padx=4)
        
        tk.Checkbutton(
            tb,
            text="Только актуальные",
            variable=self.show_only_structured_var,
            command=self.refresh_table,
            bg="#E0E0E0",
            font=("Arial", 9)
        ).pack(side=tk.RIGHT, padx=8)
    
    def _build_quick_actions_bar(self):
        """Закреплённая панель быстрых действий (всегда видимая)."""
        qa = tk.Frame(self.root, bg="#DDE7F5", pady=4)
        qa.pack(fill=tk.X)
        
        tk.Label(
            qa,
            text="Быстрые действия:",
            bg="#DDE7F5",
            fg="#1F4E79",
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(10, 6))
        
        tk.Button(
            qa, text="🧠 Объяснить риск (по выбранной записи)",
            command=self.explain_selected_risk,
            bg=CLR_BTN_PURP, fg="white", font=("Arial", 9, "bold"),
            relief=tk.FLAT, padx=10, pady=4, cursor="hand2"
        ).pack(side=tk.LEFT, padx=4)
        
        tk.Button(
            qa, text="✅ Качество анализа",
            command=self.show_quality_dashboard,
            bg=CLR_BTN_TEAL, fg="white", font=("Arial", 9, "bold"),
            relief=tk.FLAT, padx=10, pady=4, cursor="hand2"
        ).pack(side=tk.LEFT, padx=4)
        
        tk.Button(
            qa, text="🧹 Очистить неактуальные",
            command=self.prune_to_structured_records,
            bg=CLR_BTN_RED, fg="white", font=("Arial", 9, "bold"),
            relief=tk.FLAT, padx=10, pady=4, cursor="hand2"
        ).pack(side=tk.LEFT, padx=4)
        
        tk.Checkbutton(
            qa,
            text="Только актуальные по структуре (быстрый фильтр)",
            variable=self.show_only_structured_var,
            command=self.refresh_table,
            bg="#DDE7F5",
            font=("Arial", 9, "bold")
        ).pack(side=tk.RIGHT, padx=10)
    
    def _build_table(self):
        """Создаёт таблицу Treeview с современным стилем."""
        frame = tk.Frame(self.root, bg=CLR_BG)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        
        # Колонки
        columns = (
            "ID", "Система", "Подсистема", "Компонент", "Категория",
            "Вид отказа", "Причина", "Последствие", 
            "S", "O", "D", "RPN", "Уровень риска"
        )
        
        # Настройка ширин колонок
        col_cfg = {
            "ID":              40,
            "Система":         100,
            "Подсистема":      100,
            "Компонент":       130,
            "Категория":       110,
            "Вид отказа":      150,
            "Причина":         140,
            "Последствие":     140,
            "S":               40,
            "O":               40,
            "D":               40,
            "RPN":             60,
            "Уровень риска":   110,
        }
        
        # Стиль Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "FMEA.Treeview",
            rowheight=24, 
            font=("Arial", 9),
            background="white", 
            fieldbackground="white"
        )
        style.configure(
            "FMEA.Treeview.Heading",
            font=("Arial", 9, "bold"),
            background=CLR_HEADER, 
            foreground="white"
        )
        style.map(
            "FMEA.Treeview.Heading",
            background=[("active", "#1A3F6F")]
        )
        style.map(
            "FMEA.Treeview",
            background=[("selected", "#BBDEFB")],
            foreground=[("selected", "#0D47A1")]
        )
        
        # Создание Treeview
        self.tree = ttk.Treeview(
            frame, 
            columns=columns, 
            show="headings",
            style="FMEA.Treeview", 
            selectmode="browse"
        )
        
        # Настройка колонок
        for col in columns:
            width = col_cfg.get(col, 100)
            anchor = tk.CENTER if col in ["ID", "S", "O", "D", "RPN", "Уровень риска"] else tk.W
            
            self.tree.heading(
                col, 
                text=col,
                command=lambda c=col: self._sort_by(c)
            )
            self.tree.column(col, width=width, anchor=anchor, minwidth=30)
        
        # Теги цветовой раскраски
        for level, color in RPN_ROW_COLORS.items():
            self.tree.tag_configure(level, background=color)
        self.tree.tag_configure("alt", background="#FAFAFA")
        self.tree.tag_configure("incomplete", background="#FFE0E0")
        
        # Скроллбары
        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Размещение
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        
        # Двойной клик для редактирования
        self.tree.bind("<Double-1>", lambda _e: self.edit_record())
    
    def _build_status_bar(self):
        """Создаёт статусную строку."""
        self.status_var = tk.StringVar(value="Готово")
        sb = tk.Label(
            self.root, 
            textvariable=self.status_var,
            bd=1, relief=tk.SUNKEN, anchor=tk.W,
            bg="#EEEEEE", font=("Arial", 8), fg="#424242"
        )
        sb.pack(side=tk.BOTTOM, fill=tk.X)
    
    # ═══════════════════════════════════════════════════════════════════
    #  DATA HELPERS
    # ═══════════════════════════════════════════════════════════════════
    
    def show_dependency_graph(self):
        """Показ графа зависимостей."""
        data = self.db.get_all_failures()
        if not data:
            messagebox.showwarning("Нет данных", "Добавьте записи для построения графа")
            return
        
        # Диалог выбора параметров
        dialog = GraphSettingsDialog(self.root, on_build=lambda settings: self._build_graph(data, settings))
    
    def _build_graph(self, data, settings):
        """Построение графа с заданными параметрами."""
        from graph_analysis import FMEAGraph
        
        graph = FMEAGraph(data)
        
        # Показать статистику
        stats = graph.get_statistics()
        print("=" * 50)
        print("СТАТИСТИКА ГРАФА:")
        print(f"  Всего узлов: {stats['total_nodes']}")
        print(f"  Всего рёбер: {stats['total_edges']}")
        print(f"  Компоненты: {stats['components']}")
        print(f"  Типы отказов: {stats['failures']}")
        print(f"  Причины: {stats['causes']}")
        print(f"  Последствия: {stats['effects']}")
        print(f"  Средняя степень: {stats['avg_degree']:.2f}")
        print(f"  Плотность: {stats['density']:.4f}")
        print("=" * 50)
        
        # Визуализация
        graph.visualize(
            layout=settings['layout'],
            filter_rpn=settings.get('filter_rpn')
        )
        
        # Анализ центральности
        if settings.get('show_centrality'):
            centrality_df = graph.analyze_centrality()
            self._show_centrality_window(centrality_df)
    
    def _show_centrality_window(self, df: pd.DataFrame):
        """Показ окна с анализом центральности."""
        win = tk.Toplevel(self.root)
        win.title("Анализ центральности узлов графа")
        win.geometry("900x500")
        win.configure(bg=CLR_BG)
        win.grab_set()
        
        # Treeview
        cols = list(df.columns)
        tree = ttk.Treeview(win, columns=cols, show='headings', style="FMEA.Treeview")
        
        for col in cols:
            tree.heading(col, text=col)
            width = 150 if col == 'Узел' else 130
            tree.column(col, width=width, anchor=tk.W if col in ['Узел', 'Тип'] else tk.CENTER)
        
        for row in df.head(20).itertuples():
            tree.insert('', tk.END, values=list(row)[1:])
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(win, text="Топ-20 узлов по Betweenness Centrality", 
                bg=CLR_BG, font=("Arial", 9, "italic")).pack(pady=5)
        
        tk.Button(win, text="Закрыть", command=win.destroy,
                 bg=CLR_BTN_GREY, fg="white", font=("Arial", 9),
                 relief=tk.FLAT, padx=14, pady=5).pack(pady=5)

    def refresh_table(self):
        """Обновление данных в таблице."""
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Загрузка данных из БД
        data = self.db.get_all_failures()
        structured_ids = set(self.db.get_structured_failure_ids())
        
        # Фильтрация по поисковому запросу
        search = self.search_var.get().lower().strip()
        if search:
            data = [
                row for row in data
                if any(search in str(val).lower() for val in row)
            ]
        
        if self.show_only_structured_var.get():
            data = [row for row in data if row[0] in structured_ids]
        
        # Преобразование в список словарей для сортировки
        records = []
        for row in data:
            records.append({
                "ID": row[0],
                "Система": row[1],
                "Подсистема": row[2],
                "Компонент": row[3],
                "Категория": row[4] if row[4] else "Не указана",
                "Вид отказа": row[5],
                "Причина": row[6],
                "Последствие": row[7],
                "S": row[8],
                "O": row[9],
                "D": row[10],
                "RPN": row[11]
            })
        
        # Сортировка
        reverse = not self._sort_asc
        try:
            records.sort(key=lambda r: r.get(self._sort_col, ""), reverse=reverse)
        except TypeError:
            pass
        
        # Вставка в таблицу
        for idx, r in enumerate(records):
            risk = self.model.get_risk_category(r["RPN"])
            if r["ID"] in structured_ids:
                tag = risk if idx % 2 == 0 else "alt"
            else:
                tag = "incomplete"
            
            self.tree.insert(
                "", tk.END, 
                iid=str(r["ID"]),
                values=(
                    r["ID"], r["Система"], r["Подсистема"], r["Компонент"],
                    r["Категория"], r["Вид отказа"], r["Причина"], r["Последствие"],
                    r["S"], r["O"], r["D"], r["RPN"], risk
                ),
                tags=(tag,)
            )
        
        # Обновление статус-бара
        n = len(records)
        status_text = f"Записей: {n}"
        if search:
            status_text += f"  (фильтр: «{search}»)"
        if self.show_only_structured_var.get():
            status_text += "  |  показаны только актуальные по структуре"
        self.status_var.set(status_text)
    
    def _selected_id(self) -> Optional[int]:
        """Получение ID выбранной записи."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Выберите запись в таблице.")
            return None
        return int(sel[0])
    
    def _sort_by(self, col: str):
        """Сортировка таблицы по колонке."""
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = False
        self.refresh_table()
    
    def update_status(self, message: str):
        """Обновление статусной строки."""
        self.status_var.set(message)
    
    # ═══════════════════════════════════════════════════════════════════
    #  ACTIONS — CRUD ОПЕРАЦИИ
    # ═══════════════════════════════════════════════════════════════════
    
    def show_add_dialog(self):
        """Диалог добавления записи."""
        RecordDialog(self.root, self.db, self.model, title="Добавить запись FMEA", 
                    on_save=self._save_new)
    
    def _save_new(self, data: dict):
        """Сохранение новой записи."""
        try:
            # Валидация
            if not self.model.validate_sod_values(data["severity"], data["occurrence"], data["detection"]):
                messagebox.showerror("Ошибка", "Значения S, O, D должны быть от 1 до 10")
                return
            
            # Добавление компонента
            component_id = self.db.add_component(
                data["system"], data["subsystem"], data["component"], data.get("category_id")
            )
            
            # Добавление отказа
            self.db.add_failure(
                component_id, data["failure_mode"], data["cause"], data["effect"],
                data["severity"], data["occurrence"], data["detection"],
                failure_type_id=data.get("failure_type_id"),
                cause_id=data.get("cause_id"),
                effect_id=data.get("effect_id"),
                function_text=data.get("function_text"),
                local_effect=data.get("local_effect"),
                next_higher_effect=data.get("next_higher_effect"),
                end_effect=data.get("end_effect"),
                recommended_actions=data.get("recommended_actions"),
                action_owner=data.get("action_owner"),
                due_date=data.get("due_date"),
                failure_rate_lambda=data.get("failure_rate_lambda"),
                mode_ratio_alpha=data.get("mode_ratio_alpha"),
                conditional_prob_beta=data.get("conditional_prob_beta"),
                mission_time_t=data.get("mission_time_t"),
                mission_phase=data.get("mission_phase"),
                operating_mode=data.get("operating_mode"),
                residual_severity=data.get("residual_severity"),
                residual_occurrence=data.get("residual_occurrence"),
                residual_detection=data.get("residual_detection"),
                residual_rpn=data.get("residual_rpn")
            )
            
            self.refresh_table()
            self.update_status("Запись добавлена.")
            messagebox.showinfo("Успех", "Запись успешно добавлена")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить запись: {str(e)}")
    
    def edit_record(self):
        """Редактирование записи."""
        rec_id = self._selected_id()
        if rec_id is None:
            return
        
        record = self.db.get_failure_by_id(rec_id)
        
        if not record:
            messagebox.showerror("Ошибка", "Запись не найдена")
            return
        
        RecordDialog(self.root, self.db, self.model, title="Редактировать запись", 
                    initial=record, on_save=lambda d: self._save_edit(rec_id, d))
    
    def _save_edit(self, rec_id: int, data: dict):
        """Сохранение изменений записи."""
        try:
            if not self.model.validate_sod_values(data["severity"], data["occurrence"], data["detection"]):
                messagebox.showerror("Ошибка", "Значения S, O, D должны быть от 1 до 10")
                return
            
            self.db.update_failure_extended(rec_id, data)
            self.refresh_table()
            self.update_status(f"Запись #{rec_id} обновлена.")
            messagebox.showinfo("Успех", "Запись обновлена")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить запись: {str(e)}")
    
    def delete_record(self):
        """Удаление выбранной записи."""
        rec_id = self._selected_id()
        if rec_id is None:
            return
        
        if messagebox.askyesno("Удаление", f"Удалить запись #{rec_id}?"):
            self.db.delete_failure(rec_id)
            self.refresh_table()
            self.update_status(f"Запись #{rec_id} удалена.")
    
    def recalculate_rpn(self):
        """Пересчёт всех RPN."""
        self.db.recalculate_all_rpn()
        self.refresh_table()
        self.update_status("RPN пересчитаны для всех записей.")
        messagebox.showinfo("Пересчёт", "RPN пересчитаны для всех записей (S × O × D).")
    
    # ═══════════════════════════════════════════════════════════════════
    #  ИМПОРТ/ЭКСПОРТ
    # ═══════════════════════════════════════════════════════════════════
    
    def import_xml(self):
        """Импорт данных из XML."""
        filepath = filedialog.askopenfilename(
            title="Импорт FMEA из XML",
            filetypes=[("XML файлы", "*.xml"), ("Все файлы", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            failures = IOUtils.import_from_xml(filepath)
            
            if not failures:
                messagebox.showerror("Импорт", "Не удалось найти записи в XML-файле.")
                return
            
            # Спрашиваем: заменить или добавить
            replace = messagebox.askyesno(
                "Импорт", 
                f"Найдено {len(failures)} записей.\n\n"
                f"Заменить все существующие данные?\n\n"
                f"[Да] — Заменить все\n[Нет] — Добавить к существующим"
            )
            
            if replace:
                self.db.clear_all_data()
            
            # Добавление записей
            for f in failures:
                category_id = None
                if f.get('category'):
                    category_id = self.db.add_category(f['category'])
                
                comp_id = self.db.add_component(
                    f['system'], f['subsystem'], f['component'], category_id
                )
                
                self.db.add_failure(
                    comp_id, f['mode'], f['cause'], f['effect'],
                    f['severity'], f['occurrence'], f['detection']
                )
            
            self.refresh_table()
            self.update_status(f"Импортировано {len(failures)} записей из XML.")
            messagebox.showinfo("Успех", f"Импортировано записей: {len(failures)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка импорта", str(e))
    
    def _build_standardized_export_df(self, sort_by: str = "rpn") -> pd.DataFrame:
        """Подготовка стандартизированного FMECA DataFrame для экспорта."""
        raw_data = self.db.get_failures_for_standard_report(sort_by=sort_by)
        std_df = self.model.build_standardized_fmeca_dataframe(raw_data)
        return self.model.sort_standardized_fmeca(std_df, sort_by=sort_by)
    
    def export_excel(self):
        """Экспорт в Excel."""
        data = self.db.get_all_failures()
        if not data:
            messagebox.showinfo("Экспорт", "Нет данных для экспорта.")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="Сохранить как Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel файлы", "*.xlsx")]
        )
        
        if not filepath:
            return
        
        try:
            df = self.model.analyze_failures(data)
            standardized_df = self._build_standardized_export_df(sort_by="rpn")
            IOUtils.export_to_excel(df, filepath, standardized_df=standardized_df)
            self.update_status(f"Экспорт в Excel: {os.path.basename(filepath)}")
            messagebox.showinfo(
                "Экспорт",
                f"Файл сохранён:\n{filepath}\n\n"
                f"Добавлены листы стандартизированного FMECA отчёта."
            )
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", str(e))
    
    def export_pdf(self):
        """Экспорт в PDF (простой)."""
        data = self.db.get_all_failures()
        if not data:
            messagebox.showinfo("Экспорт", "Нет данных для экспорта.")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="Сохранить как PDF",
            defaultextension=".pdf",
            filetypes=[("PDF файлы", "*.pdf")]
        )
        
        if not filepath:
            return
        
        try:
            df = self.model.analyze_failures(data)
            standardized_df = self._build_standardized_export_df(sort_by="rpn")
            IOUtils.export_to_pdf(df, filepath, standardized_df=standardized_df)
            self.update_status(f"Экспорт в PDF: {os.path.basename(filepath)}")
            messagebox.showinfo(
                "Экспорт",
                f"Файл сохранён:\n{filepath}\n\n"
                f"Добавлен блок стандартизированного FMECA отчёта."
            )
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", str(e))
    
    def export_full_report_pdf(self):
        """Экспорт ПОЛНОГО отчёта с графиками."""
        data = self.db.get_all_failures()
        if not data:
            messagebox.showwarning("Нет данных", "Добавьте записи для формирования отчёта")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="Сохранить полный отчёт",
            defaultextension=".pdf",
            filetypes=[("PDF файлы", "*.pdf")]
        )
        
        if not filepath:
            return
        
        try:
            df = self.model.analyze_failures(data)
            standardized_df = self._build_standardized_export_df(sort_by="rpn")
            ReportGenerator.generate_full_report(
                df, filepath, report_format='pdf', standardized_df=standardized_df
            )
            self.update_status(f"Полный отчёт: {os.path.basename(filepath)}")
            messagebox.showinfo("Успех", f"Полный отчёт сохранён:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    # ═══════════════════════════════════════════════════════════════════
    #  ВИЗУАЛИЗАЦИЯ И АНАЛИЗ
    # ═══════════════════════════════════════════════════════════════════
    
    def show_charts_menu(self):
        """Меню графиков."""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="📊 Распределение RPN", command=self.plot_rpn_distribution)
        menu.add_command(label="📊 RPN по компонентам", command=self.plot_rpn_by_component)
        menu.add_command(label="📊 RPN по категориям", command=self.plot_rpn_by_category)
        menu.add_separator()
        menu.add_command(label="🎯 Категории риска", command=self.plot_risk_categories)
        menu.add_command(label="🔥 Матрица S-O", command=self.plot_so_matrix)
        menu.add_command(label="🔥 Матрица критичности", command=self.plot_criticality_matrix)
        menu.add_separator()
        menu.add_command(label="🕸 Граф зависимостей", command=self.show_dependency_graph)  # НОВОЕ
        
        try:
            menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            menu.grab_release()
    
    def plot_rpn_distribution(self):
        data = self.db.get_all_failures()
        if not data:
            messagebox.showwarning("Нет данных", "Добавьте записи для визуализации")
            return
        df = self.model.analyze_failures(data)
        Visualization.plot_rpn_distribution(df)
    
    def plot_rpn_by_component(self):
        data = self.db.get_all_failures()
        if not data:
            messagebox.showwarning("Нет данных", "Добавьте записи для визуализации")
            return
        df = self.model.analyze_failures(data)
        Visualization.plot_rpn_by_component(df)
    
    def plot_rpn_by_category(self):
        data = self.db.get_all_failures()
        if not data:
            messagebox.showwarning("Нет данных", "Добавьте записи для визуализации")
            return
        df = self.model.analyze_failures(data)
        Visualization.plot_rpn_by_category(df)
    
    def plot_risk_categories(self):
        data = self.db.get_all_failures()
        if not data:
            messagebox.showwarning("Нет данных", "Добавьте записи для визуализации")
            return
        df = self.model.analyze_failures(data)
        Visualization.plot_risk_categories(df)
    
    def plot_so_matrix(self):
        data = self.db.get_all_failures()
        if not data:
            messagebox.showwarning("Нет данных", "Добавьте записи для визуализации")
            return
        df = self.model.analyze_failures(data)
        Visualization.plot_severity_occurrence_matrix(df)
    
    def plot_criticality_matrix(self):
        data = self.db.get_all_failures()
        if not data:
            messagebox.showwarning("Нет данных", "Добавьте записи для визуализации")
            return
        df = self.model.analyze_failures(data)
        Visualization.plot_criticality_matrix(df)
    
    # ═══════════════════════════════════════════════════════════════════
    #  СПРАВОЧНИКИ
    # ═══════════════════════════════════════════════════════════════════
    
    def show_dict_menu(self):
        """Меню справочников."""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="📁 Категории компонентов", command=self.manage_categories)
        menu.add_command(label="⚠️ Типы отказов", command=self.manage_failure_types)
        menu.add_command(label="🔍 Причины отказов", command=self.manage_causes)
        menu.add_command(label="⚡ Последствия отказов", command=self.manage_effects)
        menu.add_separator()
        menu.add_command(label="📊 Статистика", command=self.show_statistics)
        menu.add_command(label="🏆 Топ-10 рисков", command=self.show_top_risks)
        
        try:
            menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            menu.grab_release()
    
    def manage_categories(self):
        """Окно управления категориями."""
        win = tk.Toplevel(self.root)
        win.title("Категории компонентов")
        win.geometry("500x400")
        win.configure(bg=CLR_BG)
        win.grab_set()
        
        listbox = tk.Listbox(win, height=15, font=("Arial", 10))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        categories = self.db.get_all_categories()
        for _, name in categories:
            listbox.insert(tk.END, name)
        
        btn_frame = tk.Frame(win, bg=CLR_BG)
        btn_frame.pack(pady=5)
        
        def add_cat():
            name = simpledialog.askstring("Добавить", "Название категории:", parent=win)
            if name:
                self.db.add_category(name)
                listbox.insert(tk.END, name)
        
        tk.Button(btn_frame, text="➕ Добавить", command=add_cat, 
                 bg=CLR_BTN_GRN, fg="white", font=("Arial", 9, "bold"),
                 relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Закрыть", command=win.destroy,
                 bg=CLR_BTN_GREY, fg="white", font=("Arial", 9),
                 relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=5)
    
    def manage_failure_types(self):
        """Окно управления типами отказов."""
        win = tk.Toplevel(self.root)
        win.title("Типы отказов")
        win.geometry("700x420")
        win.configure(bg=CLR_BG)
        win.grab_set()
        
        columns = ("ID", "Название", "S", "O", "D")
        tree = ttk.Treeview(win, columns=columns, show="headings", style="FMEA.Treeview")
        for col, width in zip(columns, [60, 340, 60, 60, 60]):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor=tk.W if col == "Название" else tk.CENTER)
        
        def refresh():
            for item in tree.get_children():
                tree.delete(item)
            for ft in self.db.get_all_failure_types():
                tree.insert("", tk.END, values=(ft[0], ft[1], ft[2], ft[3], ft[4]))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        btn_frame = tk.Frame(win, bg=CLR_BG)
        btn_frame.pack(pady=6)
        
        def add_item():
            name = simpledialog.askstring("Новый тип отказа", "Название:", parent=win)
            if not name:
                return
            try:
                s = simpledialog.askinteger("S", "Default Severity (1-10):", parent=win, minvalue=1, maxvalue=10) or 5
                o = simpledialog.askinteger("O", "Default Occurrence (1-10):", parent=win, minvalue=1, maxvalue=10) or 5
                d = simpledialog.askinteger("D", "Default Detection (1-10):", parent=win, minvalue=1, maxvalue=10) or 5
                self.db.add_failure_type(name=name, default_s=s, default_o=o, default_d=d)
                refresh()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e), parent=win)
        
        tk.Button(btn_frame, text="➕ Добавить", command=add_item,
                  bg=CLR_BTN_GRN, fg="white", font=("Arial", 9, "bold"),
                  relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Обновить", command=refresh,
                  bg=CLR_BTN_BLUE, fg="white", font=("Arial", 9),
                  relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Закрыть", command=win.destroy,
                  bg=CLR_BTN_GREY, fg="white", font=("Arial", 9),
                  relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=5)
        
        refresh()
    
    def manage_causes(self):
        """Окно управления причинами отказов."""
        win = tk.Toplevel(self.root)
        win.title("Причины отказов")
        win.geometry("640x420")
        win.configure(bg=CLR_BG)
        win.grab_set()
        
        columns = ("ID", "Название")
        tree = ttk.Treeview(win, columns=columns, show="headings", style="FMEA.Treeview")
        tree.heading("ID", text="ID")
        tree.heading("Название", text="Название")
        tree.column("ID", width=70, anchor=tk.CENTER)
        tree.column("Название", width=520, anchor=tk.W)
        
        def refresh():
            for item in tree.get_children():
                tree.delete(item)
            for cause in self.db.get_all_causes():
                tree.insert("", tk.END, values=(cause[0], cause[1]))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        btn_frame = tk.Frame(win, bg=CLR_BG)
        btn_frame.pack(pady=6)
        
        def add_item():
            name = simpledialog.askstring("Новая причина", "Название причины:", parent=win)
            if not name:
                return
            try:
                self.db.add_cause(name=name)
                refresh()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e), parent=win)
        
        tk.Button(btn_frame, text="➕ Добавить", command=add_item,
                  bg=CLR_BTN_GRN, fg="white", font=("Arial", 9, "bold"),
                  relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Обновить", command=refresh,
                  bg=CLR_BTN_BLUE, fg="white", font=("Arial", 9),
                  relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Закрыть", command=win.destroy,
                  bg=CLR_BTN_GREY, fg="white", font=("Arial", 9),
                  relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=5)
        
        refresh()
    
    def manage_effects(self):
        """Окно управления последствиями отказов."""
        win = tk.Toplevel(self.root)
        win.title("Последствия отказов")
        win.geometry("640x420")
        win.configure(bg=CLR_BG)
        win.grab_set()
        
        columns = ("ID", "Название")
        tree = ttk.Treeview(win, columns=columns, show="headings", style="FMEA.Treeview")
        tree.heading("ID", text="ID")
        tree.heading("Название", text="Название")
        tree.column("ID", width=70, anchor=tk.CENTER)
        tree.column("Название", width=520, anchor=tk.W)
        
        def refresh():
            for item in tree.get_children():
                tree.delete(item)
            for effect in self.db.get_all_effects():
                tree.insert("", tk.END, values=(effect[0], effect[1]))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        btn_frame = tk.Frame(win, bg=CLR_BG)
        btn_frame.pack(pady=6)
        
        def add_item():
            name = simpledialog.askstring("Новое последствие", "Название последствия:", parent=win)
            if not name:
                return
            try:
                self.db.add_effect(name=name)
                refresh()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e), parent=win)
        
        tk.Button(btn_frame, text="➕ Добавить", command=add_item,
                  bg=CLR_BTN_GRN, fg="white", font=("Arial", 9, "bold"),
                  relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Обновить", command=refresh,
                  bg=CLR_BTN_BLUE, fg="white", font=("Arial", 9),
                  relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Закрыть", command=win.destroy,
                  bg=CLR_BTN_GREY, fg="white", font=("Arial", 9),
                  relief=tk.FLAT, padx=10, pady=4).pack(side=tk.LEFT, padx=5)
        
        refresh()
    
    def show_statistics(self):
        """Показ статистики."""
        data = self.db.get_all_failures()
        if not data:
            messagebox.showinfo("Статистика", "Нет данных для анализа")
            return
        
        df = self.model.analyze_failures(data)
        stats = self.model.calculate_statistics(df)
        
        stats_text = f"""
Статистика FMEA-анализа:

Всего отказов: {stats['total_failures']}
Средний RPN: {stats['avg_rpn']:.2f}
Максимальный RPN: {stats['max_rpn']}
Минимальный RPN: {stats['min_rpn']}

Распределение по категориям:
• Критических (RPN ≥ 200): {stats['critical_count']}
• Высоких (100 ≤ RPN < 200): {stats['high_count']}
• Средних (40 ≤ RPN < 100): {stats['medium_count']}
• Низких (RPN < 40): {stats['low_count']}
        """
        
        messagebox.showinfo("Статистика", stats_text)
    
    def show_quality_dashboard(self):
        """Окно качества анализа FMECA."""
        records = self.db.get_failures_for_quality_dashboard()
        dashboard = self.model.build_quality_dashboard(records, top_n=20, low_completeness_threshold=80.0)
        summary = dashboard["summary"]
        
        win = tk.Toplevel(self.root)
        win.title("Качество анализа FMECA")
        win.geometry("1100x550")
        win.configure(bg=CLR_BG)
        win.grab_set()
        
        summary_text = (
            f"Всего записей: {summary['total_records']}    |    "
            f"Средняя полнота: {summary['average_analysis_completeness_score']}%    |    "
            f"Полностью заполнены: {summary['fully_completed_percent']}% "
            f"({summary['fully_completed_count']})"
        )
        tk.Label(win, text=summary_text, bg=CLR_BG, font=("Arial", 10, "bold")).pack(pady=10)
        
        cols = ("ID", "Компонент", "Вид отказа", "Полнота (%)", "Пропущенные поля")
        tree = ttk.Treeview(win, columns=cols, show="headings", style="FMEA.Treeview")
        for col, width in zip(cols, [60, 170, 220, 110, 500]):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor=tk.W if col in ("Компонент", "Вид отказа", "Пропущенные поля") else tk.CENTER)
        
        for row in dashboard["problematic_records"]:
            tree.insert("", tk.END, values=(
                row.get("id"),
                row.get("component") or "",
                row.get("failure_mode") or "",
                row.get("analysis_completeness_score"),
                ", ".join(row.get("missing_fields", []))
            ))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
    
    def explain_selected_risk(self):
        """Пояснение риска для выбранной записи."""
        rec_id = self._selected_id()
        if rec_id is None:
            return
        
        record = self.db.get_failure_by_id(rec_id)
        if not record:
            messagebox.showerror("Ошибка", "Запись не найдена")
            return
        
        explanation = self.model.explain_risk(record)
        messagebox.showinfo("Пояснение критичности отказа", explanation)
    
    def prune_to_structured_records(self):
        """Удаление неактуальных по структуре записей из текущей БД."""
        if not messagebox.askyesno(
            "Подтверждение очистки",
            "Будут удалены все записи, не соответствующие актуальной FMECA-структуре.\n"
            "Операция необратима для текущей БД.\n\nПродолжить?"
        ):
            return
        
        stats = self.db.prune_to_structured_failures()
        self.refresh_table()
        self.update_status(
            f"Очистка завершена: удалено {stats['deleted']} из {stats['total_before']} записей."
        )
        messagebox.showinfo(
            "Очистка завершена",
            f"Было записей: {stats['total_before']}\n"
            f"Удалено: {stats['deleted']}\n"
            f"Осталось актуальных: {stats['total_after']}"
        )
    
    def show_top_risks(self):
        """Показ топ-10 рисков."""
        data = self.db.get_all_failures()
        if not data:
            messagebox.showinfo("Топ-риски", "Нет данных")
            return
        
        df = self.model.analyze_failures(data)
        top = ReportGenerator.get_top_risks_report(df, n=10)
        
        win = tk.Toplevel(self.root)
        win.title("Топ-10 критических рисков")
        win.geometry("1200x400")
        win.configure(bg=CLR_BG)
        win.grab_set()
        
        cols = ['Компонент', 'Категория', 'Вид отказа', 'S', 'O', 'D', 'RPN']
        
        style = ttk.Style()
        style.configure("Top.Treeview", rowheight=24, font=("Arial", 9))
        
        tree = ttk.Treeview(win, columns=cols, show='headings', style="Top.Treeview")
        
        widths = [150, 120, 200, 50, 50, 50, 70]
        for col, width in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor=tk.CENTER if col in ['S','O','D','RPN'] else tk.W)
        
        for row in top.itertuples():
            tree.insert('', tk.END, values=(
                row.Компонент, row.Категория, row._6, row.S, row.O, row.D, row.RPN
            ))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Button(win, text="Закрыть", command=win.destroy,
                 bg=CLR_BTN_GREY, fg="white", font=("Arial", 9),
                 relief=tk.FLAT, padx=14, pady=5).pack(pady=5)
    
    def run(self):
        """Запуск главного цикла приложения."""
        self.root.mainloop()
    
    def __del__(self):
        """Закрытие БД при завершении."""
        if hasattr(self, 'db'):
            self.db.close()


# ═══════════════════════════════════════════════════════════════════════
#  RECORD DIALOG — диалог добавления / редактирования записи
# ═══════════════════════════════════════════════════════════════════════

class RecordDialog:
    """Модальный диалог для ввода/редактирования записи FMEA."""
    
    def __init__(self, parent, db: Database, model: FMEAModel, 
                 title: str, on_save, initial: dict = None):
        self.db = db
        self.model = model
        self.on_save = on_save
        self.initial = initial or {}
        
        self.win = tk.Toplevel(parent)
        self.win.title(title)
        self.win.grab_set()
        self.win.resizable(False, False)
        self.win.configure(bg=CLR_BG)
        
        # Кэши
        self.current_category_id = None
        self.current_failure_type_id = None
        self.category_data = {}
        self.failure_type_data = {}
        self.cause_data = {}
        self.effect_data = {}
        
        self._build()
        self._populate(self.initial)
        
        # Центрирование
        self.win.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.win.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.win.winfo_height()) // 2
        self.win.geometry(f"+{x}+{y}")
    
    def _build(self):
        """Построение интерфейса диалога."""
        pad = dict(padx=10, pady=4)
        
        # ── Верхняя часть: текстовые поля ──
        top = tk.LabelFrame(
            self.win, 
            text=" Данные об объекте и отказе ",
            bg=CLR_BG, font=("Arial", 9, "bold"), 
            padx=8, pady=6
        )
        top.pack(fill=tk.X, padx=12, pady=(12, 4))
        
        # Две колонки
        left_frame = tk.Frame(top, bg=CLR_BG)
        right_frame = tk.Frame(top, bg=CLR_BG)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0))
        
        # Левая колонка
        self.vars = {}
        
        # Система
        tk.Label(left_frame, text="Система *", bg=CLR_BG, anchor=tk.W, 
                font=("Arial", 9)).pack(fill=tk.X, **pad)
        self.vars["system"] = tk.StringVar()
        tk.Entry(left_frame, textvariable=self.vars["system"], width=34,
                font=("Arial", 9)).pack(fill=tk.X, padx=10)
        
        # Подсистема
        tk.Label(left_frame, text="Подсистема", bg=CLR_BG, anchor=tk.W,
                font=("Arial", 9)).pack(fill=tk.X, **pad)
        self.vars["subsystem"] = tk.StringVar()
        tk.Entry(left_frame, textvariable=self.vars["subsystem"], width=34,
                font=("Arial", 9)).pack(fill=tk.X, padx=10)
        
        # Компонент
        tk.Label(left_frame, text="Компонент *", bg=CLR_BG, anchor=tk.W,
                font=("Arial", 9)).pack(fill=tk.X, **pad)
        self.vars["component"] = tk.StringVar()
        tk.Entry(left_frame, textvariable=self.vars["component"], width=34,
                font=("Arial", 9)).pack(fill=tk.X, padx=10)
        
        # Категория (Combobox + кнопка)
        tk.Label(left_frame, text="Категория", bg=CLR_BG, anchor=tk.W,
                font=("Arial", 9)).pack(fill=tk.X, **pad)
        cat_frame = tk.Frame(left_frame, bg=CLR_BG)
        cat_frame.pack(fill=tk.X, padx=10)
        
        self.combo_category = ttk.Combobox(cat_frame, width=28, state='readonly')
        self.combo_category.pack(side=tk.LEFT)
        self.combo_category.bind('<<ComboboxSelected>>', self.on_category_selected)
        
        tk.Button(cat_frame, text="+", width=2, command=self.add_new_category,
                 bg=CLR_BTN_BLUE, fg="white", font=("Arial", 8, "bold"),
                 relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=2)
        
        # Правая колонка
        
        # Тип отказа
        tk.Label(right_frame, text="Тип отказа", bg=CLR_BG, anchor=tk.W,
                font=("Arial", 9)).pack(fill=tk.X, **pad)
        ft_frame = tk.Frame(right_frame, bg=CLR_BG)
        ft_frame.pack(fill=tk.X, padx=10)
        
        self.combo_failure_type = ttk.Combobox(ft_frame, width=28, state='readonly')
        self.combo_failure_type.pack(side=tk.LEFT)
        self.combo_failure_type.bind('<<ComboboxSelected>>', self.on_failure_type_selected)
        
        tk.Button(ft_frame, text="+", width=2, command=self.add_new_failure_type,
                 bg=CLR_BTN_BLUE, fg="white", font=("Arial", 8, "bold"),
                 relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=2)
        
        # Вид отказа (текстовое поле)
        tk.Label(right_frame, text="Вид отказа *", bg=CLR_BG, anchor=tk.W,
                font=("Arial", 9)).pack(fill=tk.X, **pad)
        self.vars["failure_mode"] = tk.StringVar()
        tk.Entry(right_frame, textvariable=self.vars["failure_mode"], width=34,
                font=("Arial", 9)).pack(fill=tk.X, padx=10)
        
        # Причина
        tk.Label(right_frame, text="Причина *", bg=CLR_BG, anchor=tk.W,
                font=("Arial", 9)).pack(fill=tk.X, **pad)
        cause_frame = tk.Frame(right_frame, bg=CLR_BG)
        cause_frame.pack(fill=tk.X, padx=10)
        
        self.combo_cause = ttk.Combobox(cause_frame, width=28, state='readonly')
        self.combo_cause.pack(side=tk.LEFT)
        
        tk.Button(cause_frame, text="+", width=2, command=self.add_new_cause,
                 bg=CLR_BTN_BLUE, fg="white", font=("Arial", 8, "bold"),
                 relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=2)
        
        # Последствие
        tk.Label(right_frame, text="Последствие *", bg=CLR_BG, anchor=tk.W,
                font=("Arial", 9)).pack(fill=tk.X, **pad)
        effect_frame = tk.Frame(right_frame, bg=CLR_BG)
        effect_frame.pack(fill=tk.X, padx=10)
        
        self.combo_effect = ttk.Combobox(effect_frame, width=28, state='readonly')
        self.combo_effect.pack(side=tk.LEFT)
        
        tk.Button(effect_frame, text="+", width=2, command=self.add_new_effect,
                 bg=CLR_BTN_BLUE, fg="white", font=("Arial", 8, "bold"),
                 relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=2)
        
        # ── Нижняя часть: оценки S, O, D ──
        sod_frame = tk.LabelFrame(
            self.win, 
            text=" Оценки риска (1–10) ",
            bg=CLR_BG, font=("Arial", 9, "bold"), 
            padx=8, pady=8
        )
        sod_frame.pack(fill=tk.X, padx=12, pady=4)
        
        sod_fields = [
            ("S — Severity\n(Тяжесть последствий)", "severity"),
            ("O — Occurrence\n(Вероятность возникновения)", "occurrence"),
            ("D — Detection\n(Обнаруживаемость)", "detection"),
        ]
        
        self.sod_vars = {}
        self.rpn_var = tk.StringVar(value="RPN = —")
        
        for label, key in sod_fields:
            col = tk.Frame(sod_frame, bg=CLR_BG)
            col.pack(side=tk.LEFT, padx=20)
            tk.Label(col, text=label, bg=CLR_BG, font=("Arial", 8), 
                    justify=tk.CENTER).pack()
            self.sod_vars[key] = tk.IntVar(value=5)
            spin = tk.Spinbox(
                col, from_=1, to=10, textvariable=self.sod_vars[key],
                width=5, font=("Arial", 11, "bold"),
                command=self._update_rpn, justify=tk.CENTER
            )
            spin.pack(pady=4)
            self.sod_vars[key].trace_add("write", lambda *_: self._update_rpn())
        
        # RPN preview
        rpn_frame = tk.Frame(sod_frame, bg=CLR_BG)
        rpn_frame.pack(side=tk.LEFT, padx=20)
        tk.Label(rpn_frame, text="RPN = S × O × D", bg=CLR_BG, 
                font=("Arial", 8)).pack()
        self.rpn_label = tk.Label(
            rpn_frame, textvariable=self.rpn_var,
            bg=CLR_BG, font=("Arial", 16, "bold"), fg=CLR_BTN_RED
        )
        self.rpn_label.pack(pady=4)
        
        self._update_rpn()
        
        # ── Расширенные поля FMECA / MIL / residual risk ──
        advanced_frame = tk.LabelFrame(
            self.win,
            text=" Расширенные поля FMECA / MIL / Residual ",
            bg=CLR_BG, font=("Arial", 9, "bold"),
            padx=8, pady=8
        )
        advanced_frame.pack(fill=tk.X, padx=12, pady=4)
        tk.Label(
            advanced_frame,
            text="* — обязательные поля FMECA. Поля MIL (λ, α, β, t) заполняются при наличии расчетных данных надежности.",
            bg=CLR_BG, fg="#37474F", font=("Arial", 8, "italic"), anchor=tk.W, justify=tk.LEFT
        ).grid(row=0, column=0, columnspan=4, sticky=tk.W, padx=6, pady=(0, 4))
        
        self.vars["function_text"] = tk.StringVar()
        self.vars["local_effect"] = tk.StringVar()
        self.vars["next_higher_effect"] = tk.StringVar()
        self.vars["end_effect"] = tk.StringVar()
        self.vars["recommended_actions"] = tk.StringVar()
        self.vars["action_owner"] = tk.StringVar()
        self.vars["due_date"] = tk.StringVar()
        self.vars["mission_phase"] = tk.StringVar()
        self.vars["operating_mode"] = tk.StringVar()
        
        self.mil_vars = {
            "failure_rate_lambda": tk.StringVar(),
            "mode_ratio_alpha": tk.StringVar(),
            "conditional_prob_beta": tk.StringVar(),
            "mission_time_t": tk.StringVar(),
        }
        
        # Категоризируемые справочники значений для однозначного ввода
        function_options = [
            "Обработка вычислительных задач",
            "Хранение оперативных данных",
            "Долговременное хранение данных",
            "Стабилизация электропитания",
            "Передача сетевого трафика",
            "Охлаждение и теплоотвод",
        ]
        effect_options = [
            "Снижение производительности",
            "Рост задержек",
            "Сбой вычислительных модулей",
            "Потеря доступности подсистемы",
            "Риск потери данных",
            "Срыв SLA/критичного сервиса",
        ]
        mission_phase_options = [
            "Проектирование",
            "Интеграция",
            "Испытания",
            "Эксплуатация",
            "Техническое обслуживание",
        ]
        operating_mode_options = [
            "Номинальный",
            "Пиковая нагрузка",
            "Резервный",
            "Деградированный",
            "Пуск/останов",
        ]
        action_options = [
            "Замена компонента",
            "Плановое техническое обслуживание",
            "Обновление прошивки/ПО",
            "Усиление мониторинга",
            "Изменение режима эксплуатации",
        ]
        owner_options = [
            "Инженер по надежности",
            "Системный инженер",
            "Инженер эксплуатации",
            "DBA",
            "Сетевой инженер",
        ]
        
        self.residual_vars = {
            "residual_severity": tk.IntVar(value=5),
            "residual_occurrence": tk.IntVar(value=5),
            "residual_detection": tk.IntVar(value=5),
            "residual_rpn": tk.StringVar(value=""),
        }
        
        # Текстовые поля
        grid_pad = {"padx": 6, "pady": 3}
        tk.Label(advanced_frame, text="Функция компонента *", bg=CLR_BG, font=("Arial", 8)).grid(row=1, column=0, sticky=tk.W, **grid_pad)
        self.combo_function = ttk.Combobox(
            advanced_frame, textvariable=self.vars["function_text"], values=function_options, width=26, state="readonly"
        )
        self.combo_function.grid(row=1, column=1, sticky=tk.W, **grid_pad)
        tk.Label(advanced_frame, text="Фаза миссии", bg=CLR_BG, font=("Arial", 8)).grid(row=1, column=2, sticky=tk.W, **grid_pad)
        self.combo_mission_phase = ttk.Combobox(
            advanced_frame, textvariable=self.vars["mission_phase"], values=mission_phase_options, width=18, state="readonly"
        )
        self.combo_mission_phase.grid(row=1, column=3, sticky=tk.W, **grid_pad)
        
        tk.Label(advanced_frame, text="Локальный эффект *", bg=CLR_BG, font=("Arial", 8)).grid(row=2, column=0, sticky=tk.W, **grid_pad)
        self.combo_local_effect = ttk.Combobox(
            advanced_frame, textvariable=self.vars["local_effect"], values=effect_options, width=26, state="readonly"
        )
        self.combo_local_effect.grid(row=2, column=1, sticky=tk.W, **grid_pad)
        tk.Label(advanced_frame, text="Режим работы", bg=CLR_BG, font=("Arial", 8)).grid(row=2, column=2, sticky=tk.W, **grid_pad)
        self.combo_operating_mode = ttk.Combobox(
            advanced_frame, textvariable=self.vars["operating_mode"], values=operating_mode_options, width=18, state="readonly"
        )
        self.combo_operating_mode.grid(row=2, column=3, sticky=tk.W, **grid_pad)
        
        tk.Label(advanced_frame, text="Эффект верхнего уровня *", bg=CLR_BG, font=("Arial", 8)).grid(row=3, column=0, sticky=tk.W, **grid_pad)
        self.combo_next_effect = ttk.Combobox(
            advanced_frame, textvariable=self.vars["next_higher_effect"], values=effect_options, width=26, state="readonly"
        )
        self.combo_next_effect.grid(row=3, column=1, sticky=tk.W, **grid_pad)
        tk.Label(advanced_frame, text="Конечный эффект *", bg=CLR_BG, font=("Arial", 8)).grid(row=3, column=2, sticky=tk.W, **grid_pad)
        self.combo_end_effect = ttk.Combobox(
            advanced_frame, textvariable=self.vars["end_effect"], values=effect_options, width=18, state="readonly"
        )
        self.combo_end_effect.grid(row=3, column=3, sticky=tk.W, **grid_pad)
        
        tk.Label(advanced_frame, text="Рекомендуемые меры *", bg=CLR_BG, font=("Arial", 8)).grid(row=4, column=0, sticky=tk.W, **grid_pad)
        self.combo_actions = ttk.Combobox(
            advanced_frame, textvariable=self.vars["recommended_actions"], values=action_options, width=26, state="readonly"
        )
        self.combo_actions.grid(row=4, column=1, sticky=tk.W, **grid_pad)
        tk.Label(advanced_frame, text="Ответственный *", bg=CLR_BG, font=("Arial", 8)).grid(row=4, column=2, sticky=tk.W, **grid_pad)
        self.combo_owner = ttk.Combobox(
            advanced_frame, textvariable=self.vars["action_owner"], values=owner_options, width=18, state="readonly"
        )
        self.combo_owner.grid(row=4, column=3, sticky=tk.W, **grid_pad)
        
        tk.Label(advanced_frame, text="Срок выполнения (ГГГГ-ММ-ДД) *", bg=CLR_BG, font=("Arial", 8)).grid(row=5, column=0, sticky=tk.W, **grid_pad)
        tk.Entry(advanced_frame, textvariable=self.vars["due_date"], width=28, font=("Arial", 9)).grid(row=5, column=1, sticky=tk.W, **grid_pad)
        
        # MIL-параметры
        tk.Label(advanced_frame, text="λ — интенсивность отказов (1/ч)", bg=CLR_BG, font=("Arial", 8)).grid(row=6, column=0, sticky=tk.W, **grid_pad)
        tk.Entry(advanced_frame, textvariable=self.mil_vars["failure_rate_lambda"], width=12, font=("Arial", 9)).grid(row=6, column=1, sticky=tk.W, **grid_pad)
        tk.Label(advanced_frame, text="α — доля режима отказа", bg=CLR_BG, font=("Arial", 8)).grid(row=6, column=2, sticky=tk.W, **grid_pad)
        tk.Entry(advanced_frame, textvariable=self.mil_vars["mode_ratio_alpha"], width=8, font=("Arial", 9)).grid(row=6, column=3, sticky=tk.W, **grid_pad)
        
        tk.Label(advanced_frame, text="β — условная вероятность эффекта", bg=CLR_BG, font=("Arial", 8)).grid(row=7, column=0, sticky=tk.W, **grid_pad)
        tk.Entry(advanced_frame, textvariable=self.mil_vars["conditional_prob_beta"], width=12, font=("Arial", 9)).grid(row=7, column=1, sticky=tk.W, **grid_pad)
        tk.Label(advanced_frame, text="t — время миссии (ч)", bg=CLR_BG, font=("Arial", 8)).grid(row=7, column=2, sticky=tk.W, **grid_pad)
        tk.Entry(advanced_frame, textvariable=self.mil_vars["mission_time_t"], width=8, font=("Arial", 9)).grid(row=7, column=3, sticky=tk.W, **grid_pad)
        
        # Residual risk
        tk.Label(advanced_frame, text="Остаточные S/O/D", bg=CLR_BG, font=("Arial", 8, "bold")).grid(row=8, column=0, sticky=tk.W, **grid_pad)
        tk.Spinbox(advanced_frame, from_=1, to=10, textvariable=self.residual_vars["residual_severity"], width=4, command=self._update_residual_rpn).grid(row=8, column=1, sticky=tk.W, **grid_pad)
        tk.Spinbox(advanced_frame, from_=1, to=10, textvariable=self.residual_vars["residual_occurrence"], width=4, command=self._update_residual_rpn).grid(row=8, column=1, sticky=tk.W, padx=(46, 0), pady=3)
        tk.Spinbox(advanced_frame, from_=1, to=10, textvariable=self.residual_vars["residual_detection"], width=4, command=self._update_residual_rpn).grid(row=8, column=1, sticky=tk.W, padx=(86, 0), pady=3)
        tk.Label(advanced_frame, text="Остаточный RPN", bg=CLR_BG, font=("Arial", 8)).grid(row=8, column=2, sticky=tk.W, **grid_pad)
        tk.Entry(advanced_frame, textvariable=self.residual_vars["residual_rpn"], width=8, font=("Arial", 9)).grid(row=8, column=3, sticky=tk.W, **grid_pad)
        
        self.residual_vars["residual_severity"].trace_add("write", lambda *_: self._update_residual_rpn())
        self.residual_vars["residual_occurrence"].trace_add("write", lambda *_: self._update_residual_rpn())
        self.residual_vars["residual_detection"].trace_add("write", lambda *_: self._update_residual_rpn())
        self._update_residual_rpn()
        
        # ── Кнопки ──
        btn_frame = tk.Frame(self.win, bg=CLR_BG)
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame, text="💾  Сохранить", command=self._on_save,
            bg=CLR_BTN_GRN, fg="white", font=("Arial", 10, "bold"),
            padx=14, pady=5, relief=tk.FLAT, cursor="hand2"
        ).pack(side=tk.LEFT, padx=8)
        
        tk.Button(
            btn_frame, text="Отмена", command=self.win.destroy,
            bg=CLR_BTN_GREY, fg="white", font=("Arial", 10),
            padx=14, pady=5, relief=tk.FLAT, cursor="hand2"
        ).pack(side=tk.LEFT, padx=8)
        
        # Загрузка категорий
        self.load_categories()
    
    def _populate(self, data: dict):
        """Заполнение формы начальными данными."""
        for key, var in self.vars.items():
            var.set(str(data.get(key, "")))
        
        for key, var in self.mil_vars.items():
            value = data.get(key)
            var.set("" if value is None else str(value))
        
        for key, var in self.sod_vars.items():
            val = data.get(key, 5)
            try:
                var.set(int(val))
            except (TypeError, ValueError):
                var.set(5)
        
        for key in ["residual_severity", "residual_occurrence", "residual_detection"]:
            val = data.get(key, 5)
            try:
                self.residual_vars[key].set(int(val) if val is not None else 5)
            except (TypeError, ValueError):
                self.residual_vars[key].set(5)
        
        self.residual_vars["residual_rpn"].set("" if data.get("residual_rpn") is None else str(data.get("residual_rpn")))
        
        # Восстановление комбобоксов при редактировании
        category_name = data.get("category")
        if category_name and category_name in self.category_data:
            self.combo_category.set(category_name)
            self.on_category_selected(None)
        if data.get("cause"):
            self.combo_cause.set(str(data.get("cause")))
        if data.get("effect"):
            self.combo_effect.set(str(data.get("effect")))
        
        self._update_rpn()
        self._update_residual_rpn()
    
    def _update_rpn(self):
        """Обновление RPN preview."""
        try:
            s = self.sod_vars["severity"].get()
            o = self.sod_vars["occurrence"].get()
            d = self.sod_vars["detection"].get()
            rpn = s * o * d
            level = self.model.get_risk_category(rpn)
            self.rpn_var.set(f"{rpn}  [{level}]")
            
            # Цвет по уровню риска
            colors_map = {
                "Низкий": "#2E7D32", 
                "Средний": "#E65100",
                "Высокий": "#BF360C", 
                "Критический": "#B71C1C"
            }
            self.rpn_label.configure(fg=colors_map.get(level, "#333333"))
        except Exception:
            self.rpn_var.set("RPN = ?")
    
    def _update_residual_rpn(self):
        """Обновление residual RPN preview."""
        try:
            rs = self.residual_vars["residual_severity"].get()
            ro = self.residual_vars["residual_occurrence"].get()
            rd = self.residual_vars["residual_detection"].get()
            residual = self.model.calc_residual_rpn(rs, ro, rd)
            self.residual_vars["residual_rpn"].set("" if residual is None else str(residual))
        except Exception:
            self.residual_vars["residual_rpn"].set("")
    
    def _on_save(self):
        """Обработчик кнопки сохранения."""
        data = {k: v.get().strip() for k, v in self.vars.items()}
        data.update({k: v.get() for k, v in self.sod_vars.items()})
        data.update({k: v.get().strip() for k, v in self.mil_vars.items()})
        data.update({
            "residual_severity": self.residual_vars["residual_severity"].get(),
            "residual_occurrence": self.residual_vars["residual_occurrence"].get(),
            "residual_detection": self.residual_vars["residual_detection"].get(),
            "residual_rpn": self.residual_vars["residual_rpn"].get().strip(),
        })
        
        # ID из combobox
        category_name = self.combo_category.get()
        data["category_id"] = self.category_data.get(category_name)
        data["failure_type_id"] = self.current_failure_type_id
        
        cause_name = self.combo_cause.get()
        data["cause_id"] = self.cause_data.get(cause_name)
        
        effect_name = self.combo_effect.get()
        data["effect_id"] = self.effect_data.get(effect_name)
        
        # Заполнение текстовых полей из combobox (если не заполнены вручную)
        if not data.get("cause"):
            data["cause"] = cause_name
        if not data.get("effect"):
            data["effect"] = effect_name
        
        # Нормализация числовых полей (пустое -> None)
        for key in ["failure_rate_lambda", "mode_ratio_alpha", "conditional_prob_beta", "mission_time_t"]:
            data[key] = float(data[key]) if data.get(key) else None
        data["residual_rpn"] = int(data["residual_rpn"]) if data.get("residual_rpn") else None
        
        # Проверка требований к actions
        actions_ok, action_error = self.model.validate_action_requirements(
            data.get("recommended_actions"),
            data.get("action_owner"),
            data.get("due_date"),
        )
        if not actions_ok:
            messagebox.showerror("Ошибка валидации", action_error, parent=self.win)
            return
        
        # Рекомендация по полноте эффектов
        hint = self.model.get_effect_completion_recommendation(
            data.get("end_effect"),
            data.get("local_effect"),
        )
        if hint:
            proceed = messagebox.askyesno("Рекомендация", f"{hint}\n\nСохранить запись без local_effect?", parent=self.win)
            if not proceed:
                return
        
        # Валидация
        if not data.get("component"):
            messagebox.showerror("Ошибка", "Поле «Компонент» обязательно.", parent=self.win)
            return
        if not data.get("failure_mode"):
            messagebox.showerror("Ошибка", "Поле «Вид отказа» обязательно.", parent=self.win)
            return
        if not data.get("cause"):
            messagebox.showerror("Ошибка", "Выберите или введите причину отказа.", parent=self.win)
            return
        if not data.get("effect"):
            messagebox.showerror("Ошибка", "Выберите или введите последствие.", parent=self.win)
            return
        
        # Обязательные поля FMECA (актуальная структура)
        required_fmeca_fields = {
            "function_text": "Функция компонента",
            "local_effect": "Локальный эффект",
            "next_higher_effect": "Эффект верхнего уровня",
            "end_effect": "Конечный эффект",
            "recommended_actions": "Рекомендуемые меры",
            "action_owner": "Ответственный",
            "due_date": "Срок выполнения",
        }
        missing = [label for key, label in required_fmeca_fields.items() if not data.get(key)]
        if missing:
            messagebox.showerror(
                "Ошибка валидации",
                "Заполните обязательные поля:\n- " + "\n- ".join(missing),
                parent=self.win
            )
            return
        
        self.on_save(data)
        self.win.destroy()
    
    # ═══════════════════════════════════════════════════════════════════
    #  ЗАГРУЗКА ДАННЫХ В COMBOBOX
    # ═══════════════════════════════════════════════════════════════════
    
    def load_categories(self):
        """Загрузка категорий компонентов."""
        categories = self.db.get_all_categories()
        self.category_data = {name: id for id, name in categories}
        self.combo_category['values'] = list(self.category_data.keys())
    
    def on_category_selected(self, event):
        """Обработчик выбора категории."""
        category_name = self.combo_category.get()
        if not category_name:
            return
        
        self.current_category_id = self.category_data.get(category_name)
        
        # Загрузка типов отказов
        failure_types = self.db.get_failure_types_for_category(self.current_category_id)
        self.failure_type_data = {name: (id, s, o, d) for id, name, s, o, d in failure_types}
        self.combo_failure_type['values'] = list(self.failure_type_data.keys())
        
        # Очистка зависимых полей
        self.combo_failure_type.set('')
        self.combo_cause.set('')
        self.combo_effect.set('')
    
    def on_failure_type_selected(self, event):
        """Обработчик выбора типа отказа."""
        failure_type_name = self.combo_failure_type.get()
        if not failure_type_name:
            return
        
        ft_data = self.failure_type_data.get(failure_type_name)
        if not ft_data:
            return
        
        self.current_failure_type_id, default_s, default_o, default_d = ft_data
        
        # Установка значений S-O-D по умолчанию
        self.sod_vars["severity"].set(default_s)
        self.sod_vars["occurrence"].set(default_o)
        self.sod_vars["detection"].set(default_d)
        
        # Автозаполнение "Вид отказа"
        if not self.vars["failure_mode"].get():
            self.vars["failure_mode"].set(failure_type_name)
        
        # Загрузка причин
        causes = self.db.get_causes_for_failure_type(self.current_failure_type_id)
        self.cause_data = {name: id for id, name in causes}
        self.combo_cause['values'] = list(self.cause_data.keys())
        
        # Загрузка последствий
        effects = self.db.get_effects_for_failure_type(self.current_failure_type_id)
        self.effect_data = {name: id for id, name in effects}
        self.combo_effect['values'] = list(self.effect_data.keys())
        
        self._update_rpn()
    
    # ═══════════════════════════════════════════════════════════════════
    #  ДОБАВЛЕНИЕ НОВЫХ СПРАВОЧНЫХ ЗНАЧЕНИЙ
    # ═══════════════════════════════════════════════════════════════════
    
    def add_new_category(self):
        """Добавление новой категории."""
        name = simpledialog.askstring("Новая категория", "Введите название категории:", 
                                     parent=self.win)
        if name:
            try:
                self.db.add_category(name)
                self.load_categories()
                self.combo_category.set(name)
                messagebox.showinfo("Успех", f"Категория '{name}' добавлена", parent=self.win)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e), parent=self.win)
    
    def add_new_failure_type(self):
        """Добавление нового типа отказа."""
        if not self.current_category_id:
            messagebox.showwarning("Предупреждение", 
                                  "Сначала выберите категорию компонента", 
                                  parent=self.win)
            return
        
        name = simpledialog.askstring("Новый тип отказа", 
                                     "Введите название типа отказа:", 
                                     parent=self.win)
        if name:
            try:
                ft_id = self.db.add_failure_type(name)
                self.db.link_category_to_failure_type(self.current_category_id, ft_id)
                
                # Перезагрузка списка
                self.on_category_selected(None)
                self.combo_failure_type.set(name)
                
                messagebox.showinfo("Успех", f"Тип отказа '{name}' добавлен", parent=self.win)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e), parent=self.win)
    
    def add_new_cause(self):
        """Добавление новой причины."""
        if not self.current_failure_type_id:
            messagebox.showwarning("Предупреждение", 
                                  "Сначала выберите тип отказа", 
                                  parent=self.win)
            return
        
        name = simpledialog.askstring("Новая причина", 
                                     "Введите описание причины:", 
                                     parent=self.win)
        if name:
            try:
                cause_id = self.db.add_cause(name)
                self.db.link_failure_type_to_cause(self.current_failure_type_id, cause_id)
                
                # Перезагрузка списка
                causes = self.db.get_causes_for_failure_type(self.current_failure_type_id)
                self.cause_data = {cname: cid for cid, cname in causes}
                self.combo_cause['values'] = list(self.cause_data.keys())
                self.combo_cause.set(name)
                
                messagebox.showinfo("Успех", "Причина добавлена", parent=self.win)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e), parent=self.win)
    
    def add_new_effect(self):
        """Добавление нового последствия."""
        if not self.current_failure_type_id:
            messagebox.showwarning("Предупреждение", 
                                  "Сначала выберите тип отказа", 
                                  parent=self.win)
            return
        
        name = simpledialog.askstring("Новое последствие", 
                                     "Введите описание последствия:", 
                                     parent=self.win)
        if name:
            try:
                effect_id = self.db.add_effect(name)
                self.db.link_failure_type_to_effect(self.current_failure_type_id, effect_id)
                
                # Перезагрузка списка
                effects = self.db.get_effects_for_failure_type(self.current_failure_type_id)
                self.effect_data = {ename: eid for eid, ename in effects}
                self.combo_effect['values'] = list(self.effect_data.keys())
                self.combo_effect.set(name)
                
                messagebox.showinfo("Успех", "Последствие добавлено", parent=self.win)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e), parent=self.win)

class GraphSettingsDialog:
    """Диалог настроек для построения графа зависимостей."""
    
    def __init__(self, parent, on_build):
        self.on_build = on_build
        
        self.win = tk.Toplevel(parent)
        self.win.title("Настройки графа зависимостей")
        self.win.grab_set()
        self.win.resizable(False, False)
        self.win.configure(bg=CLR_BG)
        
        self._build()
        
        # Центрирование
        self.win.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.win.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.win.winfo_height()) // 2
        self.win.geometry(f"+{x}+{y}")
    
    def _build(self):
        """Построение интерфейса."""
        frame = tk.LabelFrame(self.win, text=" Параметры визуализации ",
                             bg=CLR_BG, font=("Arial", 9, "bold"), padx=20, pady=15)
        frame.pack(padx=20, pady=20)
        
        # Тип расположения
        tk.Label(frame, text="Тип расположения узлов:", bg=CLR_BG,
                font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.layout_var = tk.StringVar(value='hierarchical')
        layouts = [
            ('Иерархическое (по уровням)', 'hierarchical'),
            ('Spring (силовое)', 'spring'),
            ('Круговое', 'circular'),
            ('Kamada-Kawai', 'kamada_kawai')
        ]
        
        for i, (label, value) in enumerate(layouts):
            tk.Radiobutton(frame, text=label, variable=self.layout_var, value=value,
                          bg=CLR_BG, font=("Arial", 9)).grid(row=i+1, column=0, sticky=tk.W, padx=20)
        
        # Фильтр по RPN
        tk.Label(frame, text="Фильтр по RPN (оставить пустым = все):", 
                bg=CLR_BG, font=("Arial", 9)).grid(row=5, column=0, sticky=tk.W, pady=(15, 5))
        
        self.rpn_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.rpn_var, width=15,
                font=("Arial", 9)).grid(row=6, column=0, sticky=tk.W, padx=20)
        
        # Показать анализ центральности
        self.centrality_var = tk.BooleanVar(value=True)
        tk.Checkbutton(frame, text="Показать анализ центральности узлов",
                      variable=self.centrality_var, bg=CLR_BG,
                      font=("Arial", 9)).grid(row=7, column=0, sticky=tk.W, pady=(15, 5))
        
        # Кнопки
        btn_frame = tk.Frame(self.win, bg=CLR_BG)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="🕸 Построить граф", command=self._on_build,
                 bg=CLR_BTN_BLUE, fg="white", font=("Arial", 10, "bold"),
                 relief=tk.FLAT, padx=14, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Отмена", command=self.win.destroy,
                 bg=CLR_BTN_GREY, fg="white", font=("Arial", 10),
                 relief=tk.FLAT, padx=14, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=5)
    
    def _on_build(self):
        """Обработчик построения графа."""
        settings = {
            'layout': self.layout_var.get(),
            'show_centrality': self.centrality_var.get()
        }
        
        # Фильтр по RPN
        rpn_text = self.rpn_var.get().strip()
        if rpn_text:
            try:
                settings['filter_rpn'] = int(rpn_text)
            except ValueError:
                messagebox.showerror("Ошибка", "RPN должен быть числом", parent=self.win)
                return
        
        self.on_build(settings)
        self.win.destroy()