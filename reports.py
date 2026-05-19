"""
Модуль генерации отчётов FMEA/FMECA.
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
    def generate_full_report(
        df: pd.DataFrame,
        output_path: str,
        report_format: str = 'pdf',
        standardized_df: pd.DataFrame = None,
        comprehensive_df: pd.DataFrame = None,
    ):
        """
        Генерация полного отчёта со всеми таблицами и графиками.
        
        Args:
            df: базовый DataFrame FMEA
            output_path: путь сохранения
            report_format: 'pdf' или 'excel'
            standardized_df: таблица FMECA (англ. заголовки)
            comprehensive_df: полная таблица ГОСТ/MIL (рус. заголовки)
        """
        if report_format == 'pdf':
            ReportGenerator._generate_pdf_report(
                df, output_path,
                standardized_df=standardized_df,
                comprehensive_df=comprehensive_df,
            )
        elif report_format == 'excel':
            ReportGenerator._generate_excel_report(
                df, output_path,
                standardized_df=standardized_df,
                comprehensive_df=comprehensive_df,
            )
    
    @staticmethod
    def _generate_pdf_report(
        df: pd.DataFrame,
        output_path: str,
        standardized_df: pd.DataFrame = None,
        comprehensive_df: pd.DataFrame = None,
    ):
        """PDF-отчёт: все таблицы (без усечения) + полный набор графиков."""
        temp_dir = tempfile.mkdtemp()
        chart_paths = []
        
        try:
            chart_specs = [
                ('rpn_dist.png', lambda p: Visualization.plot_rpn_distribution(df, save_path=p)),
                ('criticality.png', lambda p: Visualization.plot_criticality_matrix(df, save_path=p)),
                ('risk_categories.png', lambda p: Visualization.plot_risk_categories(df, save_path=p)),
                ('rpn_by_component.png', lambda p: Visualization.plot_rpn_by_component(df, save_path=p)),
                ('so_matrix.png', lambda p: Visualization.plot_severity_occurrence_matrix(df, save_path=p)),
            ]
            if 'Категория' in df.columns:
                chart_specs.append(
                    ('rpn_by_category.png', lambda p: Visualization.plot_rpn_by_category(df, save_path=p))
                )
            if comprehensive_df is not None and not comprehensive_df.empty:
                chart_specs.append(
                    ('mil_ranking.png', lambda p: Visualization.plot_mil_criticality_ranking(
                        comprehensive_df, save_path=p
                    ))
                )
            chart_specs.append(
                ('dependency_graph.png', lambda p: Visualization.show_dependency_graph(
                    df, layout='hierarchical', save_path=p, filter_rpn=80
                ))
            )
            
            for filename, plot_fn in chart_specs:
                path = os.path.join(temp_dir, filename)
                try:
                    plot_fn(path)
                    chart_paths.append(path)
                except Exception:
                    pass
            
            IOUtils.export_to_pdf(
                df, output_path,
                include_charts=True,
                chart_paths=chart_paths,
                standardized_df=standardized_df,
                comprehensive_df=comprehensive_df,
                full_report=True,
            )
        finally:
            for path in chart_paths:
                try:
                    os.remove(path)
                except OSError:
                    pass
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass
    
    @staticmethod
    def _generate_excel_report(
        df: pd.DataFrame,
        output_path: str,
        standardized_df: pd.DataFrame = None,
        comprehensive_df: pd.DataFrame = None,
    ):
        """Excel-отчёт со всеми листами."""
        IOUtils.export_to_excel(
            df, output_path,
            standardized_df=standardized_df,
            comprehensive_df=comprehensive_df,
        )
    
    @staticmethod
    def get_top_risks_report(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        return FMEAModel.get_top_risks(df, n)
    
    @staticmethod
    def get_statistics_report(df: pd.DataFrame) -> dict:
        return FMEAModel.calculate_statistics(df)
    
    @staticmethod
    def build_standardized_report_dataframe(db, sort_by: str = "rpn") -> pd.DataFrame:
        raw_data = db.get_failures_for_standard_report(sort_by=sort_by)
        std_df = FMEAModel.build_standardized_fmeca_dataframe(raw_data)
        return FMEAModel.sort_standardized_fmeca(std_df, sort_by=sort_by)
    
    @staticmethod
    def build_comprehensive_report_dataframe(db, sort_by: str = "rpn") -> pd.DataFrame:
        """Полная таблица FMECA для отчётов по ГОСТ/MIL."""
        raw_data = db.get_failures_for_standard_report(sort_by=sort_by)
        comp_df = FMEAModel.build_comprehensive_fmeca_dataframe(raw_data)
        return FMEAModel.sort_comprehensive_fmeca(comp_df, sort_by=sort_by)
