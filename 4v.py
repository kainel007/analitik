import streamlit as st
from new_pages import add_data, analyze_data

# Определяем страницы
pages = [
    st.Page(add_data.app, title="Добавление данных", url_path="add_data"),
    st.Page(analyze_data.app, title="Анализ посещений", url_path="analyze_data")
]

# Настроить навигацию
pg = st.navigation(
    {
        "Главная": [pages[0]],  # Главная страница отдельно
        "Данные": [pages[1]]  # Группа с анализом данных
    }
)

# Запуск текущей страницы
if pg:
    pg.run()
