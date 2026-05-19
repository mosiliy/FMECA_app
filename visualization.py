"""
Модуль визуализации данных FMEA/FMECA.
"""

import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import Polygon
import pandas as pd
import numpy as np
from typing import Optional
import seaborn as sns
import os

from model import FMEAModel

# Настройка шрифтов для matplotlib
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['axes.unicode_minus'] = False


class Visualization:
    """Класс для создания визуализаций FMEA-анализа."""
    
    @staticmethod
    def plot_rpn_distribution(df: pd.DataFrame, save_path: Optional[str] = None):
        """Построение гистограммы распределения RPN."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.hist(df['RPN'], bins=20, color='steelblue', edgecolor='black', alpha=0.7)
        
        # Линии категорий риска
        ax.axvline(x=40, color='green', linestyle='--', linewidth=2, label='Низкий риск')
        ax.axvline(x=100, color='orange', linestyle='--', linewidth=2, label='Средний риск')
        ax.axvline(x=200, color='red', linestyle='--', linewidth=2, label='Высокий риск')
        
        ax.set_xlabel('RPN (S×O×D)', fontsize=12)
        ax.set_ylabel('Количество отказов', fontsize=12)
        ax.set_title('Распределение приоритета рисков (RPN)', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()
    
    @staticmethod
    def plot_rpn_by_component(df: pd.DataFrame, top_n: int = 10,
                             save_path: Optional[str] = None):
        """Построение bar chart RPN по компонентам."""
        component_rpn = df.groupby('Компонент')['RPN'].sum().nlargest(top_n)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        colors_map = component_rpn.apply(lambda x:
            'red' if x >= 200 else
            'orange' if x >= 100 else
            'yellow' if x >= 40 else 'green'
        )
        
        bars = ax.barh(component_rpn.index, component_rpn.values, color=colors_map,
                      edgecolor='black', alpha=0.8)
        
        ax.set_xlabel('Суммарный RPN', fontsize=12)
        ax.set_ylabel('Компонент', fontsize=12)
        ax.set_title(f'Топ-{top_n} компонентов по суммарному RPN', fontsize=14, fontweight='bold')
        ax.grid(True, axis='x', alpha=0.3)
        
        for i, (idx, value) in enumerate(component_rpn.items()):
            ax.text(value, i, f' {int(value)}', va='center', fontsize=10)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()
    
    @staticmethod
    def plot_risk_categories(df: pd.DataFrame, save_path: Optional[str] = None):
        """Круговая диаграмма распределения категорий риска."""
        categories = {
            'Низкий': len(df[df['RPN'] < 40]),
            'Средний': len(df[(df['RPN'] >= 40) & (df['RPN'] < 100)]),
            'Высокий': len(df[(df['RPN'] >= 100) & (df['RPN'] < 200)]),
            'Критический': len(df[df['RPN'] >= 200])
        }
        
        categories = {k: v for k, v in categories.items() if v > 0}
        
        fig, ax = plt.subplots(figsize=(8, 8))
        
        colors_pie = ['green', 'yellow', 'orange', 'red']
        colors_pie = colors_pie[:len(categories)]
        
        wedges, texts, autotexts = ax.pie(
            categories.values(),
            labels=categories.keys(),
            autopct='%1.1f%%',
            colors=colors_pie,
            startangle=90,
            textprops={'fontsize': 11}
        )
        
        ax.set_title('Распределение категорий риска по RPN', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()
    
    @staticmethod
    def plot_severity_occurrence_matrix(df: pd.DataFrame,
                                       save_path: Optional[str] = None):
        """Матрица Severity vs Occurrence (bubble chart)."""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        sizes = df['RPN'] / df['RPN'].max() * 1000
        
        scatter = ax.scatter(
            df['O'], df['S'],
            s=sizes,
            c=df['RPN'],
            cmap='YlOrRd',
            alpha=0.6,
            edgecolors='black',
            linewidth=1
        )
        
        ax.set_xlabel('O — вероятность (Occurrence), шкала 1–10', fontsize=12)
        ax.set_ylabel('S — тяжесть (Severity), шкала 1–10', fontsize=12)
        ax.set_title('Матрица S×O (размер пузырька = RPN)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 11)
        ax.set_ylim(0, 11)
        
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('RPN', fontsize=11)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()
    
    @staticmethod
    def plot_criticality_matrix(df: pd.DataFrame, save_path: Optional[str] = None):
        """
        Матрица критичности (качественный подход):
        ось X — класс тяжести (IV → I);
        ось Y — уровень вероятности (E → A);
        в ячейках — число режимов отказа; пунктир — направление возрастания критичности
        (чем дальше от начала координат по диагонали, тем выше приоритет корректирующих действий).
        """
        sev_labels = FMEAModel.MIL_STD_1629A_SEVERITY_CATEGORIES  # IV, III, II, I
        prob_labels = FMEAModel.MIL_STD_1629A_PROBABILITY_LEVELS  # E..A bottom..top
        n_cols = len(sev_labels)
        n_rows = len(prob_labels)
        sev_index = {lab: i for i, lab in enumerate(sev_labels)}
        prob_index = {lab: i for i, lab in enumerate(prob_labels)}
        
        matrix = np.zeros((n_rows, n_cols), dtype=float)
        for _, row in df.iterrows():
            try:
                s = int(row["S"])
                o = int(row["O"])
            except (TypeError, ValueError):
                continue
            if not (1 <= s <= 10 and 1 <= o <= 10):
                continue
            cat = FMEAModel.map_severity_to_mil_std_1629a_category(s)
            lvl = FMEAModel.map_occurrence_to_mil_std_1629a_level(o)
            matrix[prob_index[lvl], sev_index[cat]] += 1
        
        fig, ax = plt.subplots(figsize=(11, 8.2))
        vmax = max(float(matrix.max()), 1.0)
        
        tri = Polygon(
            [
                (-0.5, n_rows - 0.5),
                (n_cols - 0.5, n_rows - 0.5),
                (n_cols - 0.5, -0.5),
            ],
            closed=True,
            facecolor="crimson",
            alpha=0.07,
            edgecolor="none",
            zorder=0,
        )
        ax.add_patch(tri)
        
        im = ax.imshow(
            matrix,
            cmap="YlOrRd",
            aspect="equal",
            origin="lower",
            vmin=0,
            vmax=vmax,
            extent=(-0.5, n_cols - 0.5, -0.5, n_rows - 0.5),
            zorder=2,
        )
        
        ax.set_xticks(np.arange(n_cols))
        ax.set_yticks(np.arange(n_rows))
        ax.set_xticklabels(
            [
                "IV\n(Minor)",
                "III\n(Marginal)",
                "II\n(Critical)",
                "I\n(Catastrophic)",
            ],
            fontsize=10,
        )
        ax.set_yticklabels(
            [
                "E — Extremely\nunlikely",
                "D — Remote",
                "C — Occasional",
                "B — Reasonably\nprobable",
                "A — Frequent",
            ],
            fontsize=9,
        )
        ax.set_xlabel("Класс тяжести (IV → I, возрастание →)", fontsize=11)
        ax.set_ylabel("Уровень вероятности (E → A, ↑ возрастание)", fontsize=11)
        ax.set_title(
            "Матрица критичности — число режимов отказа в ячейке",
            fontsize=12, fontweight="bold",
        )
        
        for i in range(n_rows):
            for j in range(n_cols):
                count = int(matrix[i, j])
                if count == 0:
                    continue
                face = im.cmap(im.norm(count))
                luminance = 0.299 * face[0] + 0.587 * face[1] + 0.114 * face[2]
                txt_color = "white" if luminance < 0.55 else "black"
                ax.text(
                    j, i, str(count),
                    ha="center", va="center", color=txt_color, fontsize=12, fontweight="bold",
                    zorder=5,
                )
        
        # Сетка по границам ячеек (вид «таблицы» как в отчёте MIL)
        for x in np.arange(-0.5, n_cols, 1):
            ax.axvline(x, color="#333333", linewidth=0.9)
        for y in np.arange(-0.5, n_rows, 1):
            ax.axhline(y, color="#333333", linewidth=0.9)
        
        # Диагональ «от начала координат»: IV/E → I/A (возрастание критичности)
        ax.plot(
            [-0.5, n_cols - 0.5],
            [-0.5, n_rows - 0.5],
            color="#1565C0",
            linestyle="--",
            linewidth=2.2,
            alpha=0.85,
            label="Increasing criticality (diagonal)",
            zorder=3,
        )
        ax.legend(loc="upper left", fontsize=8, framealpha=0.92)
        
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("Количество режимов отказа в ячейке", fontsize=10)
        
        note = (
            "Сопоставление шкал FMEA (1–10): "
            "S: 9–10→I, 7–8→II, 5–6→III, 1–4→IV  |  "
            "O: 9–10→A, 7–8→B, 5–6→C, 3–4→D, 1–2→E."
        )
        fig.text(0.5, 0.02, note, ha="center", fontsize=8, style="italic")
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.14)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            plt.close()
        else:
            plt.show()
    
    @staticmethod
    def plot_rpn_by_category(df: pd.DataFrame, save_path: Optional[str] = None):
        """
        НОВОЕ: График RPN по категориям компонентов.
        """
        if 'Категория' not in df.columns:
            print("Колонка 'Категория' отсутствует")
            return
        
        category_rpn = df.groupby('Категория')['RPN'].sum().sort_values(ascending=True)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        colors_map = category_rpn.apply(lambda x:
            'red' if x >= 300 else
            'orange' if x >= 150 else
            'yellow' if x >= 50 else 'green'
        )
        
        bars = ax.barh(category_rpn.index, category_rpn.values, color=colors_map,
                      edgecolor='black', alpha=0.8)
        
        ax.set_xlabel('Суммарный RPN', fontsize=12)
        ax.set_ylabel('Категория компонента', fontsize=12)
        ax.set_title('Суммарный RPN по категориям компонентов', fontsize=14, fontweight='bold')
        ax.grid(True, axis='x', alpha=0.3)
        
        for i, (idx, value) in enumerate(category_rpn.items()):
            ax.text(value, i, f' {int(value)}', va='center', fontsize=10)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()

    @staticmethod
    def show_dependency_graph(df: pd.DataFrame, 
                             layout: str = 'hierarchical',
                             save_path: Optional[str] = None,
                             filter_rpn: Optional[int] = None):
        """
        НОВОЕ: Построение графа зависимостей FMEA.
        
        Args:
            df: DataFrame с данными FMEA
            layout: тип расположения узлов
            save_path: путь для сохранения
            filter_rpn: фильтр по минимальному RPN
        """
        # Преобразование DataFrame обратно в формат кортежей
        data = []
        for row in df.itertuples():
            data.append((
                row.ID,
                row.Система,
                row.Подсистема,
                row.Компонент,
                row.Категория,
                row._6,  # Вид отказа
                row.Причина,
                row.Последствие,
                row.S,
                row.O,
                row.D,
                row.RPN
            ))
        
        from graph_analysis import FMEAGraph
        
        graph = FMEAGraph(data)
        graph.visualize(
            layout=layout,
            save_path=save_path,
            filter_rpn=filter_rpn
        )
    
    @staticmethod
    def plot_mil_criticality_ranking(comprehensive_df: pd.DataFrame, top_n: int = 15,
                                     save_path: Optional[str] = None):
        """Рейтинг количественной критичности Cm."""
        col = "Критичность Cm"
        if col not in comprehensive_df.columns or comprehensive_df.empty:
            return
        ranked = (
            comprehensive_df.dropna(subset=[col])
            .sort_values(by=[col, "RPN"], ascending=[False, False])
            .head(top_n)
        )
        if ranked.empty:
            return
        
        labels = [
            f"{row['Компонент'][:18]} / {row['Вид отказа'][:16]}"
            for _, row in ranked.iterrows()
        ]
        
        fig, ax = plt.subplots(figsize=(12, max(5, top_n * 0.35)))
        values = ranked[col].astype(float)
        bars = ax.barh(labels, values, color='teal', edgecolor='black', alpha=0.85)
        ax.set_xlabel('Критичность Cm = λ×α×β×t', fontsize=11)
        ax.set_title(
            f'Топ-{len(ranked)} режимов по количественной критичности',
            fontsize=13, fontweight='bold',
        )
        ax.grid(True, axis='x', alpha=0.3)
        for bar, val in zip(bars, values):
            ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                    f' {val:.4g}', va='center', fontsize=9)
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()