import warnings
from datetime import datetime
from typing import List, Optional

import pandas as pd
from pydantic import ValidationError
import gc
import re

from models.logs import Request, SalaryData
from models.user import User
from services.logs import log_request
import json
from catboost import CatBoostRegressor

warnings.filterwarnings("ignore")


def get_all_users(session) -> List[User]:
    """Возвращает список всех зарегистрированных пользователей."""
    return session.query(User).all()


def get_user(user_id: int, session) -> Optional[User]:
    """Возвращает объект класса User, если такой user_id есть в БД."""
    return session.query(User).where(User.user_id == user_id).first()


def get_user_by_email(email: str, session) -> Optional[User]:
    """Возвращает объект класса User, если такой email есть в БД."""
    return session.query(User).where(User.email == email).first()


def create_user(
    username: str,
    email: str,
    password: str,
    session
) -> dict[str, str]:
    """
    Проверяет, что пользователь с таким e-mail не зарегистрирован и
    создает нового пользователя в БД.
    """
    # Проверка на отсутствие email в БД
    old_user = session.query(User).where(User.email == email).first()
    if old_user is not None:
        return {'error': 'Email already in use'}

    # Запись информации о новом пользователе в БД
    new_user = User(
        email=email,
        username=username,
        password_hash=password
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {'success': 'Successfully created'}

# TODO разнести логику, сейчас всё в одной куче и неудобно работать

def process_request(
    user_id: int,
    specializations: str,
    text: str,
    experience: str,
    employment: str,
    area: str,
    schedule: str,
    model,
    session
) -> dict:
    """
    Принимает запрос от пользователя, обрабатывает запрос и
    возвращает результат.
    """
    # Приведение запроса в нужный формат


    raw_data = {'specializations': specializations, 'text': text, 'experience':  experience, 'employment': employment,
                'area': area, 'schedule':  schedule}

    # Получение предсказания от модели
    salary = predict(raw_data)
    #salary = model.predict(raw_data)

    # Конвертация в JSON
    response = {
        'salary': int(salary)
    }

    # Проверка ответа модели
    try:
        SalaryData(**response)
    except ValidationError:
        return {'error': 'Model failed'}

    # Сохранение данных запроса в БД
    request = Request(
        user_id=user_id,
        vacancy_name=specializations,
        vacancy_description=text,
        salary_from=response['salary'],
        salary_to=0,
        timestamp=datetime.now()
    )
    log_request(request, session)
    return response

def load_skills_from_json():
    with open('skills_list.json', 'r', encoding='utf-8') as file:
        skills_list = json.load(file)

    return skills_list

def open_dict(json_path):
    with open(json_path, 'r', encoding='utf-8') as file:
        skills_list = json.load(file)

    return skills_list

def ecd_skills(df, skills):
    df['skills'] = df['skills'].fillna('')
    df['skills'] = df['skills'].apply(lambda x: [skill.strip() for skill in x.split(',')])
    for skill_name in skills:
        df[skill_name] = df['skills'].apply(lambda x: 1 if skill_name in x else 0)
    return df

def load_model() -> CatBoostRegressor:
    model_path = './mlsys/cb_super'
    model = CatBoostRegressor()
    model.load_model(model_path)
    return model

def make_row(df, skills, city, schedule, experience, specializations, emp_dict):
    dict_schedule = open_dict('dict_schedule.json')
    dict_area = open_dict('dict_area.json')
    dict_prof = open_dict('dict_prof.json')
    ski = None
    experience = float(experience)
    if skills:
        ski = ','.join([skill.lower() for skill in skills])
    new_data = {
     'area': dict_area.get(city),
     'schedule': dict_schedule.get(schedule),
     'experience': experience,
     'professional_roles': dict_prof.get(specializations),
     'skills': ski if ski else '',
     'employment_Проектная работа': emp_dict['employment_Проектная работа'],
     'employment_Стажировка': emp_dict['employment_Стажировка'],
     'employment_Частичная занятость': emp_dict['employment_Частичная занятость'],
     'experience^3': experience ** 3 if experience else 0,
     'has_experience': 1 if experience else 0
    }

    new_row = pd.DataFrame([new_data])
    df = pd.concat([df, new_row], ignore_index=True)
    return df

def process(raw_data):

        loaded_skills = load_skills_from_json()

        specializations = raw_data['specializations']
        skills = extract_skills(raw_data['text'], loaded_skills)
        experience = raw_data['experience']
        experience = check_experience(experience)
        emp = raw_data['employment']
        city = raw_data['area']
        schedule = raw_data['schedule']

        # create df
        df = init_df()
        # process the data
        emp_dict = emp_operations(emp)
        df = make_row(df, skills, city, schedule, experience, specializations, emp_dict)
        skills_list = load_skills_from_json()
        ecd_skills(df, skills_list)
        final_df = df.drop('skills', axis=1)
        del df
        gc.collect()
        return final_df

def extract_skills(text, skills):
    # Приводим текст к нижнему регистру для нечувствительного к регистру поиска
    text_lower = text.lower()

    # Создаём множество для хранения найденных навыков
    found_skills = set()

    # Проходим по каждому навыку из списка
    for skill in skills:
        # Создаём шаблон, который ищет навык (без учета регистра)
        skill_pattern = re.escape(skill.strip().lower())

        # Проверяем, присутствует ли навык в тексте
        if re.search(skill_pattern, text_lower):
            found_skills.add(skill.strip())

    return list(found_skills)

def init_df():
    df = pd.DataFrame(columns=[
     'area', 'schedule', 'experience',
     'professional_roles', 'skills',
     'employment_Проектная работа',
     'employment_Стажировка', 'employment_Частичная занятость',
     'experience^3', 'has_experience'
    ])
    return df

def emp_operations(emp):
    emp_dict = {'employment_Проектная работа': 0,
                'employment_Стажировка': 0,
                'employment_Частичная занятость': 0}

    for key in emp_dict:
        if isinstance(emp, str):
            if key[11:].lower() == emp.lower():
                emp_dict[key] = 1
    return emp_dict



def predict(raw_data):
    final_df = process(raw_data)
    model = load_model()
    final_df5 = final_df.drop(columns=['schedule'])

    # Создайте новый DataFrame, отбирая существующие колонки
    existing_columns = [col for col in columns if col in final_df5.columns]

    # Убедитесь, что данные в new_df20 располагаются согласно order в columns
    new_df20 = final_df5[existing_columns].reindex(columns=columns).copy()


    # Предсказание зарплаты
    salary = model.predict(new_df20)
    salary = float(salary[0])
    return salary

def check_experience(exp):
    return 0 if exp == 0 or exp is None else exp

columns = ['area', 'experience', 'professional_roles', 'msa', 'erp', 'системная интеграция', 'статистика', 'разработка проектной документации', 'bpmn', '1с:erp.ух', 'анализ', 'computer vision', 'администрирование', 'gtm', 'ms excel', 'archimate', 'xsd', 'ms sql server', 'python', 'swagger', 's3', 'uml', 'power pivot', 'scada', 'фт', 'прогнозирование', 'google analytics', '1с erp', 'tcp/ip', 'ручное тестирование', 'javascript', 'mobilenet', 'bigquery', 'kubernetes', 'ms power bi', 'машинное обучение', 'ap', 'высшее образование', 'написание инструкций', 'grafana', 'навыки презентации', 'draw.io', 'аналитик 1с', 'ит', 'atlassian confluence', 'оптимизация бизнес процессов', 'алгоритмы и структуры данных', 'визуализация данных', 'appsflyer', 'автоматизация процессов управления персоналом', 'java или c++', 'qa', 'data science', 'документирование бизнес-требований', 'ценообразование', 'создание', 'c++', 'google docs', 'nosql', 'впр', 'nlp', 'аналитические способности', 'graphql', 'ux', 'ms sql', 'asana', 'tensorflow', 'контроль и анализ ценообразования', 'scala', 'моделирование бизнес процессов', 'информационная безопасность', 'разработка функциональных требований', 'waterfall', 'a/b тесты', '1с: зарплата и кадры', 'redmine', 'c4', 'разработка', 'проведение тестирований', 'конкурентная аналитика', 'edi', 'saas', 'маркетинг', 'аналитика', 'экономический анализ', 'разработка по', 'моделирование процессов', 'бухгалтерский учет', 'data vault', 'ds', 'проектная документация', '1с программирование', 'rag', 'lightgbm', 'erp-системы на базе 1с', 'scipy', 'веб-программирование', 'обновление конфигурации 1с', 'разработка пользовательской документации', 'автоматизация бизнес-процессов', 'моделирование бизнес-процессов', 'автоматизация процессов', 'abc-анализ', 'crm', '1с: управление предприятием', 'sip-телефония', 'tableau', 'разработка технической документации', 'техническая документация', 'bash', 'pci dss', 'git', 'xgboost', '1с: управление персоналом', 'тестирование', 'альфа-авто', 'маркетплейсы', 'numpy', 'kanban', 'postman', 'grpc', 'аналитика маркетплейсов', 'ar', '1с:erp', 'oracle pl/sql', 'olap', 'ux-исследования', 'visio', 'amplitude', 'web аналитика', 'постановка задач разработчикам', 'проектирование пользовательских интерфейсов', 'эдо', 'базы данных', 'nan', 'market research', 'confluence', 'ms powerpoint', 'as is/to be mapping', 'математический анализ', 'llm', 'ci/cd', 'работа с iot-устройствами', 'apache airflow', '1с: зарплата и управление персоналом', 'smm', 'use case analysis', 'agile', 'складская логистика', 'настройка по', 'atlassian', 'дашборд', 'greenplum', 'битрикс24', 'opencv', 'прогнозирование продаж', 'rest api', 'analyst', 'resnet', 'oracle', 'use case', 'финансовый анализ', 'субд', 'data engineer', 'оптимизация бизнес-процессов', 'разработка регламентов', '1c: финансы', 'разработка инструкций', 'аналитика продаж', 'data scientist', 'css', 'ms visio', 'sklearn', 'apache hive', 'работа с системами аналитики', 'аудит бизнес-процессов', 'er', '1с: унф', 'электронный документооборот', 'ui/ux', 'разработка бизнес-модели', '1c: erp', 'ms office', '1с', 'продуктовая аналитика', 'user flow', 'dax', 'rabbitmq', 'aris', 'miro', 'mvp', 'openapi', 'wms', '1с:ух', 'подготовка презентаций', 'бизнес-моделирование', '1с: управление холдингом', 'camunda', 'u-net', 'deeplab', 'apache kafka', 'wsdl', 'системный анализ', 'mlflow', 'sql', 'развитие продаж', 'экономический аудит', 'анализ целевой аудитории', 'реинжиниринг бизнес-процессов', 'linux', '1с: производство', 'мэк 61131-3', 'docker', 'управленческая отчетность', 'маркетинговый анализ', 'erd', 'google tag manager', 'xml', 'gpt', 'мониторинг рынка', 'figma', 'r', 'java', 'сводные таблицы', 'написание тз', 'use cases', 'регламентация бизнес-процессов', 'seo', 'удаленно', 'бд', 'system analysis', 'продуктовые метрики', 'mes', 'etl', 'внедрение продукта', 'hdfs', 'business analysis', 'php', 'проектирование', 'dwh', 'mysql', 'superset', '1с: управление производственным предприятием', 'функциональное тестирование', '1с: комплексная автоматизация', 'анализ требований', 'hr-аналитика', 'настройка пк', 'deep learning', 'аналитические отчеты', 'hadoop', 'управление продуктом', 'категорийный менеджмент', 'pytorch', 'анализ рынка', 'eepc', 'информационные технологии', 'бизнес-анализ', 'vba', 'notion', 'аналитическое мышление', 'планирование продаж', 'svn', 'html', 'нейронные сети', 'rest', 'scrum', 'spark', 'ии', 'администрирование сетевого оборудования', 'soap', 'отчетов', 'веб-аналитика', 'json api', 'e-commerce', 'многозадачность', 'amocrm', 'ассортиментная матрица', 'техническая поддержка пользователей', 'elk', '1с: бухгалтерия', 'маркетинговое планирование', 'idef0', 'аналитик', 'визуализация', 'ms word', 'анализ данных', '1с: управление торговлей', 'управление бизнес процессами', '1c: бухгалтерия', 'эконометрика', 'babok', 'системный аналитик', 'sla', 'разработка технических заданий', '1c: зарплата и кадры', 'микросервисная архитектура', 'wildberries', 'epc', 'yolo', 'pest-анализ', 'pandas', 'metabase', 'mathcad', 'разработка нефункциональных требований', 'xyz-анализ', 'soa', 'api', 'cистемы управления базами данных', 'бизнес-консультирование', 'plantuml', 'user story', 'http', 'спецификация требований', 'scikit-learn', 'looker studio', '1с: предприятие', 'postgres', 'clickhouse', 'aws', '1с: документооборот', 'анализ финансовых показателей', 'postgresql', 'viewability', 'jira', 'power query', 'яндекс.метрика', 'json', 'airflow', 'ecommerce', 'разработка бизнес-требований', 'openshift', 'schedule_Гибкий график', 'schedule_Сменный график', 'schedule_Удаленная работа', 'employment_Проектная работа', 'employment_Стажировка', 'employment_Частичная занятость', 'experience^3', 'internship_experience', 'has_experience']

# def process_request(
#     user_id: int,
#     name: str,
#     description: str,
#     model_from,
#     model_to,
#     session
# ) -> dict:
#     """
#     Принимает запрос от пользователя, обрабатывает запрос и
#     возвращает результат.
#     """
#     # Приведение запроса в нужный формат
#     request = pd.DataFrame({
#         'Name': [name],
#         'Description': [description]
#     })
#     # Получение предсказания от модели
#     salary_from = model_from.predict(request)
#     salary_to = model_to.predict(request)
#
#     # Конвертация в JSON
#     response = {
#         'salary_from': int(salary_from[0]),
#         'salary_to': int(salary_to[0])
#     }
#
#     # Проверка ответа модели
#     try:
#         SalaryData(**response)
#     except ValidationError:
#         return {'error': 'Model failed'}
#
#     # Сохранение данных запроса в БД
#     request = Request(
#         user_id=user_id,
#         vacancy_name=name,
#         vacancy_description=description,
#         salary_from=response['salary_from'],
#         salary_to=response['salary_to'],
#         timestamp=datetime.now()
#     )
#     log_request(request, session)
#     return response
