import streamlit as st
import pandas as pd
import requests

import pages.elements as elements

# Блок настроек по умолчанию
elements.set_wide()
elements.create_navbar()
cookie_manager = elements.get_manager()
access_token = cookie_manager.get("access_token")
elements.token_check(access_token)

st.title("История запросов")

# Запрос API и вывод результатов в виде таблицы
response = requests.get(f'http://app:8080/user/get_history/{access_token}')

# Проверка на пустую историю
if not response.json():
    st.write('Нет истории запросов')
    st.stop()

response_df_detail = pd.DataFrame(response.json())

columns_names = {
    'request_id': 'ID запроса',
    'vacancy_name': 'Название вакансии',
    'vacancy_description': 'Описание вакансии',
    'salary_from': 'Зарплата',
    'timestamp': 'Время'
}

response_df_detail = response_df_detail.rename(columns=columns_names)

st.dataframe(response_df_detail)
