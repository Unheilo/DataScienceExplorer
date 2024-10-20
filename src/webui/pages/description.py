import streamlit as st

import pages.elements as elements

# Блок настроек по умолчанию
elements.set_wide()
elements.create_navbar()
cookie_manager = elements.get_manager()
access_token = cookie_manager.get("access_token")
elements.token_check(access_token)

st.title("Как использовать сервис")

# Описание сервиса
st.write("""
### 1. **Новый запрос**:
- Перейдите на страницу "Создать" в боковом меню.
- Введите необходимые поля.
- Нажмите кнопку "Отправить запрос".
- Получите прогноз заработной платы для данной позиции.
""")

st.write("""

### 2. **История запросов**:
- Перейдите на страницу "История запросов" в боковом меню.
- Просмотрите все ваши предыдущие запросы и их результаты.

### 3. **Выход из аккаунта**:
- Используйте кнопку "Выйти из аккаунта" на этой странице для завершения
  сессии.
""")

# Кнопка выхода из аккаунта
if st.button("Выйти из аккаунта", use_container_width=True):
    cookie_manager.delete("access_token")