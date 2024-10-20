import streamlit as st
import requests

import pages.elements as elements

# Блок настроек по умолчанию
elements.set_wide()
elements.create_navbar()
cookie_manager = elements.get_manager()
access_token = cookie_manager.get("access_token")
elements.token_check(access_token)

st.title("Новый запрос")




specializations = st.selectbox(
    "Выберите специализацию вашей вакансии",
    ('Дата-сайентист',
    'Бизнес-аналитик',
    'Аналитик',
    'BI-аналитик, аналитик данных',
    'Системный аналитик',
    'Продуктовый аналитик',
    'Маркетолог-аналитик'),
)

experience = st.text_input('Опыт')

employment = st.selectbox(
    "Выберите ваш тип занятости",
    ('Полная',
    'Проектная работа',
    'Стажировка',
    'Частичная занятость'),
)

area = st.text_input('Город')

schedule = st.selectbox(
    "Выберите ваш график",
    ('Удаленная работа',
     'Гибкий график',
     'Полный день',
     'Сменный график',
     'Вахтовый метод')
)

text = st.text_area('Описание вакансии', height=300)

if st.button('Отправить запрос'):
    # Отправка запроса
    response = requests.post(
        'http://app:8080/ml/process_request/',
        params={
            'token': access_token,
            'specializations': specializations,
             'text': text,
             'experience': experience,
             'employment': employment,
             'area': area,
             'schedule': schedule
        }
    )
    response = response.json()
    #salary_from = response['salary_from']
    #salary_to = response['salary_to']

    # Fancy вывод диапазона зарплат
    st.subheader("Предсказание:")

    # Рассчитываем среднюю зарплату
    average_salary = response['salary']

    # Создаем одну колонку
    col1 = st.columns(1)  # Вернет список с одной колонкой

    with col1[0]:  # Используем первый элемент списка колонок
        st.metric(
            "Зарплата",
            f"{average_salary // 1000 * 1000:,.0f} руб."
        )



