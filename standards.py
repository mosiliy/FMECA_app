"""
Вспомогательные константы отчётности (пороги RPN, форматирование).
"""

from typing import Optional

REPORT_TITLE = "Отчёт FMECA / FMEA"
REPORT_SUBTITLE = "Анализ видов, последствий и критичности отказов"

# Пороги категорий риска по RPN (шкала 1–1000)
RPN_RISK_THRESHOLDS = {
    "Низкий": (0, 40),
    "Средний": (40, 100),
    "Высокий": (100, 200),
    "Критический": (200, 1001),
}

SEVERITY_CLASS_LABELS = {
    "I": "Катастрофические",
    "II": "Критические",
    "III": "Незначительные",
    "IV": "Малые",
}

PROBABILITY_LEVEL_LABELS = {
    "A": "Частые",
    "B": "Вероятные",
    "C": "Временные",
    "D": "Редкие",
    "E": "Крайне маловероятные",
}


def format_rpn_thresholds_plain() -> str:
    """Описание порогов RPN для справочного листа."""
    parts = []
    for name, (lo, hi) in RPN_RISK_THRESHOLDS.items():
        if hi >= 1001:
            parts.append(f"{name}: RPN ≥ {lo}")
        else:
            parts.append(f"{name}: {lo} ≤ RPN < {hi}")
    return "; ".join(parts)


def yn_flag(value) -> str:
    """Преобразование флага 0/1/None в Да/Нет."""
    if value in (1, True, "1", "да", "Да", "yes", "Yes"):
        return "Да"
    if value in (0, False, "0", "нет", "Нет", "no", "No"):
        return "Нет"
    return ""


def safe_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
