import streamlit as st
import extra_streamlit_components as stx
import requests


def create_navbar():
    """Создание навигационной панели."""
    with st.sidebar:
        st.page_link('webui.py', label='Главная')
        st.page_link('pages/description.py', label='Описание')
        st.page_link('pages/ml.py', label='Создать запрос')
        st.page_link('pages/history_req.py', label='История')


@st.cache_resource(experimental_allow_widgets=True)
def get_manager():
    """
    Функция, возвращающая объект CookieManager.

    Сохраняет результат выполнения функции и ее состояние в кеше.

    Returns:
        CookieManager: Объект для управления куки.
    """
    return stx.CookieManager()


def set_wide():
    """Установка ширины страницы."""
    st.set_page_config(layout="wide")


def token_check(token):
    """
    Выполняет проверку токена.

    Если токен невалидный, то блокирует доступ к содержимому страницы.

    Args:
        token (str): Токен для проверки.

    Returns:
        None
    """
    response = requests.get(f'http://app:8080/user/auth/{token}')
    if response.status_code == 200:
        return

    st.error('Вы не авторизованы')
    if st.button('Войти', use_container_width=True):
        st.switch_page("webui.py")
    st.stop()
