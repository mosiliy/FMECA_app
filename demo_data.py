"""
Демонстрационные данные: 50 полных записей FMECA для ЦОД / серверной инфраструктуры.
"""

import random
from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database import Database


DEMO_FAILURES = [
    # system, subsystem, component, category, function, failure_mode, cause,
    # local, next, end, S, O, D, lambda, alpha, beta, t, controls, actions, owner, due, status,
    # phase, mode, spf, latent, ccf, rs, ro, rd
    ("ЦОД «Север»", "Вычислительный кластер", "Dell R750 #01", "Сервер",
     "Обработка вычислительных задач", "Перегрев CPU", "Засорение фильтров стойки",
     "Троттлинг ядер", "Снижение SLA кластера", "Прерывание пакетной обработки",
     7, 4, 3, 2.1e-6, 0.35, 0.7, 8760, "Мониторинг температуры", "Замена фильтров и ТО вентиляторов",
     "Инженер эксплуатации", "2026-07-15", "В работе", "Эксплуатация", "Пиковая нагрузка", 0, 0, 0, 5, 3, 2),
    ("ЦОД «Север»", "Вычислительный кластер", "Dell R750 #02", "Сервер",
     "Обработка вычислительных задач", "Отказ блока питания", "Деградация конденсаторов БП",
     "Аварийное отключение узла", "Потеря резервирования N+1", "Остановка сервиса виртуализации",
     9, 3, 4, 1.5e-6, 0.5, 0.9, 8760, "Дублирование БП", "Плановая замена БП",
     "Инженер по надёжности", "2026-06-20", "Запланировано", "Эксплуатация", "Номинальный", 1, 0, 0, 6, 2, 2),
    ("ЦОД «Север»", "Система хранения", "NetApp AFF A250", "Накопитель",
     "Долговременное хранение данных", "Ошибка чтения/записи SSD", "Исчерпание ресурса P/E циклов",
     "Повреждение блока данных", "Деградация массива RAID", "Потеря критичных томов",
     10, 4, 5, 3.2e-6, 0.4, 0.85, 8760, "SMART-мониторинг", "Проактивная замена дисков",
     "DBA", "2026-08-01", "Открыто", "Эксплуатация", "Номинальный", 1, 1, 0, 7, 3, 3),
    ("ЦОД «Север»", "Сеть", "Cisco Nexus 93180", "Сетевое оборудование",
     "Передача сетевого трафика", "Потеря связности порта", "Обрыв оптического патч-корда",
     "Изоляция хоста", "Разрыв LACP-агрегации", "Недоступность сервисов east-west",
     8, 5, 2, 4.5e-6, 0.25, 0.6, 8760, "LLDP/CDP мониторинг", "Аудит кабельной инфраструктуры",
     "Сетевой инженер", "2026-06-10", "В работе", "Эксплуатация", "Пиковая нагрузка", 0, 0, 0, 5, 4, 1),
    ("ЦОД «Юг»", "Виртуализация", "VMware vSphere Host-12", "Сервер",
     "Обработка вычислительных задач", "Программный сбой гипервизора", "Ошибка обновления ESXi",
     "Kernel panic хоста", "Миграция ВМ на другие узлы", "Простой бизнес-приложений",
     8, 3, 4, 1.8e-6, 0.3, 0.75, 8760, "Канареечные обновления", "Откат патча ESXi",
     "Системный инженер", "2026-05-25", "Закрыто", "Техническое обслуживание", "Номинальный", 0, 0, 0, 5, 2, 3),
    ("ЦОД «Юг»", "Память", "DDR4 ECC 64GB #A12", "Оперативная память",
     "Хранение оперативных данных", "Корректируемая ошибка ECC", "Космическое излучение / деградация",
     "Сброс страниц памяти", "Рост latency приложений", "Нестабильность СУБД",
     6, 6, 3, 5.5e-6, 0.45, 0.5, 8760, "Счётчик CE/UE", "Замена модуля DIMM",
     "Инженер эксплуатации", "2026-07-01", "Открыто", "Эксплуатация", "Номинальный", 0, 0, 0, 4, 5, 2),
    ("ЦОД «Юг»", "Охлаждение", "Чиллер Liebert PDX", "Система охлаждения",
     "Охлаждение и теплоотвод", "Падение давления хладагента", "Микротрещина контура",
     "Рост температуры зала", "Отключение части стоек", "Тепловой shutdown оборудования",
     9, 2, 5, 8e-7, 0.6, 0.95, 8760, "Датчики температуры/влажности", "Поиск утечки и дозаправка",
     "Инженер эксплуатации", "2026-06-30", "Критично", "Эксплуатация", "Пиковая нагрузка", 1, 0, 1, 7, 1, 4),
    ("ЦОД «Восток»", "Безопасность", "Palo Alto PA-5220", "Сетевое оборудование",
     "Передача сетевого трафика", "Переполнение таблицы сессий", "DDoS-атака L7",
     "Отбрасывание новых сессий", "Блокировка API-шлюза", "Нарушение доступности портала",
     8, 4, 3, 2.8e-6, 0.5, 0.8, 8760, "Rate limiting", "Усиление WAF и scrubbing",
     "Инженер ИБ", "2026-06-05", "В работе", "Эксплуатация", "Пиковая нагрузка", 0, 0, 0, 5, 3, 2),
    ("ЦОД «Восток»", "Резервное копирование", "Veeam Backup Proxy-3", "Сервер",
     "Долговременное хранение данных", "Сбой задания резервного копирования", "Нехватка места на репозитории",
     "Пропуск окна backup", "Отсутствие актуальной копии", "Невозможность восстановления DR",
     9, 5, 2, 3.5e-6, 0.4, 0.9, 8760, "Алерты заполнения", "Расширение хранилища бэкапов",
     "Инженер эксплуатации", "2026-06-12", "Открыто", "Эксплуатация", "Номинальный", 0, 1, 0, 6, 4, 1),
    ("ЦОД «Восток»", "БД", "PostgreSQL Primary", "Сервер",
     "Хранение оперативных данных", "Дедлок транзакций", "Неоптимальный план запроса",
     "Блокировка таблиц", "Таймаут приложений", "Остановка онлайн-операций",
     7, 5, 4, 4.1e-6, 0.35, 0.65, 8760, "pg_stat_activity", "Оптимизация индексов и запросов",
     "DBA", "2026-07-20", "В работе", "Эксплуатация", "Пиковая нагрузка", 0, 0, 0, 5, 4, 3),
]

# Дополнительные шаблоны для генерации до 50 записей
_COMPONENTS = [
    ("HP ProLiant DL380 Gen10", "Сервер", "Обработка вычислительных задач"),
    ("Intel Xeon Gold 6248R", "Процессор", "Обработка вычислительных задач"),
    ("Samsung PM9A3 3.84TB", "Накопитель", "Долговременное хранение данных"),
    ("HPE MSA 2060", "Накопитель", "Долговременное хранение данных"),
    ("Juniper QFX5100", "Сетевое оборудование", "Передача сетевого трафика"),
    ("APC Symmetra PX 40kW", "Блок питания", "Стабилизация электропитания"),
    ("Supermicro X12DPI", "Материнская плата", "Обработка вычислительных задач"),
    ("NVIDIA A100 80GB", "Процессор", "Обработка вычислительных задач"),
    ("Redis Cluster Node-4", "Сервер", "Хранение оперативных данных"),
    ("Kafka Broker-7", "Сервер", "Передача сетевого трафика"),
]

_MODES = [
    ("Перегрев", "Забитые радиаторы", "Троттлинг", "Рост latency", "Деградация сервиса"),
    ("Полный отказ", "Старение компонента", "Неработоспособность узла", "Потеря HA", "Простой системы"),
    ("Деградация производительности", "Износ носителя", "Медленные I/O", "Очередь задач", "SLA breach"),
    ("Скачки напряжения", "Скачок в сети 380В", "Сброс питания", "Рестарт кластера", "Потеря сессий"),
    ("Ошибка чтения/записи", "Битовые ошибки", "CRC mismatch", "Ретраи I/O", "Повреждение данных"),
]

_SYSTEMS = ["ЦОД «Север»", "ЦОД «Юг»", "ЦОД «Восток»", "ЦОД «Запад»", "DR-площадка"]
_SUBSYSTEMS = ["Кластер A", "Кластер B", "СХД", "Сеть spine-leaf", "Платформа данных", "ИБ", "Охлаждение"]
_OWNERS = ["Инженер по надёжности", "Системный инженер", "Инженер эксплуатации", "DBA", "Сетевой инженер"]
_PHASES = ["Проектирование", "Интеграция", "Испытания", "Эксплуатация", "Техническое обслуживание"]
_MODES_OP = ["Номинальный", "Пиковая нагрузка", "Резервный", "Деградированный", "Пуск/останов"]
_STATUSES = ["Открыто", "В работе", "Запланировано", "Закрыто", "Критично"]


def _generate_extra_records(count: int, rng: random.Random):
    records = []
    base_date = date(2026, 6, 1)
    for i in range(count):
        comp, cat, func = rng.choice(_COMPONENTS)
        mode, cause, local, next_e, end = rng.choice(_MODES)
        s, o, d = rng.randint(4, 10), rng.randint(2, 8), rng.randint(2, 7)
        lam = round(rng.uniform(5e-7, 8e-6), 7)
        alpha = round(rng.uniform(0.2, 0.6), 2)
        beta = round(rng.uniform(0.4, 0.95), 2)
        t = 8760
        rs = max(1, s - rng.randint(1, 3))
        ro = max(1, o - rng.randint(0, 2))
        rd = max(1, d - rng.randint(0, 2))
        due = (base_date + timedelta(days=rng.randint(10, 120))).isoformat()
        records.append((
            rng.choice(_SYSTEMS), rng.choice(_SUBSYSTEMS), f"{comp} #{i+11}", cat, func,
            mode, cause, local, next_e, end,
            s, o, d, lam, alpha, beta, t,
            "Регулярный мониторинг и алерты", rng.choice([
                "Замена компонента", "Плановое ТО", "Обновление прошивки",
                "Усиление мониторинга", "Изменение режима эксплуатации",
            ]),
            rng.choice(_OWNERS), due, rng.choice(_STATUSES),
            rng.choice(_PHASES), rng.choice(_MODES_OP),
            rng.randint(0, 1), rng.randint(0, 1), rng.randint(0, 1),
            rs, ro, rd,
        ))
    return records


def seed_demo_database(db: "Database", replace: bool = True) -> int:
    """
    Заполнение БД демонстрационными данными (50 отказов).
    
    Args:
        db: экземпляр Database
        replace: если True — удалить текущие компоненты и отказы
    
    Returns:
        число созданных записей об отказах
    """
    if replace:
        db.clear_all_data()
    
    rng = random.Random(42)
    all_records = list(DEMO_FAILURES) + _generate_extra_records(50 - len(DEMO_FAILURES), rng)
    
    cat_cache = {name: cid for cid, name in db.get_all_categories()}
    ft_cache = {}
    for ft in db.get_all_failure_types():
        ft_cache[ft[1]] = ft[0]
    cause_cache = {name: cid for cid, name in db.get_all_causes()}
    effect_cache = {name: cid for cid, name in db.get_all_effects()}
    
    created = 0
    for rec in all_records:
        (system, subsystem, component, category, function_text, failure_mode, cause,
         local_eff, next_eff, end_eff, s, o, d, lam, alpha, beta, t_mission,
         controls, actions, owner, due, status, phase, op_mode, spf, latent, ccf,
         rs, ro, rd) = rec
        
        cat_id = cat_cache.get(category)
        if cat_id is None:
            cat_id = db.add_category(category)
            cat_cache[category] = cat_id
        
        ft_id = ft_cache.get(failure_mode)
        if ft_id is None:
            ft_id = db.add_failure_type(failure_mode, default_s=s, default_o=o, default_d=d)
            ft_cache[failure_mode] = ft_id
        db.link_category_to_failure_type(cat_id, ft_id)
        
        cause_id = cause_cache.get(cause)
        if cause_id is None:
            cause_id = db.add_cause(cause)
            cause_cache[cause] = cause_id
        db.link_failure_type_to_cause(ft_id, cause_id)
        
        effect_name = end_eff
        effect_id = effect_cache.get(effect_name)
        if effect_id is None:
            effect_id = db.add_effect(effect_name)
            effect_cache[effect_name] = effect_id
        db.link_failure_type_to_effect(ft_id, effect_id)
        
        for domain, value in [
            ("function", function_text),
            ("effect", local_eff),
            ("effect", next_eff),
            ("effect", end_eff),
            ("action", actions),
            ("owner", owner),
            ("mission_phase", phase),
            ("operating_mode", op_mode),
        ]:
            db.ensure_fmeca_lookup_value(domain, value)
        
        comp_id = db.add_component(system, subsystem, component, cat_id)
        residual_rpn = s * o * d  # placeholder, recalculated in add_failure
        
        db.add_failure(
            comp_id, failure_mode, cause, end_eff, s, o, d,
            failure_type_id=ft_id, cause_id=cause_id, effect_id=effect_id,
            function_text=function_text,
            local_effect=local_eff,
            next_higher_effect=next_eff,
            end_effect=end_eff,
            current_controls=controls,
            recommended_actions=actions,
            action_owner=owner,
            due_date=due,
            action_status=status,
            failure_rate_lambda=lam,
            mode_ratio_alpha=alpha,
            conditional_prob_beta=beta,
            mission_time_t=t_mission,
            mission_phase=phase,
            operating_mode=op_mode,
            is_single_point=spf,
            is_latent=latent,
            is_common_cause=ccf,
            residual_severity=rs,
            residual_occurrence=ro,
            residual_detection=rd,
        )
        created += 1
    
    return created


def get_failure_count(db: "Database") -> int:
    db.cursor.execute("SELECT COUNT(*) FROM failures")
    return db.cursor.fetchone()[0]
