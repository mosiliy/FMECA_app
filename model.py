"""
Бизнес-логика приложения.
Расчёты в соответствии со стандартами MIL-STD-1629A, ГОСТ 27.310-95,
ГОСТ Р 58629-2020, ГОСТ Р 27.303-2021.
"""

from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

from standards import yn_flag, safe_float


class FMEAModel:
    """Модель для расчётов FMEA/FMECA."""
    
    FMECA_COMPLETENESS_FIELDS = [
        "function_text",
        "failure_mode",
        "failure_cause",
        "local_effect",
        "next_higher_effect",
        "end_effect",
        "recommended_actions",
        "severity",
        "occurrence",
        "detection",
    ]
    
    # Интерпретация шкал согласно стандартам
    SEVERITY_SCALE = {
        1: "Незначительный",
        2: "Малый",
        3: "Малый",
        4: "Умеренный",
        5: "Умеренный",
        6: "Умеренный",
        7: "Высокий",
        8: "Высокий",
        9: "Критический",
        10: "Критический"
    }
    
    OCCURRENCE_SCALE = {
        1: "Практически невозможен",
        2: "Редкий",
        3: "Редкий",
        4: "Средний",
        5: "Средний",
        6: "Средний",
        7: "Частый",
        8: "Частый",
        9: "Очень частый",
        10: "Очень частый"
    }
    
    DETECTION_SCALE = {
        1: "Очень высокая",
        2: "Высокая",
        3: "Высокая",
        4: "Средняя",
        5: "Средняя",
        6: "Средняя",
        7: "Низкая",
        8: "Низкая",
        9: "Очень низкая",
        10: "Очень низкая"
    }
    
    @staticmethod
    def calculate_rpn(severity: int, occurrence: int, detection: int) -> int:
        """
        Расчёт RPN (Risk Priority Number) согласно MIL-STD-1629A.
        
        Args:
            severity: тяжесть последствий (1-10)
            occurrence: вероятность возникновения (1-10)
            detection: вероятность обнаружения (1-10)
        
        Returns:
            RPN = S * O * D (диапазон 1-1000)
        """
        return severity * occurrence * detection
    
    @staticmethod
    def calc_mil_criticality(
        lambda_p: Optional[float],
        alpha: Optional[float],
        beta: Optional[float],
        t: Optional[float]
    ) -> Optional[float]:
        """
        Расчёт MIL-критичности (mode criticality).
        Формула: C_m = lambda_p * alpha * beta * t
        """
        if any(value is None for value in (lambda_p, alpha, beta, t)):
            return None
        
        try:
            return float(lambda_p) * float(alpha) * float(beta) * float(t)
        except (TypeError, ValueError):
            return None
    
    @staticmethod
    def calc_residual_rpn(
        severity: Optional[int],
        occurrence: Optional[int],
        detection: Optional[int]
    ) -> Optional[int]:
        """Расчёт остаточного RPN с безопасной обработкой старых данных."""
        if any(value is None for value in (severity, occurrence, detection)):
            return None
        
        try:
            severity_i = int(severity)
            occurrence_i = int(occurrence)
            detection_i = int(detection)
        except (TypeError, ValueError):
            return None
        
        if not FMEAModel.validate_sod_values(severity_i, occurrence_i, detection_i):
            return None
        
        return FMEAModel.calculate_rpn(severity_i, occurrence_i, detection_i)
    
    @staticmethod
    def calculate_dual_scores(
        severity: int,
        occurrence: int,
        detection: int,
        lambda_p: Optional[float] = None,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        mission_time_t: Optional[float] = None
    ) -> Dict[str, Optional[float]]:
        """
        Dual scoring:
        - rpn: текущий расчёт без изменений
        - mil_criticality: MIL-метрика при наличии полей
        """
        return {
            "rpn": FMEAModel.calculate_rpn(severity, occurrence, detection),
            "mil_criticality": FMEAModel.calc_mil_criticality(
                lambda_p, alpha, beta, mission_time_t
            ),
        }
    
    @staticmethod
    def validate_sod_values(severity: int, occurrence: int, detection: int) -> bool:
        """Валидация значений S-O-D."""
        return all(1 <= val <= 10 for val in [severity, occurrence, detection])
    
    # MIL-STD-1629A Task 102: qualitative severity (4.4.3) и уровни вероятности (3.1)
    MIL_STD_1629A_SEVERITY_CATEGORIES = ("IV", "III", "II", "I")  # слева направо: возрастание тяжести
    MIL_STD_1629A_PROBABILITY_LEVELS = ("E", "D", "C", "B", "A")  # снизу вверх: возрастание вероятности
    
    @staticmethod
    def map_severity_to_mil_std_1629a_category(severity) -> str:
        """
        Классификация тяжести по MIL-STD-1629A п. 4.4.3 (Category I … IV).
        Числовая шкала 1–10 (IEC/RPN) сопоставляется с четырьмя категориями для матрицы критичности.
        """
        try:
            s = int(severity)
        except (TypeError, ValueError):
            return "IV"
        s = max(1, min(10, s))
        if s >= 9:
            return "I"    # Catastrophic
        if s >= 7:
            return "II"   # Critical
        if s >= 5:
            return "III"  # Marginal
        return "IV"       # Minor
    
    @staticmethod
    def map_occurrence_to_mil_std_1629a_level(occurrence) -> str:
        """
        Уровень вероятности по MIL-STD-1629A п. 3.1 (Level A … E).
        Числовая шкала 1–10 (частота в FMEA) сопоставляется с уровнями A–E для качественного CA.
        """
        try:
            o = int(occurrence)
        except (TypeError, ValueError):
            return "E"
        o = max(1, min(10, o))
        if o >= 9:
            return "A"
        if o >= 7:
            return "B"
        if o >= 5:
            return "C"
        if o >= 3:
            return "D"
        return "E"
    
    @staticmethod
    def get_risk_category(rpn: int) -> str:
        """
        Категория риска на основе RPN согласно IEC 60812.
        
        Returns:
            Категория: "Низкий", "Средний", "Высокий", "Критический"
        """
        if rpn < 40:
            return "Низкий"
        elif rpn < 100:
            return "Средний"
        elif rpn < 200:
            return "Высокий"
        else:
            return "Критический"
    
    @staticmethod
    def analyze_failures(data: List[tuple]) -> pd.DataFrame:
        """
        Преобразование данных БД в pandas DataFrame для анализа.
        
        Args:
            data: список кортежей из БД
                (id, system, subsystem, component, category, 
                 failure_mode, failure_cause, failure_effect,
                 severity, occurrence, detection, rpn)
        
        Returns:
            DataFrame с результатами FMEA
        """
        columns = [
            'ID', 'Система', 'Подсистема', 'Компонент', 'Категория',
            'Вид отказа', 'Причина', 'Последствие',
            'S', 'O', 'D', 'RPN'
        ]
        
        df = pd.DataFrame(data, columns=columns)
        
        df['Категория риска'] = df['RPN'].apply(FMEAModel.get_risk_category)
        
        # Обработка NULL значений в категории
        df['Категория'] = df['Категория'].fillna('Не указана')
        
        return df
    
    @staticmethod
    def aggregate_component_mil_criticality(df: pd.DataFrame) -> pd.DataFrame:
        """
        Суммарная критичность по компоненту: sum(mil_criticality).
        """
        component_column = "Компонент" if "Компонент" in df.columns else "Component"
        mil_column = (
            "mil_criticality"
            if "mil_criticality" in df.columns
            else "MIL Criticality"
            if "MIL Criticality" in df.columns
            else None
        )
        
        if component_column not in df.columns or mil_column is None:
            return pd.DataFrame(columns=[component_column, "Суммарная MIL критичность"])
        
        aggregated = (
            df.groupby(component_column, dropna=False)[mil_column]
            .sum(min_count=1)
            .fillna(0.0)
            .reset_index()
        )
        aggregated.columns = [component_column, "Суммарная MIL критичность"]
        return aggregated.sort_values("Суммарная MIL критичность", ascending=False)
    
    @staticmethod
    def validate_action_requirements(
        recommended_actions: Optional[str],
        action_owner: Optional[str],
        due_date: Optional[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Если заполнено recommended_actions, обязательны action_owner и due_date.
        """
        actions = (recommended_actions or "").strip()
        owner = (action_owner or "").strip()
        due = (due_date or "").strip()
        
        if actions and (not owner or not due):
            return False, "При наличии recommended_actions необходимо заполнить action_owner и due_date."
        return True, None
    
    @staticmethod
    def get_effect_completion_recommendation(
        end_effect: Optional[str],
        local_effect: Optional[str]
    ) -> Optional[str]:
        """
        Рекомендация по полноте данных: если есть end_effect, желательно local_effect.
        """
        end_value = (end_effect or "").strip()
        local_value = (local_effect or "").strip()
        if end_value and not local_value:
            return "Рекомендуется заполнить local_effect, так как указан end_effect."
        return None
    
    @staticmethod
    def get_missing_fields(failure: dict) -> List[str]:
        """
        Возвращает список отсутствующих обязательных полей FMECA-записи.
        Поле mil_criticality учитывается как условное: если присутствует в словаре,
        но пустое/None, добавляется в список пропусков.
        """
        missing = []
        
        for field_name in FMEAModel.FMECA_COMPLETENESS_FIELDS:
            value = failure.get(field_name)
            if value is None:
                missing.append(field_name)
                continue
            if isinstance(value, str) and not value.strip():
                missing.append(field_name)
        
        if "mil_criticality" in failure:
            mil_value = failure.get("mil_criticality")
            if mil_value is None or (isinstance(mil_value, str) and not mil_value.strip()):
                missing.append("mil_criticality")
        
        return missing
    
    @staticmethod
    def calculate_analysis_completeness(failure: dict) -> float:
        """
        Расчёт полноты FMECA-анализа записи в процентах (0..100).
        
        Формула:
            completeness = (filled_fields / total_considered_fields) * 100
        """
        considered_fields = list(FMEAModel.FMECA_COMPLETENESS_FIELDS)
        if "mil_criticality" in failure:
            considered_fields.append("mil_criticality")
        
        if not considered_fields:
            return 0.0
        
        missing_fields = set(FMEAModel.get_missing_fields(failure))
        filled_count = len([field for field in considered_fields if field not in missing_fields])
        completeness = (filled_count / len(considered_fields)) * 100
        return round(completeness, 2)
    
    @staticmethod
    def calculate_residual_risk(
        failure: dict,
        fallback_to_residual_sod: bool = True
    ) -> Dict[str, Optional[int]]:
        """
        Расчёт риска до/после мер:
        - initial_rpn: исходный RPN (из failure['rpn'] или пересчёт из severity/occurrence/detection)
        - residual_rpn: из failure['residual_rpn'], либо пересчёт из residual_severity/residual_occurrence/residual_detection
        """
        initial_rpn = failure.get("rpn")
        if initial_rpn is None:
            initial_rpn = FMEAModel.calc_residual_rpn(
                failure.get("severity"),
                failure.get("occurrence"),
                failure.get("detection"),
            )
        
        residual_rpn = failure.get("residual_rpn")
        if residual_rpn is None and fallback_to_residual_sod:
            residual_rpn = FMEAModel.calc_residual_rpn(
                failure.get("residual_severity"),
                failure.get("residual_occurrence"),
                failure.get("residual_detection"),
            )
        
        return {
            "initial_rpn": initial_rpn,
            "residual_rpn": residual_rpn,
            "risk_reduction": (
                initial_rpn - residual_rpn
                if initial_rpn is not None and residual_rpn is not None
                else None
            ),
        }
    
    @staticmethod
    def get_top_risks(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """Получение топ-N критических рисков."""
        return df.nlargest(n, 'RPN')
    
    @staticmethod
    def calculate_statistics(df: pd.DataFrame) -> Dict:
        """
        Статистика по FMEA-анализу.
        
        Returns:
            Словарь со статистикой
        """
        return {
            'total_failures': len(df),
            'avg_rpn': df['RPN'].mean(),
            'max_rpn': df['RPN'].max(),
            'min_rpn': df['RPN'].min(),
            'critical_count': len(df[df['RPN'] >= 200]),
            'high_count': len(df[(df['RPN'] >= 100) & (df['RPN'] < 200)]),
            'medium_count': len(df[(df['RPN'] >= 40) & (df['RPN'] < 100)]),
            'low_count': len(df[df['RPN'] < 40])
        }
    
    COMPREHENSIVE_REPORT_COLUMNS = [
        "№", "Система", "Подсистема", "Компонент", "Категория",
        "Функция", "Вид отказа", "Причина",
        "Локальный эффект", "Эффект верхнего уровня", "Конечный эффект", "Последствие (общ.)",
        "S", "O", "D", "RPN", "Категория риска",
        "Тяжесть (описание)", "Вероятность (описание)", "Обнаруживаемость (описание)",
        "Класс тяжести", "Уровень вероятности",
        "λ (1/ч)", "α", "β", "t (ч)", "Критичность Cm",
        "Текущие меры контроля", "Рекомендуемые меры", "Ответственный", "Срок", "Статус мер",
        "Фаза миссии", "Режим работы",
        "ОПФ", "Скрытый отказ", "ОППО",
        "S ост.", "O ост.", "D ост.",
        "RPN до мер", "RPN после мер", "Снижение риска",
        "Полнота анализа, %",
    ]
    
    @staticmethod
    def _row_to_failure_dict(row: tuple) -> Dict[str, Any]:
        """Преобразование строки отчёта БД в словарь для расчётов."""
        if len(row) >= 35:
            return {
                "id": row[0],
                "system": row[1],
                "subsystem": row[2],
                "component": row[3],
                "category": row[4],
                "function_text": row[5],
                "failure_mode": row[6],
                "failure_cause": row[7],
                "local_effect": row[8],
                "next_higher_effect": row[9],
                "end_effect": row[10],
                "failure_effect": row[11],
                "severity": row[12],
                "occurrence": row[13],
                "detection": row[14],
                "rpn": row[15],
                "mil_criticality": row[16],
                "failure_rate_lambda": row[17],
                "mode_ratio_alpha": row[18],
                "conditional_prob_beta": row[19],
                "mission_time_t": row[20],
                "current_controls": row[21],
                "recommended_actions": row[22],
                "action_owner": row[23],
                "due_date": row[24],
                "action_status": row[25],
                "mission_phase": row[26],
                "operating_mode": row[27],
                "is_single_point": row[28],
                "is_latent": row[29],
                "is_common_cause": row[30],
                "residual_severity": row[31],
                "residual_occurrence": row[32],
                "residual_detection": row[33],
                "residual_rpn": row[34],
            }
        # Устаревший короткий формат (20 полей)
        return {
            "id": row[0],
            "system": row[1],
            "subsystem": row[2],
            "component": row[3],
            "category": row[4],
            "function_text": row[5],
            "failure_mode": row[6],
            "failure_cause": row[7],
            "local_effect": row[8],
            "next_higher_effect": row[9],
            "end_effect": row[10],
            "severity": row[11],
            "occurrence": row[12],
            "detection": row[13],
            "rpn": row[14],
            "mil_criticality": row[15],
            "recommended_actions": row[16],
            "action_owner": row[17],
            "due_date": row[18],
            "residual_rpn": row[19],
        }
    
    @staticmethod
    def build_comprehensive_fmeca_dataframe(data: List[tuple]) -> pd.DataFrame:
        """
        Полная таблица FMECA для отчётов по ГОСТ / MIL-STD-1629A
        (все поля БД + производные показатели).
        """
        rows = []
        for row in data:
            f = FMEAModel._row_to_failure_dict(row)
            s = f.get("severity")
            o = f.get("occurrence")
            d = f.get("detection")
            rpn = f.get("rpn")
            if rpn is None and all(v is not None for v in (s, o, d)):
                rpn = FMEAModel.calculate_rpn(int(s), int(o), int(d))
            
            risk = FMEAModel.get_risk_category(int(rpn)) if rpn is not None else ""
            mil_cat = FMEAModel.map_severity_to_mil_std_1629a_category(s) if s is not None else ""
            mil_prob = FMEAModel.map_occurrence_to_mil_std_1629a_level(o) if o is not None else ""
            
            mil_cm = f.get("mil_criticality")
            if mil_cm is None:
                mil_cm = FMEAModel.calc_mil_criticality(
                    f.get("failure_rate_lambda"),
                    f.get("mode_ratio_alpha"),
                    f.get("conditional_prob_beta"),
                    f.get("mission_time_t"),
                )
            
            residual = FMEAModel.calculate_residual_risk(f)
            completeness = FMEAModel.calculate_analysis_completeness(f)
            
            sev_text = FMEAModel.SEVERITY_SCALE.get(int(s), "") if s is not None else ""
            occ_text = FMEAModel.OCCURRENCE_SCALE.get(int(o), "") if o is not None else ""
            det_text = FMEAModel.DETECTION_SCALE.get(int(d), "") if d is not None else ""
            
            rows.append({
                "№": f.get("id"),
                "Система": f.get("system") or "",
                "Подсистема": f.get("subsystem") or "",
                "Компонент": f.get("component") or "",
                "Категория": f.get("category") or "",
                "Функция": f.get("function_text") or "",
                "Вид отказа": f.get("failure_mode") or "",
                "Причина": f.get("failure_cause") or "",
                "Локальный эффект": f.get("local_effect") or "",
                "Эффект верхнего уровня": f.get("next_higher_effect") or "",
                "Конечный эффект": f.get("end_effect") or "",
                "Последствие (общ.)": f.get("failure_effect") or "",
                "S": s,
                "O": o,
                "D": d,
                "RPN": rpn,
                "Категория риска": risk,
                "Тяжесть (описание)": sev_text,
                "Вероятность (описание)": occ_text,
                "Обнаруживаемость (описание)": det_text,
                "Класс тяжести": mil_cat,
                "Уровень вероятности": mil_prob,
                "λ (1/ч)": safe_float(f.get("failure_rate_lambda")),
                "α": safe_float(f.get("mode_ratio_alpha")),
                "β": safe_float(f.get("conditional_prob_beta")),
                "t (ч)": safe_float(f.get("mission_time_t")),
                "Критичность Cm": mil_cm,
                "Текущие меры контроля": f.get("current_controls") or "",
                "Рекомендуемые меры": f.get("recommended_actions") or "",
                "Ответственный": f.get("action_owner") or "",
                "Срок": f.get("due_date") or "",
                "Статус мер": f.get("action_status") or "",
                "Фаза миссии": f.get("mission_phase") or "",
                "Режим работы": f.get("operating_mode") or "",
                "ОПФ": yn_flag(f.get("is_single_point")),
                "Скрытый отказ": yn_flag(f.get("is_latent")),
                "ОППО": yn_flag(f.get("is_common_cause")),
                "S ост.": f.get("residual_severity"),
                "O ост.": f.get("residual_occurrence"),
                "D ост.": f.get("residual_detection"),
                "RPN до мер": residual.get("initial_rpn"),
                "RPN после мер": residual.get("residual_rpn"),
                "Снижение риска": residual.get("risk_reduction"),
                "Полнота анализа, %": completeness,
            })
        
        return pd.DataFrame(rows, columns=FMEAModel.COMPREHENSIVE_REPORT_COLUMNS)
    
    @staticmethod
    def build_standardized_fmeca_dataframe(data: List[tuple]) -> pd.DataFrame:
        """
        Стандартизированная таблица FMECA (англ. заголовки) для совместимости экспорта.
        Строится из полной таблицы ГОСТ/MIL.
        """
        full_df = FMEAModel.build_comprehensive_fmeca_dataframe(data)
        if full_df.empty:
            return pd.DataFrame(columns=[
                "ID", "System", "Subsystem", "Component", "Category",
                "Function", "Failure Mode", "Cause",
                "Local Effect", "Next Higher Effect", "End Effect",
                "Severity", "Occurrence", "Detection", "RPN", "MIL Criticality",
                "Recommended Actions", "Action Owner", "Due Date", "Residual RPN",
                "Before Actions (RPN)", "After Actions (Residual RPN)", "Risk Reduction",
            ])
        
        df = pd.DataFrame({
            "ID": full_df["№"],
            "System": full_df["Система"],
            "Subsystem": full_df["Подсистема"],
            "Component": full_df["Компонент"],
            "Category": full_df["Категория"],
            "Function": full_df["Функция"],
            "Failure Mode": full_df["Вид отказа"],
            "Cause": full_df["Причина"],
            "Local Effect": full_df["Локальный эффект"],
            "Next Higher Effect": full_df["Эффект верхнего уровня"],
            "End Effect": full_df["Конечный эффект"],
            "Severity": full_df["S"],
            "Occurrence": full_df["O"],
            "Detection": full_df["D"],
            "RPN": full_df["RPN"],
            "MIL Criticality": full_df["Критичность Cm"],
            "Recommended Actions": full_df["Рекомендуемые меры"],
            "Action Owner": full_df["Ответственный"],
            "Due Date": full_df["Срок"],
            "Residual RPN": full_df["RPN после мер"],
        })
        df["Before Actions (RPN)"] = full_df["RPN до мер"]
        df["After Actions (Residual RPN)"] = full_df["RPN после мер"]
        df["Risk Reduction"] = full_df["Снижение риска"]
        return df
    
    @staticmethod
    def sort_standardized_fmeca(df: pd.DataFrame, sort_by: str = "rpn") -> pd.DataFrame:
        """
        Сортировка стандартизированной таблицы:
        - sort_by='rpn'
        - sort_by='mil_criticality'
        """
        if sort_by == "mil_criticality" and "MIL Criticality" in df.columns:
            return df.sort_values(
                by=["MIL Criticality", "RPN"],
                ascending=[False, False],
                na_position="last"
            )
        return df.sort_values(by=["RPN"], ascending=[False])
    
    @staticmethod
    def sort_comprehensive_fmeca(df: pd.DataFrame, sort_by: str = "rpn") -> pd.DataFrame:
        """Сортировка полной таблицы FMECA."""
        if df.empty:
            return df
        if sort_by == "mil_criticality" and "Критичность Cm" in df.columns:
            return df.sort_values(
                by=["Критичность Cm", "RPN"],
                ascending=[False, False],
                na_position="last",
            )
        return df.sort_values(by=["RPN"], ascending=[False], na_position="last")
    
    @staticmethod
    def build_mil_quantitative_sheet(df: pd.DataFrame) -> pd.DataFrame:
        """Лист количественной критичности MIL-STD-1629A Task 101."""
        cols = [
            "№", "Компонент", "Вид отказа", "λ (1/ч)", "α", "β", "t (ч)",
            "Критичность Cm", "RPN", "Класс тяжести", "Уровень вероятности",
        ]
        if df.empty:
            return pd.DataFrame(columns=cols)
        out = df[cols].copy()
        return out.sort_values(by=["Критичность Cm", "RPN"], ascending=[False, False], na_position="last")
    
    @staticmethod
    def build_analysis_summary(df: pd.DataFrame) -> pd.DataFrame:
        """Сводка полноты и рисков анализа."""
        if df.empty:
            return pd.DataFrame(columns=["Показатель", "Значение"])
        total = len(df)
        complete = len(df[df["Полнота анализа, %"] >= 100.0]) if "Полнота анализа, %" in df.columns else 0
        with_cm = len(df[df["Критичность Cm"].notna()]) if "Критичность Cm" in df.columns else 0
        with_actions = len(df[df["Рекомендуемые меры"].astype(str).str.strip() != ""])
        return pd.DataFrame({
            "Показатель": [
                "Всего режимов отказа",
                "Записей с полнотой 100%",
                "Доля полных записей, %",
                "Записей с Cm",
                "Записей с рекомендуемыми мерами",
                "Средний RPN",
                "Максимальный RPN",
                "Критических (RPN ≥ 200)",
                "Высоких (100 ≤ RPN < 200)",
            ],
            "Значение": [
                total,
                complete,
                round(complete / total * 100, 1) if total else 0,
                with_cm,
                with_actions,
                round(df["RPN"].mean(), 2) if "RPN" in df.columns else "",
                df["RPN"].max() if "RPN" in df.columns else "",
                len(df[df["RPN"] >= 200]) if "RPN" in df.columns else 0,
                len(df[(df["RPN"] >= 100) & (df["RPN"] < 200)]) if "RPN" in df.columns else 0,
            ],
        })
    
    build_gost_compliance_summary = build_analysis_summary
    
    @staticmethod
    def build_quality_dashboard(
        failures: List[dict],
        top_n: int = 10,
        low_completeness_threshold: float = 80.0
    ) -> Dict:
        """
        Построение dashboard метрик качества анализа FMECA.
        
        Returns:
            {
              "summary": агрегированная статистика,
              "problematic_records": список записей с низкой полнотой
            }
        """
        if not failures:
            return {
                "summary": {
                    "total_records": 0,
                    "average_analysis_completeness_score": 0.0,
                    "fully_completed_percent": 0.0,
                    "fully_completed_count": 0,
                    "low_completeness_threshold": low_completeness_threshold,
                },
                "problematic_records": [],
            }
        
        processed = []
        for failure in failures:
            completeness = FMEAModel.calculate_analysis_completeness(failure)
            missing_fields = FMEAModel.get_missing_fields(failure)
            processed.append({
                "id": failure.get("id"),
                "component": failure.get("component"),
                "failure_mode": failure.get("failure_mode"),
                "analysis_completeness_score": completeness,
                "missing_fields": missing_fields,
            })
        
        total = len(processed)
        fully_completed = [r for r in processed if r["analysis_completeness_score"] >= 100.0]
        avg_score = round(sum(r["analysis_completeness_score"] for r in processed) / total, 2)
        fully_completed_percent = round((len(fully_completed) / total) * 100, 2)
        
        problematic = [
            r for r in processed
            if r["analysis_completeness_score"] < low_completeness_threshold
        ]
        problematic.sort(key=lambda r: (r["analysis_completeness_score"], -len(r["missing_fields"])))
        
        return {
            "summary": {
                "total_records": total,
                "average_analysis_completeness_score": avg_score,
                "fully_completed_percent": fully_completed_percent,
                "fully_completed_count": len(fully_completed),
                "low_completeness_threshold": low_completeness_threshold,
            },
            "problematic_records": problematic[:top_n],
        }
    
    @staticmethod
    def explain_risk(failure: dict) -> str:
        """
        Текстовое объяснение критичности отказа для отчётов и dashboard.
        
        Включает:
        - интерпретацию RPN;
        - интерпретацию MIL criticality;
        - влияние на систему (effects);
        - рекомендации.
        """
        component = failure.get("component", "Не указан компонент")
        failure_mode = failure.get("failure_mode", "Не указан вид отказа")
        
        # RPN и его интерпретация
        rpn = failure.get("rpn")
        if rpn is None:
            rpn = FMEAModel.calc_residual_rpn(
                failure.get("severity"),
                failure.get("occurrence"),
                failure.get("detection"),
            )
        
        if rpn is None:
            rpn_text = "RPN: недостаточно данных для расчёта."
        else:
            rpn_category = FMEAModel.get_risk_category(int(rpn))
            rpn_text = f"RPN: {rpn} ({rpn_category} риск)."
        
        # MIL criticality и её интерпретация
        mil_value = failure.get("mil_criticality")
        if mil_value is None:
            mil_value = FMEAModel.calc_mil_criticality(
                failure.get("failure_rate_lambda"),
                failure.get("mode_ratio_alpha"),
                failure.get("conditional_prob_beta"),
                failure.get("mission_time_t"),
            )
        
        if mil_value is None:
            mil_text = "Критичность Cm: не рассчитана (нет достаточных данных)."
        else:
            if mil_value < 1e-4:
                mil_level = "очень низкая"
            elif mil_value < 1e-3:
                mil_level = "низкая"
            elif mil_value < 1e-2:
                mil_level = "средняя"
            else:
                mil_level = "высокая"
            mil_text = f"Критичность Cm: {mil_value:.6g} ({mil_level})."
        
        # Влияние на систему
        local_effect = (failure.get("local_effect") or "").strip()
        next_effect = (failure.get("next_higher_effect") or "").strip()
        end_effect = (failure.get("end_effect") or "").strip()
        legacy_effect = (failure.get("failure_effect") or "").strip()
        
        effects_parts = []
        if local_effect:
            effects_parts.append(f"локальный эффект: {local_effect}")
        if next_effect:
            effects_parts.append(f"эффект верхнего уровня: {next_effect}")
        if end_effect:
            effects_parts.append(f"конечный эффект: {end_effect}")
        if not effects_parts and legacy_effect:
            effects_parts.append(f"последствие: {legacy_effect}")
        
        effects_text = (
            "Влияние на систему: " + "; ".join(effects_parts) + "."
            if effects_parts
            else "Влияние на систему: эффекты не задокументированы."
        )
        
        # Рекомендации
        recommendations = []
        recommended_actions = (failure.get("recommended_actions") or "").strip()
        action_owner = (failure.get("action_owner") or "").strip()
        due_date = (failure.get("due_date") or "").strip()
        
        if recommended_actions:
            recommendations.append(f"выполнить меры: {recommended_actions}")
            if action_owner:
                recommendations.append(f"ответственный: {action_owner}")
            if due_date:
                recommendations.append(f"срок: {due_date}")
        else:
            recommendations.append("добавить recommended_actions для снижения риска")
        
        effect_hint = FMEAModel.get_effect_completion_recommendation(
            failure.get("end_effect"),
            failure.get("local_effect"),
        )
        if effect_hint:
            recommendations.append(effect_hint)
        
        action_valid, action_error = FMEAModel.validate_action_requirements(
            failure.get("recommended_actions"),
            failure.get("action_owner"),
            failure.get("due_date"),
        )
        if not action_valid and action_error:
            recommendations.append(action_error)
        
        rec_text = "Рекомендации: " + "; ".join(recommendations) + "."
        
        return (
            f"Компонент: {component}. Отказ: {failure_mode}. "
            f"{rpn_text} {mil_text} {effects_text} {rec_text}"
        )