"""
Модуль импорта/экспорта данных FMEA/FMECA.
"""

import xml.etree.ElementTree as ET
import pandas as pd
from typing import List, Dict, Optional
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, 
                                Paragraph, Spacer, PageBreak, Image)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

from standards import REPORT_TITLE, REPORT_SUBTITLE, format_rpn_thresholds_plain
from model import FMEAModel


class IOUtils:
    """Утилиты для импорта и экспорта данных с поддержкой кириллицы."""
    
    # Путь к шрифтам
    FONTS_DIR = "fonts"
    
    @staticmethod
    def _register_fonts():
        """Регистрация TTF шрифтов для поддержки русского языка."""
        try:
            font_path_regular = os.path.join(IOUtils.FONTS_DIR, "DejaVuSans.ttf")
            font_path_bold = os.path.join(IOUtils.FONTS_DIR, "DejaVuSans-Bold.ttf")
            
            if os.path.exists(font_path_regular):
                pdfmetrics.registerFont(TTFont('DejaVuSans', font_path_regular))
            if os.path.exists(font_path_bold):
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', font_path_bold))
                
        except Exception as e:
            print(f"Предупреждение: не удалось загрузить шрифты: {e}")
    
    @staticmethod
    def import_from_xml(xml_path: str) -> List[Dict]:
        """Импорт FMEA-данных из XML."""
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        failures = []
        for failure_elem in root.findall('failure'):
            failure = {
                'system': failure_elem.findtext('system', 'Не указано'),
                'subsystem': failure_elem.findtext('subsystem', ''),
                'component': failure_elem.findtext('component', 'Не указано'),
                'category': failure_elem.findtext('category', ''),
                'mode': failure_elem.findtext('mode', 'Не указано'),
                'cause': failure_elem.findtext('cause', 'Не указано'),
                'effect': failure_elem.findtext('effect', 'Не указано'),
                'severity': int(failure_elem.findtext('severity', '5')),
                'occurrence': int(failure_elem.findtext('occurrence', '5')),
                'detection': int(failure_elem.findtext('detection', '5'))
            }
            failures.append(failure)
        
        return failures
    
    @staticmethod
    def export_to_excel(
        df: pd.DataFrame,
        filepath: str,
        standardized_df: pd.DataFrame = None,
        comprehensive_df: pd.DataFrame = None,
    ):
        """Экспорт FMEA/FMECA в Excel со всеми листами отчётности."""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='FMEA Analysis', index=False)
            
            if comprehensive_df is not None and not comprehensive_df.empty:
                comprehensive_df.to_excel(writer, sheet_name='FMECA полный', index=False)
                FMEAModel.build_mil_quantitative_sheet(comprehensive_df).to_excel(
                    writer, sheet_name='Количественная критичность', index=False
                )
                FMEAModel.build_analysis_summary(comprehensive_df).to_excel(
                    writer, sheet_name='Сводка анализа', index=False
                )
                before_after_ru = comprehensive_df[
                    ["№", "Компонент", "Вид отказа", "RPN до мер", "RPN после мер", "Снижение риска"]
                ].copy()
                before_after_ru.to_excel(writer, sheet_name='До-После мер', index=False)
                comprehensive_df.nlargest(20, "RPN").to_excel(
                    writer, sheet_name='Топ-20 по RPN', index=False
                )
                if "Критичность Cm" in comprehensive_df.columns:
                    comprehensive_df.sort_values(
                        by=["Критичность Cm", "RPN"],
                        ascending=[False, False],
                        na_position="last",
                    ).head(20).to_excel(writer, sheet_name='Топ-20 по Cm', index=False)
            
            if standardized_df is not None and not standardized_df.empty:
                standardized_df.to_excel(writer, sheet_name='FMECA Standardized', index=False)
                before_after_cols = [
                    "ID", "Component", "Failure Mode",
                    "Before Actions (RPN)", "After Actions (Residual RPN)", "Risk Reduction",
                ]
                standardized_df[
                    [c for c in before_after_cols if c in standardized_df.columns]
                ].to_excel(writer, sheet_name='Before-After Actions', index=False)
                if "MIL Criticality" in standardized_df.columns:
                    standardized_df.sort_values(
                        by=["MIL Criticality", "RPN"],
                        ascending=[False, False],
                        na_position="last",
                    ).to_excel(writer, sheet_name='Top by MIL', index=False)
            
            stats = {
                'Показатель': [
                    'Всего отказов', 'Средний RPN', 'Макс RPN',
                    'Мин RPN', 'Критических', 'Высоких',
                    'Средних', 'Низких',
                ],
                'Значение': [
                    len(df),
                    round(df['RPN'].mean(), 2) if len(df) else 0,
                    df['RPN'].max() if len(df) else 0,
                    df['RPN'].min() if len(df) else 0,
                    len(df[df['RPN'] >= 200]),
                    len(df[(df['RPN'] >= 100) & (df['RPN'] < 200)]),
                    len(df[(df['RPN'] >= 40) & (df['RPN'] < 100)]),
                    len(df[df['RPN'] < 40]),
                ],
            }
            pd.DataFrame(stats).to_excel(writer, sheet_name='Статистика RPN', index=False)
            df.nlargest(10, 'RPN').to_excel(writer, sheet_name='Топ-10 рисков', index=False)
            
            methodology = pd.DataFrame({
                "Раздел": ["Пороги категорий риска по RPN"],
                "Содержание": [format_rpn_thresholds_plain()],
            })
            methodology.to_excel(writer, sheet_name='Справка', index=False)
    
    @staticmethod
    def _pdf_styles():
        IOUtils._register_fonts()
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle', parent=styles['Title'],
            fontName='DejaVuSans-Bold', fontSize=15, alignment=TA_CENTER, spaceAfter=14,
        )
        section_style = ParagraphStyle(
            'SectionTitle', parent=styles['Heading2'],
            fontName='DejaVuSans-Bold', fontSize=11, spaceAfter=8,
        )
        normal_style = ParagraphStyle(
            'CustomNormal', parent=styles['Normal'],
            fontName='DejaVuSans', fontSize=9, alignment=TA_LEFT,
        )
        return title_style, section_style, normal_style
    
    @staticmethod
    def _dataframe_to_pdf_table(
        data_df: pd.DataFrame,
        columns: List[str],
        header_bg: str = '#4472C4',
        font_size: int = 7,
        max_cell_len: int = 28,
    ) -> Table:
        """Преобразование DataFrame в ReportLab Table (все строки)."""
        cols = [c for c in columns if c in data_df.columns]
        table_data = [cols]
        for _, row in data_df.iterrows():
            table_data.append([
                str(row.get(c, ""))[:max_cell_len] if row.get(c, "") is not None else ""
                for c in cols
            ])
        ncols = max(len(cols), 1)
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_bg)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),
            ('FONTSIZE', (0, 0), (-1, -1), font_size),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ]))
        return table
    
    @staticmethod
    def export_to_pdf(
        df: pd.DataFrame,
        filepath: str,
        include_charts: bool = False,
        chart_paths: List[str] = None,
        standardized_df: pd.DataFrame = None,
        comprehensive_df: pd.DataFrame = None,
        full_report: bool = False,
    ):
        """Экспорт FMEA/FMECA в PDF."""
        title_style, section_style, normal_style = IOUtils._pdf_styles()
        doc = SimpleDocTemplate(
            filepath, pagesize=landscape(A4),
            leftMargin=0.8 * cm, rightMargin=0.8 * cm,
            topMargin=1.2 * cm, bottomMargin=1.2 * cm,
        )
        elements = []
        
        elements.append(Paragraph(f"<b>{REPORT_TITLE}</b>", title_style))
        elements.append(Paragraph(f"<i>{REPORT_SUBTITLE}</i>", normal_style))
        elements.append(Spacer(1, 0.3 * cm))
        if len(df):
            stats_text = (
                f"<b>Статистика RPN:</b><br/>"
                f"Всего отказов: {len(df)}; средний RPN: {df['RPN'].mean():.2f}; "
                f"макс. RPN: {df['RPN'].max()}; критических (≥200): {len(df[df['RPN'] >= 200])}; "
                f"высоких (100–199): {len(df[(df['RPN'] >= 100) & (df['RPN'] < 200)])}.<br/>"
                f"<i>Пороги: {format_rpn_thresholds_plain()}</i>"
            )
            elements.append(Paragraph(stats_text, normal_style))
            elements.append(Spacer(1, 0.3 * cm))
        
        comp = comprehensive_df
        if comp is None or comp.empty:
            comp = None
        
        if comp is not None:
            summary = FMEAModel.build_analysis_summary(comp)
            elements.append(Paragraph("<b>Сводка анализа</b>", section_style))
            elements.append(IOUtils._dataframe_to_pdf_table(summary, list(summary.columns), '#2A9D8F', 8))
            elements.append(Spacer(1, 0.4 * cm))
            
            sections = [
                ("1. Идентификация объекта и отказа", [
                    "№", "Система", "Подсистема", "Компонент", "Категория",
                    "Функция", "Вид отказа", "Причина",
                ], '#1565C0'),
                ("2. Эффекты и оценка риска", [
                    "№", "Локальный эффект", "Эффект верхнего уровня", "Конечный эффект",
                    "S", "O", "D", "RPN", "Категория риска",
                    "Класс тяжести", "Уровень вероятности",
                    "Тяжесть (описание)", "Вероятность (описание)", "Обнаруживаемость (описание)",
                ], '#6A1B9A'),
                ("3. Количественная критичность (λ, α, β, t)", [
                    "№", "Компонент", "Вид отказа", "λ (1/ч)", "α", "β", "t (ч)",
                    "Критичность Cm", "RPN",
                ], '#2E7D32'),
                ("4. Меры и остаточный риск", [
                    "№", "Текущие меры контроля", "Рекомендуемые меры",
                    "Ответственный", "Срок", "Статус мер",
                    "RPN до мер", "RPN после мер", "Снижение риска",
                    "S ост.", "O ост.", "D ост.",
                ], '#E65100'),
                ("5. Контекст эксплуатации и признаки", [
                    "№", "Фаза миссии", "Режим работы", "ОПФ", "Скрытый отказ", "ОППО",
                    "Полнота анализа, %",
                ], '#455A64'),
            ]
            row_limit = None if full_report else 25
            comp_sorted = comp.sort_values(by=["RPN"], ascending=False, na_position="last")
            if row_limit:
                comp_sorted = comp_sorted.head(row_limit)
            
            for title, cols, color in sections:
                elements.append(PageBreak())
                elements.append(Paragraph(f"<b>{title}</b>", section_style))
                if row_limit and len(comp) > row_limit:
                    elements.append(Paragraph(
                        f"<i>Показаны топ-{row_limit} записей по RPN (полная таблица — в Excel).</i>",
                        normal_style,
                    ))
                elements.append(Spacer(1, 0.15 * cm))
                elements.append(IOUtils._dataframe_to_pdf_table(comp_sorted, cols, color, 6, 22))
        else:
            df_show = df if full_report or len(df) <= 30 else df.nlargest(30, 'RPN')
            elements.append(Paragraph("<b>Реестр отказов (базовая таблица)</b>", section_style))
            basic_cols = ['ID', 'Система', 'Подсистема', 'Компонент', 'Категория',
                          'Вид отказа', 'S', 'O', 'D', 'RPN', 'Категория риска']
            basic_cols = [c for c in basic_cols if c in df_show.columns]
            elements.append(IOUtils._dataframe_to_pdf_table(df_show, basic_cols))
        
        if standardized_df is not None and not standardized_df.empty:
            elements.append(PageBreak())
            elements.append(Paragraph("<b>Таблица FMECA (сводный формат)</b>", section_style))
            std_cols = [
                "ID", "Component", "Function", "Failure Mode", "Cause",
                "Local Effect", "Next Higher Effect", "End Effect",
                "Severity", "Occurrence", "Detection", "RPN", "MIL Criticality",
                "Recommended Actions", "Action Owner", "Due Date",
                "Before Actions (RPN)", "After Actions (Residual RPN)", "Risk Reduction",
            ]
            std_df = standardized_df if full_report else standardized_df.head(25)
            elements.append(IOUtils._dataframe_to_pdf_table(std_df, std_cols, '#264653', 6, 20))
        
        if include_charts and chart_paths:
            elements.append(PageBreak())
            elements.append(Paragraph("<b>Визуализация результатов</b>", section_style))
            elements.append(Spacer(1, 0.3 * cm))
            for chart_path in chart_paths:
                if os.path.exists(chart_path):
                    try:
                        elements.append(Image(chart_path, width=18 * cm, height=11 * cm))
                        elements.append(Spacer(1, 0.4 * cm))
                    except Exception:
                        pass
        
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph(
            "<i>Отчёт сформирован автоматически средствами FMEA/FMECA Analysis Tool.</i>",
            normal_style,
        ))
        doc.build(elements)
    
    @staticmethod
    def create_sample_xml(filepath: str):
        """Создание примера XML-файла."""
        root = ET.Element('fmea')
        
        sample_data = [
            {
                'system': 'Сервер Dell PowerEdge R740',
                'subsystem': 'Процессорный модуль',
                'component': 'CPU Intel Xeon Gold 6154',
                'category': 'Процессор',
                'mode': 'Перегрев',
                'cause': 'Отказ системы охлаждения',
                'effect': 'Деградация производительности',
                'severity': 7,
                'occurrence': 4,
                'detection': 3
            },
            {
                'system': 'Сервер Dell PowerEdge R740',
                'subsystem': 'Память',
                'component': 'DDR4 ECC RDIMM 32GB',
                'category': 'Оперативная память',
                'mode': 'Ошибка чтения/записи',
                'cause': 'Деградация ячеек памяти',
                'effect': 'Потеря данных',
                'severity': 9,
                'occurrence': 3,
                'detection': 5
            }
        ]
        
        for data in sample_data:
            failure = ET.SubElement(root, 'failure')
            for key, value in data.items():
                elem = ET.SubElement(failure, key)
                elem.text = str(value)
        
        tree = ET.ElementTree(root)
        tree.write(filepath, encoding='utf-8', xml_declaration=True)