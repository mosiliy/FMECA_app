"""
Модуль построения графа зависимостей FMEA.
Визуализация связей: Причина → Тип отказа → Последствие → Компонент

ЛОГИКА:
--------
Каждая запись FMEA создаёт цепочку из 4 узлов:
1. ПРИЧИНА (жёлтый) - что вызвало отказ
2. ТИП ОТКАЗА (красный) - какой отказ произошёл  
3. ПОСЛЕДСТВИЕ (зелёный) - к чему это привело
4. КОМПОНЕНТ (синий) - какой компонент затронут

Связи направленные:
- ПРИЧИНА → ТИП ОТКАЗА (вес = Occurrence)
- ТИП ОТКАЗА → ПОСЛЕДСТВИЕ (вес = Severity)
- ПОСЛЕДСТВИЕ → КОМПОНЕНТ (вес = Detection)

Если несколько записей имеют одинаковые причины/последствия,
они объединяются в один узел, создавая более сложную сеть.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import networkx as nx
from typing import List, Dict, Tuple, Optional
import pandas as pd
import textwrap

# Настройка шрифтов
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['axes.unicode_minus'] = False


class FMEAGraph:
    """Класс для построения и анализа графа зависимостей FMEA."""
    
    def __init__(self, data: List[Tuple]):
        """
        Инициализация графа.
        
        Args:
            data: список кортежей из БД
                (id, system, subsystem, component, category,
                 failure_mode, failure_cause, failure_effect,
                 severity, occurrence, detection, rpn)
        """
        self.data = data
        self.graph = nx.DiGraph()
        self._build_graph()
    
    def _build_graph(self):
        """Построение направленного графа зависимостей."""
        for record in self.data:
            record_id = record[0]
            component = record[3]
            category = record[4] if record[4] else "Без категории"
            failure_mode = record[5]
            cause = record[6]
            effect = record[7]
            severity = record[8]
            occurrence = record[9]
            detection = record[10]
            rpn = record[11]
            
            # Создание уникальных идентификаторов узлов
            node_cause = f"[CAUSE] {cause}"
            node_failure = f"[FAIL] {failure_mode}"
            node_effect = f"[EFFECT] {effect}"
            node_component = f"[COMP] {component}"
            
            # Добавление узлов с атрибутами
            # Узлы могут дублироваться - это нормально, NetworkX их объединит
            self.graph.add_node(node_cause, 
                               type='cause', 
                               label=cause,
                               occurrence=occurrence)
            
            self.graph.add_node(node_failure, 
                               type='failure', 
                               label=failure_mode,
                               severity=severity,
                               rpn=rpn)
            
            self.graph.add_node(node_effect, 
                               type='effect', 
                               label=effect,
                               detection=detection)
            
            self.graph.add_node(node_component, 
                               type='component', 
                               label=component,
                               category=category,
                               rpn=rpn)
            
            # Добавление направленных связей
            # Цепочка: ПРИЧИНА → ОТКАЗ → ПОСЛЕДСТВИЕ → КОМПОНЕНТ
            self.graph.add_edge(node_cause, node_failure, 
                               weight=occurrence, 
                               edge_type='cause_to_failure')
            
            self.graph.add_edge(node_failure, node_effect, 
                               weight=severity, 
                               edge_type='failure_to_effect')
            
            self.graph.add_edge(node_effect, node_component, 
                               weight=detection, 
                               edge_type='effect_to_component')
        
        print(f"\n{'='*60}")
        print(f"ГРАФ ЗАВИСИМОСТЕЙ ПОСТРОЕН")
        print(f"{'='*60}")
        print(f"Всего узлов: {self.graph.number_of_nodes()}")
        print(f"Всего связей: {self.graph.number_of_edges()}")
        print(f"{'='*60}\n")
    
    def visualize(self, 
                  layout: str = 'hierarchical',
                  save_path: Optional[str] = None,
                  figsize: Tuple[int, int] = (20, 14),
                  show_labels: bool = True,
                  filter_rpn: Optional[int] = None):
        """
        Визуализация графа зависимостей.
        
        Args:
            layout: тип расположения узлов
            save_path: путь для сохранения
            figsize: размер фигуры
            show_labels: показывать подписи
            filter_rpn: минимальный RPN для отображения
        """
        # Фильтрация по RPN
        if filter_rpn:
            # Находим компоненты с RPN >= filter_rpn
            filtered_components = [
                node for node, attr in self.graph.nodes(data=True)
                if attr.get('type') == 'component' and attr.get('rpn', 0) >= filter_rpn
            ]
            
            # Находим все узлы, связанные с этими компонентами
            filtered_nodes = set()
            for comp in filtered_components:
                # Все предшественники компонента
                filtered_nodes.update(nx.ancestors(self.graph, comp))
                filtered_nodes.add(comp)
            
            subgraph = self.graph.subgraph(filtered_nodes)
        else:
            subgraph = self.graph
        
        if len(subgraph.nodes()) == 0:
            print("⚠️ Нет узлов для отображения после фильтрации")
            return
        
        print(f"Отображается узлов: {subgraph.number_of_nodes()}")
        print(f"Отображается связей: {subgraph.number_of_edges()}")
        
        # Создание фигуры
        fig, ax = plt.subplots(figsize=figsize, facecolor='white')
        
        # Выбор алгоритма расположения
        if layout == 'hierarchical':
            pos = self._hierarchical_layout(subgraph)
        elif layout == 'spring':
            pos = nx.spring_layout(subgraph, k=3, iterations=50, seed=42)
        elif layout == 'circular':
            pos = nx.circular_layout(subgraph)
        elif layout == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(subgraph)
        else:
            pos = nx.spring_layout(subgraph, seed=42)
        
        # Разделение узлов по типам
        node_types = {
            'component': [],
            'failure': [],
            'cause': [],
            'effect': []
        }
        
        for node, attr in subgraph.nodes(data=True):
            node_type = attr.get('type', 'unknown')
            if node_type in node_types:
                node_types[node_type].append(node)
        
        # Цветовая схема
        colors = {
            'component': '#1E88E5',  # Синий
            'failure': '#E53935',    # Красный
            'cause': '#FDD835',      # Жёлтый
            'effect': '#43A047'      # Зелёный
        }
        
        # Размеры узлов - увеличены для лучшей видимости текста
        sizes = {
            'component': 4000,
            'failure': 3500,
            'cause': 3000,
            'effect': 3000
        }
        
        # Отрисовка узлов по типам
        for node_type, nodes in node_types.items():
            if not nodes:
                continue
            
            nx.draw_networkx_nodes(
                subgraph, pos,
                nodelist=nodes,
                node_color=colors[node_type],
                node_size=sizes[node_type],
                alpha=0.85,
                ax=ax,
                node_shape='o',
                edgecolors='white',
                linewidths=2
            )
        
        # Отрисовка рёбер с улучшенной видимостью
        edges = subgraph.edges()
        
        if edges:
            weights = [subgraph[u][v].get('weight', 1) for u, v in edges]
            
            nx.draw_networkx_edges(
                subgraph, pos,
                edgelist=edges,
                width=[w * 0.8 for w in weights],
                alpha=0.6,
                edge_color='#424242',
                arrows=True,
                arrowsize=25,
                arrowstyle='->',
                connectionstyle='arc3,rad=0.15',
                ax=ax,
                min_source_margin=25,
                min_target_margin=25
            )
        
        # Подписи узлов с переносом строк
        if show_labels:
            labels = {}
            for node, attr in subgraph.nodes(data=True):
                label = attr.get('label', node)
                # Перенос длинных подписей
                wrapped = self._wrap_label(label, width=20)
                labels[node] = wrapped
            
            # Отрисовка подписей с улучшенной читаемостью
            for node, label in labels.items():
                x, y = pos[node]
                ax.text(x, y, label,
                       fontsize=8,
                       fontweight='bold',
                       ha='center',
                       va='center',
                       color='white',
                       bbox=dict(boxstyle='round,pad=0.3', 
                                facecolor='black', 
                                alpha=0.3,
                                edgecolor='none'))
        
        # Легенда
        legend_elements = [
            mpatches.Patch(facecolor=colors['cause'], edgecolor='white', 
                          label='🟡 Причины отказов'),
            mpatches.Patch(facecolor=colors['failure'], edgecolor='white', 
                          label='🔴 Типы отказов'),
            mpatches.Patch(facecolor=colors['effect'], edgecolor='white', 
                          label='🟢 Последствия'),
            mpatches.Patch(facecolor=colors['component'], edgecolor='white', 
                          label='🔵 Компоненты'),
        ]
        
        ax.legend(handles=legend_elements, 
                 loc='upper left', 
                 fontsize=11, 
                 framealpha=0.95,
                 edgecolor='gray')
        
        # Заголовок
        title = "Граф зависимостей FMEA\nПричина → Тип отказа → Последствие → Компонент"
        if filter_rpn:
            title += f"\n(Фильтр: RPN ≥ {filter_rpn})"
        
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        # Добавление пояснения
        info_text = (
            f"Узлов: {subgraph.number_of_nodes()} | "
            f"Связей: {subgraph.number_of_edges()}\n"
            f"Направление стрелок показывает причинно-следственную связь"
        )
        ax.text(0.5, -0.05, info_text,
               transform=ax.transAxes,
               ha='center',
               fontsize=9,
               style='italic',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        ax.axis('off')
        ax.margins(0.1)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
        else:
            plt.show()
    
    def _hierarchical_layout(self, graph: nx.DiGraph) -> Dict:
        """
        Иерархическое расположение узлов по уровням.
        
        Уровни (сверху вниз):
        0 - Причины (CAUSE) - верхний уровень
        1 - Типы отказов (FAIL)
        2 - Последствия (EFFECT)
        3 - Компоненты (COMP) - нижний уровень
        """
        pos = {}
        
        # Разделение по уровням
        levels = {
            0: [],  # Причины
            1: [],  # Отказы
            2: [],  # Последствия
            3: []   # Компоненты
        }
        
        for node, attr in graph.nodes(data=True):
            node_type = attr.get('type', 'unknown')
            if node_type == 'cause':
                levels[0].append(node)
            elif node_type == 'failure':
                levels[1].append(node)
            elif node_type == 'effect':
                levels[2].append(node)
            elif node_type == 'component':
                levels[3].append(node)
        
        # Y-координаты уровней (сверху вниз)
        y_positions = {0: 3, 1: 2, 2: 1, 3: 0}
        
        for level, nodes in levels.items():
            y = y_positions[level]
            n = len(nodes)
            if n == 0:
                continue
            
            # Равномерное распределение по X
            if n == 1:
                x_positions = [0]
            else:
                x_positions = [i * 8.0 / (n - 1) - 4 for i in range(n)]
            
            for i, node in enumerate(sorted(nodes)):
                pos[node] = (x_positions[i], y)
        
        return pos
    
    def _wrap_label(self, text: str, width: int = 20) -> str:
        """
        Перенос длинных подписей на несколько строк.
        
        Args:
            text: исходный текст
            width: максимальная ширина строки в символах
        
        Returns:
            Текст с переносами строк
        """
        if len(text) <= width:
            return text
        
        # Разбиваем на слова и собираем с переносами
        lines = textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False)
        
        # Ограничиваем 3 строками
        if len(lines) > 3:
            lines = lines[:3]
            lines[-1] = lines[-1][:width-3] + '...'
        
        return '\n'.join(lines)
    
    def get_statistics(self) -> Dict:
        """Получение статистики по графу."""
        stats = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'components': len([n for n, a in self.graph.nodes(data=True) if a.get('type') == 'component']),
            'failures': len([n for n, a in self.graph.nodes(data=True) if a.get('type') == 'failure']),
            'causes': len([n for n, a in self.graph.nodes(data=True) if a.get('type') == 'cause']),
            'effects': len([n for n, a in self.graph.nodes(data=True) if a.get('type') == 'effect']),
        }
        
        if stats['total_nodes'] > 0:
            stats['avg_degree'] = sum(dict(self.graph.degree()).values()) / stats['total_nodes']
            stats['density'] = nx.density(self.graph)
        else:
            stats['avg_degree'] = 0
            stats['density'] = 0
        
        return stats
    
    def find_critical_paths(self, top_n: int = 5) -> List[Tuple]:
        """
        Поиск критических путей (с наибольшим суммарным весом).
        
        Критический путь - это полная цепочка:
        ПРИЧИНА → ОТКАЗ → ПОСЛЕДСТВИЕ → КОМПОНЕНТ
        
        Args:
            top_n: количество путей для возврата
        
        Returns:
            Список путей с их весами
        """
        paths = []
        
        # Находим все пути от причин к компонентам
        cause_nodes = [n for n, a in self.graph.nodes(data=True) if a.get('type') == 'cause']
        comp_nodes = [n for n, a in self.graph.nodes(data=True) if a.get('type') == 'component']
        
        for cause in cause_nodes:
            for comp in comp_nodes:
                if nx.has_path(self.graph, cause, comp):
                    try:
                        # Все простые пути
                        for path in nx.all_simple_paths(self.graph, cause, comp, cutoff=4):
                            # Вычисление суммарного веса
                            weight = sum(
                                self.graph[path[i]][path[i+1]].get('weight', 1)
                                for i in range(len(path) - 1)
                            )
                            
                            # Извлекаем читаемые названия
                            readable_path = [
                                self.graph.nodes[node].get('label', node)
                                for node in path
                            ]
                            
                            paths.append((readable_path, weight))
                    except:
                        continue
        
        # Сортировка по весу
        paths.sort(key=lambda x: x[1], reverse=True)
        
        return paths[:top_n]
    
    def analyze_centrality(self) -> pd.DataFrame:
        """
        Анализ центральности узлов.
        
        Центральность показывает "важность" узла в сети.
        - Degree: количество связей
        - Betweenness: как часто узел лежит на кратчайших путях
        - Closeness: средняя близость к другим узлам
        
        Returns:
            DataFrame с метриками центральности
        """
        degree_centrality = nx.degree_centrality(self.graph)
        betweenness_centrality = nx.betweenness_centrality(self.graph)
        
        try:
            closeness_centrality = nx.closeness_centrality(self.graph)
        except:
            closeness_centrality = {n: 0 for n in self.graph.nodes()}
        
        data = []
        for node, attr in self.graph.nodes(data=True):
            data.append({
                'Узел': attr.get('label', node)[:40],
                'Тип': self._get_type_label(attr.get('type', 'unknown')),
                'Degree Centrality': round(degree_centrality[node], 4),
                'Betweenness Centrality': round(betweenness_centrality[node], 4),
                'Closeness Centrality': round(closeness_centrality[node], 4),
                'RPN': attr.get('rpn', 0)
            })
        
        df = pd.DataFrame(data)
        return df.sort_values('Betweenness Centrality', ascending=False)
    
    def _get_type_label(self, node_type: str) -> str:
        """Получение русского названия типа узла."""
        labels = {
            'component': 'Компонент',
            'failure': 'Тип отказа',
            'cause': 'Причина',
            'effect': 'Последствие'
        }
        return labels.get(node_type, node_type)
    
    def export_to_graphml(self, filepath: str):
        """Экспорт графа в формат GraphML."""
        nx.write_graphml(self.graph, filepath)
        print(f"Граф экспортирован в {filepath}")
    
    def print_summary(self):
        """Вывод сводной информации о графе в консоль."""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("СВОДКА ПО ГРАФУ ЗАВИСИМОСТЕЙ FMEA")
        print("="*60)
        print(f"Всего узлов: {stats['total_nodes']}")
        print(f"  • Причины: {stats['causes']}")
        print(f"  • Типы отказов: {stats['failures']}")
        print(f"  • Последствия: {stats['effects']}")
        print(f"  • Компоненты: {stats['components']}")
        print(f"\nВсего связей: {stats['total_edges']}")
        print(f"Средняя степень узла: {stats['avg_degree']:.2f}")
        print(f"Плотность графа: {stats['density']:.4f}")
        
        print("\n" + "-"*60)
        print("ТОП-5 КРИТИЧЕСКИХ ПУТЕЙ:")
        print("-"*60)
        
        critical_paths = self.find_critical_paths(top_n=5)
        for i, (path, weight) in enumerate(critical_paths, 1):
            print(f"\n{i}. Суммарный вес: {weight}")
            for j, node_label in enumerate(path):
                arrow = " → " if j < len(path) - 1 else ""
                print(f"   {node_label}{arrow}")
        
        print("\n" + "="*60 + "\n")