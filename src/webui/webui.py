import streamlit as st
import requests

import pages.elements as elements

# Блок настроек по умолчанию
elements.set_wide()
elements.create_navbar()
cookie_manager = elements.get_manager()
access_token = cookie_manager.get("access_token")

st.title("DataScienceExplorer")

overview_col, tabs_col = st.columns(2)

# Колонка с описанием
with overview_col:
    st.write('## Описание')
    st.write("""
    С помощью модели машинного обучения, обученной на данных по вакансиям Data Science специалистов, сервис позволяет получить предсказание зарплаты, исходя из резюме.
    """)
    st.write('## Сценарии использования')
    st.write("""
    1) **HR и рекрутинг**: HR-специалисты могут анализировать сервис для составления резюме, релевантному рынку. 
    2) **Исследование рынка труда**: Аналитики могут использовать сервис для выявления закономерность и трендов изменения рынка.
    3) **Использование для проверки своего резюме**: специалисты данной области могут проверить свое резюме и получить обратную связь относительно рынка.
    """)

# Колонка со входом и регистрацией
with tabs_col:
    login, register = st.tabs(["Вход", "Регистрация"])

# Вкладка входа
with login:
    email = st.text_input("E-mail", key="email")
    password = st.text_input("Пароль", type="password", key="password")

    if st.button("Войти", type="primary", key="signin"):
        response = requests.post('http://app:8080/user/signin',
                                 params={'email': email,
                                         'password': password})
        if response.status_code in [401, 404]:
            error_desc = response.json()["detail"]
            st.error("""Пароль или e-mail введены неверно или
                     аккаунт с таким e-mail не существует""")
        else:
            token = response.json()["access_token"]
            cookie_manager.set('access_token', token)
    if access_token is not None:
        st.success('Вы вошли!', icon="✅")
        if st.button("Перейти к описанию сервиса"):
            st.switch_page("pages/description.py")

# Вкладка регистрации
with register:
    username = st.text_input("Имя пользователя")
    email = st.text_input("E-mail")
    password = st.text_input("Пароль", type="password")

    if st.button("Зарегистрироваться", type="primary", key="sign_up"):
        response = requests.post('http://app:8080/user/signup',
                                 params={'username': username,
                                         'password': password,
                                         'email': email})
        if response.status_code == 200:
            message = response.json()
            st.success('Регистрация успешна!', icon="✅")
        else:
            message = response.json()
            st.error(message['detail'], icon="🚨")
