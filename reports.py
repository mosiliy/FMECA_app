"""
Модуль генерации отчётов FMEA.
Создание комплексных отчётов с графиками.
"""

import pandas as pd
from typing import List
import os
import tempfile

from model import FMEAModel
from visualization import Visualization
from io_utils import IOUtils


class ReportGenerator:
    """Генератор отчётов FMEA/FMECA."""
    
    @staticmethod
    def generate_full_report(df: pd.DataFrame, output_path: str, 
                            report_format: str = 'pdf',
                            standardized_df: pd.DataFrame = None):
        """
        Генерация полного отчёта с графиками.
        
        Args:
            df: DataFrame с данными FMEA
            output_path: путь для сохранения отчёта
            report_format: формат ('pdf' или 'excel')
        """
        if report_format == 'pdf':
            ReportGenerator._generate_pdf_report(df, output_path, standardized_df=standardized_df)
        elif report_format == 'excel':
            ReportGenerator._generate_excel_report(df, output_path, standardized_df=standardized_df)
    
    @staticmethod
    def _generate_pdf_report(df: pd.DataFrame, output_path: str):
        """Генерация PDF отчёта с графиками."""
        # Создание временных файлов для графиков
        temp_dir = tempfile.mkdtemp()
        chart_paths = []
        
        try:
            # График 1: Распределение RPN
            chart1_path = os.path.join(temp_dir, 'rpn_dist.png')
            Visualization.plot_rpn_distribution(df, save_path=chart1_path)
            chart_paths.append(chart1_path)
            
            # График 2: Матрица критичности
            chart2_path = os.path.join(temp_dir, 'criticality.png')
            Visualization.plot_criticality_matrix(df, save_path=chart2_path)
            chart_paths.append(chart2_path)
            
            # График 3: RPN по категориям
            if 'Категория' in df.columns:
                chart3_path = os.path.join(temp_dir, 'rpn_by_category.png')
                Visualization.plot_rpn_by_category(df, save_path=chart3_path)
                chart_paths.append(chart3_path)
            
            # График 4: Категории риска
            chart4_path = os.path.join(temp_dir, 'risk_categories.png')
            Visualization.plot_risk_categories(df, save_path=chart4_path)
            chart_paths.append(chart4_path)
            
            # Генерация PDF
            IOUtils.export_to_pdf(df, output_path, 
                                include_charts=True, 
                                chart_paths=chart_paths)
            
        finally:
            # Очистка временных файлов
            for path in chart_paths:
                try:
                    os.remove(path)
                except:
                    pass
            try:
                os.rmdir(temp_dir)
            except:
                pass
    
    @staticmethod
    def _generate_excel_report(df: pd.DataFrame, output_path: str,
                               standardized_df: pd.DataFrame = None):
        """Генерация Excel отчёта."""
        IOUtils.export_to_excel(df, output_path, standardized_df=standardized_df)
    
    @staticmethod
    def get_top_risks_report(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """Получение отчёта по топ-рискам."""
        top_df = FMEAModel.get_top_risks(df, n)
        return top_df
    
    @staticmethod
    def get_statistics_report(df: pd.DataFrame) -> dict:
        """Получение статистического отчёта."""
        return FMEAModel.calculate_statistics(df)
    
    @staticmethod
    def build_standardized_report_dataframe(db, sort_by: str = "rpn") -> pd.DataFrame:
        """
        Формирование стандартизированного DataFrame FMECA из БД
        для расширенного экспорта Excel/PDF.
        """
        raw_data = db.get_failures_for_standard_report(sort_by=sort_by)
        std_df = FMEAModel.build_standardized_fmeca_dataframe(raw_data)
        return FMEAModel.sort_standardized_fmeca(std_df, sort_by=sort_by)
    
    @staticmethod
    def _generate_pdf_report(df: pd.DataFrame, output_path: str,
                             standardized_df: pd.DataFrame = None):
        """Генерация PDF отчёта с графиками."""
        temp_dir = tempfile.mkdtemp()
        chart_paths = []
        
        try:
            # График 1: Распределение RPN
            chart1_path = os.path.join(temp_dir, 'rpn_dist.png')
            Visualization.plot_rpn_distribution(df, save_path=chart1_path)
            chart_paths.append(chart1_path)
            
            # График 2: Матрица критичности
            chart2_path = os.path.join(temp_dir, 'criticality.png')
            Visualization.plot_criticality_matrix(df, save_path=chart2_path)
            chart_paths.append(chart2_path)
            
            # График 3: RPN по категориям
            if 'Категория' in df.columns:
                chart3_path = os.path.join(temp_dir, 'rpn_by_category.png')
                Visualization.plot_rpn_by_category(df, save_path=chart3_path)
                chart_paths.append(chart3_path)
            
            # График 4: Категории риска
            chart4_path = os.path.join(temp_dir, 'risk_categories.png')
            Visualization.plot_risk_categories(df, save_path=chart4_path)
            chart_paths.append(chart4_path)
            
            # НОВОЕ: График 5: Граф зависимостей
            chart5_path = os.path.join(temp_dir, 'dependency_graph.png')
            Visualization.show_dependency_graph(df, layout='hierarchical', 
                                               save_path=chart5_path, filter_rpn=100)
            chart_paths.append(chart5_path)
            
            # Генерация PDF
            IOUtils.export_to_pdf(df, output_path, 
                                include_charts=True, 
                                chart_paths=chart_paths,
                                standardized_df=standardized_df)
            
        finally:
            # Очистка
            for path in chart_paths:
                try:
                    os.remove(path)
                except:
                    pass
            try:
                os.rmdir(temp_dir)
            except:
                pass