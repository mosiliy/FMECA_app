"""
Модуль импорта/экспорта данных.
Улучшенная поддержка русского языка в PDF.
"""

import xml.etree.ElementTree as ET
import pandas as pd
from typing import List, Dict
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
    def export_to_excel(df: pd.DataFrame, filepath: str, standardized_df: pd.DataFrame = None):
        """Экспорт FMEA-таблицы в Excel (с опциональным стандартизированным FMECA листом)."""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Основная таблица
            df.to_excel(writer, sheet_name='FMEA Analysis', index=False)
            
            # Новый стандартизированный FMECA лист (без ломки старого экспорта)
            if standardized_df is not None and not standardized_df.empty:
                standardized_df.to_excel(writer, sheet_name='FMECA Standardized', index=False)
                
                # Before/After блок отдельным листом для наглядности
                before_after_cols = [
                    "ID", "Component", "Failure Mode",
                    "Before Actions (RPN)", "After Actions (Residual RPN)", "Risk Reduction"
                ]
                before_after_df = standardized_df[
                    [c for c in before_after_cols if c in standardized_df.columns]
                ].copy()
                before_after_df.to_excel(writer, sheet_name='Before-After Actions', index=False)
                
                # Сортировка по MIL criticality
                if "MIL Criticality" in standardized_df.columns:
                    standardized_df.sort_values(
                        by=["MIL Criticality", "RPN"],
                        ascending=[False, False],
                        na_position="last"
                    ).to_excel(writer, sheet_name='Top by MIL', index=False)
            
            # Статистика
            stats = {
                'Показатель': [
                    'Всего отказов', 'Средний RPN', 'Макс RPN',
                    'Мин RPN', 'Критических', 'Высоких',
                    'Средних', 'Низких'
                ],
                'Значение': [
                    len(df),
                    round(df['RPN'].mean(), 2),
                    df['RPN'].max(),
                    df['RPN'].min(),
                    len(df[df['RPN'] >= 200]),
                    len(df[(df['RPN'] >= 100) & (df['RPN'] < 200)]),
                    len(df[(df['RPN'] >= 40) & (df['RPN'] < 100)]),
                    len(df[df['RPN'] < 40])
                ]
            }
            stats_df = pd.DataFrame(stats)
            stats_df.to_excel(writer, sheet_name='Статистика', index=False)
            
            # Топ-рисков
            top_risks = df.nlargest(10, 'RPN')
            top_risks.to_excel(writer, sheet_name='Топ-10 рисков', index=False)
    
    @staticmethod
    def export_to_pdf(df: pd.DataFrame, filepath: str, 
                     include_charts: bool = False, chart_paths: List[str] = None,
                     standardized_df: pd.DataFrame = None):
        """
        Экспорт FMEA-таблицы в PDF с поддержкой русского языка.
        """
        # Регистрация шрифтов
        IOUtils._register_fonts()
        
        doc = SimpleDocTemplate(filepath, pagesize=landscape(A4),
                               leftMargin=1*cm, rightMargin=1*cm,
                               topMargin=1.5*cm, bottomMargin=1.5*cm)
        elements = []
        
        # Создание стилей с поддержкой кириллицы
        styles = getSampleStyleSheet()
        
        # Стиль заголовка
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName='DejaVuSans-Bold',
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        # Стиль обычного текста
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName='DejaVuSans',
            fontSize=10,
            alignment=TA_LEFT
        )
        
        # Заголовок
        title = Paragraph("<b>Отчёт FMEA/FMECA Analysis</b>", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        # Статистика
        stats_text = f"""
        <b>Общая статистика:</b><br/>
        Всего отказов: {len(df)}<br/>
        Средний RPN: {df['RPN'].mean():.2f}<br/>
        Максимальный RPN: {df['RPN'].max()}<br/>
        Критических рисков (RPN ≥ 200): {len(df[df['RPN'] >= 200])}<br/>
        Высоких рисков (100 ≤ RPN &lt; 200): {len(df[(df['RPN'] >= 100) & (df['RPN'] < 200)])}<br/>
        """
        elements.append(Paragraph(stats_text, normal_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Таблица (сокращённая для PDF)
        df_top = df.nlargest(20, 'RPN') if len(df) > 20 else df
        
        # ИСПРАВЛЕНО: Добавлена колонка "Категория"
        table_data = [['№', 'Компонент', 'Категория', 'Вид отказа', 'S', 'O', 'D', 'RPN']]
        
        for idx, row in enumerate(df_top.itertuples(), 1):
            table_data.append([
                str(idx),
                str(row.Компонент)[:20],
                str(row.Категория)[:15],
                str(row._6)[:30],  # ИСПРАВЛЕНО: индекс "Вид отказа"
                str(row.S),
                str(row.O),
                str(row.D),
                str(row.RPN)
            ])
        
        # Создание таблицы
        table = Table(table_data, colWidths=[1*cm, 3.5*cm, 2.5*cm, 5*cm, 1*cm, 1*cm, 1*cm, 1.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        # Цветовая индикация RPN
        for i, row in enumerate(df_top.itertuples(), 1):
            rpn = row.RPN
            if rpn >= 200:
                bg_color = colors.HexColor('#FF6B6B')
            elif rpn >= 100:
                bg_color = colors.HexColor('#FFD93D')
            elif rpn >= 40:
                bg_color = colors.HexColor('#FFF68F')
            else:
                bg_color = colors.HexColor('#C1FFC1')
            
            table.setStyle(TableStyle([
                ('BACKGROUND', (7, i), (7, i), bg_color)
            ]))
        
        elements.append(table)
        elements.append(Spacer(1, 1*cm))
        
        # Стандартизированный FMECA-блок (опционально)
        if standardized_df is not None and not standardized_df.empty:
            elements.append(PageBreak())
            elements.append(Paragraph("<b>Стандартизированная таблица FMECA</b>", title_style))
            elements.append(Spacer(1, 0.4*cm))
            
            # Сортировка по RPN
            by_rpn = standardized_df.sort_values(by=["RPN"], ascending=[False]).head(15)
            elements.append(Paragraph("<b>Сортировка: по RPN</b>", normal_style))
            elements.append(Spacer(1, 0.2*cm))
            
            rpn_table_data = [[
                "Component", "Function", "Failure Mode", "Cause",
                "Local", "Next", "End", "S", "O", "D", "RPN", "MIL",
                "Action", "Owner", "Due", "Before", "After"
            ]]
            for _, row in by_rpn.iterrows():
                rpn_table_data.append([
                    str(row.get("Component", ""))[:16],
                    str(row.get("Function", ""))[:14],
                    str(row.get("Failure Mode", ""))[:18],
                    str(row.get("Cause", ""))[:18],
                    str(row.get("Local Effect", ""))[:14],
                    str(row.get("Next Higher Effect", ""))[:14],
                    str(row.get("End Effect", ""))[:14],
                    str(row.get("Severity", "")),
                    str(row.get("Occurrence", "")),
                    str(row.get("Detection", "")),
                    str(row.get("RPN", "")),
                    str(row.get("MIL Criticality", "")),
                    str(row.get("Recommended Actions", ""))[:16],
                    str(row.get("Action Owner", ""))[:12],
                    str(row.get("Due Date", ""))[:12],
                    str(row.get("Before Actions (RPN)", "")),
                    str(row.get("After Actions (Residual RPN)", "")),
                ])
            
            std_table = Table(
                rpn_table_data,
                colWidths=[1.7*cm, 1.7*cm, 2.0*cm, 2.0*cm, 1.4*cm, 1.4*cm, 1.4*cm,
                           0.7*cm, 0.7*cm, 0.7*cm, 0.9*cm, 1.2*cm, 1.8*cm, 1.4*cm, 1.2*cm, 1.0*cm, 1.0*cm]
            )
            std_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#264653')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),
                ('FONTSIZE', (0, 0), (-1, 0), 7),
                ('FONTSIZE', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(std_table)
            elements.append(Spacer(1, 0.3*cm))
            
            # Сортировка по MIL criticality
            if "MIL Criticality" in standardized_df.columns:
                by_mil = standardized_df.sort_values(
                    by=["MIL Criticality", "RPN"],
                    ascending=[False, False],
                    na_position="last"
                ).head(10)
                elements.append(Paragraph("<b>Сортировка: по MIL criticality</b>", normal_style))
                elements.append(Spacer(1, 0.2*cm))
                
                mil_table_data = [["Component", "Failure Mode", "MIL", "RPN", "Before", "After", "Risk Reduction"]]
                for _, row in by_mil.iterrows():
                    mil_table_data.append([
                        str(row.get("Component", ""))[:24],
                        str(row.get("Failure Mode", ""))[:28],
                        str(row.get("MIL Criticality", "")),
                        str(row.get("RPN", "")),
                        str(row.get("Before Actions (RPN)", "")),
                        str(row.get("After Actions (Residual RPN)", "")),
                        str(row.get("Risk Reduction", "")),
                    ])
                
                mil_table = Table(mil_table_data, colWidths=[4.2*cm, 5.0*cm, 2.2*cm, 1.4*cm, 1.7*cm, 1.7*cm, 2.1*cm])
                mil_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2A9D8F')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),
                    ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                elements.append(mil_table)
        
        # Добавление графиков (если указаны)
        if include_charts and chart_paths:
            elements.append(PageBreak())
            elements.append(Paragraph("<b>Визуализация результатов</b>", title_style))
            elements.append(Spacer(1, 0.5*cm))
            
            for chart_path in chart_paths:
                if os.path.exists(chart_path):
                    try:
                        img = Image(chart_path, width=18*cm, height=12*cm)
                        elements.append(img)
                        elements.append(Spacer(1, 0.5*cm))
                    except:
                        pass
        
        # Сноска
        footer_text = """
        <br/><br/>
        <i>Отчёт сформирован автоматически средствами FMEA/FMECA Analysis Tool<br/>
        Соответствие стандартам: MIL-STD-1629A, IEC 60812, ГОСТ 27.310-95</i>
        """
        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph(footer_text, normal_style))
        
        # Сборка документа
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