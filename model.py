"""
Бизнес-логика приложения.
Расчёты в соответствии со стандартами MIL-STD-1629A, IEC 60812.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd


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
    
    @staticmethod
    def build_standardized_fmeca_dataframe(data: List[tuple]) -> pd.DataFrame:
        """
        Формирование стандартизированной таблицы FMECA для экспорта/отчётов.
        
        Ожидаемый формат data (из Database.get_failures_for_standard_report):
            (id, system, subsystem, component, category, function_text,
             failure_mode, failure_cause, local_effect, next_higher_effect, end_effect,
             severity, occurrence, detection, rpn, mil_criticality,
             recommended_actions, action_owner, due_date, residual_rpn)
        """
        columns = [
            "ID", "System", "Subsystem", "Component", "Category",
            "Function", "Failure Mode", "Cause",
            "Local Effect", "Next Higher Effect", "End Effect",
            "Severity", "Occurrence", "Detection", "RPN", "MIL Criticality",
            "Recommended Actions", "Action Owner", "Due Date", "Residual RPN"
        ]
        df = pd.DataFrame(data, columns=columns)
        
        # Блок "Before actions / After actions"
        df["Before Actions (RPN)"] = df["RPN"]
        df["After Actions (Residual RPN)"] = df["Residual RPN"]
        df["Risk Reduction"] = df["Before Actions (RPN)"] - df["After Actions (Residual RPN)"]
        
        # Безопасная обработка NaN для последующего экспорта
        text_columns = [
            "Function", "Failure Mode", "Cause", "Local Effect", "Next Higher Effect", "End Effect",
            "Recommended Actions", "Action Owner", "Due Date", "Category", "System", "Subsystem", "Component"
        ]
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].fillna("")
        
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
            mil_text = "MIL criticality: не рассчитана (нет достаточных данных)."
        else:
            if mil_value < 1e-4:
                mil_level = "очень низкая"
            elif mil_value < 1e-3:
                mil_level = "низкая"
            elif mil_value < 1e-2:
                mil_level = "средняя"
            else:
                mil_level = "высокая"
            mil_text = f"MIL criticality: {mil_value:.6g} ({mil_level})."
        
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